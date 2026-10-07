from math import ceil
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.errors import AppError
from app.models.enterprise import Department, Organization, Plant
from app.schemas.enterprise import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
    Page,
    PlantCreate,
    PlantRead,
    PlantUpdate,
)


def _normalize_code(value: str) -> str:
    return value.strip().upper()


def _total_pages(total: int, page_size: int) -> int:
    return ceil(total / page_size) if total else 0


async def _commit_or_conflict(
    session: AsyncSession, *, code: str, message: str
) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(code=code, message=message, status_code=409) from exc


async def get_organization(session: AsyncSession, organization_id: UUID) -> Organization:
    entity = await session.get(Organization, organization_id)
    if entity is None:
        raise AppError(
            code="organization.not_found", message="Organization not found", status_code=404
        )
    return entity


async def list_organizations(
    session: AsyncSession, *, page: int, page_size: int, is_active: bool | None
) -> Page[OrganizationRead]:
    filters: list[ColumnElement[bool]] = []
    if is_active is not None:
        filters.append(Organization.is_active == is_active)
    total = int(
        (await session.scalar(select(func.count()).select_from(Organization).where(*filters))) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(Organization)
                .where(*filters)
                .order_by(Organization.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
    )
    return Page[OrganizationRead](
        items=[OrganizationRead.model_validate(item) for item in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
    )


async def create_organization(
    session: AsyncSession, payload: OrganizationCreate
) -> Organization:
    entity = Organization(
        code=_normalize_code(payload.code),
        name=payload.name.strip(),
        short_name=payload.short_name.strip() if payload.short_name else None,
        is_active=payload.is_active,
    )
    session.add(entity)
    await _commit_or_conflict(
        session,
        code="organization.code_conflict",
        message="Organization code already exists",
    )
    await session.refresh(entity)
    return entity


async def update_organization(
    session: AsyncSession, organization_id: UUID, payload: OrganizationUpdate
) -> Organization:
    entity = await get_organization(session, organization_id)
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "code" in data:
        data["code"] = _normalize_code(data["code"])
    if "name" in data:
        data["name"] = data["name"].strip()
    for key, value in data.items():
        setattr(entity, key, value)
    entity.version += 1
    await _commit_or_conflict(
        session,
        code="organization.code_conflict",
        message="Organization code already exists",
    )
    await session.refresh(entity)
    return entity


async def get_plant(session: AsyncSession, plant_id: UUID) -> Plant:
    entity = await session.get(Plant, plant_id)
    if entity is None:
        raise AppError(code="plant.not_found", message="Plant not found", status_code=404)
    return entity


async def list_plants(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    organization_id: UUID | None,
    is_active: bool | None,
) -> Page[PlantRead]:
    filters: list[ColumnElement[bool]] = []
    if organization_id is not None:
        filters.append(Plant.organization_id == organization_id)
    if is_active is not None:
        filters.append(Plant.is_active == is_active)
    total = int(
        (await session.scalar(select(func.count()).select_from(Plant).where(*filters))) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(Plant)
                .where(*filters)
                .order_by(Plant.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
    )
    return Page[PlantRead](
        items=[PlantRead.model_validate(item) for item in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
    )


async def create_plant(session: AsyncSession, payload: PlantCreate) -> Plant:
    await get_organization(session, payload.organization_id)
    entity = Plant(
        organization_id=payload.organization_id,
        code=_normalize_code(payload.code),
        name=payload.name.strip(),
        timezone=payload.timezone.strip(),
        country_code=payload.country_code.upper(),
        province=payload.province,
        city=payload.city,
        address=payload.address,
        is_active=payload.is_active,
    )
    session.add(entity)
    await _commit_or_conflict(
        session, code="plant.code_conflict", message="Plant code already exists in organization"
    )
    await session.refresh(entity)
    return entity


async def update_plant(
    session: AsyncSession, plant_id: UUID, payload: PlantUpdate
) -> Plant:
    entity = await get_plant(session, plant_id)
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "code" in data:
        data["code"] = _normalize_code(data["code"])
    if "country_code" in data:
        data["country_code"] = data["country_code"].upper()
    for key, value in data.items():
        setattr(entity, key, value)
    entity.version += 1
    await _commit_or_conflict(
        session, code="plant.code_conflict", message="Plant code already exists in organization"
    )
    await session.refresh(entity)
    return entity


async def get_department(session: AsyncSession, department_id: UUID) -> Department:
    entity = await session.get(Department, department_id)
    if entity is None:
        raise AppError(
            code="department.not_found", message="Department not found", status_code=404
        )
    return entity


async def _validate_department_scope(
    session: AsyncSession,
    *,
    organization_id: UUID,
    plant_id: UUID | None,
    parent_id: UUID | None,
    current_department_id: UUID | None = None,
) -> None:
    await get_organization(session, organization_id)
    if plant_id is not None:
        plant = await get_plant(session, plant_id)
        if plant.organization_id != organization_id:
            raise AppError(
                code="department.plant_scope_mismatch",
                message="Plant does not belong to organization",
                status_code=409,
            )
    if parent_id is not None:
        if current_department_id == parent_id:
            raise AppError(
                code="department.parent_cycle",
                message="Department cannot be its own parent",
                status_code=409,
            )
        parent = await get_department(session, parent_id)
        if parent.organization_id != organization_id:
            raise AppError(
                code="department.parent_scope_mismatch",
                message="Parent department does not belong to organization",
                status_code=409,
            )


async def list_departments(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    organization_id: UUID | None,
    plant_id: UUID | None,
    parent_id: UUID | None,
    is_active: bool | None,
) -> Page[DepartmentRead]:
    filters: list[ColumnElement[bool]] = []
    if organization_id is not None:
        filters.append(Department.organization_id == organization_id)
    if plant_id is not None:
        filters.append(Department.plant_id == plant_id)
    if parent_id is not None:
        filters.append(Department.parent_id == parent_id)
    if is_active is not None:
        filters.append(Department.is_active == is_active)
    total = int(
        (await session.scalar(select(func.count()).select_from(Department).where(*filters))) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(Department)
                .where(*filters)
                .order_by(Department.sort_order.asc(), Department.created_at.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
    )
    return Page[DepartmentRead](
        items=[DepartmentRead.model_validate(item) for item in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
    )


async def create_department(session: AsyncSession, payload: DepartmentCreate) -> Department:
    await _validate_department_scope(
        session,
        organization_id=payload.organization_id,
        plant_id=payload.plant_id,
        parent_id=payload.parent_id,
    )
    entity = Department(
        organization_id=payload.organization_id,
        plant_id=payload.plant_id,
        parent_id=payload.parent_id,
        code=_normalize_code(payload.code),
        name=payload.name.strip(),
        department_type=payload.department_type,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    session.add(entity)
    await _commit_or_conflict(
        session,
        code="department.code_conflict",
        message="Department code already exists in organization",
    )
    await session.refresh(entity)
    return entity


async def update_department(
    session: AsyncSession, department_id: UUID, payload: DepartmentUpdate
) -> Department:
    entity = await get_department(session, department_id)
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    next_plant_id = data.get("plant_id", entity.plant_id)
    next_parent_id = data.get("parent_id", entity.parent_id)
    await _validate_department_scope(
        session,
        organization_id=entity.organization_id,
        plant_id=next_plant_id,
        parent_id=next_parent_id,
        current_department_id=entity.id,
    )
    if "code" in data:
        data["code"] = _normalize_code(data["code"])
    for key, value in data.items():
        setattr(entity, key, value)
    entity.version += 1
    await _commit_or_conflict(
        session,
        code="department.code_conflict",
        message="Department code already exists in organization",
    )
    await session.refresh(entity)
    return entity
