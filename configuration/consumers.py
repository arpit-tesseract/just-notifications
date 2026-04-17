import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("Connected to WebSocket")
        # 1. Get the user ID from the URL (we'll set the URL up next)
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        
        # 2. Create a unique group name for this specific user
        self.user_group_name = f'user_notifications_{self.user_id}'

        # 3. Join the group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        # 4. Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group when the user closes the tab
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    # 5. This method receives the message from Celery and sends it to the Frontend
    async def send_notification(self, event):
        message = event['message']
        notification_type = event.get('type_status', 'info')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'status': notification_type
        }))


# class ExcelImportConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # Extract the room name from the URL route
#         self.room_name = self.scope['url_route']['kwargs']['room_name']
        
#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_name,
#             self.channel_name
#         )
#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_name,
#             self.channel_name
#         )

#     # Receive message from room group (Sent by Celery!)
#     async def import_update(self, event):
#         message = event['message']

#         # Send message to WebSocket frontend
#         await self.send(text_data=json.dumps({
#             'message': message
#         }))