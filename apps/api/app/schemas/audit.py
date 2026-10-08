from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: UUID
    organization_id: UUID | None
    actor_user_id: UUID | None
    session_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    result: str
    reason: str | None
    permission_code: str | None
    scope_type: str | None
    request_id: str | None
    ip_address: str | None
    user_agent: str | None
    metadata: dict[str, Any]
    occurred_at: datetime


class SecurityEventRead(BaseModel):
    id: UUID
    organization_id: UUID | None
    actor_user_id: UUID | None
    session_id: UUID | None
    event_type: str
    category: str
    severity: str
    outcome: str
    reason: str | None
    request_id: str | None
    ip_address: str | None
    user_agent: str | None
    metadata: dict[str, Any]
    occurred_at: datetime
