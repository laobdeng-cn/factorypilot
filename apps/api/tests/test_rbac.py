from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db.session import AsyncSessionFactory
from app.main import app
from app.models.enterprise import Organization
from app.models.user import User


@pytest.mark.asyncio
async def test_rbac_role_assignment_and_api_authorization() -> None:
    suffix = uuid4().hex[:8]
    organization_id: str | None = None
    admin_user_id: str | None = None
    viewer_user_id: str | None = None
    admin_username = f"rbac.admin.{suffix}"
    viewer_username = f"rbac.viewer.{suffix}"
    admin_password = "FactoryPilot#Admin2026!"
    viewer_password = "FactoryPilot#Viewer2026!"

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/rbac/bootstrap",
                json={
                    "organization_code": f"RBAC-{suffix}",
                    "organization_name": "RBAC Test Organization",
                    "username": admin_username,
                    "employee_no": f"ADM-{suffix}",
                    "display_name": "RBAC 管理员",
                    "password": admin_password,
                },
            )
            assert response.status_code == 201
            bootstrap = response.json()
            organization_id = bootstrap["organization_id"]
            admin_user_id = bootstrap["user"]["id"]
            assert bootstrap["role_codes"] == ["system_admin"]

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": admin_username, "password": admin_password},
            )
            assert response.status_code == 200
            admin_headers = {
                "Authorization": f"Bearer {response.json()['access_token']}"
            }

            response = await client.post(
                "/api/v1/users",
                headers=admin_headers,
                json={
                    "organization_id": organization_id,
                    "username": viewer_username,
                    "employee_no": f"VIEW-{suffix}",
                    "display_name": "只读测试用户",
                    "password": viewer_password,
                },
            )
            assert response.status_code == 201
            viewer_user_id = response.json()["id"]

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": viewer_username, "password": viewer_password},
            )
            assert response.status_code == 200
            viewer_headers = {
                "Authorization": f"Bearer {response.json()['access_token']}"
            }

            response = await client.get("/api/v1/organizations", headers=viewer_headers)
            assert response.status_code == 403
            assert response.json()["error"]["code"] == "auth.permission_denied"

            response = await client.get("/api/v1/roles", headers=admin_headers)
            assert response.status_code == 200
            viewer_role = next(
                role for role in response.json() if role["code"] == "viewer"
            )

            response = await client.put(
                f"/api/v1/users/{viewer_user_id}/roles",
                headers=admin_headers,
                json={"role_ids": [viewer_role["id"]]},
            )
            assert response.status_code == 200
            assert response.json()["role_codes"] == ["viewer"]

            response = await client.get("/api/v1/organizations", headers=viewer_headers)
            assert response.status_code == 200

            response = await client.post(
                "/api/v1/organizations",
                headers=viewer_headers,
                json={"code": f"DENY-{suffix}", "name": "Should Be Denied"},
            )
            assert response.status_code == 403
            assert response.json()["error"]["code"] == "auth.permission_denied"

            response = await client.get("/api/v1/auth/me", headers=viewer_headers)
            assert response.status_code == 200
            current = response.json()
            assert current["role_codes"] == ["viewer"]
            assert "enterprise.organization.read" in current["permission_codes"]
            assert "enterprise.organization.manage" not in current["permission_codes"]
    finally:
        async with AsyncSessionFactory() as session:
            if viewer_user_id is not None:
                await session.execute(delete(User).where(User.id == viewer_user_id))
            if admin_user_id is not None:
                await session.execute(delete(User).where(User.id == admin_user_id))
            if organization_id is not None:
                await session.execute(
                    delete(Organization).where(Organization.id == organization_id)
                )
            await session.commit()
