from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.laya import LayaRouter
from app.ai.llm import OpenAICompatibleGenerator
from app.models import Conversation, Customer, Message, MessageDirection
from app.services.knowledge import build_context, search_knowledge
from app.services.packages import build_package_context, search_packages


class ConversationOrchestrator:
    def __init__(self) -> None:
        self.router = LayaRouter()
        self.generator = OpenAICompatibleGenerator()

    async def handle_message(self, db: AsyncSession, message_id) -> str | None:
        message = await db.get(Message, message_id)
        if not message or message.direction != MessageDirection.inbound or not message.text:
            return None

        conversation = await db.get(Conversation, message.conversation_id)
        if not conversation:
            return None

        result = await self.router.classify(message.text)
        if result.requires_human:
            conversation.status = "human"
            await db.commit()
            return None

        intent = result.intent.lower()
        context_parts: list[str] = []

        if "package" in intent or "price" in intent or "availability" in intent:
            packages = await search_packages(db, organization_id=conversation.organization_id, limit=5)
            context_parts.append(build_package_context(packages))

        documents = await search_knowledge(
            db,
            organization_id=conversation.organization_id,
            query=message.text,
            limit=5,
        )
        knowledge_context = build_context(documents)
        if knowledge_context:
            context_parts.append(knowledge_context)

        context = "\n\n---\n\n".join(part for part in context_parts if part)
        if not context:
            # Never allow the model to invent business facts when our source of
            # truth has no relevant information.
            return None

        return await self.generator.generate(
            user_message=message.text,
            context=context,
            instructions=(
                "You are a WhatsApp travel-business assistant. Be concise and helpful. "
                "Use only the supplied business context for factual claims. Never invent "
                "prices, availability, inclusions, policies, or booking status. If the "
                "context does not answer the question, ask for the missing information "
                "or offer human assistance. Match the customer's language when practical."
            ),
        )
