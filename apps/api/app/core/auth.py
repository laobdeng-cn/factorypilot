from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.tokens import TokenClaims, decode_token
from app.db.session import get_db_session
from app.models.auth import AuthSession
from app.models.user import User
from app.services.auth import get_active_session

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class CurrentUser:
    user: User
    auth_session: AuthSession
    claims: TokenClaims

    @property
    def user_id(self) -> UUID:
        return self.user.id

    @property
    def session_id(self) -> UUID:
        return self.auth_session.id

    @property
    def organization_id(self) -> UUID:
        return self.user.organization_id

    @property
    def department_id(self) -> UUID | None:
        return self.user.department_id

    @property
    def primary_plant_id(self) -> UUID | None:
        return self.user.primary_plant_id


CredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(credentials: CredentialsDep, session: SessionDep) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            code="auth.missing_token",
            message="Bearer access token is required",
            status_code=401,
        )

    claims = decode_token(credentials.credentials, expected_type="access")
    auth_session = await get_active_session(session, claims, now=datetime.now(UTC))
    user = await session.get(User, claims.user_id)
    if user is None:
        raise AppError(
            code="auth.user_not_found",
            message="Authenticated user not found",
            status_code=401,
        )
    if not user.is_active:
        raise AppError(
            code="auth.account_inactive",
            message="Account is inactive",
            status_code=403,
        )
    return CurrentUser(user=user, auth_session=auth_session, claims=claims)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
