"""
notification/services/channels.py
===================================
Phase 4 — Channel Dispatchers.

This module provides one dispatcher per notification channel:

* :class:`EmailChannelDispatcher`     — wraps an SMTP / transactional-email API.
* :class:`SMSChannelDispatcher`       — wraps an SMS gateway API (e.g. Twilio).
* :func:`dispatch_websocket_alert`    — pushes real-time messages via Django Channels.

Design decisions
----------------
* **Class-based (Email / SMS)**: Accepting API keys in ``__init__`` makes
  each dispatcher trivially unit-testable — pass dummy keys in tests without
  monkey-patching ``settings``.
* **Function-based (WebSocket)**: WebSocket delivery is stateless; a plain
  function is the simplest correct abstraction.  Django Channels'
  ``get_channel_layer()`` is already a module-level singleton.
* **Dummy `.send()` implementations**: The ``print`` + ``logger`` approach
  means local development works without any 3rd-party API credentials while
  still exercising the full code path.

Pipeline position
-----------------
    send_email_task       ──► EmailChannelDispatcher.send()
    send_sms_task         ──► SMSChannelDispatcher.send()
    send_websocket_task   ──► dispatch_websocket_alert()
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

class EmailChannelDispatcher:
    """Wraps a transactional-email API (e.g. SendGrid, Mailgun, AWS SES).

    In production, replace the body of :meth:`send` with the SDK call for
    your chosen provider.  The constructor accepts an explicit ``api_key``
    parameter so that tests can inject a fake key without touching
    ``settings``.

    Attributes
    ----------
    api_key : str
        The API key used to authenticate with the email provider.  Falls back
        to ``settings.EMAIL_HOST_PASSWORD`` if not supplied explicitly.
    sender : str
        The "From" address.  Falls back to ``settings.DEFAULT_FROM_EMAIL``.

    Example
    -------
    >>> dispatcher = EmailChannelDispatcher()
    >>> dispatcher.send(
    ...     to_address="alice@example.com",
    ...     subject="Your invoice is ready",
    ...     body="Dear Alice, ...",
    ... )
    """

    def __init__(
        self,
        api_key: str | None = None,
        sender: str | None = None,
    ) -> None:
        """Initialise the dispatcher.

        Parameters
        ----------
        api_key:
            Explicit API key.  If ``None``, falls back to
            ``settings.EMAIL_HOST_PASSWORD`` (a reasonable stand-in until a
            dedicated transactional-email setting is added).
        sender:
            Explicit "From" address.  If ``None``, falls back to
            ``settings.DEFAULT_FROM_EMAIL``.
        """
        self.api_key: str = api_key or getattr(settings, "EMAIL_HOST_PASSWORD", "")
        self.sender: str = sender or getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")

    def send(self, to_address: str, subject: str, body: str) -> None:
        """Dispatch an email to ``to_address``.

        Parameters
        ----------
        to_address:
            Recipient's email address.
        subject:
            Email subject line (rendered by :class:`~renderers.EmailRenderer`).
        body:
            Email body content (rendered by :class:`~renderers.EmailRenderer`).

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            Re-raised from the underlying API client on non-retryable failures.
            Transient errors are left as bare exceptions so Celery's retry
            mechanism in ``send_email_task`` can handle them.

        Notes
        -----
        *Dummy implementation*: Logs and prints the outgoing message.
        Replace with real SDK calls (e.g. ``sendgrid.SendGridAPIClient``) in
        production.
        """
        logger.info(
            "EmailChannelDispatcher.send: FROM=%r TO=%r SUBJECT=%r",
            self.sender,
            to_address,
            subject,
        )

        try:
            send_mail(
                subject=subject,
                message=body,           # Plain text fallback
                from_email=self.sender,
                recipient_list=[to_address],
                fail_silently=False,    # Let it fail so Celery can catch & retry it
                html_message=body       # (Optional) If your templates use HTML
            )
            logger.info(
                "EmailChannelDispatcher.send: Successfully sent email to %s with subject %r",
                to_address,
                subject,
            )
        except Exception as exc:
            logger.error(
                "EmailChannelDispatcher.send: Failed to send email to %s with subject %r. Error: %s",
                to_address,
                subject,
                exc,
            )
            raise
        # ────────────────────────────────────────────────────────────────────


# ---------------------------------------------------------------------------
# SMS
# ---------------------------------------------------------------------------

class SMSChannelDispatcher:
    """Wraps an SMS gateway API (e.g. Twilio, Kaleyra, MSG91).

    Parameters
    ----------
    api_key:
        Explicit API key.  Falls back to ``settings.SMS_API_KEY`` if not
        supplied.
    sender_id:
        Alphanumeric sender ID or phone number shown to the recipient.  Falls
        back to ``settings.SMS_SENDER_ID``.

    Example
    -------
    >>> dispatcher = SMSChannelDispatcher()
    >>> dispatcher.send(to_number="+919876543210", body="Your OTP is 123456")
    """

    def __init__(
        self,
        api_key: str | None = None,
        sender_id: str | None = None,
    ) -> None:
        """Initialise the SMS dispatcher.

        Parameters
        ----------
        api_key:
            Explicit API key.  Falls back to ``settings.SMS_API_KEY``.
        sender_id:
            Sender ID shown to the recipient.  Falls back to
            ``settings.SMS_SENDER_ID``.
        """
        self.api_key: str = api_key or getattr(settings, "SMS_API_KEY", "")
        self.sender_id: str = sender_id or getattr(settings, "SMS_SENDER_ID", "NOTIFY")

    def send(self, to_number: str, body: str) -> None:
        """Dispatch an SMS to ``to_number``.

        Parameters
        ----------
        to_number:
            Recipient's phone number in E.164 format (e.g. ``"+919876543210"``).
        body:
            Message text.  Should be ≤ 160 characters for single-part SMS.

        Returns
        -------
        None

        Raises
        ------
        Exception
            Any exception from the underlying SMS SDK.  The Celery task
            ``send_sms_task`` handles retries.

        Notes
        -----
        *Dummy implementation*: Logs and prints.  Replace with a real gateway
        SDK call (e.g. ``twilio.rest.Client``) in production.
        """
        logger.info(
            "SMSChannelDispatcher.send: sender_id=%r TO=%r",
            self.sender_id,
            to_number,
        )
        # ── Replace the block below with your real SMS SDK call ──────────────
        print(
            f"[SMS] From: {self.sender_id} | To: {to_number} | "
            f"Body: {body[:160]}{'...' if len(body) > 160 else ''}"
        )
        # ────────────────────────────────────────────────────────────────────


# ---------------------------------------------------------------------------
# WebSocket / In-App (Django Channels)
# ---------------------------------------------------------------------------

def dispatch_websocket_alert(user_id: int, payload: dict[str, Any]) -> None:
    """Push a real-time notification to a connected WebSocket client.

    Uses Django Channels' ``get_channel_layer()`` to send a message to the
    group ``"user_notifications_{user_id}"``.  Any consumer subscribed to
    that group (typically the user's browser tab) will receive the event
    immediately.

    The function bridges the sync Celery world into the async Channels world
    via ``async_to_sync`` — no ``asyncio`` event loop management is needed by
    the caller.

    Parameters
    ----------
    user_id:
        PK of the target user.  Used to construct the channel group name.
    payload:
        JSON-serialisable dict forwarded verbatim to the WebSocket consumer.
        The consumer should handle messages of type ``"notification.alert"``.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        Raised if no channel layer is configured (i.e.
        ``settings.CHANNEL_LAYERS`` is missing or empty).  The Celery task
        ``send_websocket_task`` handles retries.

    Notes
    -----
    Group name convention: ``"user_notifications_{user_id}"``

    The WebSocket consumer on the frontend should include the following
    handler::

        async def notification_alert(self, event):
            await self.send(text_data=json.dumps(event["data"]))

    Example
    -------
    >>> dispatch_websocket_alert(
    ...     user_id=42,
    ...     payload={"title": "New invoice", "content": "Your invoice is ready."},
    ... )
    """
    from channels.layers import get_channel_layer  # noqa: PLC0415
    from asgiref.sync import async_to_sync  # noqa: PLC0415

    channel_layer = get_channel_layer()

    if channel_layer is None:
        raise RuntimeError(
            "dispatch_websocket_alert: no channel layer configured. "
            "Ensure CHANNEL_LAYERS is set in settings.py."
        )

    group_name: str = f"user_notifications_{user_id}"

    message: dict[str, Any] = {
        "type": "notification.alert",  # maps to consumer method `notification_alert`
        "data": payload,
    }

    logger.info(
        "dispatch_websocket_alert: sending to group=%r payload_keys=%s",
        group_name,
        list(payload.keys()),
    )

    async_to_sync(channel_layer.group_send)(group_name, message)

    logger.info(
        "dispatch_websocket_alert: successfully sent to group=%r", group_name
    )
