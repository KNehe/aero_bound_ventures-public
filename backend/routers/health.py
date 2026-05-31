import os

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.application.health.check_system_health import CheckSystemHealth
from backend.crud.database import get_session
from backend.infrastructure.health.kafka_producer_health_probe import (
    KafkaProducerHealthProbe,
)
from backend.infrastructure.health.redis_health_probe import RedisHealthProbe
from backend.infrastructure.health.sqlmodel_database_health_probe import (
    SqlModelDatabaseHealthProbe,
)
from backend.utils.kafka import kafka_producer

router = APIRouter(prefix="/health", tags=["Health"])


def get_check_system_health_use_case(
    session: Session = Depends(get_session),
) -> CheckSystemHealth:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    return CheckSystemHealth(
        probes=(
            SqlModelDatabaseHealthProbe(session),
            RedisHealthProbe(redis_url),
            KafkaProducerHealthProbe(kafka_producer),
        )
    )


@router.get("")
async def health_check(
    check_system_health_use_case: CheckSystemHealth = Depends(
        get_check_system_health_use_case
    ),
):
    """
    Comprehensive health check for the system.
    Checks:
    - Database connectivity
    - Redis connectivity
    - Kafka producer status
    """
    return check_system_health_use_case.execute().as_response()
