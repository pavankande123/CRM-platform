from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime


class DependencyStatus(BaseModel):
    status: str  # "healthy" | "unhealthy" | "degraded"
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class ReadinessResponse(BaseModel):
    status: str  # "ready" | "not_ready"
    dependencies: Dict[str, DependencyStatus]
    timestamp: datetime
