"""
notification/services/dispatcher.py
====================================
Phase 1 — The Trigger.

This module is the *only* public entry-point for the notification pipeline.
Business logic elsewhere in the codebase should call ``trigger_event`` and
nothing else.  The function is intentionally kept thin: its sole
responsibility is to hand work off to Celery so the HTTP response cycle is
never blocked.

Pipeline position
-----------------
    caller ──► trigger_event()  ──► [Celery queue]
                   (this file)            │
                                          ▼
                              process_event_task   (tasks.py)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def trigger_event(
    event_type: str,
    user_id: int,
    context_data: dict[str, Any],
) -> None:
    """Fire a notification event and hand it off to the Celery worker.

    This function is deliberately side-effect-free from the caller's
    perspective: it never touches the database directly and never blocks on
    I/O.  All heavy work is deferred to ``process_event_task``.

    Parameters
    ----------
    event_type:
        A dot-separated string that identifies the business event, e.g.
        ``"subscription.renewed"`` or ``"invoice.overdue"``.  This value is
        used by ``process_event_task`` to look up the matching
        ``NotificationTemplate`` (via its ``NotificationCategory.name``).
    user_id:
        Primary key of the ``User`` who triggered (or is the target of) the
        event.
    context_data:
        Arbitrary JSON-serialisable key/value pairs that will be interpolated
        into the notification template, e.g. ``{"plan_name": "Pro", "amount":
        "₹999"}``.

    Returns
    -------
    None
        The return value is intentionally ``None``; callers must not depend on
        any result from this function.

    Raises
    ------
    Does not raise.  Any Celery broker connectivity errors are swallowed and
    logged at ERROR level so that a broker outage never bubbles up to the
    end-user HTTP response.

    Examples
    --------
    >>> from notification.services import trigger_event
    >>> trigger_event(
    ...     event_type="subscription.renewed",
    ...     user_id=42,
    ...     context_data={"plan_name": "Pro", "next_billing_date": "2026-06-27"},
    ... )
    """
    # Import here to avoid circular imports at module load time (tasks.py
    # imports from services/, so a top-level import would form a cycle).
    from notification.tasks import process_event_task  # noqa: PLC0415

    try:
        process_event_task.delay(
            event_type=event_type,
            user_id=user_id,
            context_data=context_data,
        )
        logger.info(
            "trigger_event: queued event_type=%r for user_id=%d",
            event_type,
            user_id,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "trigger_event: failed to enqueue event_type=%r for user_id=%d",
            event_type,
            user_id,
        )
