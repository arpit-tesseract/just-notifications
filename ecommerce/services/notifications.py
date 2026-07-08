"""
Thin wrapper over the notification module's public API (`trigger_event`).

`trigger_event` hands work to Celery and never raises, but we still guard every call so
a broker outage or a missing template can never break the order flow. Template names use
the ``ecommerce.*`` namespace and are seeded by ``manage.py seed_ecommerce``.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _enabled():
    # Lets a broker-less environment (or tests) turn dispatch off so order APIs never block.
    return getattr(settings, 'ECOMMERCE_NOTIFICATIONS_ENABLED', True)


def notify(template_name, user, context=None):
    """Send one notification to a single user (no-op if user is falsy or disabled)."""
    if not _enabled():
        return
    user_id = getattr(user, 'id', None)
    if not user_id:
        return
    try:
        from notification.services import trigger_event
        trigger_event(template_name, user_id, context or {})
    except Exception:  # pragma: no cover - defensive; trigger_event already swallows
        logger.exception("ecommerce.notify failed for %s / user %s", template_name, user_id)


def notify_business_members(template_name, business_family, context=None):
    """Notify every active employee of a business (e.g. a vendor's team)."""
    if not _enabled() or not business_family:
        return
    from user.models import BusinessFamilyMember
    user_ids = list(
        BusinessFamilyMember.objects
        .filter(business_family=business_family, is_active=True)
        .values_list('user_id', flat=True)
    )
    if not user_ids:
        return
    try:
        from notification.services import trigger_event
        for uid in user_ids:
            trigger_event(template_name, uid, context or {})
    except Exception:  # pragma: no cover
        logger.exception("ecommerce.notify_business_members failed for %s", template_name)


def notify_area_admins(template_name, area_node, context=None):
    """Notify Shashan admins responsible for an area node (the routing queue owners)."""
    if not _enabled() or not area_node:
        return
    from user.models import AdminResidentialNodeAssignment
    user_ids = list(
        AdminResidentialNodeAssignment.objects
        .filter(node=area_node, is_active=True)
        .values_list('user_id', flat=True)
        .distinct()
    )
    if not user_ids:
        return
    try:
        from notification.services import trigger_event
        for uid in user_ids:
            trigger_event(template_name, uid, context or {})
    except Exception:  # pragma: no cover
        logger.exception("ecommerce.notify_area_admins failed for %s", template_name)
