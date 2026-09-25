import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import AppException, format_error_response
from app.core.logging import logger, request_id_ctx, setup_logging
from app.db.base import Base
from app.db.session import engine
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.timing import LatencyMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown routines."""
    # Initialize structured JSON logging
    setup_logging(level=settings.LOG_LEVEL, service_name="enermax-backend")
    logger.info(
        f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode",
        extra={"event": "APP_STARTUP", "env": settings.APP_ENV},
    )

    # In local development or testing with SQLite, ensure tables are created
    if "sqlite" in settings.get_database_url():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized for SQLite dev mode")

    # Initialize Redis connection pool
    from app.core.redis import redis_manager
    await redis_manager.initialize()

    yield

    # Clean shutdown
    logger.info("Shutting down application and disposing resources")
    await redis_manager.close()
    await engine.dispose()


def create_application() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Production-grade SaaS CRM Platform for Enermax",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Register Middlewares (LIFO execution order in Starlette)
    from app.middleware.rate_limit import RateLimitMiddleware
    from app.middleware.request_size import RequestSizeLimitMiddleware

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LatencyMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    # Global Exception Handlers for consistent, RFC-compliant error responses
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None) or request_id_ctx.get()
        logger.warning(
            f"AppException [{exc.code}]: {exc.message}",
            extra={"request_id": req_id, "error_code": exc.code, "status_code": exc.status_code},
        )
        return format_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            request_id=req_id,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None) or request_id_ctx.get()
        # Clean up Pydantic errors for readable client consumption
        errors = [
            {"loc": [str(x) for x in err["loc"] if x != "body"], "msg": err["msg"], "type": err["type"]}
            for err in exc.errors()
        ]
        return format_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Request input validation failed",
            request_id=req_id,
            details=errors,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None) or request_id_ctx.get() or f"req_{uuid.uuid4().hex[:12]}"
        logger.error(
            f"Unhandled internal server error: {exc}",
            exc_info=True,
            extra={"request_id": req_id, "event": "UNHANDLED_EXCEPTION"},
        )
        # Never expose internal stack traces or database errors in production
        return format_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Please contact support with the request ID.",
            request_id=req_id,
            details={"request_id": req_id} if not settings.is_production else None,
        )

    # Mount health checks at root for container orchestrators
    app.include_router(health_router, tags=["Health"])

    # Mount API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
