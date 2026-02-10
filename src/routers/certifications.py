from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.schemas.certifications import (
    CertificationCreate,
    CertificationRead,
)
from src.crud import certifications as crud

router = APIRouter(
    prefix="/certifications",
    tags=["Certifications"],
)


@router.post(
    "",
    response_model=CertificationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_certification(
    data: CertificationCreate,
    db: AsyncSession = Depends(get_db),
) -> CertificationRead:
    cert = await crud.create_certification(db, data=data)
    return CertificationRead.model_validate(cert)


@router.get(
    "",
    response_model=List[CertificationRead],
)
async def get_certifications(
    db: AsyncSession = Depends(get_db),
) -> List[CertificationRead]:
    certs = await crud.get_certifications(db)
    return [CertificationRead.model_validate(c) for c in certs]
