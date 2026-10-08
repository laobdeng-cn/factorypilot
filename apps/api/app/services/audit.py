from datetime import datetime
from math import ceil
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.data_scope import DataScopeContext, DataScopeType
from app.db.session import AsyncSessionFactory
from app.models.audit import AuditLog, SecurityEvent
from app.schemas.audit import AuditLogRead, SecurityEventRead
from app.schemas.enterprise import Page


def _total_pages(total: int, page_size: int) -> int:
    return ceil(total / page_size) if total else 0


def _request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", maxsplit=1)[0].strip() or None
    return request.client.host if request.client is not None else None


def _route_name(request: Request) -> str:
    route = request.scope.get("route")
    name = getattr(route, "name", None)
    return str(name or f"{request.method.lower()}:{request.url.path}")[:128]


def _resource_type(request: Request) -> str:
    parts = [part for part in request.url.path.split("/") if part]
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1":
        value = parts[2]
    else:
        value = parts[0] if parts else "service"
    return value[:64]


def _resource_id(request: Request) -> str | None:
    for key, value in request.path_params.items():
        if key.endswith("_id"):
            return str(value)[:128]
    return None


def _result_for_status(status_code: int) -> str:
    if status_code < 400:
        return "success"
    if status_code in {401, 403, 423}:
        return "denied"
    return "error"


def _security_event_type(
    request: Request,
    status_code: int,
) -> tuple[str, str, str] | None:
    explicit = getattr(request.state, "security_event_type", None)
    if explicit:
        return (
            str(explicit),
            str(getattr(request.state, "security_event_category", "session")),
            str(getattr(request.state, "security_event_severity", "warning")),
        )

    path = request.url.path
    reason = getattr(request.state, "error_code", None)
    if path.endswith("/auth/login"):
        if status_code < 400:
            return ("auth.login_success", "authentication", "info")
        high_severity = reason in {"auth.account_locked", "auth.account_inactive"}
        return (
            str(reason or "auth.login_failed"),
            "authentication",
            "high" if high_severity else "warning",
        )
    if path.endswith("/auth/refresh"):
        if status_code < 400:
            return ("auth.refresh_success", "session", "info")
        severity = "high" if reason == "auth.refresh_token_reused" else "warning"
        return (str(reason or "auth.refresh_failed"), "session", severity)
    if path.endswith("/auth/logout") and status_code < 400:
        return ("auth.logout", "session", "info")
    if status_code in {401, 403, 423}:
        return (
            str(reason or "auth.authorization_denied"),
            "authorization",
            "warning",
        )
    return None


def _request_metadata(request: Request, status_code: int) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
    }
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if route_path:
        metadata["route"] = str(route_path)
    if request.url.query:
        metadata["query"] = request.url.query
    subject = getattr(request.state, "audit_subject", None)
    if subject is not None:
        metadata["subject"] = str(subject)
    authorization_result = getattr(request.state, "authorization_result", None)
    if authorization_result is not None:
        metadata["authorization_result"] = str(authorization_result)
    return metadata


async def persist_request_audit(request: Request, status_code: int) -> None:
    path = request.url.path
    if not path.startswith("/api/v1/") or path.startswith("/api/v1/health"):
        return

    actor_user_id = getattr(request.state, "actor_user_id", None)
    organization_id = getattr(request.state, "organization_id", None)
    session_id = getattr(request.state, "auth_session_id", None)
    error_reason = getattr(request.state, "error_code", None)
    explicit_reason = getattr(request.state, "security_event_reason", None)
    reason = explicit_reason or error_reason
    permission_code = getattr(request.state, "required_permission", None)
    scope_type = getattr(request.state, "data_scope_type", None)
    request_id = getattr(request.state, "request_id", None)
    metadata = _request_metadata(request, status_code)
    ip_address = _request_ip(request)
    user_agent = request.headers.get("user-agent")

    audit_log = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        session_id=session_id,
        action=_route_name(request),
        resource_type=_resource_type(request),
        resource_id=_resource_id(request),
        result=_result_for_status(status_code),
        reason=str(reason) if reason else None,
        permission_code=str(permission_code) if permission_code else None,
        scope_type=str(scope_type) if scope_type else None,
        request_id=str(request_id) if request_id else None,
        ip_address=ip_address,
        user_agent=user_agent[:512] if user_agent else None,
        metadata_json=metadata,
    )

    security_descriptor = _security_event_type(request, status_code)
    async with AsyncSessionFactory() as session:
        session.add(audit_log)
        if security_descriptor is not None:
            event_type, category, severity = security_descriptor
            session.add(
                SecurityEvent(
                    organization_id=organization_id,
                    actor_user_id=actor_user_id,
                    session_id=session_id,
                    event_type=event_type[:128],
                    category=category[:64],
                    severity=severity[:16],
                    outcome=_result_for_status(status_code),
                    reason=str(reason) if reason else None,
                    request_id=str(request_id) if request_id else None,
                    ip_address=ip_address,
                    user_agent=user_agent[:512] if user_agent else None,
                    metadata_json=metadata,
                )
            )
        await session.commit()


def _append_scope_filter(
    filters: list[ColumnElement[bool]],
    organization_column: Any,
    data_scope: DataScopeContext,
) -> None:
    if data_scope.scope_type is DataScopeType.GLOBAL:
        return
    filters.append(organization_column == data_scope.organization_id)


def _audit_read(item: AuditLog) -> AuditLogRead:
    return AuditLogRead(
        id=item.id,
        organization_id=item.organization_id,
        actor_user_id=item.actor_user_id,
        session_id=item.session_id,
        action=item.action,
        resource_type=item.resource_type,
        resource_id=item.resource_id,
        result=item.result,
        reason=item.reason,
        permission_code=item.permission_code,
        scope_type=item.scope_type,
        request_id=item.request_id,
        ip_address=item.ip_address,
        user_agent=item.user_agent,
        metadata=item.metadata_json,
        occurred_at=item.occurred_at,
    )


def _security_read(item: SecurityEvent) -> SecurityEventRead:
    return SecurityEventRead(
        id=item.id,
        organization_id=item.organization_id,
        actor_user_id=item.actor_user_id,
        session_id=item.session_id,
        event_type=item.event_type,
        category=item.category,
        severity=item.severity,
        outcome=item.outcome,
        reason=item.reason,
        request_id=item.request_id,
        ip_address=item.ip_address,
        user_agent=item.user_agent,
        metadata=item.metadata_json,
        occurred_at=item.occurred_at,
    )


async def list_audit_logs(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    data_scope: DataScopeContext,
    actor_user_id: UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    result: str | None = None,
    permission_code: str | None = None,
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
    authorization_only: bool = False,
) -> Page[AuditLogRead]:
    filters: list[ColumnElement[bool]] = []
    _append_scope_filter(filters, AuditLog.organization_id, data_scope)
    if actor_user_id is not None:
        filters.append(AuditLog.actor_user_id == actor_user_id)
    if action:
        filters.append(AuditLog.action == action)
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    if result:
        filters.append(AuditLog.result == result)
    if permission_code:
        filters.append(AuditLog.permission_code == permission_code)
    if occurred_from is not None:
        filters.append(AuditLog.occurred_at >= occurred_from)
    if occurred_to is not None:
        filters.append(AuditLog.occurred_at <= occurred_to)
    if authorization_only:
        filters.append(AuditLog.permission_code.is_not(None))

    total = int(
        (
            await session.scalar(
                select(func.count()).select_from(AuditLog).where(*filters)
            )
        )
        or 0
    )
    rows = list(
        (
            await session.scalars(
                select(AuditLog)
                .where(*filters)
                .order_by(AuditLog.occurred_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
    )
    return Page[AuditLogRead](
        items=[_audit_read(item) for item in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
    )


async def list_security_events(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    data_scope: DataScopeContext,
    actor_user_id: UUID | None = None,
    event_type: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    outcome: str | None = None,
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
) -> Page[SecurityEventRead]:
    filters: list[ColumnElement[bool]] = []
    _append_scope_filter(filters, SecurityEvent.organization_id, data_scope)
    if actor_user_id is not None:
        filters.append(SecurityEvent.actor_user_id == actor_user_id)
    if event_type:
        filters.append(SecurityEvent.event_type == event_type)
    if category:
        filters.append(SecurityEvent.category == category)
    if severity:
        filters.append(SecurityEvent.severity == severity)
    if outcome:
        filters.append(SecurityEvent.outcome == outcome)
    if occurred_from is not None:
        filters.append(SecurityEvent.occurred_at >= occurred_from)
    if occurred_to is not None:
        filters.append(SecurityEvent.occurred_at <= occurred_to)

    total = int(
        (
            await session.scalar(
                select(func.count()).select_from(SecurityEvent).where(*filters)
            )
        )
        or 0
    )
    rows = list(
        (
            await session.scalars(
                select(SecurityEvent)
                .where(*filters)
                .order_by(SecurityEvent.occurred_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
    )
    return Page[SecurityEventRead](
        items=[_security_read(item) for item in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
    )
