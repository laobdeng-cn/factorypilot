from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db.session import AsyncSessionFactory
from app.main import app
from app.models.enterprise import Department, Organization, Plant
from app.models.user import User


@pytest.mark.asyncio
async def test_hierarchical_data_scope_filters_reads_and_writes() -> None:
    suffix = uuid4().hex[:8]
    admin_user_id: str | None = None
    viewer_user_id: str | None = None
    organization_a_id: str | None = None
    organization_b_id: str | None = None
    plant_a_id: str | None = None
    plant_b_id: str | None = None
    department_a_id: str | None = None
    department_b_id: str | None = None
    admin_username = f"scope.admin.{suffix}"
    viewer_username = f"scope.viewer.{suffix}"
    admin_password = "FactoryPilot#ScopeAdmin2026!"
    viewer_password = "FactoryPilot#ScopeViewer2026!"

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/rbac/bootstrap",
                json={
                    "organization_code": f"SCOPE-A-{suffix}",
                    "organization_name": "Scope Organization A",
                    "username": admin_username,
                    "employee_no": f"SADM-{suffix}",
                    "display_name": "Scope 管理员",
                    "password": admin_password,
                },
            )
            assert response.status_code == 201
            bootstrap = response.json()
            organization_a_id = bootstrap["organization_id"]
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
                "/api/v1/organizations",
                headers=admin_headers,
                json={
                    "code": f"SCOPE-B-{suffix}",
                    "name": "Scope Organization B",
                },
            )
            assert response.status_code == 201
            organization_b_id = response.json()["id"]

            async def create_plant(code: str, name: str) -> str:
                response = await client.post(
                    "/api/v1/plants",
                    headers=admin_headers,
                    json={
                        "organization_id": organization_a_id,
                        "code": code,
                        "name": name,
                    },
                )
                assert response.status_code == 201
                return str(response.json()["id"])

            plant_a_id = await create_plant(f"PA-{suffix}", "Plant A")
            plant_b_id = await create_plant(f"PB-{suffix}", "Plant B")

            async def create_department(code: str, name: str, plant_id: str) -> str:
                response = await client.post(
                    "/api/v1/departments",
                    headers=admin_headers,
                    json={
                        "organization_id": organization_a_id,
                        "plant_id": plant_id,
                        "code": code,
                        "name": name,
                        "sort_order": 10,
                    },
                )
                assert response.status_code == 201
                return str(response.json()["id"])

            department_a_id = await create_department(
                f"DA-{suffix}", "Department A", plant_a_id
            )
            department_b_id = await create_department(
                f"DB-{suffix}", "Department B", plant_b_id
            )

            response = await client.post(
                "/api/v1/users",
                headers=admin_headers,
                json={
                    "organization_id": organization_a_id,
                    "primary_plant_id": plant_a_id,
                    "department_id": department_a_id,
                    "username": viewer_username,
                    "employee_no": f"SVIEW-{suffix}",
                    "display_name": "Scope Viewer",
                    "password": viewer_password,
                },
            )
            assert response.status_code == 201
            viewer_user_id = response.json()["id"]

            response = await client.get("/api/v1/roles", headers=admin_headers)
            assert response.status_code == 200
            roles = {role["code"]: role for role in response.json()}
            viewer_role_id = roles["viewer"]["id"]
            factory_manager_role_id = roles["factory_manager"]["id"]
            assert roles["system_admin"]["data_scope"] == "global"
            assert roles["factory_manager"]["data_scope"] == "plant"
            assert roles["viewer"]["data_scope"] == "organization"

            response = await client.put(
                f"/api/v1/users/{viewer_user_id}/roles",
                headers=admin_headers,
                json={"role_ids": [viewer_role_id]},
            )
            assert response.status_code == 200

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": viewer_username, "password": viewer_password},
            )
            assert response.status_code == 200
            viewer_headers = {
                "Authorization": f"Bearer {response.json()['access_token']}"
            }

            response = await client.get("/api/v1/auth/me", headers=viewer_headers)
            assert response.status_code == 200
            assert response.json()["data_scope_type"] == "organization"

            response = await client.get("/api/v1/organizations", headers=viewer_headers)
            assert response.status_code == 200
            assert {item["id"] for item in response.json()["items"]} == {
                organization_a_id
            }

            response = await client.get(
                f"/api/v1/organizations/{organization_b_id}",
                headers=viewer_headers,
            )
            assert response.status_code == 404

            response = await client.put(
                f"/api/v1/users/{viewer_user_id}/roles",
                headers=admin_headers,
                json={"role_ids": [factory_manager_role_id]},
            )
            assert response.status_code == 200

            response = await client.get("/api/v1/auth/me", headers=viewer_headers)
            assert response.status_code == 200
            assert response.json()["data_scope_type"] == "plant"

            response = await client.get("/api/v1/plants", headers=viewer_headers)
            assert response.status_code == 200
            assert {item["id"] for item in response.json()["items"]} == {plant_a_id}

            response = await client.get("/api/v1/departments", headers=viewer_headers)
            assert response.status_code == 200
            assert {item["id"] for item in response.json()["items"]} == {
                department_a_id
            }

            response = await client.patch(
                f"/api/v1/plants/{plant_b_id}",
                headers=viewer_headers,
                json={"name": "Out of scope"},
            )
            assert response.status_code == 403
            assert response.json()["error"]["code"] == "auth.data_scope_denied"

            response = await client.put(
                f"/api/v1/users/{viewer_user_id}/data-scope",
                headers=admin_headers,
                json={"scope_type": "department"},
            )
            assert response.status_code == 200
            assert response.json()["effective_scope_type"] == "department"

            response = await client.get("/api/v1/auth/me", headers=viewer_headers)
            assert response.status_code == 200
            assert response.json()["data_scope_type"] == "department"
            assert response.json()["data_scope_source"] == "user_override"

            response = await client.get("/api/v1/departments", headers=viewer_headers)
            assert response.status_code == 200
            assert {item["id"] for item in response.json()["items"]} == {
                department_a_id
            }

            response = await client.put(
                f"/api/v1/users/{viewer_user_id}/data-scope",
                headers=admin_headers,
                json={"scope_type": "self"},
            )
            assert response.status_code == 200
            assert response.json()["effective_scope_type"] == "self"

            response = await client.get("/api/v1/users", headers=viewer_headers)
            assert response.status_code == 200
            assert [item["id"] for item in response.json()["items"]] == [
                viewer_user_id
            ]
    finally:
        async with AsyncSessionFactory() as session:
            if viewer_user_id is not None:
                await session.execute(delete(User).where(User.id == viewer_user_id))
            if admin_user_id is not None:
                await session.execute(delete(User).where(User.id == admin_user_id))
            if department_a_id is not None:
                await session.execute(
                    delete(Department).where(Department.id == department_a_id)
                )
            if department_b_id is not None:
                await session.execute(
                    delete(Department).where(Department.id == department_b_id)
                )
            if plant_a_id is not None:
                await session.execute(delete(Plant).where(Plant.id == plant_a_id))
            if plant_b_id is not None:
                await session.execute(delete(Plant).where(Plant.id == plant_b_id))
            if organization_a_id is not None:
                await session.execute(
                    delete(Organization).where(Organization.id == organization_a_id)
                )
            if organization_b_id is not None:
                await session.execute(
                    delete(Organization).where(Organization.id == organization_b_id)
                )
            await session.commit()
