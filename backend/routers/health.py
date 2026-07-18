import os

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel import Session

from backend.application.health.check_system_health import CheckSystemHealth
from backend.crud.database import get_session
from backend.infrastructure.health.redis_health_probe import RedisHealthProbe
from backend.infrastructure.health.sqlmodel_database_health_probe import (
    SqlModelDatabaseHealthProbe,
)

router = APIRouter(tags=["Health"])


def get_check_readiness_use_case(
    session: Session = Depends(get_session),
) -> CheckSystemHealth:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    return CheckSystemHealth(
        probes=(
            SqlModelDatabaseHealthProbe(session),
            RedisHealthProbe(redis_url),
        )
    )


@router.get("/live", include_in_schema=False)
async def liveness_check() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready", include_in_schema=False)
async def readiness_check(
    check_readiness_use_case: CheckSystemHealth = Depends(get_check_readiness_use_case),
) -> JSONResponse:
    readiness = check_readiness_use_case.execute()
    if readiness.status != "healthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ready"},
    )
