from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db.session import AsyncSessionFactory
from app.main import app
from app.models.enterprise import Department, Organization, Plant
from app.models.user import User


@pytest.mark.asyncio
async def test_user_and_password_authentication_flow() -> None:
    suffix = uuid4().hex[:8]
    organization_id: str | None = None
    plant_id: str | None = None
    department_id: str | None = None
    user_id: str | None = None
    username = f"planner.{suffix}"
    initial_password = "FactoryPilot#2026!"
    new_password = "FactoryPilot#2027!"

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/organizations",
                json={"code": f"AUTH-{suffix}", "name": "Authentication Test Organization"},
            )
            assert response.status_code == 201
            organization_id = response.json()["id"]

            response = await client.post(
                "/api/v1/plants",
                json={
                    "organization_id": organization_id,
                    "code": f"P-{suffix}",
                    "name": "Authentication Test Plant",
                },
            )
            assert response.status_code == 201
            plant_id = response.json()["id"]

            response = await client.post(
                "/api/v1/departments",
                json={
                    "organization_id": organization_id,
                    "plant_id": plant_id,
                    "code": f"D-{suffix}",
                    "name": "Production Planning",
                },
            )
            assert response.status_code == 201
            department_id = response.json()["id"]

            response = await client.post(
                "/api/v1/users",
                json={
                    "organization_id": organization_id,
                    "department_id": department_id,
                    "primary_plant_id": plant_id,
                    "username": username,
                    "employee_no": f"E-{suffix}",
                    "display_name": "计划员测试用户",
                    "email": f"{username}@factorypilot.test",
                    "password": initial_password,
                },
            )
            assert response.status_code == 201
            user = response.json()
            user_id = user["id"]
            assert user["username"] == username
            assert user["failed_login_count"] == 0
            assert "password_hash" not in user

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": "WrongPassword#2026!"},
            )
            assert response.status_code == 401
            assert response.json()["error"]["code"] == "auth.invalid_credentials"

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": initial_password},
            )
            assert response.status_code == 200
            assert response.json()["authenticated"] is True
            assert response.json()["user"]["failed_login_count"] == 0
            assert response.json()["user"]["last_login_at"] is not None

            response = await client.post(
                f"/api/v1/users/{user_id}/password",
                json={"new_password": new_password},
            )
            assert response.status_code == 204

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": new_password},
            )
            assert response.status_code == 200

            response = await client.get(
                "/api/v1/users",
                params={"organization_id": organization_id, "q": username},
            )
            assert response.status_code == 200
            assert any(item["id"] == user_id for item in response.json()["items"])
    finally:
        async with AsyncSessionFactory() as session:
            if user_id is not None:
                await session.execute(delete(User).where(User.id == user_id))
            if department_id is not None:
                await session.execute(delete(Department).where(Department.id == department_id))
            if plant_id is not None:
                await session.execute(delete(Plant).where(Plant.id == plant_id))
            if organization_id is not None:
                cleanup = delete(Organization).where(Organization.id == organization_id)
                await session.execute(cleanup)
            await session.commit()
