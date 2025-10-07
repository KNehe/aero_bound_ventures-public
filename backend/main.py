from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import users
from backend.crud.database import init_db
from backend.routers import flights
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

origins = os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(users.router)
app.include_router(flights.router)


@app.get("/")
def hello():
    return {"message": "Flight Booking API"}
