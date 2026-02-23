import json
import asyncio
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import numpy as np
from django.db.models import Avg

from dashboard.aggregation import compute_metrics_from_buckets
from .models import Events
from channels.db import database_sync_to_async

class EventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.window_minutes = 10
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
        # Send raw event
        await self.send(text_data=json.dumps(event["data"]))

        metrics = compute_metrics_from_buckets(self.window_minutes)

        await self.send(text_data=json.dumps(metrics))

    async def metrics_message(self, event):
        await self.send(text_data=json.dumps(event["data"]))
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("type") == "update_window":
            self.window_minutes = int(data.get("window",10))
            metrics = compute_metrics_from_buckets(self.window_minutes)
            await self.send(text_data=json.dumps(metrics))