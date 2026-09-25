from fastapi import APIRouter

# Phase 1 Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.users import router as users_router
from app.api.v1.audit import router as audit_router

# Phase 2 Core CRM Routers
from app.api.v1.customers import router as customers_router
from app.api.v1.products import router as products_router
from app.api.v1.pipelines import router as pipelines_router
from app.api.v1.projects import router as projects_router
from app.api.v1.follow_ups import router as follow_ups_router
from app.api.v1.payments import router as payments_router
from app.api.v1.notes import router as notes_router
from app.api.v1.documents import router as documents_router
from app.api.v1.search import router as search_router
from app.api.v1.dashboard import router as dashboard_router

# Phase 3 Platform Configurability & Automation Routers
from app.api.v1.custom_fields import router as custom_fields_router
from app.api.v1.views import router as views_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.approvals import router as approvals_router

# Phase 4 Production Hardening Routers
from app.api.v1.jobs import router as jobs_router

api_v1_router = APIRouter()

# Phase 1 Endpoints
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(tenants_router, prefix="/tenants", tags=["Tenants"])
api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
api_v1_router.include_router(audit_router, prefix="/audit", tags=["Audit"])

# Phase 2 Endpoints
api_v1_router.include_router(customers_router, prefix="/customers", tags=["Customers"])
api_v1_router.include_router(products_router, prefix="/products", tags=["Products"])
api_v1_router.include_router(pipelines_router, prefix="/pipelines", tags=["Pipelines"])
api_v1_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(follow_ups_router, prefix="/follow-ups", tags=["Follow-ups"])
api_v1_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_v1_router.include_router(notes_router, prefix="/notes", tags=["Notes"])
api_v1_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_v1_router.include_router(search_router, prefix="/search", tags=["Search"])
api_v1_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

# Phase 3 Endpoints
api_v1_router.include_router(custom_fields_router, prefix="/custom-fields", tags=["Custom Fields"])
api_v1_router.include_router(views_router, prefix="/views", tags=["Saved Views"])
api_v1_router.include_router(workflows_router, prefix="/workflows", tags=["Workflows"])
api_v1_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_v1_router.include_router(approvals_router, prefix="/approvals", tags=["Approvals"])

# Phase 4 Endpoints
api_v1_router.include_router(jobs_router, prefix="/jobs", tags=["Background Jobs"])

