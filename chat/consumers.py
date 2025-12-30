import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

from .models import Conversation, Message

User = get_user_model()

ONLINE_USERS = set()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']

        try:
            self.user = await sync_to_async(User.objects.get)(username=self.username)
        except User.DoesNotExist:
            await self.close()
            return

        self.user_group = f"user_{self.user.username}"

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

        ONLINE_USERS.add(self.user.username)

        await self.send(text_data=json.dumps({
            'type': 'presence',
            'user': self.user.username,
            'status': 'online'
        }))

    async def disconnect(self, close_code):
        ONLINE_USERS.discard(self.user.username)
        await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        # READ RECEIPT EVENT
        if data.get('type') == 'read':
            message_id = data.get('message_id')
            if message_id:
                await sync_to_async(Message.objects.filter(id=message_id).update)(is_read=True)

                await self.channel_layer.group_send(
                    f"user_{data.get('to')}",
                    {
                        'type': 'read_event',
                        'message_id': message_id
                    }
                )
            return

        # TYPING EVENT
        if data.get('type') == 'typing':
            await self.channel_layer.group_send(
                f"user_{data.get('to')}",
                {
                    'type': 'typing_event',
                    'from': self.user.username
                }
            )
            return

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
            'id': msg.id,
            'from': self.user.username,
            'to': receiver.username,
            'message': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'read': False
        }

        await self.send(text_data=json.dumps(payload))

        if receiver.username in ONLINE_USERS:
            await self.channel_layer.group_send(
                f"user_{receiver.username}",
                {
                    'type': 'forward_message',
                    'payload': payload
                }
            )

    async def forward_message(self, event):
        await self.send(text_data=json.dumps(event['payload']))

    async def typing_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'from': event['from']
        }))

    async def read_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message_id': event['message_id']
        }))

    @sync_to_async
    def get_or_create_conversation(self, user1, user2):
        if user1.id > user2.id:
            user1, user2 = user2, user1

        conversation, _ = Conversation.objects.get_or_create(
            user1=user1,
            user2=user2
        )
        return conversation
