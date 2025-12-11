from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import users
from backend.crud.database import init_db
from backend.routers import flights
from backend.routers import payments
from backend.routers import admin
from backend.routers import tickets
from dotenv import load_dotenv
import os
from guard.middleware import SecurityMiddleware
from guard.models import SecurityConfig

load_dotenv()

app = FastAPI()

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


@app.on_event("startup")
def startup():
    init_db()


app.include_router(users.router)
app.include_router(flights.router)
app.include_router(payments.router)
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(tickets.router)


@app.get("/")
def hello():
    return {"message": "Flight Booking API"}
