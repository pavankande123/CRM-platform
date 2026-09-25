from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.search import SearchResponse
from app.services.search_service import global_search

router = APIRouter()


@router.get("", response_model=StandardResponse[SearchResponse], summary="Global CRM Search")
async def search_endpoint(
    q: str = Query(..., min_length=1, description="Search term for customer name, phone, email, project number"),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[SearchResponse]:
    results = await global_search(db, current_user.organization_id, q)
    return StandardResponse(data=results, message=f"Found {results.total_results} matching records")
