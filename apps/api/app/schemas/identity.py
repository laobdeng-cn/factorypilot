from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    organization_id: UUID
    department_id: UUID | None = None
    primary_plant_id: UUID | None = None
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    employee_no: str = Field(min_length=1, max_length=50)
    display_name: str = Field(min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    mobile: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=12, max_length=128)
    is_active: bool = True


class UserUpdate(BaseModel):
    department_id: UUID | None = None
    primary_plant_id: UUID | None = None
    username: str | None = Field(
        default=None, min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._-]+$"
    )
    employee_no: str | None = Field(default=None, min_length=1, max_length=50)
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    mobile: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    department_id: UUID | None
    primary_plant_id: UUID | None
    username: str
    employee_no: str
    display_name: str
    email: str | None
    mobile: str | None
    is_active: bool
    failed_login_count: int
    locked_until: datetime | None
    last_login_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime


class PasswordChange(BaseModel):
    new_password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    authenticated: bool = True
    user: UserRead
