from contextlib import asynccontextmanager
import os

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from guard import SecurityConfig, SecurityMiddleware
from guard.lifespan import make_lifespan
from prometheus_fastapi_instrumentator import Instrumentator

from backend.crud.database import init_db
from backend.utils.kafka import kafka_producer
from backend.utils.log_manager import log_manager

load_dotenv()
log_manager.setup_security_logger()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str, default: str = "") -> list[str]:
    return [
        item.strip() for item in os.getenv(name, default).split(",") if item.strip()
    ]


guard_api_key = os.environ["GUARD_API_KEY"]
cors_origins = _csv_env("CORS_ORIGINS")


security_config = SecurityConfig(
    rate_limit=int(os.getenv("RATE_LIMIT", 100)),
    rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", 60)),
    enable_redis=os.getenv("ENABLE_REDIS", "true").strip().lower() == "true",
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    redis_prefix=os.getenv("GUARD_REDIS_PREFIX", "aero_bound:guard_core:"),
    blocked_user_agents=_csv_env("BLOCKED_USER_AGENTS", "curl,wget"),
    auto_ban_threshold=int(os.getenv("AUTO_BAN_THRESHOLD", 5)),
    auto_ban_duration=int(os.getenv("AUTO_BAN_DURATION", 86400)),
    enable_penetration_detection=(
        os.getenv("ENABLE_PENETRATION_DETECTION", "true").strip().lower() == "true"
    ),
    enable_rate_limiting=True,
    enable_agent=True,
    agent_api_key=guard_api_key,
    agent_endpoint="https://api.guard-core.com",
    fail_secure=_env_bool("GUARD_FAIL_SECURE", True),
    enable_cors=bool(cors_origins),
    cors_allow_origins=cors_origins,
    cors_allow_methods=_csv_env("CORS_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS"),
    cors_allow_headers=_csv_env("CORS_HEADERS", "*"),
    cors_allow_credentials=("*" not in cors_origins),
    custom_log_file=None,
    # Log suspicious activity but don't block for testing.
    passive_mode=os.getenv("PASSIVE_MODE", "true").strip().lower() == "true",
    exclude_paths=[
        "/docs",
        "/redoc",
        "/openapi.json",
        "/openapi.yaml",
        "/favicon.ico",
        "/static",
        "/live",
        "/ready",
        "/metrics",
    ],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    kafka_producer.start()

    try:
        yield
    finally:
        kafka_producer.stop()


app = FastAPI(lifespan=make_lifespan(lifespan))


Instrumentator().instrument(app).expose(app)

app.add_middleware(SecurityMiddleware, config=security_config)

from backend.routers import (  # noqa: E402
    admin,
    flights,
    health,
    notifications,
    oauth,
    payments,
    tickets,
    users,
)

api_v1_router = APIRouter(prefix="/api/v1", tags=["Version One"])

api_v1_router.include_router(users.router)
api_v1_router.include_router(oauth.router)
api_v1_router.include_router(flights.router)
api_v1_router.include_router(payments.router)
api_v1_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_v1_router.include_router(tickets.router)
api_v1_router.include_router(notifications.router)

app.include_router(api_v1_router)
app.include_router(health.router)


@app.get("/")
def hello():
    return {"message": "Flight Booking API"}
