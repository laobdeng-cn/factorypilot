from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.data_scope import DataScopeType
from app.schemas.identity import UserRead


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    module: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RoleCreate(BaseModel):
    code: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9._-]+$")
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    data_scope: DataScopeType = DataScopeType.SELF


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class RoleRead(BaseModel):
    id: UUID
    organization_id: UUID | None
    code: str
    name: str
    description: str | None
    is_system: bool
    is_active: bool
    data_scope: DataScopeType
    permission_codes: list[str]
    created_at: datetime
    updated_at: datetime


class RolePermissionsUpdate(BaseModel):
    permission_codes: list[str] = Field(default_factory=list, max_length=100)


class RoleDataScopeRead(BaseModel):
    role_id: UUID
    scope_type: DataScopeType


class RoleDataScopeUpdate(BaseModel):
    scope_type: DataScopeType


class UserRolesRead(BaseModel):
    user_id: UUID
    role_ids: list[UUID]
    role_codes: list[str]


class UserRolesUpdate(BaseModel):
    role_ids: list[UUID] = Field(default_factory=list, max_length=50)


class UserDataScopeRead(BaseModel):
    user_id: UUID
    role_scope_type: DataScopeType
    override_scope_type: DataScopeType | None
    effective_scope_type: DataScopeType
    source: str


class UserDataScopeUpdate(BaseModel):
    scope_type: DataScopeType | None = None


class BootstrapAdminRequest(BaseModel):
    organization_id: UUID | None = None
    organization_code: str | None = Field(
        default=None, min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$"
    )
    organization_name: str | None = Field(default=None, min_length=2, max_length=120)
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    employee_no: str = Field(min_length=1, max_length=50)
    display_name: str = Field(min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @model_validator(mode="after")
    def validate_organization_source(self) -> "BootstrapAdminRequest":
        if self.organization_id is None:
            if not self.organization_code or not self.organization_name:
                raise ValueError(
                    "organization_code and organization_name are required "
                    "when organization_id is omitted"
                )
        return self


class BootstrapAdminResponse(BaseModel):
    organization_id: UUID
    user: UserRead
    role_codes: list[str]
