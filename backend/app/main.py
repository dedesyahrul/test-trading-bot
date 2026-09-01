import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.core.security_hardening import SecurityMiddleware, AuditLogger
from app.core.events import EventSubscriber
from app.websocket.manager import manager

logger = logging.getLogger(__name__)
audit_logger = AuditLogger()

_subscriber_task = None
_event_subscriber = None


def _init_sentry():
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                integrations=[FastApiIntegration(), SqlalchemyIntegration()],
                traces_sample_rate=0.1,
            )
            logger.info("Sentry initialized")
        except ImportError:
            logger.warning("sentry-sdk not installed, skipping Sentry init")


_init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup/shutdown."""
    global _subscriber_task, _event_subscriber

    if settings.AUTO_CREATE_TABLES:
        logger.info("Creating database tables (AUTO_CREATE_TABLES=true)...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created.")
    else:
        logger.info("Skipping auto table creation — use Alembic migrations.")

    logger.info("Environment: %s", os.getenv("ENVIRONMENT", "development"))

    async def handle_event(event: dict):
        await manager.broadcast_event(event)

    _event_subscriber = EventSubscriber(handle_event)
    _subscriber_task = asyncio.create_task(_event_subscriber.start())
    logger.info("Redis event subscriber task started")

    yield

    if _event_subscriber:
        await _event_subscriber.stop()
    if _subscriber_task:
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass

    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Application shutdown complete.")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(SecurityMiddleware)

    is_dev = settings.DEBUG or settings.ENVIRONMENT == "development"
    cors_origins = ["*"] if is_dev else ["http://localhost:13456", "http://localhost"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    from app.api import router as api_router
    app.include_router(api_router, prefix=settings.API_PREFIX)

    from app.websocket.manager import websocket_endpoint
    app.websocket("/ws")(websocket_endpoint)

    @app.get("/health")
    async def health_check():
        """System health check."""
        return {"status": "healthy", "version": settings.APP_VERSION}

    @app.get("/metrics", include_in_schema=False)
    async def root_metrics():
        """Prometheus metrics at root (for scrapers)."""
        from app.core.database import async_session_maker
        from app.core.metrics_service import refresh_business_metrics
        from app.core.metrics import metrics_response
        from fastapi import Response

        async with async_session_maker() as session:
            await refresh_business_metrics(session)
        body, content_type = metrics_response()
        return Response(content=body, media_type=content_type)

    return app


app = create_app()
