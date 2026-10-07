"""Create organization, plant and department foundation.

Revision ID: 20261008_0002
Revises: 20261008_0001
Create Date: 2026-10-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261008_0002"
down_revision: str | None = "20261008_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _common_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("short_name", sa.String(length=100), nullable=True),
        *_common_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_organizations_code"),
    )

    op.create_table(
        "plants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Asia/Shanghai"),
        sa.Column("country_code", sa.String(length=2), nullable=False, server_default="CN"),
        sa.Column("province", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("address", sa.String(length=300), nullable=True),
        *_common_columns(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_plants_org_code"),
    )
    op.create_index("ix_plants_organization_id", "plants", ["organization_id"])

    op.create_table(
        "departments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("plant_id", sa.Uuid(), nullable=True),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("department_type", sa.String(length=50), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_common_columns(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["plant_id"], ["plants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_departments_org_code"),
    )
    op.create_index("ix_departments_organization_id", "departments", ["organization_id"])
    op.create_index("ix_departments_plant_id", "departments", ["plant_id"])
    op.create_index("ix_departments_parent_id", "departments", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_departments_parent_id", table_name="departments")
    op.drop_index("ix_departments_plant_id", table_name="departments")
    op.drop_index("ix_departments_organization_id", table_name="departments")
    op.drop_table("departments")
    op.drop_index("ix_plants_organization_id", table_name="plants")
    op.drop_table("plants")
    op.drop_table("organizations")
