"""FastAPI application entry point.

Creates and configures the FastAPI application with CORS, routers,
exception handlers, and lifecycle management.
"""

import logging
import os
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config.settings import settings
from app.core.database import initialize_database, close_database_connection
from app.utils.exceptions import AppException
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def get_cors_origins() -> list[str]:
    """Return the list of allowed CORS origins.

    In development mode with CORS_ORIGINS=*, allows all origins.
    Otherwise returns the explicit origins list + any detected ngrok origin.
    """
    origins = settings.cors_origins_list

    # If wildcard is set in development, trust the user explicitly asked for it
    if settings.use_cors_wildcard:
        return ["*"]

    # Ensure common localhost variants are always present
    localhost_patterns = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    for origin in localhost_patterns:
        if origin not in origins:
            origins.append(origin)

    return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    setup_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    # Validate Google OAuth configuration
    if not settings.GOOGLE_CLIENT_ID:
        logger.warning(
            "--- Google OAuth is NOT configured ---\n"
            "  To enable Google Sign-In:\n"
            "    1. Go to https://console.cloud.google.com/apis/credentials\n"
            "    2. Create an OAuth 2.0 Client ID (Web application)\n"
            "    3. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to backend/.env"
        )
    else:
        logger.info(
            "Google OAuth is configured (client_id: %s...)",
            settings.GOOGLE_CLIENT_ID[:20],
        )

    # Log CORS configuration
    cors_origins = get_cors_origins()
    logger.info("CORS origins: %s", cors_origins)

    try:
        await initialize_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning("Database initialization skipped: %s", e)
    yield
    await close_database_connection()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware — use allow_origins=['*'] only in development
    # when explicitly configured, otherwise use granular origins.
    cors_origins = get_cors_origins()
    allow_all = cors_origins == ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if not allow_all else ["*"],
        allow_origin_regex=".*" if allow_all else None,
        allow_credentials=True if not allow_all else True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-CSRF-Token",
            "X-API-Key",
            "Cache-Control",
        ],
        expose_headers=[
            "Content-Length",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
        ],
        max_age=600,  # Preflight cache for 10 minutes
    )

    # Proxy headers middleware — enables correct client IP and protocol
    # detection when behind Render's proxy or any reverse proxy.
    # This works regardless of whether Uvicorn is started via CLI or
    # the __main__ block (unlike uvicorn's --proxy-headers CLI flag).
    app.add_middleware(
        ProxyHeadersMiddleware,
        trusted_hosts="*",
    )

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": exc.error_code,
                "errors": exc.errors,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error_code": "INTERNAL_ERROR",
            },
        )

    # Register routers
    from app.api.v1.auth.routes import router as auth_router
    from app.api.v1.files.routes import router as files_router
    from app.api.v1.scans.routes import router as scans_router
    from app.api.v1.alerts.routes import router as alerts_router
    from app.api.v1.reports.routes import router as reports_router
    from app.api.v1.dashboard.routes import router as dashboard_router
    from app.api.v1.ai.routes import router as ai_router
    from app.api.v1.health.routes import router as health_router
    from app.api.v1.users.routes import router as users_router

    prefix = settings.API_PREFIX
    app.include_router(auth_router, prefix=prefix)
    app.include_router(health_router, prefix=prefix)
    app.include_router(users_router, prefix=prefix)
    app.include_router(files_router, prefix=prefix)
    app.include_router(scans_router, prefix=prefix)
    app.include_router(alerts_router, prefix=prefix)
    app.include_router(reports_router, prefix=prefix)
    app.include_router(dashboard_router, prefix=prefix)
    app.include_router(ai_router, prefix=prefix)

    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": f"{prefix}/health",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        reload_excludes=[".venv/*", ".venv"],
        log_level=settings.LOG_LEVEL.lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
