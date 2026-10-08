from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db.session import AsyncSessionFactory
from app.main import app
from app.models.enterprise import Organization
from app.models.user import User


@pytest.mark.asyncio
async def test_audit_and_security_event_query() -> None:
    suffix = uuid4().hex[:8]
    organization_id: str | None = None
    admin_user_id: str | None = None
    username = f"audit.admin.{suffix}"
    password = "FactoryPilot#Audit2026!"

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/rbac/bootstrap",
                json={
                    "organization_code": f"AUD-{suffix}",
                    "organization_name": "Audit Test Organization",
                    "username": username,
                    "employee_no": f"AUD-{suffix}",
                    "display_name": "Audit Admin",
                    "password": password,
                },
            )
            assert response.status_code == 201
            organization_id = response.json()["organization_id"]
            admin_user_id = response.json()["user"]["id"]

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": password},
            )
            assert response.status_code == 200
            headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

            response = await client.get("/api/v1/organizations", headers=headers)
            assert response.status_code == 200

            response = await client.get(
                "/api/v1/audit/authorization?page=1&page_size=100",
                headers=headers,
            )
            assert response.status_code == 200
            items = response.json()["items"]
            assert any(
                item["permission_code"] == "enterprise.organization.read"
                and item["result"] == "success"
                for item in items
            )

            response = await client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": "wrong-password"},
            )
            assert response.status_code == 401

            response = await client.get(
                "/api/v1/audit/security-events?page=1&page_size=100",
                headers=headers,
            )
            assert response.status_code == 200
            events = response.json()["items"]
            assert any(
                item["event_type"] == "auth.invalid_credentials"
                and item["category"] == "authentication"
                for item in events
            )
    finally:
        async with AsyncSessionFactory() as session:
            if admin_user_id is not None:
                await session.execute(delete(User).where(User.id == admin_user_id))
            if organization_id is not None:
                await session.execute(
                    delete(Organization).where(Organization.id == organization_id)
                )
            await session.commit()
