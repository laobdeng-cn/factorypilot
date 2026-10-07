from datetime import UTC, datetime, timedelta
from hashlib import sha256
from hmac import compare_digest
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.tokens import TokenClaims, create_access_token, create_refresh_token, decode_token
from app.models.auth import AuthSession
from app.models.user import User
from app.schemas.identity import LoginRequest, LoginResponse, TokenPairResponse, UserRead
from app.services.identity import authenticate_credentials

settings = get_settings()


def hash_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _remaining_seconds(expires_at: datetime, *, now: datetime) -> int:
    return max(0, int((expires_at - now).total_seconds()))


def _token_pair(
    *, user: User, auth_session: AuthSession, now: datetime
) -> tuple[str, datetime, str]:
    access_token, access_expires_at = create_access_token(
        user_id=user.id,
        session_id=auth_session.id,
        organization_id=user.organization_id,
        department_id=user.department_id,
        primary_plant_id=user.primary_plant_id,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        session_id=auth_session.id,
        expires_at=auth_session.refresh_expires_at,
    )
    return access_token, access_expires_at, refresh_token


def _response(
    *,
    user: User,
    auth_session: AuthSession,
    access_token: str,
    access_expires_at: datetime,
    refresh_token: str,
    now: datetime,
) -> TokenPairResponse:
    return TokenPairResponse(
        access_token=access_token,
        expires_in=_remaining_seconds(access_expires_at, now=now),
        refresh_token=refresh_token,
        refresh_expires_in=_remaining_seconds(auth_session.refresh_expires_at, now=now),
        user=UserRead.model_validate(user),
    )


async def login(session: AsyncSession, payload: LoginRequest) -> LoginResponse:
    user = await authenticate_credentials(session, payload)
    now = datetime.now(UTC)
    auth_session = AuthSession(
        id=uuid4(),
        user_id=user.id,
        refresh_token_hash=uuid4().hex + uuid4().hex,
        refresh_expires_at=now + timedelta(days=settings.refresh_token_days),
    )
    session.add(auth_session)
    access_token, access_expires_at, refresh_token = _token_pair(
        user=user, auth_session=auth_session, now=now
    )
    auth_session.refresh_token_hash = hash_refresh_token(refresh_token)
    await session.commit()
    return LoginResponse(
        authenticated=True,
        **_response(
            user=user,
            auth_session=auth_session,
            access_token=access_token,
            access_expires_at=access_expires_at,
            refresh_token=refresh_token,
            now=now,
        ).model_dump(),
    )


async def _active_session(
    session: AsyncSession, claims: TokenClaims, *, now: datetime
) -> AuthSession:
    auth_session = await session.get(AuthSession, claims.session_id)
    if auth_session is None or auth_session.user_id != claims.user_id:
        raise AppError(
            code="auth.session_not_found", message="Authentication session was not found", status_code=401
        )
    if auth_session.revoked_at is not None:
        raise AppError(
            code="auth.session_revoked", message="Authentication session has been revoked", status_code=401
        )
    if auth_session.refresh_expires_at <= now:
        raise AppError(
            code="auth.session_expired", message="Authentication session has expired", status_code=401
        )
    return auth_session


async def refresh(session: AsyncSession, refresh_token: str) -> TokenPairResponse:
    claims = decode_token(refresh_token, expected_type="refresh")
    now = datetime.now(UTC)
    auth_session = await _active_session(session, claims, now=now)

    if not compare_digest(auth_session.refresh_token_hash, hash_refresh_token(refresh_token)):
        auth_session.revoked_at = now
        auth_session.revoke_reason = "refresh_token_reuse"
        auth_session.updated_at = now
        await session.commit()
        raise AppError(
            code="auth.refresh_token_reused",
            message="Refresh token is no longer valid",
            status_code=401,
        )

    user = await session.get(User, claims.user_id)
    if user is None:
        raise AppError(code="auth.user_not_found", message="Authenticated user not found", status_code=401)
    if not user.is_active:
        auth_session.revoked_at = now
        auth_session.revoke_reason = "account_inactive"
        auth_session.updated_at = now
        await session.commit()
        raise AppError(code="auth.account_inactive", message="Account is inactive", status_code=403)

    access_token, access_expires_at, new_refresh_token = _token_pair(
        user=user, auth_session=auth_session, now=now
    )
    auth_session.refresh_token_hash = hash_refresh_token(new_refresh_token)
    auth_session.last_used_at = now
    auth_session.updated_at = now
    await session.commit()
    return _response(
        user=user,
        auth_session=auth_session,
        access_token=access_token,
        access_expires_at=access_expires_at,
        refresh_token=new_refresh_token,
        now=now,
    )


async def revoke_session(
    session: AsyncSession, session_id: UUID, *, reason: str = "logout"
) -> None:
    auth_session = await session.get(AuthSession, session_id)
    if auth_session is None:
        return
    if auth_session.revoked_at is None:
        now = datetime.now(UTC)
        auth_session.revoked_at = now
        auth_session.revoke_reason = reason
        auth_session.updated_at = now
        await session.commit()
