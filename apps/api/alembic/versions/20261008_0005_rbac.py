"""Create RBAC roles, permissions and assignments.

Revision ID: 20261008_0005
Revises: 20261008_0004
Create Date: 2026-10-08
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "20261008_0005"
down_revision: str | None = "20261008_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = [
    (
        "10000000-0000-0000-0000-000000000001",
        "enterprise.organization.read",
        "组织查看",
        "enterprise",
    ),
    (
        "10000000-0000-0000-0000-000000000002",
        "enterprise.organization.manage",
        "组织管理",
        "enterprise",
    ),
    (
        "10000000-0000-0000-0000-000000000003",
        "enterprise.plant.read",
        "工厂查看",
        "enterprise",
    ),
    (
        "10000000-0000-0000-0000-000000000004",
        "enterprise.plant.manage",
        "工厂管理",
        "enterprise",
    ),
    (
        "10000000-0000-0000-0000-000000000005",
        "enterprise.department.read",
        "部门查看",
        "enterprise",
    ),
    (
        "10000000-0000-0000-0000-000000000006",
        "enterprise.department.manage",
        "部门管理",
        "enterprise",
    ),
    ("10000000-0000-0000-0000-000000000007", "identity.user.read", "用户查看", "identity"),
    ("10000000-0000-0000-0000-000000000008", "identity.user.manage", "用户管理", "identity"),
    ("10000000-0000-0000-0000-000000000009", "rbac.permission.read", "权限查看", "rbac"),
    ("10000000-0000-0000-0000-000000000010", "rbac.role.read", "角色查看", "rbac"),
    ("10000000-0000-0000-0000-000000000011", "rbac.role.manage", "角色管理", "rbac"),
    ("10000000-0000-0000-0000-000000000012", "rbac.user_role.read", "用户角色查看", "rbac"),
    ("10000000-0000-0000-0000-000000000013", "rbac.user_role.manage", "用户角色管理", "rbac"),
]

ROLES = [
    (
        "20000000-0000-0000-0000-000000000001",
        "system_admin",
        "系统管理员",
        "FactoryPilot 全局系统管理员",
    ),
    (
        "20000000-0000-0000-0000-000000000002",
        "factory_manager",
        "工厂经理",
        "工厂运营基础管理角色",
    ),
    (
        "20000000-0000-0000-0000-000000000003",
        "viewer",
        "只读用户",
        "企业基础信息只读角色",
    ),
]


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])
    op.create_index("ix_permissions_module", "permissions", ["module"])
    op.create_index("ix_permissions_is_active", "permissions", ["is_active"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])
    op.create_index("ix_roles_code", "roles", ["code"])
    op.create_index("ix_roles_is_system", "roles", ["is_system"])
    op.create_index("ix_roles_is_active", "roles", ["is_active"])

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    permission_table = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("module", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        permission_table,
        [
            {
                "id": UUID(permission_id),
                "code": code,
                "name": name,
                "module": module,
                "description": None,
                "is_active": True,
            }
            for permission_id, code, name, module in PERMISSIONS
        ],
    )

    role_table = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_system", sa.Boolean()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        role_table,
        [
            {
                "id": UUID(role_id),
                "organization_id": None,
                "code": code,
                "name": name,
                "description": description,
                "is_system": True,
                "is_active": True,
            }
            for role_id, code, name, description in ROLES
        ],
    )

    permission_ids = {code: UUID(permission_id) for permission_id, code, _, _ in PERMISSIONS}
    role_ids = {code: UUID(role_id) for role_id, code, _, _ in ROLES}
    all_codes = [code for _, code, _, _ in PERMISSIONS]
    role_permissions = {
        "system_admin": all_codes,
        "factory_manager": [
            "enterprise.organization.read",
            "enterprise.plant.read",
            "enterprise.plant.manage",
            "enterprise.department.read",
            "enterprise.department.manage",
            "identity.user.read",
            "rbac.role.read",
            "rbac.user_role.read",
        ],
        "viewer": [
            "enterprise.organization.read",
            "enterprise.plant.read",
            "enterprise.department.read",
            "identity.user.read",
        ],
    }
    role_permission_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )
    op.bulk_insert(
        role_permission_table,
        [
            {"role_id": role_ids[role_code], "permission_id": permission_ids[permission_code]}
            for role_code, codes in role_permissions.items()
            for permission_code in codes
        ],
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_index("ix_roles_is_active", table_name="roles")
    op.drop_index("ix_roles_is_system", table_name="roles")
    op.drop_index("ix_roles_code", table_name="roles")
    op.drop_index("ix_roles_organization_id", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_permissions_is_active", table_name="permissions")
    op.drop_index("ix_permissions_module", table_name="permissions")
    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")
