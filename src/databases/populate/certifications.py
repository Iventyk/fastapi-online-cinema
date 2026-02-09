from sqlalchemy.ext.asyncio import AsyncSession
from src.databases.models.movies import Certification

CERTIFICATIONS = ["G", "PG", "PG-13", "R", "NC-17"]

async def populate_certifications(db: AsyncSession) -> None:
    for name in CERTIFICATIONS:
        db.add(Certification(name=name))
    await db.commit()
