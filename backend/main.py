from contextlib import asynccontextmanager
import asyncio
import os

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from guard import SecurityConfig, SecurityMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from backend.consumers.booking_notifications import process_booking_notifications
from backend.consumers.payment_notifications import process_payment_notifications
from backend.consumers.ticket_notifications import process_ticket_notifications
from backend.consumers.user_notifications import process_user_notifications
from backend.crud.database import init_db
from backend.utils.constants import KafkaTopics
from backend.utils.dependencies import notification_consumer
from backend.utils.kafka import kafka_producer

load_dotenv()


security_config = SecurityConfig(
    rate_limit=int(os.getenv("RATE_LIMIT", 100)),
    enable_redis=os.getenv("ENABLE_REDIS", "true").strip().lower() == "true",
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    blocked_user_agents=os.getenv("BLOCKED_USER_AGENTS", "curl,wget").split(","),
    auto_ban_threshold=int(os.getenv("AUTO_BAN_THRESHOLD", 5)),
    auto_ban_duration=int(os.getenv("AUTO_BAN_DURATION", 86400)),
    enable_penetration_detection=(
        os.getenv("ENABLE_PENETRATION_DETECTION", "true").strip().lower() == "true"
    ),
    custom_log_file=os.getenv("CUSTOM_LOG_FILE", "security.log"),
    # Log suspicious activity but don't block for testing.
    passive_mode=os.getenv("PASSIVE_MODE", "true").strip().lower() == "true",
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


app = FastAPI(lifespan=lifespan)


Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
