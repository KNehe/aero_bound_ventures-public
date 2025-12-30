from fastapi import APIRouter, Depends
import redis
from backend.crud.database import get_session
from backend.utils.kafka import kafka_producer
import time
from sqlmodel import text, Session
import os

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check(session: Session = Depends(get_session)):
    """
    Comprehensive health check for the system.
    Checks:
    - Database connectivity
    - Redis connectivity
    - Kafka producer status
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "database": "unknown",
            "redis": "unknown",
            "kafka_producer": "unknown",
        },
    }

    # 1. Check postgreSQL
    try:
        session.exec(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # 2. Check redis
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
        r.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # 3. Check kafka producer
    try:
        metadata = kafka_producer.producer.list_topics(timeout=1)
        if metadata and metadata.brokers:
            health_status["services"]["kafka_producer"] = "healthy"
        else:
            health_status["services"]["kafka_producer"] = (
                "unhealthy: No brokers reached"
            )
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["kafka_producer"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    if all(
        status.startswith("unhealthy") for status in health_status["services"].values()
    ):
        health_status["status"] = "down"

    return health_status
