from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import users
from backend.crud.database import init_db
from backend.routers import flights, payments, admin, tickets, notifications, health
from dotenv import load_dotenv
import os
from guard.middleware import SecurityMiddleware
from guard.models import SecurityConfig
from contextlib import asynccontextmanager
from backend.utils.kafka import kafka_producer
from backend.utils.dependencies import notification_consumer
from backend.consumers.user_notifications import process_user_notifications
from backend.consumers.booking_notifications import process_booking_notifications
from backend.consumers.payment_notifications import process_payment_notifications
from backend.consumers.ticket_notifications import process_ticket_notifications
from backend.utils.constants import KafkaTopics
import asyncio
from prometheus_fastapi_instrumentator import Instrumentator

load_dotenv()


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

security_config = SecurityConfig(
    rate_limit=int(os.getenv("RATE_LIMIT", 100)),
    enable_redis=bool(os.getenv("ENABLE_REDIS", True)),
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    blocked_user_agents=os.getenv("BLOCKED_USER_AGENTS", "curl,wget").split(","),
    auto_ban_threshold=int(os.getenv("AUTO_BAN_THRESHOLD", 5)),
    auto_ban_duration=int(os.getenv("AUTO_BAN_DURATION", 86400)),
    enable_penetration_detection=bool(os.getenv("ENABLE_PENETRATION_DETECTION", True)),
    custom_log_file=os.getenv("CUSTOM_LOG_FILE", "security.log"),
    # Log suspicious activity but don't block for testing
    passive_mode=bool(os.getenv("PASSIVE_MODE", True)),
)

origins = os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityMiddleware, config=security_config)

app.include_router(users.router)
app.include_router(flights.router)
app.include_router(payments.router)
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(tickets.router)
app.include_router(notifications.router)
app.include_router(health.router)


@app.get("/")
def hello():
    return {"message": "Flight Booking API"}
