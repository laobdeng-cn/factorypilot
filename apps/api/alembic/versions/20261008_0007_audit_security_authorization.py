"""Add audit log, security event and authorization audit foundation.

Revision ID: 20261008_0007
Revises: 20261008_0006
Create Date: 2026-10-08
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "20261008_0007"
down_revision: str | None = "20261008_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

AUDIT_LOG_READ_ID = UUID("10000000-0000-0000-0000-000000000016")
SECURITY_EVENT_READ_ID = UUID("10000000-0000-0000-0000-000000000017")
AUTHORIZATION_AUDIT_READ_ID = UUID("10000000-0000-0000-0000-000000000018")
SYSTEM_ADMIN_ROLE_ID = UUID("20000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=128), nullable=True),
        sa.Column("permission_code", sa.String(length=128), nullable=True),
        sa.Column("scope_type", sa.String(length=32), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "metadata_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_occurred_at", "audit_logs", ["occurred_at"])
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])
    op.create_index("ix_audit_logs_result", "audit_logs", ["result"])
    op.create_index("ix_audit_logs_permission_code", "audit_logs", ["permission_code"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])

    op.create_table(
        "security_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=128), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "metadata_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_events_occurred_at", "security_events", ["occurred_at"])
    op.create_index(
        "ix_security_events_organization_id",
        "security_events",
        ["organization_id"],
    )
    op.create_index(
        "ix_security_events_actor_user_id",
        "security_events",
        ["actor_user_id"],
    )
    op.create_index("ix_security_events_event_type", "security_events", ["event_type"])
    op.create_index("ix_security_events_category", "security_events", ["category"])
    op.create_index("ix_security_events_severity", "security_events", ["severity"])
    op.create_index("ix_security_events_outcome", "security_events", ["outcome"])
    op.create_index("ix_security_events_request_id", "security_events", ["request_id"])

    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION factorypilot_prevent_audit_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'audit records are immutable';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    for table_name in ("audit_logs", "security_events"):
        op.execute(
            sa.text(
                f"""
                CREATE TRIGGER trg_{table_name}_immutable
                BEFORE UPDATE OR DELETE ON {table_name}
                FOR EACH ROW EXECUTE FUNCTION factorypilot_prevent_audit_mutation();
                """
            )
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
                "id": AUDIT_LOG_READ_ID,
                "code": "audit.log.read",
                "name": "审计日志查看",
                "module": "audit",
                "description": "查看不可变业务与操作审计日志",
                "is_active": True,
            },
            {
                "id": SECURITY_EVENT_READ_ID,
                "code": "audit.security_event.read",
                "name": "安全事件查看",
                "module": "audit",
                "description": "查看认证、会话与安全异常事件",
                "is_active": True,
            },
            {
                "id": AUTHORIZATION_AUDIT_READ_ID,
                "code": "audit.authorization.read",
                "name": "授权审计查看",
                "module": "audit",
                "description": "查看 RBAC 权限判定与授权审计记录",
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
            {"role_id": SYSTEM_ADMIN_ROLE_ID, "permission_id": AUDIT_LOG_READ_ID},
            {"role_id": SYSTEM_ADMIN_ROLE_ID, "permission_id": SECURITY_EVENT_READ_ID},
            {
                "role_id": SYSTEM_ADMIN_ROLE_ID,
                "permission_id": AUTHORIZATION_AUDIT_READ_ID,
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (
                '10000000-0000-0000-0000-000000000016',
                '10000000-0000-0000-0000-000000000017',
                '10000000-0000-0000-0000-000000000018'
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM permissions
            WHERE id IN (
                '10000000-0000-0000-0000-000000000016',
                '10000000-0000-0000-0000-000000000017',
                '10000000-0000-0000-0000-000000000018'
            )
            """
        )
    )
    for table_name in ("security_events", "audit_logs"):
        op.execute(
            sa.text(
                f"DROP TRIGGER IF EXISTS trg_{table_name}_immutable ON {table_name}"
            )
        )
    op.execute(sa.text("DROP FUNCTION IF EXISTS factorypilot_prevent_audit_mutation"))

    op.drop_index("ix_security_events_request_id", table_name="security_events")
    op.drop_index("ix_security_events_outcome", table_name="security_events")
    op.drop_index("ix_security_events_severity", table_name="security_events")
    op.drop_index("ix_security_events_category", table_name="security_events")
    op.drop_index("ix_security_events_event_type", table_name="security_events")
    op.drop_index("ix_security_events_actor_user_id", table_name="security_events")
    op.drop_index("ix_security_events_organization_id", table_name="security_events")
    op.drop_index("ix_security_events_occurred_at", table_name="security_events")
    op.drop_table("security_events")

    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_permission_code", table_name="audit_logs")
    op.drop_index("ix_audit_logs_result", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_organization_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_occurred_at", table_name="audit_logs")
    op.drop_table("audit_logs")
