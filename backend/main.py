from fastapi import FastAPI, APIRouter
from backend.routers import users, oauth
from backend.crud.database import init_db
from backend.routers import flights, payments, admin, tickets, notifications, health
from dotenv import load_dotenv
import os
from guard import SecurityConfig, SecurityMiddleware
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from backend.utils.kafka import kafka_producer
from backend.utils.dependencies import notification_consumer
from backend.consumers.user_notifications import process_user_notifications
from backend.consumers.booking_notifications import process_booking_notifications
from backend.consumers.payment_notifications import process_payment_notifications
from backend.consumers.ticket_notifications import process_ticket_notifications
from backend.utils.constants import KafkaTopics
from prometheus_fastapi_instrumentator import Instrumentator
import asyncio

load_dotenv()


def get_bool_env(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() == "true"


def get_csv_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def build_security_config() -> SecurityConfig:
    api_key = os.getenv("FASTAPI_GUARD_AGENT_API_KEY", "").strip()
    project_id = os.getenv("FASTAPI_GUARD_AGENT_PROJECT_ID", "").strip()
    enable_agent = get_bool_env("FASTAPI_GUARD_ENABLE_AGENT", False)

    if enable_agent and not api_key:
        raise RuntimeError(
            "FASTAPI_GUARD_AGENT_API_KEY must be set when FASTAPI_GUARD_ENABLE_AGENT=true"
        )
    if enable_agent and not project_id:
        raise RuntimeError(
            "FASTAPI_GUARD_AGENT_PROJECT_ID must be set when FASTAPI_GUARD_ENABLE_AGENT=true"
        )

    config_kwargs = {
        "rate_limit": int(os.getenv("RATE_LIMIT", 100)),
        "rate_limit_window": int(os.getenv("RATE_LIMIT_WINDOW", 60)),
        "enable_redis": get_bool_env("ENABLE_REDIS", True),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "blocked_user_agents": get_csv_env("BLOCKED_USER_AGENTS") or ["curl", "wget"],
        "auto_ban_threshold": int(os.getenv("AUTO_BAN_THRESHOLD", 5)),
        "auto_ban_duration": int(os.getenv("AUTO_BAN_DURATION", 86400)),
        "enable_penetration_detection": get_bool_env(
            "ENABLE_PENETRATION_DETECTION", True
        ),
        "custom_log_file": None,
        "enable_rate_limiting": get_bool_env("ENABLE_RATE_LIMITING", True),
        "enable_agent": enable_agent,
        "agent_api_key": api_key or None,
        "agent_project_id": project_id or None,
        "agent_endpoint": os.getenv(
            "FASTAPI_GUARD_AGENT_ENDPOINT", "https://api.guard-core.com/api/v1"
        ).rstrip("/"),
        "agent_buffer_size": int(os.getenv("FASTAPI_GUARD_AGENT_BUFFER_SIZE", 5000)),
        "agent_flush_interval": int(
            os.getenv("FASTAPI_GUARD_AGENT_FLUSH_INTERVAL", 2)
        ),
        "agent_enable_events": get_bool_env(
            "FASTAPI_GUARD_AGENT_ENABLE_EVENTS", True
        ),
        "agent_enable_metrics": get_bool_env(
            "FASTAPI_GUARD_AGENT_ENABLE_METRICS", True
        ),
        "enable_cors": True,
        "cors_allow_origins": get_csv_env("CORS_ORIGINS"),
        "cors_allow_methods": ["*"],
        "cors_allow_headers": ["*"],
        "cors_allow_credentials": True,
    }

    model_fields = getattr(SecurityConfig, "model_fields", {})

    if "agent_project_encryption_key" in model_fields:
        config_kwargs["agent_project_encryption_key"] = (
            os.getenv("FASTAPI_GUARD_AGENT_PROJECT_ENCRYPTION_KEY", "").strip()
            or None
        )
    if "fail_secure" in model_fields:
        config_kwargs["fail_secure"] = get_bool_env(
            "FASTAPI_GUARD_FAIL_SECURE", True
        )

    return SecurityConfig(**config_kwargs)


try:
    from guard.lifespan import guard_lifespan
except ImportError:
    guard_lifespan = None


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    if guard_lifespan is None:
        yield
        return

    async with guard_lifespan(app):
        yield


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

    async with app_lifespan(app):
        yield
    # Shutdown

    notification_consumer.stop()
    kafka_producer.stop()


app = FastAPI(lifespan=lifespan)


Instrumentator().instrument(app).expose(app)

security_config = build_security_config()

app.add_middleware(SecurityMiddleware, config=security_config)

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


@app.get("/")
def hello():
    return {"message": "Flight Booking API"}
