from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.databases.models.movies import Certification
from src.schemas.certifications import CertificationCreate


async def create_certification(
    db: AsyncSession,
    *,
    data: CertificationCreate,
) -> Certification:
    cert = Certification(name=data.name)
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    return cert


async def get_certifications(
    db: AsyncSession,
) -> list[Certification]:
    result = await db.execute(select(Certification))
    return list(result.scalars().all())
