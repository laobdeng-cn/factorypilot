from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.schemas.enterprise import OrganizationCreate
from app.schemas.identity import UserCreate, UserRead
from app.schemas.rbac import (
    BootstrapAdminRequest,
    BootstrapAdminResponse,
    PermissionRead,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    UserRolesRead,
)
from app.services import enterprise as enterprise_service
from app.services import identity as identity_service

SYSTEM_ADMIN_ROLE_CODE = "system_admin"


async def load_authorization(
    session: AsyncSession, user_id: UUID
) -> tuple[frozenset[str], frozenset[str]]:
    role_codes = frozenset(
        (
            await session.scalars(
                select(Role.code)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == user_id, Role.is_active.is_(True))
            )
        ).all()
    )
    permission_codes = frozenset(
        (
            await session.scalars(
                select(Permission.code)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .join(Role, Role.id == RolePermission.role_id)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(
                    UserRole.user_id == user_id,
                    Role.is_active.is_(True),
                    Permission.is_active.is_(True),
                )
                .distinct()
            )
        ).all()
    )
    return role_codes, permission_codes


async def list_permissions(session: AsyncSession) -> list[PermissionRead]:
    rows = list(
        (
            await session.scalars(
                select(Permission)
                .where(Permission.is_active.is_(True))
                .order_by(Permission.code)
            )
        ).all()
    )
    return [PermissionRead.model_validate(item) for item in rows]


async def _role_permission_codes(session: AsyncSession, role_id: UUID) -> list[str]:
    return list(
        (
            await session.scalars(
                select(Permission.code)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id == role_id)
                .order_by(Permission.code)
            )
        ).all()
    )


async def _role_read(session: AsyncSession, role: Role) -> RoleRead:
    return RoleRead(
        id=role.id,
        organization_id=role.organization_id,
        code=role.code,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        is_active=role.is_active,
        permission_codes=await _role_permission_codes(session, role.id),
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


async def list_roles(session: AsyncSession, organization_id: UUID) -> list[RoleRead]:
    rows = list(
        (
            await session.scalars(
                select(Role)
                .where(
                    or_(Role.organization_id.is_(None), Role.organization_id == organization_id)
                )
                .order_by(Role.is_system.desc(), Role.code)
            )
        ).all()
    )
    return [await _role_read(session, role) for role in rows]


async def get_role(session: AsyncSession, role_id: UUID, organization_id: UUID) -> Role:
    role = await session.get(Role, role_id)
    if role is None:
        raise AppError(code="rbac.role_not_found", message="Role not found", status_code=404)
    if role.organization_id is not None and role.organization_id != organization_id:
        raise AppError(code="rbac.role_not_found", message="Role not found", status_code=404)
    return role


async def create_role(
    session: AsyncSession, organization_id: UUID, payload: RoleCreate
) -> RoleRead:
    role = Role(
        organization_id=organization_id,
        code=payload.code.strip().lower(),
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        is_system=False,
        is_active=True,
    )
    session.add(role)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            code="rbac.role_code_conflict",
            message="Role code already exists",
            status_code=409,
        ) from exc
    await session.refresh(role)
    return await _role_read(session, role)


async def update_role(
    session: AsyncSession,
    role_id: UUID,
    organization_id: UUID,
    payload: RoleUpdate,
) -> RoleRead:
    role = await get_role(session, role_id, organization_id)
    if role.is_system:
        raise AppError(
            code="rbac.system_role_immutable",
            message="System roles cannot be modified",
            status_code=409,
        )
    data = payload.model_dump(exclude_unset=True)
    if data.get("name") is not None:
        data["name"] = data["name"].strip()
    if "description" in data and data["description"] is not None:
        data["description"] = data["description"].strip() or None
    for key, value in data.items():
        setattr(role, key, value)
    await session.commit()
    await session.refresh(role)
    return await _role_read(session, role)


async def set_role_permissions(
    session: AsyncSession,
    role_id: UUID,
    organization_id: UUID,
    permission_codes: list[str],
) -> RoleRead:
    role = await get_role(session, role_id, organization_id)
    if role.is_system:
        raise AppError(
            code="rbac.system_role_immutable",
            message="System role permissions cannot be modified",
            status_code=409,
        )

    normalized = sorted(set(code.strip() for code in permission_codes if code.strip()))
    permissions = list(
        (
            await session.scalars(
                select(Permission).where(
                    Permission.code.in_(normalized), Permission.is_active.is_(True)
                )
            )
        ).all()
    )
    if len(permissions) != len(normalized):
        found = {permission.code for permission in permissions}
        missing = sorted(set(normalized) - found)
        raise AppError(
            code="rbac.permission_not_found",
            message="One or more permissions do not exist",
            status_code=422,
            details={"missing": missing},
        )

    await session.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    session.add_all(
        RolePermission(role_id=role.id, permission_id=permission.id)
        for permission in permissions
    )
    await session.commit()
    return await _role_read(session, role)


async def get_user_roles(
    session: AsyncSession,
    user_id: UUID,
    actor_organization_id: UUID,
    actor_role_codes: frozenset[str],
) -> UserRolesRead:
    user = await identity_service.get_user(session, user_id)
    if (
        SYSTEM_ADMIN_ROLE_CODE not in actor_role_codes
        and user.organization_id != actor_organization_id
    ):
        raise AppError(code="user.not_found", message="User not found", status_code=404)

    roles = list(
        (
            await session.scalars(
                select(Role)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == user.id)
                .order_by(Role.code)
            )
        ).all()
    )
    return UserRolesRead(
        user_id=user.id,
        role_ids=[role.id for role in roles],
        role_codes=[role.code for role in roles],
    )


async def set_user_roles(
    session: AsyncSession,
    user_id: UUID,
    role_ids: list[UUID],
    *,
    actor_user_id: UUID,
    actor_organization_id: UUID,
    actor_role_codes: frozenset[str],
) -> UserRolesRead:
    user = await identity_service.get_user(session, user_id)
    if (
        SYSTEM_ADMIN_ROLE_CODE not in actor_role_codes
        and user.organization_id != actor_organization_id
    ):
        raise AppError(code="user.not_found", message="User not found", status_code=404)

    normalized_ids = sorted(set(role_ids), key=str)
    roles = list(
        (
            await session.scalars(
                select(Role).where(Role.id.in_(normalized_ids), Role.is_active.is_(True))
            )
        ).all()
    )
    if len(roles) != len(normalized_ids):
        raise AppError(
            code="rbac.role_not_found",
            message="One or more roles do not exist",
            status_code=422,
        )
    for role in roles:
        if role.organization_id is not None and role.organization_id != user.organization_id:
            raise AppError(
                code="rbac.role_scope_mismatch",
                message="Role does not belong to target user organization",
                status_code=409,
            )

    await session.execute(delete(UserRole).where(UserRole.user_id == user.id))
    session.add_all(
        UserRole(
            user_id=user.id,
            role_id=role.id,
            assigned_by_user_id=actor_user_id,
        )
        for role in roles
    )
    await session.commit()
    return await get_user_roles(
        session,
        user.id,
        actor_organization_id=actor_organization_id,
        actor_role_codes=actor_role_codes,
    )


async def claim_system_admin(session: AsyncSession, user: User) -> UserRolesRead:
    assignment_count = int(
        (await session.scalar(select(func.count()).select_from(UserRole))) or 0
    )
    if assignment_count != 0:
        raise AppError(
            code="rbac.bootstrap_closed",
            message="RBAC bootstrap is already complete",
            status_code=409,
        )
    role = await session.scalar(select(Role).where(Role.code == SYSTEM_ADMIN_ROLE_CODE))
    if role is None:
        raise AppError(
            code="rbac.system_role_missing",
            message="System administrator role is not seeded",
            status_code=500,
        )
    session.add(UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=user.id))
    await session.commit()
    return UserRolesRead(user_id=user.id, role_ids=[role.id], role_codes=[role.code])


async def bootstrap_initial_admin(
    session: AsyncSession, payload: BootstrapAdminRequest
) -> BootstrapAdminResponse:
    user_count = int((await session.scalar(select(func.count()).select_from(User))) or 0)
    assignment_count = int(
        (await session.scalar(select(func.count()).select_from(UserRole))) or 0
    )
    if user_count != 0 or assignment_count != 0:
        raise AppError(
            code="rbac.bootstrap_closed",
            message="Initial administrator bootstrap is already closed",
            status_code=409,
        )

    if payload.organization_id is not None:
        organization = await enterprise_service.get_organization(
            session, payload.organization_id
        )
    else:
        organization = await enterprise_service.create_organization(
            session,
            OrganizationCreate(
                code=payload.organization_code or "",
                name=payload.organization_name or "",
                short_name=None,
                is_active=True,
            ),
        )

    user = await identity_service.create_user(
        session,
        UserCreate(
            organization_id=organization.id,
            username=payload.username,
            employee_no=payload.employee_no,
            display_name=payload.display_name,
            email=payload.email,
            password=payload.password,
            is_active=True,
        ),
    )
    role = await session.scalar(select(Role).where(Role.code == SYSTEM_ADMIN_ROLE_CODE))
    if role is None:
        raise AppError(
            code="rbac.system_role_missing",
            message="System administrator role is not seeded",
            status_code=500,
        )
    session.add(UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=user.id))
    await session.commit()
    return BootstrapAdminResponse(
        organization_id=organization.id,
        user=UserRead.model_validate(user),
        role_codes=[role.code],
    )
