from typing import List
from app.schemas.common import BaseSchema
from app.schemas.customer import CustomerRead
from app.schemas.project import ProjectRead
from app.schemas.product import ProductRead


class SearchResponse(BaseSchema):
    query: str
    customers: List[CustomerRead] = []
    projects: List[ProjectRead] = []
    products: List[ProductRead] = []
    total_results: int = 0
