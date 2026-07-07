import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract the user ID from the URL route
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"user_notifications_{self.user_id}"

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Receive message from new notification module
    async def notification_alert(self, event):
        data = event['data']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': data
        }))

    # Receive message from legacy configuration module
    async def send_notification(self, event):
        message = event['message']
        notification_type = event.get('type_status', 'info')
        print(f"[WS DEBUG] Received send_notification event: {event}")

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'status': notification_type
        }))
