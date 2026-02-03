from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from events.models import Events
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
