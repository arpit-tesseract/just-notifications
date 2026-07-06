from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import NotificationRecipient
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=NotificationRecipient)
def send_websocket_notification(sender, instance, created, **kwargs):
    if created:
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                logger.warning("Channel layer is not configured. WebSocket notification not sent.")
                return
                
            group_name = f'user_notifications_{instance.user.id}'
            notification = instance.notification
            
            # This payload matches what configuration.consumers.NotificationConsumer expects
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'message': notification.message,
                    'type_status': notification.priority.code if notification.priority else 'info'
                }
            )
            logger.info(f"WebSocket notification sent to {group_name}")
        except Exception as e:
            logger.error(f"Error sending websocket notification: {e}")
