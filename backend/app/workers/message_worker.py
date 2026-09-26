import uuid

from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import get_settings
from app.core.crypto import decrypt_secret
from app.db import SessionLocal
from app.models import Conversation, Customer, Message, MessageDirection, WhatsAppAccount
from app.services.orchestrator import ConversationOrchestrator
from app.services.whatsapp import WhatsAppClient


async def process_message(ctx: dict, message_id: str) -> None:
    message_uuid = uuid.UUID(message_id)
    async with SessionLocal() as db:
        orchestrator = ConversationOrchestrator()
        reply = await orchestrator.handle_message(db, message_uuid)
        if not reply:
            return

        row = await db.execute(
            select(Message, Conversation, Customer, WhatsAppAccount)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .join(Customer, Conversation.customer_id == Customer.id)
            .join(WhatsAppAccount, Conversation.whatsapp_account_id == WhatsAppAccount.id)
            .where(Message.id == message_uuid)
        )
        record = row.one_or_none()
        if not record:
            return

        _, conversation, customer, account = record
        token = decrypt_secret(account.access_token_encrypted) if account.access_token_encrypted else None
        client = WhatsAppClient()
        response = await client.send_text(
            phone_number_id=account.phone_number_id,
            recipient=customer.phone,
            text=reply,
            access_token=token,
        )

        response_message_id = response.get("messages", [{}])[0].get("id")
        if response_message_id:
            db.add(
                Message(
                    conversation_id=conversation.id,
                    direction=MessageDirection.outbound,
                    message_type="text",
                    whatsapp_message_id=response_message_id,
                    text=reply,
                    extra_metadata={"source": "ai"},
                )
            )
        await db.commit()


class WorkerSettings:
    functions = [process_message]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url) if get_settings().redis_url else RedisSettings()
    max_jobs = 20
