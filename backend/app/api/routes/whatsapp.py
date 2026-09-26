from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db
from app.models import Conversation, Customer, Message, MessageDirection, WhatsAppAccount, WebhookEvent
from app.services.whatsapp import WhatsAppClient, extract_text_message
from app.workers.queue import enqueue_message_processing

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> str:
    settings = get_settings()
    if hub_mode != "subscribe" or hub_verify_token != settings.whatsapp_verify_token:
        raise HTTPException(status_code=403, detail="Webhook verification failed")
    return hub_challenge


@router.post("")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str]:
    body = await request.body()
    client = WhatsAppClient()

    if not client.verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    message = extract_text_message(payload)

    if not message or not message.get("message_id") or not message.get("phone_number_id"):
        return {"status": "ignored"}

    external_id = message["message_id"]
    existing = await db.scalar(
        select(WebhookEvent).where(
            WebhookEvent.provider == "whatsapp",
            WebhookEvent.external_event_id == external_id,
        )
    )
    if existing:
        return {"status": "duplicate"}

    account = await db.scalar(
        select(WhatsAppAccount).where(
            WhatsAppAccount.phone_number_id == message["phone_number_id"],
            WhatsAppAccount.active.is_(True),
        )
    )
    if not account:
        db.add(
            WebhookEvent(
                provider="whatsapp",
                external_event_id=external_id,
                event_type="message",
                payload=payload,
            )
        )
        await db.commit()
        return {"status": "unconfigured"}

    customer = await db.scalar(
        select(Customer).where(
            Customer.organization_id == account.organization_id,
            Customer.phone == message["from"],
        )
    )
    if not customer:
        customer = Customer(
            organization_id=account.organization_id,
            phone=message["from"],
        )
        db.add(customer)
        await db.flush()

    conversation = await db.scalar(
        select(Conversation).where(
            Conversation.organization_id == account.organization_id,
            Conversation.customer_id == customer.id,
            Conversation.whatsapp_account_id == account.id,
            Conversation.status != "closed",
        ).order_by(Conversation.created_at.desc())
    )

    received_at = datetime.fromtimestamp(int(message["timestamp"]), tz=timezone.utc)
    if not conversation:
        conversation = Conversation(
            organization_id=account.organization_id,
            customer_id=customer.id,
            whatsapp_account_id=account.id,
        )
        db.add(conversation)
        await db.flush()

    conversation.last_customer_message_at = received_at
    conversation.window_expires_at = received_at + timedelta(hours=24)

    inbound = Message(
        conversation_id=conversation.id,
        direction=MessageDirection.inbound,
        message_type="text",
        whatsapp_message_id=external_id,
        text=message["text"],
        extra_metadata={"raw": message["raw"]},
        created_at=received_at,
    )
    db.add(inbound)
    db.add(
        WebhookEvent(
            provider="whatsapp",
            external_event_id=external_id,
            event_type="message",
            payload=payload,
            processed_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()

    queued = await enqueue_message_processing(str(inbound.id))
    return {"status": "queued" if queued else "stored"}
