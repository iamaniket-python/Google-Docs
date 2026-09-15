import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Document, DocumentShare


class DocumentConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def user_can_access(self, user, document_id):
        document = Document.objects.filter(pk=document_id).first()
        if not document:
            return False
        if document.owner == user:
            return True
        return DocumentShare.objects.filter(document=document, user=user).exists()

    async def connect(self):
      self.user = self.scope['user']
      self.document_id = self.scope['url_route']['kwargs']['document_id']
      self.room_group_name = f'document_{self.document_id}'

      await self.accept()

      if not self.user.is_authenticated:
         await self.close(code=4001)
         return

      has_access = await self.user_can_access(self.user, self.document_id)
      if not has_access:
        await self.close(code=4003)
        return

      await self.channel_layer.group_add(
        self.room_group_name,
        self.channel_name
    )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'document_update',
                'content': data.get('content'),
                'username': self.user.username,
                'sender_channel': self.channel_name,
            }
        )

    async def document_update(self, event):
        if event['sender_channel'] == self.channel_name:
            return

        await self.send(text_data=json.dumps({
            'content': event['content'],
            'username': event['username'],
        }))