from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.dashboard import CoreDashboardResponse
from app.services.dashboard_service import get_core_dashboard

router = APIRouter()


@router.get("", response_model=StandardResponse[CoreDashboardResponse], summary="Get Core Operational Dashboard")
async def get_dashboard_endpoint(
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[CoreDashboardResponse]:
    dashboard_data = await get_core_dashboard(db, current_user.organization_id)
    return StandardResponse(data=dashboard_data, message="Core dashboard data computed")
