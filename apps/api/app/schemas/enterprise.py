from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Page[T](BaseModel):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int


class OrganizationCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    short_name: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class OrganizationUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    short_name: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    short_name: str | None
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


class PlantCreate(BaseModel):
    organization_id: UUID
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    timezone: str = Field(default="Asia/Shanghai", min_length=3, max_length=64)
    country_code: str = Field(default="CN", min_length=2, max_length=2)
    province: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=300)
    is_active: bool = True


class PlantUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    timezone: str | None = Field(default=None, min_length=3, max_length=64)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    province: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=300)
    is_active: bool | None = None


class PlantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    code: str
    name: str
    timezone: str
    country_code: str
    province: str | None
    city: str | None
    address: str | None
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


class DepartmentCreate(BaseModel):
    organization_id: UUID
    plant_id: UUID | None = None
    parent_id: UUID | None = None
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    department_type: str | None = Field(default=None, max_length=50)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class DepartmentUpdate(BaseModel):
    plant_id: UUID | None = None
    parent_id: UUID | None = None
    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    department_type: str | None = Field(default=None, max_length=50)
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    plant_id: UUID | None
    parent_id: UUID | None
    code: str
    name: str
    department_type: str | None
    sort_order: int
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime
