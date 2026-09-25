from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.users import router as users_router
from app.api.v1.audit import router as audit_router

api_v1_router = APIRouter()

# Mount health checks directly on v1 as well as root
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(tenants_router, prefix="/tenants", tags=["Tenants"])
api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
api_v1_router.include_router(audit_router, prefix="/audit", tags=["Audit"])
