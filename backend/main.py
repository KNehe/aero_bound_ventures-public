from contextlib import asynccontextmanager
import asyncio
import os

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from guard import SecurityConfig, SecurityMiddleware
from guard.lifespan import make_lifespan
from prometheus_fastapi_instrumentator import Instrumentator

from backend.consumers.booking_notifications import process_booking_notifications
from backend.consumers.payment_notifications import process_payment_notifications
from backend.consumers.ticket_notifications import process_ticket_notifications
from backend.consumers.user_notifications import process_user_notifications
from backend.crud.database import init_db
from backend.utils.constants import KafkaTopics
from backend.utils.dependencies import notification_consumer
from backend.utils.kafka import kafka_producer
from backend.utils.log_manager import log_manager

load_dotenv()
log_manager.setup_security_logger()


try:
    from guard import __version__ as _GUARD_VERSION
except ImportError:
    _GUARD_VERSION = None


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _csv_env(name: str, default: str = "") -> list[str]:
    return [
        item.strip() for item in os.getenv(name, default).split(",") if item.strip()
    ]


guard_api_key = _env_first("GUARD_API_KEY_W_ENCRYPTION", "GUARD_API_KEY")
guard_api_key = guard_api_key or _env_first(
    "GUARD_CORE_API_KEY_W_ENCRYPTION", "GUARD_CORE_API_KEY"
)
guard_project_id = _env_first("GUARD_PROJECT_ID", "GUARD_CORE_PROJECT_ID")
guard_core_url = _env_first(
    "GUARD_CORE_URL",
    "GUARD_CORE_ENDPOINT",
    default="https://api.guard-core.com/api/v1",
)
guard_agent_endpoint = guard_core_url.rstrip("/").removesuffix("/api/v1")
guard_project_encryption_key = _env_first(
    "GUARD_PROJECT_ENCRYPTION_KEY",
    "GUARD_ENCRYPTION_KEY",
    "GUARD_CORE_PROJECT_ENCRYPTION_KEY",
) or None
guard_enable_agent = _env_bool(
    "GUARD_ENABLE_AGENT", _env_bool("GUARD_CORE_ENABLE_AGENT", True)
)
guard_enable_dynamic_rules = _env_bool(
    "GUARD_ENABLE_DYNAMIC_RULES", _env_bool("GUARD_CORE_ENABLE_DYNAMIC_RULES", False)
)
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
    enable_ip_banning=_env_bool("ENABLE_IP_BANNING", True),
    enable_rate_limiting=_env_bool("ENABLE_RATE_LIMITING", True),
    enable_agent=bool(guard_api_key) and guard_enable_agent,
    agent_api_key=guard_api_key or None,
    agent_endpoint=guard_agent_endpoint,
    agent_project_id=guard_project_id or None,
    agent_project_encryption_key=guard_project_encryption_key,
    agent_guard_version=_GUARD_VERSION,
    agent_buffer_size=int(os.getenv("GUARD_AGENT_BUFFER_SIZE", 5000)),
    agent_flush_interval=int(os.getenv("GUARD_AGENT_FLUSH_INTERVAL", 2)),
    agent_enable_events=True,
    agent_enable_metrics=True,
    agent_retry_attempts=int(os.getenv("GUARD_AGENT_RETRY_ATTEMPTS", 3)),
    agent_timeout=int(os.getenv("GUARD_AGENT_TIMEOUT", 30)),
    agent_status_interval=int(os.getenv("GUARD_AGENT_STATUS_INTERVAL", 300)),
    enable_dynamic_rules=bool(guard_api_key) and guard_enable_dynamic_rules,
    dynamic_rule_interval=int(os.getenv("GUARD_DYNAMIC_RULE_INTERVAL", 60)),
    fail_secure=_env_bool("GUARD_FAIL_SECURE", True),
    enable_cors=bool(cors_origins),
    cors_allow_origins=cors_origins,
    cors_allow_methods=_csv_env(
        "CORS_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    ),
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
        "/health",
        "/metrics",
    ],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()

    kafka_producer.start()

    notification_consumer.register_handler(
        KafkaTopics.USER_EVENTS, process_user_notifications
    )
    notification_consumer.register_handler(
        KafkaTopics.BOOKING_EVENTS, process_booking_notifications
    )
    notification_consumer.register_handler(
        KafkaTopics.PAYMENT_EVENTS, process_payment_notifications
    )
    notification_consumer.register_handler(
        KafkaTopics.TICKET_EVENTS, process_ticket_notifications
    )

    loop = asyncio.get_running_loop()

    notification_consumer.start(loop)

    yield
    # Shutdown

    notification_consumer.stop()
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
api_v1_router.include_router(health.router)

app.include_router(api_v1_router)
app.include_router(health.router, include_in_schema=False)


@app.get("/")
def hello():
    return {"message": "Flight Booking API"}
