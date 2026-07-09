"""
notification/tasks.py
======================
Phase 2 — Fan-Out & Celery Setup.

This module owns *all* Celery tasks for the notification pipeline.  There are
two tiers of tasks:

Tier 1 — Orchestration
    ``process_event_task``:  Resolves the correct ``NotificationTemplate``,
    creates ``NotificationRecipient`` rows, and fans out to Tier-2 delivery
    tasks based on the user's channel preferences.

Tier 2 — Delivery (one task per channel)
    ``send_email_task``, ``send_websocket_task``, ``send_sms_task``:
    Each task calls the appropriate channel dispatcher in
    ``notification.services.channels`` and retries up to 3 times on failure.

Pipeline position
-----------------
    trigger_event()  ──► [queue] ──► process_event_task
                                           │
                          ┌────────────────┼──────────────────┐
                          ▼                ▼                   ▼
                  send_email_task  send_websocket_task  send_sms_task
                          │                │                   │
                          ▼                ▼                   ▼
                    channels.py      channels.py          channels.py
"""

from __future__ import annotations

import logging
from typing import Any

from celery import shared_task
from django.contrib.auth import get_user_model

from notification.models import (
    Notification,
    NotificationChannel,
    NotificationRecipient,
    NotificationRecipientStatus,
    NotificationStatus,
    NotificationTemplate,
    NotificationStatusLog,
    
)
import uuid
from django.db import transaction

logger = logging.getLogger(__name__)

User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# User channel preferences have been removed as per user request.
# Channels will be fetched directly from the NotificationTemplate.


# ---------------------------------------------------------------------------
# Tier 1 — Orchestration task
# ---------------------------------------------------------------------------

@shared_task(name="notification.process_event_task", bind=True)
def process_event_task(
    self: Any,
    template_name: str,
    user_id: int,
    context_data: dict[str, Any],
) -> dict[str, Any]:
    """Orchestrate the full notification pipeline for a single event.

    This task is the hub of the fan-out pattern.  It performs three actions:

    1. Resolves the ``NotificationTemplate`` by its ``name``.
    2. Renders the template title/content and persists a ``Notification`` +
       ``NotificationRecipient`` row for every active channel the user has
       enabled.
    3. Dispatches a Tier-2 Celery task for each channel so that slow I/O
       (SMTP, SMS API, WebSocket push) never blocks this orchestrator.

    Parameters
    ----------
    template_name:
        The name of the template to use.
    user_id:
        Primary key of the target ``User``.
    context_data:
        Template interpolation variables.

    Returns
    -------
    dict
        A summary dict ``{"notification_id": int, "channels_dispatched": list}``
        suitable for Celery result inspection.
    """
    from notification.services.renderers import EmailRenderer, PushRenderer  # noqa: PLC0415

    logger.info(
        "process_event_task: processing template_name=%r for user_id=%d",
        template_name,
        user_id,
    )

    # ── 1. Resolve template ──────────────────────────────────────────────────
    try:
        template: NotificationTemplate = NotificationTemplate.objects.select_related(
            "category"
        ).get(name=template_name, is_active=True)
    except NotificationTemplate.DoesNotExist:
        logger.warning(
            "process_event_task: no active template for template_name=%r; aborting.",
            template_name,
        )
        return {"notification_id": None, "channels_dispatched": []}

# ── 2. Render title & separate contents ──────────────────────────────────
    email_renderer = EmailRenderer()
    push_renderer = PushRenderer()
    
    # We can use push_renderer for the title as it's just plain text
    rendered_title: str = push_renderer.render(template.title, context_data)
    
    # Render Push/In-App/SMS Content (Always uses the database text field)
    push_rendered_content: str = push_renderer.render(template.content, context_data)

    # Render Email Content (Uses templatefile if available, otherwise fallback to database)
    raw_email_content = template.content
    if NotificationChannel.EMAIL in template.channels and template.templatefile:
        try:
            with template.templatefile.open('r') as f:
                raw_email_content = f.read()
                if isinstance(raw_email_content, bytes):
                    raw_email_content = raw_email_content.decode('utf-8')
        except Exception as e:
            logger.error(f"process_event_task: Failed to read templatefile for {template_name}: {e}")
            
    email_rendered_content: str = email_renderer.render(raw_email_content, context_data)

    # ── 3. Persist Notification record ──────────────────────────────────────
    # Save the push content to the DB for history (so your frontend doesn't load massive HTML),
    # unless it's strictly an email-only notification.
    db_content = push_rendered_content if template.content else email_rendered_content
    
    notification: Notification = Notification.objects.create(
        template=template,
        title=rendered_title,
        content=db_content,
        icon=template.icon,
        icon_color=template.icon_color,
        context_data=context_data,
        channels=template.channels,
        status=NotificationStatus.INITIATED,
    )
    
    NotificationStatusLog.objects.create(
        notification=notification,
        status=NotificationStatus.INITIATED,
    )

    logger.info(
        "process_event_task: created Notification pk=%d for template_name=%r",
        notification.pk,
        template_name,
    )

    # ── 4. Fan-out per channel ────────────────────────────────────────────────
    active_channels: list[str] = template.channels or []
    dispatched: list[str] = []

    for channel in active_channels:
        recipient: NotificationRecipient = NotificationRecipient.objects.create(
            notification=notification,
            user_id=user_id,
            channel=channel,
            status=NotificationRecipientStatus.UNREAD,
        )

        # CHOOSE THE CORRECT CONTENT BASED ON THE CHANNEL
        channel_content = email_rendered_content if channel == NotificationChannel.EMAIL else push_rendered_content

        payload: dict[str, Any] = {
            "notification_id": notification.pk,
            "recipient_id": recipient.pk,
            "title": rendered_title,
            "content": channel_content, 
            "icon": template.icon,
            "icon_color": template.icon_color,
            "context_data": context_data,
        }

        if channel == NotificationChannel.EMAIL:
            send_email_task.delay(user_id=user_id, payload=payload)
        elif channel == NotificationChannel.IN_APP:
            send_websocket_task.delay(user_id=user_id, payload=payload)
        elif channel == NotificationChannel.SMS:
            send_sms_task.delay(user_id=user_id, payload=payload)

        dispatched.append(channel)
        logger.info(
            "process_event_task: dispatched channel=%r for recipient_id=%d",
            channel,
            recipient.pk,
        )

    # ── 5. Mark Notification as SENT if at least one channel was dispatched ─
    if dispatched:
        Notification.objects.filter(pk=notification.pk).update(
            status=NotificationStatus.SENT
        )
        NotificationStatusLog.objects.create(
            notification=notification,
            status=NotificationStatus.SENT,
        )

    return {"notification_id": notification.pk, "channels_dispatched": dispatched}


@shared_task(name="notification.bulk_process_event_task", bind=True)
def bulk_process_event_task(
    self: Any,
    template_name: str,
    user_ids: list[int],
    context_data: dict[str, Any],
    idempotency_key: str, 
) -> dict[str, Any]:
    """Orchestrate bulk notifications with idempotency and atomic transactions."""
    from notification.services.renderers import EmailRenderer, PushRenderer
    
    logger.info(f"bulk_process_event_task: starting template_name={template_name} with key {idempotency_key}")

    # 1. Idempotency Check
    if Notification.objects.filter(idempotency_key=idempotency_key).exists():
        logger.warning(f"bulk_process_event_task: key {idempotency_key} already processed. Skipping.")
        return {"status": "skipped", "reason": "already_processed"}

    # 2. Resolve template
    try:
        template = NotificationTemplate.objects.get(name=template_name, is_active=True)
    except NotificationTemplate.DoesNotExist:
        logger.warning(f"bulk_process_event_task: no active template for template_name={template_name}")
        return {"status": "failed", "reason": "template_missing"}

    renderer = EmailRenderer() if NotificationChannel.EMAIL in template.channels else PushRenderer()
    rendered_title = renderer.render(template.title, context_data)

    # loading html content
    raw_content = template.content
    if NotificationChannel.EMAIL in template.channels and template.templatefile:
        try:
            template.templatefile.open('r')
            raw_content = template.templatefile.read()
            if isinstance(raw_content, bytes):
                raw_content = raw_content.decode('utf-8')
            template.templatefile.close()
        except Exception as e:
            logger.error(f"bulk_process_event_task: Failed to read templatefile for {template_name}: {e}")

    rendered_content = renderer.render(raw_content, context_data)

    dispatched = []

    try:
        # 3. ATOMIC BLOCK: Ensure all DB writes succeed, or none do.
        with transaction.atomic():
            notification = Notification.objects.create(
                template=template,
                title=rendered_title,
                content=rendered_content,
                icon=template.icon,
                icon_color=template.icon_color,
                context_data=context_data,
                channels=template.channels,
                status=NotificationStatus.INITIATED,
                idempotency_key=idempotency_key 
            )

            NotificationStatusLog.objects.create(
                notification=notification,
                status=NotificationStatus.INITIATED,
            )

            recipients_to_create = []
            for uid in user_ids:
                for channel in template.channels:
                    recipients_to_create.append(
                        NotificationRecipient(
                            notification=notification,
                            user_id=uid,
                            channel=channel,
                            status=NotificationRecipientStatus.UNREAD,
                        )
                    )
            
            created_recipients = NotificationRecipient.objects.bulk_create(recipients_to_create)

        # 4. Dispatch Tier 2 tasks (Outside the atomic block)
        for recipient in created_recipients:
            payload = {
                "notification_id": notification.pk,
                "recipient_id": recipient.pk,
                "title": rendered_title,
                "content": rendered_content,
                "icon": template.icon,
                "icon_color": template.icon_color,
                "context_data": context_data,
            }

            if recipient.channel == NotificationChannel.EMAIL:
                send_email_task.delay(user_id=recipient.user_id, payload=payload)
            elif recipient.channel == NotificationChannel.IN_APP:
                send_websocket_task.delay(user_id=recipient.user_id, payload=payload)
            elif recipient.channel == NotificationChannel.SMS:
                send_sms_task.delay(user_id=recipient.user_id, payload=payload)
            
            if recipient.channel not in dispatched:
                dispatched.append(recipient.channel)

        notification.status = NotificationStatus.SENT
        notification.save(update_fields=['status'])
        
        NotificationStatusLog.objects.create(
            notification=notification,
            status=NotificationStatus.SENT,
        )

        return {"notification_id": notification.pk, "channels_dispatched": dispatched}

    except Exception as e:
        logger.error(f"bulk_process_event_task: failed for key {idempotency_key}: {e}")
        # Re-queue the task; since DB rolls back, no duplicate records will exist
        raise self.retry(exc=e, countdown=60)

# ---------------------------------------------------------------------------
# Tier 2 — Delivery tasks
# ---------------------------------------------------------------------------

@shared_task(
    name="notification.send_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,  # seconds
)
def send_email_task(
    self: Any,
    user_id: int,
    payload: dict[str, Any],
) -> None:
    """Deliver a notification via email.

    Fetches the user's email address, builds the message with
    ``EmailChannelDispatcher``, and calls ``.send()``.  Retries up to 3 times
    with a 30-second back-off on any transient failure.

    Parameters
    ----------
    user_id:
        PK of the target user; used to look up the email address.
    payload:
        Dict produced by ``process_event_task`` containing at minimum
        ``title``, ``content``, and ``recipient_id``.
    """
    from notification.services.channels import EmailChannelDispatcher  # noqa: PLC0415

    try:
        user = User.objects.get(pk=user_id)
        dispatcher = EmailChannelDispatcher()
        dispatcher.send(
            to_address=user.email,
            subject=payload["title"],
            body=payload["content"],
        )
        _mark_recipient_delivered(payload["recipient_id"])
        logger.info("send_email_task: delivered to user_id=%d", user_id)
    except Exception as exc:
        logger.warning(
            "send_email_task: attempt %d failed for user_id=%d: %s",
            self.request.retries + 1,
            user_id,
            exc,
        )
        _mark_recipient_failed(payload["recipient_id"])
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@shared_task(
    name="notification.send_websocket_task",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def send_websocket_task(
    self: Any,
    user_id: int,
    payload: dict[str, Any],
) -> None:
    """Deliver a real-time in-app notification via Django Channels WebSocket.

    Calls ``dispatch_websocket_alert`` which uses ``async_to_sync`` to push
    a message to the user's personal channel group.

    Parameters
    ----------
    user_id:
        PK of the target user; determines the channel group name.
    payload:
        Dict produced by ``process_event_task``.
    """
    from notification.services.channels import dispatch_websocket_alert  # noqa: PLC0415

    try:
        dispatch_websocket_alert(user_id=user_id, payload=payload)
        _mark_recipient_delivered(payload["recipient_id"])
        logger.info("send_websocket_task: pushed to user_id=%d", user_id)
    except Exception as exc:
        logger.warning(
            "send_websocket_task: attempt %d failed for user_id=%d: %s",
            self.request.retries + 1,
            user_id,
            exc,
        )
        _mark_recipient_failed(payload["recipient_id"])
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))


@shared_task(
    name="notification.send_sms_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_sms_task(
    self: Any,
    user_id: int,
    payload: dict[str, Any],
) -> None:
    """Deliver a notification via SMS.

    Uses ``SMSChannelDispatcher`` which wraps whatever SMS gateway is
    configured in ``settings.SMS_API_KEY``.  Retries up to 3 times with
    exponential back-off (60 s, 120 s, 240 s).

    Parameters
    ----------
    user_id:
        PK of the target user; used to look up the phone number.
    payload:
        Dict produced by ``process_event_task``.
    """
    from notification.services.channels import SMSChannelDispatcher  # noqa: PLC0415

    try:
        user = User.objects.get(pk=user_id)
        phone: str = getattr(user, "phone_number", "") or ""
        if not phone:
            logger.warning(
                "send_sms_task: user_id=%d has no phone_number; skipping.", user_id
            )
            return

        dispatcher = SMSChannelDispatcher()
        dispatcher.send(to_number=phone, body=payload["content"])
        _mark_recipient_delivered(payload["recipient_id"])
        logger.info("send_sms_task: delivered to user_id=%d", user_id)
    except Exception as exc:
        logger.warning(
            "send_sms_task: attempt %d failed for user_id=%d: %s",
            self.request.retries + 1,
            user_id,
            exc,
        )
        _mark_recipient_failed(payload["recipient_id"])
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# ---------------------------------------------------------------------------
# Private helpers shared across Tier-2 tasks
# ---------------------------------------------------------------------------

def _mark_recipient_delivered(recipient_id: int) -> None:
    """Set delivery_status=DELIVERED on a ``NotificationRecipient`` row."""
    NotificationRecipient.objects.filter(pk=recipient_id).update(
        delivery_status=NotificationStatus.SENT
    )

    try:
        notification_recipient_obj = NotificationRecipient.objects.get(pk=recipient_id)
    except NotificationRecipient.DoesNotExist:
        return


def _mark_recipient_failed(recipient_id: int) -> None:
    """Set delivery_status=FAILED on a ``NotificationRecipient`` row."""
    NotificationRecipient.objects.filter(pk=recipient_id).update(
        delivery_status=NotificationStatus.FAILED
    )

    try:
        notification_recipient_obj = NotificationRecipient.objects.get(pk=recipient_id)
    except NotificationRecipient.DoesNotExist:
        return

