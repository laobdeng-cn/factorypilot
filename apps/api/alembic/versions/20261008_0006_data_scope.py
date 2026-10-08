"""Add hierarchical data scope foundation.

Revision ID: 20261008_0006
Revises: 20261008_0005
Create Date: 2026-10-08
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "20261008_0006"
down_revision: str | None = "20261008_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DATA_SCOPE_VALUES = ("self", "department", "plant", "organization", "global")
DATA_SCOPE_READ_ID = UUID("10000000-0000-0000-0000-000000000014")
DATA_SCOPE_MANAGE_ID = UUID("10000000-0000-0000-0000-000000000015")
SYSTEM_ADMIN_ROLE_ID = UUID("20000000-0000-0000-0000-000000000001")
FACTORY_MANAGER_ROLE_ID = UUID("20000000-0000-0000-0000-000000000002")
VIEWER_ROLE_ID = UUID("20000000-0000-0000-0000-000000000003")


def upgrade() -> None:
    op.create_table(
        "role_data_scopes",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "scope_type IN ('self','department','plant','organization','global')",
            name="ck_role_data_scopes_scope_type",
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("role_id"),
    )
    op.create_index(
        "ix_role_data_scopes_scope_type",
        "role_data_scopes",
        ["scope_type"],
    )

    op.create_table(
        "user_data_scope_overrides",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "scope_type IN ('self','department','plant','organization','global')",
            name="ck_user_data_scope_overrides_scope_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        "ix_user_data_scope_overrides_scope_type",
        "user_data_scope_overrides",
        ["scope_type"],
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
                "id": DATA_SCOPE_READ_ID,
                "code": "rbac.data_scope.read",
                "name": "数据范围查看",
                "module": "rbac",
                "description": None,
                "is_active": True,
            },
            {
                "id": DATA_SCOPE_MANAGE_ID,
                "code": "rbac.data_scope.manage",
                "name": "数据范围管理",
                "module": "rbac",
                "description": None,
                "is_active": True,
            },
        ],
    )

    role_permission_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )
    op.bulk_insert(
        role_permission_table,
        [
            {
                "role_id": SYSTEM_ADMIN_ROLE_ID,
                "permission_id": DATA_SCOPE_READ_ID,
            },
            {
                "role_id": SYSTEM_ADMIN_ROLE_ID,
                "permission_id": DATA_SCOPE_MANAGE_ID,
            },
            {
                "role_id": FACTORY_MANAGER_ROLE_ID,
                "permission_id": DATA_SCOPE_READ_ID,
            },
        ],
    )

    role_scope_table = sa.table(
        "role_data_scopes",
        sa.column("role_id", sa.Uuid()),
        sa.column("scope_type", sa.String()),
        sa.column("updated_by_user_id", sa.Uuid()),
    )
    op.bulk_insert(
        role_scope_table,
        [
            {
                "role_id": SYSTEM_ADMIN_ROLE_ID,
                "scope_type": "global",
                "updated_by_user_id": None,
            },
            {
                "role_id": FACTORY_MANAGER_ROLE_ID,
                "scope_type": "plant",
                "updated_by_user_id": None,
            },
            {
                "role_id": VIEWER_ROLE_ID,
                "scope_type": "organization",
                "updated_by_user_id": None,
            },
        ],
    )
    op.execute(
        sa.text(
            """
            INSERT INTO role_data_scopes (role_id, scope_type, updated_by_user_id)
            SELECT roles.id, 'self', NULL
            FROM roles
            WHERE NOT EXISTS (
                SELECT 1
                FROM role_data_scopes
                WHERE role_data_scopes.role_id = roles.id
            )
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (
                '10000000-0000-0000-0000-000000000014',
                '10000000-0000-0000-0000-000000000015'
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM permissions
            WHERE id IN (
                '10000000-0000-0000-0000-000000000014',
                '10000000-0000-0000-0000-000000000015'
            )
            """
        )
    )
    op.drop_index(
        "ix_user_data_scope_overrides_scope_type",
        table_name="user_data_scope_overrides",
    )
    op.drop_table("user_data_scope_overrides")
    op.drop_index(
        "ix_role_data_scopes_scope_type",
        table_name="role_data_scopes",
    )
    op.drop_table("role_data_scopes")
