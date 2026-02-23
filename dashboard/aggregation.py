from datetime import datetime, timedelta, timezone
import numpy as np
from analytics_dashboard.redis_client import redis_client


def compute_metrics_from_buckets(window_minutes=10):
    now = datetime.now(timezone.utc)

    total = 0
    success = 0
    error = 0
    duration_sum = 0
    all_durations = []
    print("Existing keys:", redis_client.keys("metrics:*"))
    for i in range(window_minutes):
        minute = now - timedelta(minutes=i)
        bucket = minute.strftime("%Y%m%d%H%M")
        
        bucket_key = f"metrics:{bucket}"
        duration_key = f"{bucket_key}:durations"
        data = redis_client.hgetall(bucket_key)
        if not data:
            continue

        total += int(data.get("total", 0))
        success += int(data.get("success", 0))
        error += int(data.get("error", 0))
        duration_sum += int(data.get("duration_sum", 0))

        durations = redis_client.lrange(duration_key, 0, -1)
        all_durations.extend([int(d) for d in durations])

    success_rate = round((success / total) * 100) if total else 0
    error_rate = round((error / total) * 100) if total else 0

    avg_duration = int(duration_sum / total) if total else 0
    p95 = int(np.percentile(all_durations, 95)) if all_durations else 0

    return {
        "type": "metrics_update",
        "total": total,
        "success": success,
        "error": error,
        "success_rate": success_rate,
        "error_rate": error_rate,
        "avg_duration": avg_duration,
        "p95_duration": p95,
        "events_per_minute": round(total / window_minutes) if window_minutes else 0,
    }