import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel

from src.core.config import get_settings
from src.core.database import engine
from src.core.redis import redis_client
from src.core.kafka import _producer

logger = logging.getLogger(__name__)
settings = get_settings()


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    checks: Dict[str, Any]


health_status = HealthCheck(status="healthy", timestamp=datetime.utcnow(), checks={})


async def check_database() -> Dict[str, Any]:
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy", "message": "Database connection OK"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "message": str(e)}


async def check_redis() -> Dict[str, Any]:
    try:
        if redis_client:
            await redis_client.ping()
            return {"status": "healthy", "message": "Redis connection OK"}
        return {"status": "unhealthy", "message": "Redis client not initialized"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "message": str(e)}


async def check_kafka() -> Dict[str, Any]:
    try:
        if _producer:
            return {"status": "healthy", "message": "Kafka producer OK"}
        return {"status": "unhealthy", "message": "Kafka producer not initialized"}
    except Exception as e:
        logger.error(f"Kafka health check failed: {e}")
        return {"status": "unhealthy", "message": str(e)}


async def run_health_checks() -> HealthCheck:
    global health_status

    database_check = await check_database()
    redis_check = await check_redis()
    kafka_check = await check_kafka()

    health_status.checks = {
        "database": database_check,
        "redis": redis_check,
        "kafka": kafka_check,
    }

    all_healthy = all(check.get("status") == "healthy" for check in health_status.checks.values())
    health_status.status = "healthy" if all_healthy else "degraded"
    health_status.timestamp = datetime.utcnow()

    return health_status


def setup_health_checks(app: FastAPI):
    @app.get("/health", response_model=HealthCheck)
    async def health_endpoint():
        return await run_health_checks()

    @app.get("/ready")
    async def readiness_check():
        checks = await run_health_checks()
        if checks.status == "healthy":
            return {"status": "ready"}
        return {"status": "not_ready", "checks": checks.checks}

    @app.get("/live")
    async def liveness_check():
        return {"status": "alive", "timestamp": datetime.utcnow()}

    if settings.monitoring.health_check.enabled:

        async def periodic_health_check():
            while True:
                try:
                    await run_health_checks()
                    await asyncio.sleep(settings.monitoring.health_check.interval_seconds)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Periodic health check error: {e}")
                    await asyncio.sleep(5)

        asyncio.create_task(periodic_health_check())
