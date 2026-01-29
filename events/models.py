from django.db import models
import uuid
# Create your models here.

class Events(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    event_type = models.CharField(max_length=50)
    source = models.CharField(max_length=50)

    timestamp = models.DateTimeField()
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("success", "success"),
            ("error", "error"),
        ],
    )

    payload = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} | {self.status}"