from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db.session import AsyncSessionFactory
from app.main import app
from app.models.enterprise import Department, Organization, Plant
from app.models.user import User


@pytest.mark.asyncio
async def test_user_and_token_authentication_flow() -> None:
    suffix = uuid4().hex[:8]
    organization_id: str | None = None
    plant_id: str | None = None
    department_id: str | None = None
    admin_user_id: str | None = None
    user_id: str | None = None
    admin_username = f"admin.{suffix}"
    username = f"planner.{suffix}"
    admin_password = "FactoryPilot#Admin2026!"
    initial_password = "FactoryPilot#2026!"
    new_password = "FactoryPilot#2027!"

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/rbac/bootstrap",
                json={
                    "organization_code": f"AUTH-{suffix}",
                    "organization_name": "Authentication Test Organization",
                    "username": admin_username,
                    "employee_no": f"ADM-{suffix}",
                    "display_name": "认证测试管理员",
                    "password": admin_password,
                },
            )
            assert response.status_code == 201
            bootstrap = response.json()
            organization_id = bootstrap["organization_id"]
            admin_user_id = bootstrap["user"]["id"]

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": admin_username, "password": admin_password},
            )
            assert response.status_code == 200
            admin_headers = {
                "Authorization": f"Bearer {response.json()['access_token']}"
            }

            response = await client.post(
                "/api/v1/plants",
                headers=admin_headers,
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
                headers=admin_headers,
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
                headers=admin_headers,
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
            login = response.json()
            access_token = login["access_token"]
            refresh_token = login["refresh_token"]

            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200
            current = response.json()
            assert current["user_id"] == user_id
            assert current["organization_id"] == organization_id
            assert current["role_codes"] == []
            assert current["permission_codes"] == []

            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            assert response.status_code == 200
            refreshed = response.json()
            assert refreshed["access_token"] != access_token
            assert refreshed["refresh_token"] != refresh_token
            access_token = refreshed["access_token"]

            response = await client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 204

            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 401
            assert response.json()["error"]["code"] == "auth.session_revoked"

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": initial_password},
            )
            assert response.status_code == 200
            second_access_token = response.json()["access_token"]

            response = await client.post(
                f"/api/v1/users/{user_id}/password",
                headers=admin_headers,
                json={"new_password": new_password},
            )
            assert response.status_code == 204

            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {second_access_token}"},
            )
            assert response.status_code == 401
            assert response.json()["error"]["code"] == "auth.session_revoked"

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": new_password},
            )
            assert response.status_code == 200
    finally:
        async with AsyncSessionFactory() as session:
            if user_id is not None:
                await session.execute(delete(User).where(User.id == user_id))
            if admin_user_id is not None:
                await session.execute(delete(User).where(User.id == admin_user_id))
            if department_id is not None:
                await session.execute(delete(Department).where(Department.id == department_id))
            if plant_id is not None:
                await session.execute(delete(Plant).where(Plant.id == plant_id))
            if organization_id is not None:
                await session.execute(
                    delete(Organization).where(Organization.id == organization_id)
                )
            await session.commit()
