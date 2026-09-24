from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.app.config import settings
from api.app.middleware import setup_middleware
from api.app.routers import api_router
from api.core.database import create_tables, close_database


def create_application() -> FastAPI:
    app = FastAPI(
        title="ClipForge API",
        description="AI Video Clipping SaaS API",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/openapi.json",
    )

    setup_middleware(app)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": settings.APP_VERSION}

    @app.on_event("startup")
    async def startup():
        await create_tables()

    @app.on_event("shutdown")
    async def shutdown():
        await close_database()

    return app


app = create_application()
