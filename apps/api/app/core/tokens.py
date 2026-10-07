from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, cast
from uuid import UUID, uuid4

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import get_settings
from app.core.errors import AppError

settings = get_settings()
TokenType = Literal["access", "refresh"]


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: UUID
    session_id: UUID
    token_id: UUID
    token_type: TokenType
    issued_at: datetime
    expires_at: datetime
    organization_id: UUID | None = None
    department_id: UUID | None = None
    primary_plant_id: UUID | None = None


def _uuid_claim(payload: dict[str, object], name: str, *, required: bool = True) -> UUID | None:
    value = payload.get(name)
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Invalid {name} claim")
    return UUID(value)


def _timestamp_claim(payload: dict[str, object], name: str) -> datetime:
    value = payload.get(name)
    if not isinstance(value, int):
        raise ValueError(f"Invalid {name} claim")
    return datetime.fromtimestamp(value, UTC)


def _encode(
    *,
    user_id: UUID,
    session_id: UUID,
    token_type: TokenType,
    expires_at: datetime,
    organization_id: UUID | None = None,
    department_id: UUID | None = None,
    primary_plant_id: UUID | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "sub": str(user_id),
        "sid": str(session_id),
        "jti": str(uuid4()),
        "typ": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    if organization_id is not None:
        payload["org"] = str(organization_id)
    if department_id is not None:
        payload["dept"] = str(department_id)
    if primary_plant_id is not None:
        payload["plant"] = str(primary_plant_id)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    *,
    user_id: UUID,
    session_id: UUID,
    organization_id: UUID,
    department_id: UUID | None,
    primary_plant_id: UUID | None,
) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    token = _encode(
        user_id=user_id,
        session_id=session_id,
        token_type="access",
        expires_at=expires_at,
        organization_id=organization_id,
        department_id=department_id,
        primary_plant_id=primary_plant_id,
    )
    return token, expires_at


def create_refresh_token(
    *, user_id: UUID, session_id: UUID, expires_at: datetime
) -> str:
    return _encode(
        user_id=user_id,
        session_id=session_id,
        token_type="refresh",
        expires_at=expires_at,
    )


def decode_token(token: str, *, expected_type: TokenType) -> TokenClaims:
    try:
        payload = cast(
            dict[str, object],
            jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
                options={"require": ["sub", "sid", "jti", "typ", "iat", "exp"]},
            ),
        )
        token_type = payload.get("typ")
        if token_type != expected_type:
            raise ValueError("Unexpected token type")
        return TokenClaims(
            user_id=cast(UUID, _uuid_claim(payload, "sub")),
            session_id=cast(UUID, _uuid_claim(payload, "sid")),
            token_id=cast(UUID, _uuid_claim(payload, "jti")),
            token_type=expected_type,
            issued_at=_timestamp_claim(payload, "iat"),
            expires_at=_timestamp_claim(payload, "exp"),
            organization_id=_uuid_claim(payload, "org", required=False),
            department_id=_uuid_claim(payload, "dept", required=False),
            primary_plant_id=_uuid_claim(payload, "plant", required=False),
        )
    except ExpiredSignatureError as exc:
        raise AppError(
            code="auth.token_expired", message="Authentication token has expired", status_code=401
        ) from exc
    except (InvalidTokenError, ValueError) as exc:
        raise AppError(
            code="auth.invalid_token", message="Authentication token is invalid", status_code=401
        ) from exc
