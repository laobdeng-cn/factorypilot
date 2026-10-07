from datetime import UTC, datetime, timedelta
from math import ceil
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.errors import AppError
from app.core.security import hash_password, password_needs_rehash, verify_password
from app.models.user import User
from app.schemas.enterprise import Page
from app.schemas.identity import LoginRequest, LoginResponse, UserCreate, UserRead, UserUpdate
from app.services import enterprise as enterprise_service

_MAX_FAILED_LOGIN_ATTEMPTS = 5
_LOCK_DURATION = timedelta(minutes=15)
_DUMMY_PASSWORD_HASH = hash_password("FactoryPilot#Dummy2026!")


def _normalize_username(value: str) -> str:
    return value.strip().lower()


def _normalize_employee_no(value: str) -> str:
    return value.strip().upper()


def _total_pages(total: int, page_size: int) -> int:
    return ceil(total / page_size) if total else 0


def _optional_text(value: str | None, *, lowercase: bool = False) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized.lower() if lowercase else normalized


def _hash_password_or_error(password: str) -> str:
    try:
        return hash_password(password)
    except ValueError as exc:
        raise AppError(
            code="auth.weak_password",
            message=str(exc),
            status_code=422,
        ) from exc


async def _commit_or_conflict(session: AsyncSession) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            code="user.identity_conflict",
            message="Username, employee number, email or mobile already exists",
            status_code=409,
        ) from exc


async def _validate_user_scope(
    session: AsyncSession,
    *,
    organization_id: UUID,
    department_id: UUID | None,
    primary_plant_id: UUID | None,
) -> None:
    await enterprise_service.get_organization(session, organization_id)

    if primary_plant_id is not None:
        plant = await enterprise_service.get_plant(session, primary_plant_id)
        if plant.organization_id != organization_id:
            raise AppError(
                code="user.plant_scope_mismatch",
                message="Primary plant does not belong to user organization",
                status_code=409,
            )

    if department_id is not None:
        department = await enterprise_service.get_department(session, department_id)
        if department.organization_id != organization_id:
            raise AppError(
                code="user.department_scope_mismatch",
                message="Department does not belong to user organization",
                status_code=409,
            )
        if (
            department.plant_id is not None
            and primary_plant_id is not None
            and department.plant_id != primary_plant_id
        ):
            raise AppError(
                code="user.department_plant_mismatch",
                message="Department does not belong to primary plant",
                status_code=409,
            )


async def get_user(session: AsyncSession, user_id: UUID) -> User:
    entity = await session.get(User, user_id)
    if entity is None:
        raise AppError(code="user.not_found", message="User not found", status_code=404)
    return entity


async def list_users(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    organization_id: UUID | None,
    department_id: UUID | None,
    primary_plant_id: UUID | None,
    is_active: bool | None,
    q: str | None,
) -> Page[UserRead]:
    filters: list[ColumnElement[bool]] = []
    if organization_id is not None:
        filters.append(User.organization_id == organization_id)
    if department_id is not None:
        filters.append(User.department_id == department_id)
    if primary_plant_id is not None:
        filters.append(User.primary_plant_id == primary_plant_id)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    if q:
        term = f"%{q.strip()}%"
        filters.append(
            or_(
                User.username.ilike(term),
                User.employee_no.ilike(term),
                User.display_name.ilike(term),
                User.email.ilike(term),
            )
        )

    total = int(
        (await session.scalar(select(func.count()).select_from(User).where(*filters))) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(User)
                .where(*filters)
                .order_by(User.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
    )
    return Page[UserRead](
        items=[UserRead.model_validate(item) for item in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
    )


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    await _validate_user_scope(
        session,
        organization_id=payload.organization_id,
        department_id=payload.department_id,
        primary_plant_id=payload.primary_plant_id,
    )
    entity = User(
        organization_id=payload.organization_id,
        department_id=payload.department_id,
        primary_plant_id=payload.primary_plant_id,
        username=_normalize_username(payload.username),
        employee_no=_normalize_employee_no(payload.employee_no),
        display_name=payload.display_name.strip(),
        email=_optional_text(payload.email, lowercase=True),
        mobile=_optional_text(payload.mobile),
        password_hash=_hash_password_or_error(payload.password),
        is_active=payload.is_active,
    )
    session.add(entity)
    await _commit_or_conflict(session)
    await session.refresh(entity)
    return entity


async def update_user(session: AsyncSession, user_id: UUID, payload: UserUpdate) -> User:
    entity = await get_user(session, user_id)
    data = payload.model_dump(exclude_unset=True)

    next_department_id = data.get("department_id", entity.department_id)
    next_primary_plant_id = data.get("primary_plant_id", entity.primary_plant_id)
    await _validate_user_scope(
        session,
        organization_id=entity.organization_id,
        department_id=next_department_id,
        primary_plant_id=next_primary_plant_id,
    )

    if data.get("username") is not None:
        data["username"] = _normalize_username(data["username"])
    if data.get("employee_no") is not None:
        data["employee_no"] = _normalize_employee_no(data["employee_no"])
    if data.get("display_name") is not None:
        data["display_name"] = data["display_name"].strip()
    if "email" in data:
        data["email"] = _optional_text(data["email"], lowercase=True)
    if "mobile" in data:
        data["mobile"] = _optional_text(data["mobile"])

    for key, value in data.items():
        if key in {"username", "employee_no", "display_name"} and value is None:
            continue
        setattr(entity, key, value)
    entity.version += 1
    await _commit_or_conflict(session)
    await session.refresh(entity)
    return entity


async def change_password(session: AsyncSession, user_id: UUID, new_password: str) -> User:
    entity = await get_user(session, user_id)
    entity.password_hash = _hash_password_or_error(new_password)
    entity.failed_login_count = 0
    entity.locked_until = None
    entity.version += 1
    await session.commit()
    await session.refresh(entity)
    return entity


async def authenticate_user(session: AsyncSession, payload: LoginRequest) -> LoginResponse:
    username = _normalize_username(payload.username)
    entity = await session.scalar(select(User).where(User.username == username))
    if entity is None:
        verify_password(payload.password, _DUMMY_PASSWORD_HASH)
        raise AppError(
            code="auth.invalid_credentials",
            message="Invalid username or password",
            status_code=401,
        )

    now = datetime.now(UTC)
    if entity.locked_until is not None and entity.locked_until > now:
        raise AppError(
            code="auth.account_locked",
            message="Account is temporarily locked",
            status_code=423,
            details={"locked_until": entity.locked_until.isoformat()},
        )

    if not verify_password(payload.password, entity.password_hash):
        entity.failed_login_count += 1
        if entity.failed_login_count >= _MAX_FAILED_LOGIN_ATTEMPTS:
            entity.locked_until = now + _LOCK_DURATION
        await session.commit()
        raise AppError(
            code="auth.invalid_credentials",
            message="Invalid username or password",
            status_code=401,
        )

    if not entity.is_active:
        raise AppError(
            code="auth.account_inactive",
            message="Account is inactive",
            status_code=403,
        )

    if password_needs_rehash(entity.password_hash):
        entity.password_hash = hash_password(payload.password)
    entity.failed_login_count = 0
    entity.locked_until = None
    entity.last_login_at = now
    await session.commit()
    await session.refresh(entity)
    return LoginResponse(authenticated=True, user=UserRead.model_validate(entity))
