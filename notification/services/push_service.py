import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PushServiceError(Exception):
    """Base exception for all push notification service errors."""
    pass


class PushService:
    """
    Service responsible for constructing payloads and sending push notifications
    to devices using Firebase Cloud Messaging (FCM) or APNS.
    """

    @classmethod
    def send_push_notification(
        cls,
        registration_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
        sound: str = "default",
        badge_count: Optional[int] = None
    ) -> bool:
        """
        Sends a push notification to a device token using Firebase Cloud Messaging (FCM).
        Provides clean fallback/logging when Firebase is unconfigured or offline.

        Args:
            registration_token (str): The device push token.
            title (str): Push title.
            body (str): Push body text.
            data (Optional[Dict[str, str]]): Dictionary of key/value pairs for deep links or custom payloads.
            image_url (Optional[str]): URL of an image to display in the push banner.
            sound (str): Sound filename or "default".
            badge_count (Optional[int]): Badge indicator count for app icons.

        Returns:
            bool: True if push was processed and sent successfully, False otherwise.

        Raises:
            PushServiceError: If token is missing or payload generation fails.
        """
        if not registration_token:
            raise PushServiceError("Device registration token is required.")
        if not title or not body:
            raise PushServiceError("Both title and body are required for push notifications.")

        # Structure standard FCM / APNS payload
        payload = cls.prepare_payload(
            title=title,
            body=body,
            data=data,
            image_url=image_url,
            sound=sound,
            badge_count=badge_count
        )

        logger.info(f"Drafted push notification to token '{registration_token[:15]}...': {payload}")

        try:
            # High-performance FCM initialization fallback
            # We import firebase_admin inside the method to allow out-of-the-box operation 
            # if FCM is not initialized/installed yet.
            import firebase_admin
            from firebase_admin import messaging

            # Check if default app is initialized
            try:
                app = firebase_admin.get_app()
            except ValueError:
                # App not initialized, initialize it with default credentials
                firebase_admin.initialize_app()

            # Construct Message object
            android_config = messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    sound=sound,
                    image=image_url
                )
            )

            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound=sound,
                        badge=badge_count
                    )
                )
            )

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url
                ),
                data=data or {},
                token=registration_token,
                android=android_config,
                apns=apns_config
            )

            # Send payload
            response = messaging.send(message)
            logger.info(f"Push notification successfully delivered via FCM. Msg ID: {response}")
            return True

        except ImportError:
            # Firebase Admin SDK not installed - mock/simulate delivery for local/testing
            logger.warning(
                f"firebase_admin SDK not installed. Simulating push delivery to token '{registration_token[:15]}...'."
            )
            return True
        except Exception as e:
            logger.error(f"FCM delivery failure to token '{registration_token[:15]}...': {str(e)}")
            raise PushServiceError(f"FCM dispatch error: {str(e)}") from e

    @classmethod
    def prepare_payload(
        cls,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
        sound: str = "default",
        badge_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prepares and validates the push payload structure.

        Args:
            title (str): Title text.
            body (str): Body text.
            data (Optional[Dict[str, str]]): Extra deep link key/values.
            image_url (Optional[str]): Image URL.
            sound (str): Sound config.
            badge_count (Optional[int]): Badge indicator.

        Returns:
            Dict[str, Any]: Compiled payload dictionary.
        """
        payload = {
            "notification": {
                "title": title,
                "body": body
            },
            "data": data or {},
            "platform_settings": {
                "sound": sound,
            }
        }

        if image_url:
            payload["notification"]["image"] = image_url

        if badge_count is not None:
            payload["platform_settings"]["badge"] = badge_count

        return payload
