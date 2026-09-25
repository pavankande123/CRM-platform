import uuid
from decimal import Decimal
from typing import List
from app.schemas.activity import ActivityRead
from app.schemas.common import BaseSchema
from app.schemas.customer import CustomerRead
from app.schemas.follow_up import FollowUpRead


class StageDistribution(BaseSchema):
    stage_id: uuid.UUID
    stage_name: str
    stage_color: str
    count: int
    total_value: Decimal


class CoreDashboardResponse(BaseSchema):
    total_customers: int = 0
    active_projects: int = 0
    projects_by_stage: List[StageDistribution] = []
    todays_follow_ups: List[FollowUpRead] = []
    overdue_follow_ups: List[FollowUpRead] = []
    total_project_value: Decimal = Decimal("0.00")
    total_paid: Decimal = Decimal("0.00")
    total_outstanding: Decimal = Decimal("0.00")
    recent_customers: List[CustomerRead] = []
    recent_activity: List[ActivityRead] = []
