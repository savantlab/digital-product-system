import os
import json
from datetime import datetime, timedelta, timezone
import redis
from rq import Connection, Worker

from email_mailgun import send_mailgun

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
r = redis.from_url(REDIS_URL)

# Simple in-memory suppressions cache (persist in DB in production)
SUPPRESSIONS = set()


def handle_event(event: dict):
    """Entry point queued by /api/track."""
    etype = event.get("type")
    user = event.get("user", {})
    email = user.get("email")

    if not email:
        return

    # Example rules — expand as needed
    if etype == "license.provisioned":
        send_mailgun(
            "welcome",
            to=email,
            variables={
                "first_name": user.get("first_name"),
                "book_domain": os.environ.get("BOOK_DOMAIN"),
                "lab_domain": os.environ.get("LAB_DOMAIN") if event.get("entitlements", {}).get("lab") else None,
                "app_domain": os.environ.get("APP_DOMAIN") if event.get("entitlements", {}).get("app") else None,
            },
        )
    elif etype == "checkout.abandoned":
        resume_url = event.get("resume_url")
        if resume_url and not is_suppressed(email):
            send_mailgun(
                "abandoned_cart",
                to=email,
                variables={
                    "first_name": user.get("first_name"),
                    "tier": event.get("tier"),
                    "resume_url": resume_url,
                },
            )


def handle_mailgun_event(event_data_str: str):
    try:
        data = json.loads(event_data_str)
    except Exception:
        return

    evt = data.get("event")
    recipient = data.get("recipient")
    if evt in {"complained", "bounced"} and recipient:
        SUPPRESSIONS.add(recipient)


def is_suppressed(email: str) -> bool:
    return email in SUPPRESSIONS


if __name__ == "__main__":
    with Connection(r):
        Worker(["events"]).work()