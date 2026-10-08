from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_permission
from app.db.session import get_db_session
from app.schemas.audit import AuditLogRead, SecurityEventRead
from app.schemas.enterprise import Page
from app.services import audit as service

router = APIRouter(prefix="/audit")
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
PageParam = Annotated[int, Query(ge=1)]
PageSizeParam = Annotated[int, Query(ge=1, le=100)]
AuditLogReadDep = Annotated[CurrentUser, Depends(require_permission("audit.log.read"))]
SecurityReadDep = Annotated[
    CurrentUser,
    Depends(require_permission("audit.security_event.read")),
]
AuthorizationReadDep = Annotated[
    CurrentUser,
    Depends(require_permission("audit.authorization.read")),
]


@router.get("/logs", response_model=Page[AuditLogRead], summary="审计日志")
async def list_audit_logs(
    session: SessionDep,
    actor: AuditLogReadDep,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    actor_user_id: UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    result: str | None = None,
    permission_code: str | None = None,
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
) -> Page[AuditLogRead]:
    return await service.list_audit_logs(
        session,
        page=page,
        page_size=page_size,
        data_scope=actor.data_scope,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        result=result,
        permission_code=permission_code,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
    )


@router.get(
    "/authorization",
    response_model=Page[AuditLogRead],
    summary="授权判定审计",
)
async def list_authorization_audit(
    session: SessionDep,
    actor: AuthorizationReadDep,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    actor_user_id: UUID | None = None,
    result: str | None = None,
    permission_code: str | None = None,
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
) -> Page[AuditLogRead]:
    return await service.list_audit_logs(
        session,
        page=page,
        page_size=page_size,
        data_scope=actor.data_scope,
        actor_user_id=actor_user_id,
        result=result,
        permission_code=permission_code,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
        authorization_only=True,
    )


@router.get(
    "/security-events",
    response_model=Page[SecurityEventRead],
    summary="安全事件",
)
async def list_security_events(
    session: SessionDep,
    actor: SecurityReadDep,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    actor_user_id: UUID | None = None,
    event_type: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    outcome: str | None = None,
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
) -> Page[SecurityEventRead]:
    return await service.list_security_events(
        session,
        page=page,
        page_size=page_size,
        data_scope=actor.data_scope,
        actor_user_id=actor_user_id,
        event_type=event_type,
        category=category,
        severity=severity,
        outcome=outcome,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
    )
