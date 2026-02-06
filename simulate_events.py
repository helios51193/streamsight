import time
import random
import requests
from datetime import datetime, timezone

INGEST_URL = "http://localhost:8000/api/events/ingest"  # adjust if needed

EVENT_TYPES = [
    "user_login",
    "user_logout",
    "file_upload",
    "file_download",
    "payment_initiated",
    "payment_success",
    "payment_failed",
]

SOURCES = [
    "web",
    "mobile",
    "backend",
    "cron",
]

STATUSES = ["success", "error"]


def generate_event():
    status = random.choices(
        STATUSES,
        weights=[0.85, 0.15],  # mostly success
    )[0]

    return {
        "event_type": random.choice(EVENT_TYPES),
        "source": random.choice(SOURCES),
        "status": status,
        "duration_ms": random.randint(20, 1200),\
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "request_id": f"req_{random.randint(1000, 9999)}",
        },
    }


def main(times):
    print("Starting event simulator...")
    print("Sending events to:", INGEST_URL)
    
    for index in range(times):
        print(f"Event No. {index}")
        event = generate_event()

        try:
            r = requests.post(INGEST_URL, json=event, timeout=3)
            print(r.text)
            print(
                f"[{r.status_code}] {event['event_type']} | "
                f"{event['status']} | {event['duration_ms']}ms"
            )
        except Exception as e:
            print("Error sending event:", e)

        time.sleep(random.uniform(0.05, 0.2))  # adjust rate here


if __name__ == "__main__":
    main(50)