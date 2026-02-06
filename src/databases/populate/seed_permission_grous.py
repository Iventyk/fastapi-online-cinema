from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.databases import get_db
from src.databases.models.accounts import UserGroupModel, UserGroupEnum


async def seed_groups(db: Annotated[AsyncSession, Depends(get_db)]) -> None:
    for group_name in UserGroupEnum:
        stmt = select(UserGroupModel).where(UserGroupModel.name == group_name)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            db.add(UserGroupModel(name=group_name))

    await db.commit()
