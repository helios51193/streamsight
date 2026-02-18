import json
import asyncio
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import numpy as np
from django.db.models import Avg
from .models import Events
from channels.db import database_sync_to_async

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
    

    @database_sync_to_async
    def compute_metrics_sync(self, window=10):
        cutoff = timezone.now() - timedelta(minutes=window)

        qs = Events.objects.filter(timestamp__gte=cutoff)

        total = qs.count()
        success = qs.filter(status="success").count()
        error = qs.filter(status="error").count()

        success_rate = round((success / total) * 100) if total else 0
        error_rate = round((error / total) * 100) if total else 0

        avg_duration = qs.aggregate(avg=Avg("duration_ms"))["avg"] or 0

        durations = list(qs.values_list("duration_ms", flat=True))
        p95 = int(np.percentile(durations, 95)) if durations else 0

        return {
            "type": "metrics_update",
            "total": total,
            "success": success,
            "error": error,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_duration": int(avg_duration),
            "p95_duration": p95,
            "events_per_minute": round(total / window) if window else 0,
        }

    async def event_message(self, event):
        # Send raw event
        await self.send(text_data=json.dumps(event["data"]))

        # Compute metrics
        metrics = await self.compute_metrics_sync(10)

        # Send metrics update
        await self.send(text_data=json.dumps(metrics))