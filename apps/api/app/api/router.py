from fastapi import APIRouter

from app.api.routes.audit import router as audit_router
from app.api.routes.enterprise import router as enterprise_router
from app.api.routes.health import router as health_router
from app.api.routes.identity import router as identity_router
from app.api.routes.rbac import router as rbac_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(enterprise_router, tags=["enterprise"])
api_router.include_router(identity_router, tags=["identity"])
api_router.include_router(rbac_router, tags=["rbac"])
api_router.include_router(audit_router, tags=["audit"])
