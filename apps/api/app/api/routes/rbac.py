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
    RoleDataScopeRead,
    RoleDataScopeUpdate,
    RolePermissionsUpdate,
    RoleRead,
    RoleUpdate,
    UserDataScopeRead,
    UserDataScopeUpdate,
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
DataScopeReadDep = Annotated[
    CurrentUser, Depends(require_permission("rbac.data_scope.read"))
]
DataScopeManageDep = Annotated[
    CurrentUser, Depends(require_permission("rbac.data_scope.manage"))
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
    return await service.create_role(
        session,
        actor.organization_id,
        payload,
        actor_user_id=actor.user_id,
        actor_data_scope=actor.data_scope,
    )


@router.get("/roles/{role_id}", response_model=RoleRead, summary="角色详情")
async def get_role(role_id: UUID, session: SessionDep, actor: RoleReadDep) -> RoleRead:
    role = await service.get_role(session, role_id, actor.organization_id)
    return await service._role_read(session, role)


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
    "/roles/{role_id}/data-scope",
    response_model=RoleDataScopeRead,
    summary="角色数据范围",
)
async def get_role_data_scope(
    role_id: UUID,
    session: SessionDep,
    actor: DataScopeReadDep,
) -> RoleDataScopeRead:
    return await service.get_role_data_scope(
        session,
        role_id,
        actor.organization_id,
    )


@router.put(
    "/roles/{role_id}/data-scope",
    response_model=RoleDataScopeRead,
    summary="替换角色数据范围",
)
async def set_role_data_scope(
    role_id: UUID,
    payload: RoleDataScopeUpdate,
    session: SessionDep,
    actor: DataScopeManageDep,
) -> RoleDataScopeRead:
    return await service.set_role_data_scope(
        session,
        role_id,
        actor.organization_id,
        payload.scope_type,
        actor_user_id=actor.user_id,
        actor_data_scope=actor.data_scope,
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
        actor_data_scope=actor.data_scope,
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
        actor_data_scope=actor.data_scope,
    )


@router.get(
    "/users/{user_id}/data-scope",
    response_model=UserDataScopeRead,
    summary="用户有效数据范围",
)
async def get_user_data_scope(
    user_id: UUID,
    session: SessionDep,
    actor: DataScopeReadDep,
) -> UserDataScopeRead:
    return await service.get_user_data_scope(
        session,
        user_id,
        actor_data_scope=actor.data_scope,
    )


@router.put(
    "/users/{user_id}/data-scope",
    response_model=UserDataScopeRead,
    summary="设置用户数据范围覆盖",
)
async def set_user_data_scope(
    user_id: UUID,
    payload: UserDataScopeUpdate,
    session: SessionDep,
    actor: DataScopeManageDep,
) -> UserDataScopeRead:
    return await service.set_user_data_scope(
        session,
        user_id,
        payload.scope_type,
        actor_user_id=actor.user_id,
        actor_data_scope=actor.data_scope,
    )
