from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class DataScopeType(StrEnum):
    SELF = "self"
    DEPARTMENT = "department"
    PLANT = "plant"
    ORGANIZATION = "organization"
    GLOBAL = "global"


_SCOPE_RANK = {
    DataScopeType.SELF: 0,
    DataScopeType.DEPARTMENT: 1,
    DataScopeType.PLANT: 2,
    DataScopeType.ORGANIZATION: 3,
    DataScopeType.GLOBAL: 4,
}


def scope_rank(scope_type: DataScopeType) -> int:
    return _SCOPE_RANK[scope_type]


def most_permissive(scopes: list[DataScopeType]) -> DataScopeType:
    if not scopes:
        return DataScopeType.SELF
    return max(scopes, key=scope_rank)


@dataclass(frozen=True, slots=True)
class DataScopeContext:
    scope_type: DataScopeType
    user_id: UUID
    organization_id: UUID
    primary_plant_id: UUID | None
    department_id: UUID | None
    source: str

    def can_access_organization(self, organization_id: UUID) -> bool:
        return (
            self.scope_type is DataScopeType.GLOBAL
            or organization_id == self.organization_id
        )

    def can_create_organization(self) -> bool:
        return self.scope_type is DataScopeType.GLOBAL

    def can_access_plant(self, *, plant_id: UUID, organization_id: UUID) -> bool:
        if self.scope_type is DataScopeType.GLOBAL:
            return True
        if organization_id != self.organization_id:
            return False
        if self.scope_type is DataScopeType.ORGANIZATION:
            return True
        return self.primary_plant_id is not None and plant_id == self.primary_plant_id

    def can_create_plant(self, *, organization_id: UUID) -> bool:
        if self.scope_type is DataScopeType.GLOBAL:
            return True
        return (
            self.scope_type is DataScopeType.ORGANIZATION
            and organization_id == self.organization_id
        )

    def can_access_department(
        self,
        *,
        department_id: UUID,
        organization_id: UUID,
        plant_id: UUID | None,
    ) -> bool:
        if self.scope_type is DataScopeType.GLOBAL:
            return True
        if organization_id != self.organization_id:
            return False
        if self.scope_type is DataScopeType.ORGANIZATION:
            return True
        if self.scope_type is DataScopeType.PLANT:
            return self.primary_plant_id is not None and plant_id == self.primary_plant_id
        return self.department_id is not None and department_id == self.department_id

    def can_create_department(
        self,
        *,
        organization_id: UUID,
        plant_id: UUID | None,
    ) -> bool:
        if self.scope_type is DataScopeType.GLOBAL:
            return True
        if organization_id != self.organization_id:
            return False
        if self.scope_type is DataScopeType.ORGANIZATION:
            return True
        return (
            self.scope_type is DataScopeType.PLANT
            and self.primary_plant_id is not None
            and plant_id == self.primary_plant_id
        )

    def can_access_user(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        primary_plant_id: UUID | None,
        department_id: UUID | None,
    ) -> bool:
        if user_id == self.user_id:
            return True
        if self.scope_type is DataScopeType.GLOBAL:
            return True
        if organization_id != self.organization_id:
            return False
        if self.scope_type is DataScopeType.ORGANIZATION:
            return True
        if self.scope_type is DataScopeType.PLANT:
            return (
                self.primary_plant_id is not None
                and primary_plant_id == self.primary_plant_id
            )
        if self.scope_type is DataScopeType.DEPARTMENT:
            return (
                self.department_id is not None
                and department_id == self.department_id
            )
        return False

    def can_create_user(
        self,
        *,
        organization_id: UUID,
        primary_plant_id: UUID | None,
        department_id: UUID | None,
    ) -> bool:
        if self.scope_type is DataScopeType.GLOBAL:
            return True
        if organization_id != self.organization_id:
            return False
        if self.scope_type is DataScopeType.ORGANIZATION:
            return True
        if self.scope_type is DataScopeType.PLANT:
            return (
                self.primary_plant_id is not None
                and primary_plant_id == self.primary_plant_id
            )
        if self.scope_type is DataScopeType.DEPARTMENT:
            return (
                self.department_id is not None
                and department_id == self.department_id
            )
        return False
