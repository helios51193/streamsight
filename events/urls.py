from django.urls import path
from . import views

app_name = "events"

urlpatterns = [path('ingest', views.ingest_event, name="ingest_event"),
               path("testpage", views.test_page, name="test_page")]
