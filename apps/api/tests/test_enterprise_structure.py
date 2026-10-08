from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db.session import AsyncSessionFactory
from app.main import app
from app.models.enterprise import Department, Organization, Plant
from app.models.user import User


@pytest.mark.asyncio
async def test_enterprise_structure_crud_flow() -> None:
    suffix = uuid4().hex[:8].upper()
    organization_id: str | None = None
    user_id: str | None = None
    plant_id: str | None = None
    department_id: str | None = None
    password = "FactoryPilot#2026!"
    username = f"admin.{suffix.lower()}"

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/rbac/bootstrap",
                json={
                    "organization_code": f"ORG-{suffix}",
                    "organization_name": "华南精密电子有限公司",
                    "username": username,
                    "employee_no": f"ADM-{suffix}",
                    "display_name": "企业结构测试管理员",
                    "password": password,
                },
            )
            assert response.status_code == 201
            bootstrap = response.json()
            organization_id = bootstrap["organization_id"]
            user_id = bootstrap["user"]["id"]

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": password},
            )
            assert response.status_code == 200
            headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

            response = await client.get(
                f"/api/v1/organizations/{organization_id}", headers=headers
            )
            assert response.status_code == 200
            assert response.json()["code"] == f"ORG-{suffix}"

            response = await client.post(
                "/api/v1/plants",
                headers=headers,
                json={
                    "organization_id": organization_id,
                    "code": f"DG-{suffix}",
                    "name": "东莞制造基地",
                    "province": "广东省",
                    "city": "东莞市",
                },
            )
            assert response.status_code == 201
            plant = response.json()
            plant_id = plant["id"]
            assert plant["organization_id"] == organization_id

            response = await client.post(
                "/api/v1/departments",
                headers=headers,
                json={
                    "organization_id": organization_id,
                    "plant_id": plant_id,
                    "code": f"PMC-{suffix}",
                    "name": "生产计划与物控部",
                    "department_type": "pmc",
                    "sort_order": 10,
                },
            )
            assert response.status_code == 201
            department = response.json()
            department_id = department["id"]
            assert department["plant_id"] == plant_id

            response = await client.get(
                "/api/v1/departments",
                headers=headers,
                params={"organization_id": organization_id, "plant_id": plant_id},
            )
            assert response.status_code == 200
            page = response.json()
            assert page["total"] >= 1
            assert any(item["id"] == department_id for item in page["items"])

            response = await client.patch(
                f"/api/v1/departments/{department_id}",
                headers=headers,
                json={"is_active": False},
            )
            assert response.status_code == 200
            assert response.json()["is_active"] is False
            assert response.json()["version"] == 2
    finally:
        async with AsyncSessionFactory() as session:
            if user_id is not None:
                await session.execute(delete(User).where(User.id == user_id))
            if department_id is not None:
                await session.execute(delete(Department).where(Department.id == department_id))
            if plant_id is not None:
                await session.execute(delete(Plant).where(Plant.id == plant_id))
            if organization_id is not None:
                await session.execute(
                    delete(Organization).where(Organization.id == organization_id)
                )
            await session.commit()
