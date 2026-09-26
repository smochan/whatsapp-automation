from datetime import datetime, timedelta, timezone

from app.models import Conversation


CUSTOMER_SERVICE_WINDOW = timedelta(hours=24)


def refresh_customer_service_window(conversation: Conversation, customer_message_at: datetime) -> None:
    if customer_message_at.tzinfo is None:
        customer_message_at = customer_message_at.replace(tzinfo=timezone.utc)
    conversation.last_customer_message_at = customer_message_at
    conversation.window_expires_at = customer_message_at + CUSTOMER_SERVICE_WINDOW


def is_service_window_open(conversation: Conversation, *, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    expires_at = conversation.window_expires_at
    if not expires_at:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return now < expires_at
