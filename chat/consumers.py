import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

from .models import Conversation, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']

        try:
            self.user = await sync_to_async(User.objects.get)(username=self.username)
        except User.DoesNotExist:
            await self.close()
            return

        # private channel for this user
        self.user_group = f"user_{self.user.username}"

        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )

        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': f'Connected as {self.username}'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        receiver_username = data.get('to')
        message_text = data.get('message')

        if not receiver_username or not message_text:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
            return

        try:
            receiver = await sync_to_async(User.objects.get)(username=receiver_username)
        except User.DoesNotExist:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'User {receiver_username} does not exist'
            }))
            return

        conversation = await self.get_or_create_conversation(self.user, receiver)

        msg = await sync_to_async(Message.objects.create)(
            conversation=conversation,
            sender=self.user,
            content=message_text
        )

        payload = {
            'type': 'chat_message',
            'from': self.user.username,
            'to': receiver.username,
            'message': msg.content,
            'timestamp': msg.timestamp.isoformat()
        }

        # send to sender
        await self.send(text_data=json.dumps(payload))

        # send to receiver if online
        await self.channel_layer.group_send(
            f"user_{receiver.username}",
            {
                'type': 'forward_message',
                'payload': payload
            }
        )

    async def forward_message(self, event):
        await self.send(text_data=json.dumps(event['payload']))

    @sync_to_async
    def get_or_create_conversation(self, user1, user2):
        if user1.id > user2.id:
            user1, user2 = user2, user1

        conversation, _ = Conversation.objects.get_or_create(
            user1=user1,
            user2=user2
        )
        return conversation