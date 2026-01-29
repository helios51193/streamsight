import json
import asyncio
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

class EventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "events_stream",
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "events_stream",
            self.channel_name,
        )

    async def event_message(self, event):
        await self.send(text_data=json.dumps(event["data"]))