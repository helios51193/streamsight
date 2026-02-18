from django.urls import path
from . import views

app_name = "dashboard"


urlpatterns = [
    path("", views.dashboard_index, name="dashboard_index"),
    path("initial/", views.initial_events, name="dashboard_initial_events"),
    path("api/metrics/summary", views.metrics_summary, name="dashboard_metric_summary")
]