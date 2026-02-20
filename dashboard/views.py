from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from events.models import Events
from django.db.models import Avg
import numpy as np
@login_required
def dashboard_index(request):
    return render(request, "dashboard/index.jinja")

@login_required
def initial_events(request):
    events = (Events.objects
        .order_by("-timestamp")[:20]
        .values(
            "id",
            "timestamp",
            "event_type",
            "source",
            "status",
            "duration_ms",
        )
    )

    return JsonResponse(list(events), safe=False)

def metrics_summary(request):
    window = int(request.GET.get("window", 10))

    cutoff = timezone.now() - timedelta(minutes=window)

    qs = Events.objects.filter(timestamp__gte=cutoff)

    total = qs.count()
    success = qs.filter(status="success").count()
    error = qs.filter(status="error").count()

    success_rate = round((success / total) * 100) if total else 0
    error_rate = round((error / total) * 100) if total else 0

    avg_duration = qs.aggregate(avg=Avg("duration_ms"))["avg"] or 0

    durations = list(qs.values_list("duration_ms", flat=True))
    p95 = 0
    if durations:
        p95 = int(np.percentile(durations, 95))

    events_per_minute = round(total / window) if window else 0

    return JsonResponse({
        "total": total,
        "success": success,
        "error": error,
        "success_rate": success_rate,
        "error_rate": error_rate,
        "avg_duration": int(avg_duration),
        "p95_duration": p95,
        "events_per_minute": events_per_minute,
    })
