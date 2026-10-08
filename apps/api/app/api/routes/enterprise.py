from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_permission
from app.db.session import get_db_session
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
from app.services import enterprise as service

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
PageParam = Annotated[int, Query(ge=1)]
PageSizeParam = Annotated[int, Query(ge=1, le=100)]
OrganizationReadDep = Annotated[
    CurrentUser, Depends(require_permission("enterprise.organization.read"))
]
OrganizationManageDep = Annotated[
    CurrentUser, Depends(require_permission("enterprise.organization.manage"))
]
PlantReadDep = Annotated[CurrentUser, Depends(require_permission("enterprise.plant.read"))]
PlantManageDep = Annotated[
    CurrentUser, Depends(require_permission("enterprise.plant.manage"))
]
DepartmentReadDep = Annotated[
    CurrentUser, Depends(require_permission("enterprise.department.read"))
]
DepartmentManageDep = Annotated[
    CurrentUser, Depends(require_permission("enterprise.department.manage"))
]


@router.get("/organizations", response_model=Page[OrganizationRead], summary="组织列表")
async def list_organizations(
    session: SessionDep,
    _actor: OrganizationReadDep,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    is_active: bool | None = None,
) -> Page[OrganizationRead]:
    return await service.list_organizations(
        session, page=page, page_size=page_size, is_active=is_active
    )


@router.post(
    "/organizations",
    response_model=OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建组织",
)
async def create_organization(
    payload: OrganizationCreate, session: SessionDep, _actor: OrganizationManageDep
) -> Organization:
    return await service.create_organization(session, payload)


@router.get("/organizations/{organization_id}", response_model=OrganizationRead, summary="组织详情")
async def get_organization(
    organization_id: UUID, session: SessionDep, _actor: OrganizationReadDep
) -> Organization:
    return await service.get_organization(session, organization_id)


@router.patch(
    "/organizations/{organization_id}", response_model=OrganizationRead, summary="更新组织"
)
async def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    session: SessionDep,
    _actor: OrganizationManageDep,
) -> Organization:
    return await service.update_organization(session, organization_id, payload)


@router.get("/plants", response_model=Page[PlantRead], summary="工厂列表")
async def list_plants(
    session: SessionDep,
    _actor: PlantReadDep,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    organization_id: UUID | None = None,
    is_active: bool | None = None,
) -> Page[PlantRead]:
    return await service.list_plants(
        session,
        page=page,
        page_size=page_size,
        organization_id=organization_id,
        is_active=is_active,
    )


@router.post(
    "/plants",
    response_model=PlantRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建工厂",
)
async def create_plant(
    payload: PlantCreate, session: SessionDep, _actor: PlantManageDep
) -> Plant:
    return await service.create_plant(session, payload)


@router.get("/plants/{plant_id}", response_model=PlantRead, summary="工厂详情")
async def get_plant(plant_id: UUID, session: SessionDep, _actor: PlantReadDep) -> Plant:
    return await service.get_plant(session, plant_id)


@router.patch("/plants/{plant_id}", response_model=PlantRead, summary="更新工厂")
async def update_plant(
    plant_id: UUID,
    payload: PlantUpdate,
    session: SessionDep,
    _actor: PlantManageDep,
) -> Plant:
    return await service.update_plant(session, plant_id, payload)


@router.get("/departments", response_model=Page[DepartmentRead], summary="部门列表")
async def list_departments(
    session: SessionDep,
    _actor: DepartmentReadDep,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    organization_id: UUID | None = None,
    plant_id: UUID | None = None,
    parent_id: UUID | None = None,
    is_active: bool | None = None,
) -> Page[DepartmentRead]:
    return await service.list_departments(
        session,
        page=page,
        page_size=page_size,
        organization_id=organization_id,
        plant_id=plant_id,
        parent_id=parent_id,
        is_active=is_active,
    )


@router.post(
    "/departments",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建部门",
)
async def create_department(
    payload: DepartmentCreate, session: SessionDep, _actor: DepartmentManageDep
) -> Department:
    return await service.create_department(session, payload)


@router.get("/departments/{department_id}", response_model=DepartmentRead, summary="部门详情")
async def get_department(
    department_id: UUID, session: SessionDep, _actor: DepartmentReadDep
) -> Department:
    return await service.get_department(session, department_id)


@router.patch("/departments/{department_id}", response_model=DepartmentRead, summary="更新部门")
async def update_department(
    department_id: UUID,
    payload: DepartmentUpdate,
    session: SessionDep,
    _actor: DepartmentManageDep,
) -> Department:
    return await service.update_department(session, department_id, payload)
