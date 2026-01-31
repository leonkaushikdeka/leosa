import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.api.routers import api_router
from src.core.logging import setup_logging
from src.core.database import init_db, close_db
from src.core.redis import init_redis, close_redis
from src.core.kafka import init_kafka, close_kafka
from src.ml.serving import init_ml_model, close_ml_model
from src.middleware.rate_limiter import RateLimitMiddleware
from src.middleware.security import SecurityHeadersMiddleware
from src.monitoring.health import setup_health_checks


settings = get_settings()
setup_logging(settings.app.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Ransomware Protection Platform...")

    logger.info("Initializing database...")
    await init_db()

    logger.info("Initializing Redis...")
    await init_redis()

    logger.info("Initializing Kafka...")
    await init_kafka()

    logger.info("Initializing ML models...")
    await init_ml_model()

    logger.info("Setting up health checks...")
    setup_health_checks(app)

    logger.info("Application startup complete")

    yield

    logger.info("Shutting down application...")

    await close_ml_model()
    await close_kafka()
    await close_redis()
    await close_db()

    logger.info("Application shutdown complete")


app = FastAPI(
    title="Ransomware Protection Platform API",
    description="AI-Driven Ransomware Protection for Hybrid Clouds",
    version=settings.app.version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

if settings.security.rate_limiting_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.security.requests_per_minute,
        burst_size=settings.security.burst_size,
    )

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        workers=settings.app.workers,
        reload=settings.app.debug,
    )
