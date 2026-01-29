from events.models import Events
from django.shortcuts import render
import json
from datetime import datetime
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from analytics_dashboard.redis_client import redis_client
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
# Create your views here.

@csrf_exempt
def ingest_event(request):

    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")
    
    # Decoding json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")
    

    required_fields = ["event_type", "source", "timestamp", "status"]

    for field in required_fields:
        if field not in data:
            return HttpResponseBadRequest(f"Missing field: {field}")
    
    timestamp = parse_datetime(data["timestamp"])
    if not timestamp:
        return HttpResponseBadRequest("Invalid timestamp format")

    event = Events.objects.create(
        event_type=data["event_type"],
        source=data["source"],
        timestamp=timestamp,
        status=data["status"],
        duration_ms=data.get("duration_ms"),
        payload=data.get("payload", {}),
    )

    channel_layer = get_channel_layer()


    # 🔴 Publish to Redis
    async_to_sync(channel_layer.group_send)(
        "events_stream",
        {
            "type": "event.message",
            "data": {
                "id": str(event.id),
                "event_type": event.event_type,
                "source": event.source,
                "timestamp": event.timestamp.isoformat(),
                "status": event.status,
                "duration_ms": event.duration_ms,
                "payload": event.payload,
            },
        },
    )

    return JsonResponse(
        {
            "success": True,
            "event_id": str(event.id),
        },
        status=201,
    )

def test_page(request):

    return render(request, "events/test_ws.jinja", context={})