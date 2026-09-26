from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeDocument


async def search_knowledge(
    db: AsyncSession,
    *,
    organization_id,
    query: str,
    limit: int = 5,
) -> list[KnowledgeDocument]:
    terms = [term.strip() for term in query.split() if len(term.strip()) >= 3]
    if not terms:
        return []

    filters = []
    for term in terms[:8]:
        pattern = f"%{term}%"
        filters.append(or_(KnowledgeDocument.title.ilike(pattern), KnowledgeDocument.content.ilike(pattern)))

    result = await db.scalars(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.organization_id == organization_id)
        .where(or_(*filters))
        .limit(limit)
    )
    return list(result.all())


def build_context(documents: list[KnowledgeDocument]) -> str:
    if not documents:
        return ""
    chunks = [f"## {doc.title}\n{doc.content}" for doc in documents]
    return "\n\n".join(chunks)
