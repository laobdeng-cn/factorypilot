from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, CurrentUserDep, require_permission
from app.db.session import get_db_session
from app.schemas.rbac import (
    BootstrapAdminRequest,
    BootstrapAdminResponse,
    PermissionRead,
    RoleCreate,
    RolePermissionsUpdate,
    RoleRead,
    RoleUpdate,
    UserRolesRead,
    UserRolesUpdate,
)
from app.services import rbac as service

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
PermissionReadDep = Annotated[
    CurrentUser, Depends(require_permission("rbac.permission.read"))
]
RoleReadDep = Annotated[CurrentUser, Depends(require_permission("rbac.role.read"))]
RoleManageDep = Annotated[CurrentUser, Depends(require_permission("rbac.role.manage"))]
UserRoleReadDep = Annotated[
    CurrentUser, Depends(require_permission("rbac.user_role.read"))
]
UserRoleManageDep = Annotated[
    CurrentUser, Depends(require_permission("rbac.user_role.manage"))
]


@router.post(
    "/rbac/bootstrap",
    response_model=BootstrapAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="首次部署创建系统管理员",
)
async def bootstrap_admin(
    payload: BootstrapAdminRequest, session: SessionDep
) -> BootstrapAdminResponse:
    return await service.bootstrap_initial_admin(session, payload)


@router.post(
    "/rbac/claim-system-admin",
    response_model=UserRolesRead,
    summary="升级已有用户为首个系统管理员",
)
async def claim_system_admin(
    current_user: CurrentUserDep, session: SessionDep
) -> UserRolesRead:
    return await service.claim_system_admin(session, current_user.user)


@router.get("/permissions", response_model=list[PermissionRead], summary="权限列表")
async def list_permissions(
    session: SessionDep, _actor: PermissionReadDep
) -> list[PermissionRead]:
    return await service.list_permissions(session)


@router.get("/roles", response_model=list[RoleRead], summary="角色列表")
async def list_roles(session: SessionDep, actor: RoleReadDep) -> list[RoleRead]:
    return await service.list_roles(session, actor.organization_id)


@router.post(
    "/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建角色",
)
async def create_role(
    payload: RoleCreate, session: SessionDep, actor: RoleManageDep
) -> RoleRead:
    return await service.create_role(session, actor.organization_id, payload)


@router.get("/roles/{role_id}", response_model=RoleRead, summary="角色详情")
async def get_role(role_id: UUID, session: SessionDep, actor: RoleReadDep) -> RoleRead:
    role = await service.get_role(session, role_id, actor.organization_id)
    permission_codes = await service._role_permission_codes(session, role.id)
    return RoleRead(
        id=role.id,
        organization_id=role.organization_id,
        code=role.code,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        is_active=role.is_active,
        permission_codes=permission_codes,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.patch("/roles/{role_id}", response_model=RoleRead, summary="更新角色")
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    session: SessionDep,
    actor: RoleManageDep,
) -> RoleRead:
    return await service.update_role(session, role_id, actor.organization_id, payload)


@router.put(
    "/roles/{role_id}/permissions",
    response_model=RoleRead,
    summary="替换角色权限",
)
async def set_role_permissions(
    role_id: UUID,
    payload: RolePermissionsUpdate,
    session: SessionDep,
    actor: RoleManageDep,
) -> RoleRead:
    return await service.set_role_permissions(
        session,
        role_id,
        actor.organization_id,
        payload.permission_codes,
    )


@router.get(
    "/users/{user_id}/roles",
    response_model=UserRolesRead,
    summary="用户角色列表",
)
async def get_user_roles(
    user_id: UUID, session: SessionDep, actor: UserRoleReadDep
) -> UserRolesRead:
    return await service.get_user_roles(
        session,
        user_id,
        actor_organization_id=actor.organization_id,
        actor_role_codes=actor.role_codes,
    )


@router.put(
    "/users/{user_id}/roles",
    response_model=UserRolesRead,
    summary="替换用户角色",
)
async def set_user_roles(
    user_id: UUID,
    payload: UserRolesUpdate,
    session: SessionDep,
    actor: UserRoleManageDep,
) -> UserRolesRead:
    return await service.set_user_roles(
        session,
        user_id,
        payload.role_ids,
        actor_user_id=actor.user_id,
        actor_organization_id=actor.organization_id,
        actor_role_codes=actor.role_codes,
    )
