from fastapi import FastAPI
from backend.routers import users
from backend.crud.database import init_db
from backend.routers import flights

app = FastAPI()


@app.on_event("startup")
def startup():
    init_db()


app.include_router(users.router)
app.include_router(flights.router)


@app.get("/")
def hello():
    return {"message": "Flight Booking API"}
