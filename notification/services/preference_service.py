from typing import List
from django.core.exceptions import ObjectDoesNotExist
from user.models import User
from ..models import NotificationCategory, NotificationPreference


class PreferenceServiceError(Exception):
    """Base exception for all preference service errors."""
    pass


class PreferenceService:
    """
    Service responsible for checking and managing user notification preferences.
    """

    @classmethod
    def clear_cache(cls, user_id: int) -> None:
        """Clear any cached preference state for a user. The current implementation is a no-op."""
        return None

    @classmethod
    def get_enabled_channels(cls, user: User, category: NotificationCategory) -> List[str]:
        """
        Determines which delivery channels are enabled for a user and a given notification category.

        Args:
            user (User): The user recipient.
            category (NotificationCategory): The notification category.

        Returns:
            List[str]: A list of enabled channel codes (e.g., ['in_app', 'email', 'push']).
        """
        if not user or not user.is_active:
            return []

        try:
            # Select related/prefetch to avoid extra queries if pre-loaded
            preference = NotificationPreference.objects.prefetch_related('enabled_categories').get(user=user)
        except ObjectDoesNotExist:
            # Default preferences if none are set for the user (opt-in by default for basic channels)
            return ['in_app', 'email']

        # Check category preferences (if user configured specific categories, they must opt-in to this category)
        # Note: If no categories are configured, assume all are enabled by default (standard opt-out model)
        # If there are configured categories, the requested category must be present.
        if preference.enabled_categories.exists():
            if not preference.enabled_categories.filter(id=category.id).exists():
                return []  # Category not enabled, send nothing

        enabled_channels = []
        if preference.in_app:
            enabled_channels.append('in_app')
        if preference.email:
            enabled_channels.append('email')

        # Future extensions like push/sms can be appended here once added to DB fields
        # Note: push and sms fields were commented out in models.py, but channels can be mapped here:
        # e.g., if getattr(preference, 'push', True): enabled_channels.append('push')

        return enabled_channels
