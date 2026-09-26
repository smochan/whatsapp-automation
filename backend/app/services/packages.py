from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Package


async def search_packages(
    db: AsyncSession,
    *,
    organization_id,
    destination: str | None = None,
    limit: int = 5,
) -> list[Package]:
    query = select(Package).where(
        Package.organization_id == organization_id,
        Package.active.is_(True),
    )
    if destination:
        query = query.where(Package.destination.ilike(f"%{destination}%"))
    query = query.order_by(Package.created_at.desc()).limit(limit)
    result = await db.scalars(query)
    return list(result.all())


def build_package_context(packages: list[Package]) -> str:
    if not packages:
        return "No matching active packages were found in the organizer's database."

    rows = []
    for package in packages:
        price = f"{package.currency} {package.price}" if package.price is not None else "Price not configured"
        rows.append(
            "\n".join(
                [
                    f"Package: {package.name}",
                    f"Destination: {package.destination}",
                    f"Duration: {package.duration_days or 'Not specified'} days",
                    f"Price: {price}",
                    f"Description: {package.description or 'Not specified'}",
                    f"Inclusions: {', '.join(package.inclusions) if package.inclusions else 'Not specified'}",
                    f"Exclusions: {', '.join(package.exclusions) if package.exclusions else 'Not specified'}",
                ]
            )
        )
    return "\n\n".join(rows)
