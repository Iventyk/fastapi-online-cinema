from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.databases.models import UserModel
from src.exceptions import UserNotExist, TokenExpiredError, InvalidTokenError
from src.schemas import CurrentUser
from src.security import JWTAuthManagerInterface
from src.config import get_jwt_manager
from src.databases import get_db

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/accounts/login/")
security_scheme = HTTPBearer()


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    # token: Annotated[str, Depends(oauth2_scheme)],
    auth: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
) -> CurrentUser:
    token = auth.credentials
    try:
        user_data = jwt_manager.decode_access_token(token)

    except (TokenExpiredError, InvalidTokenError):
        raise

    user_id = user_data.get("user_id")

    auth_user = await db.get(
        UserModel,
        user_id,
        options=[joinedload(UserModel.profile), joinedload(UserModel.group)],
    )

    if not auth_user:
        raise UserNotExist()

    return CurrentUser(
        user_id=auth_user.id,
        email=auth_user.email,
        is_active=auth_user.is_active,
        permission=auth_user.group.name,
        profile_id=auth_user.profile.id if auth_user.profile else None,
    )
