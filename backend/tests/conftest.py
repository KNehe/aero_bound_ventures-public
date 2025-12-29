import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel
from fastapi.testclient import TestClient

TEST_DB_NAME = "test_db"
PG_HOST = "127.0.0.1"
URL = os.getenv(
    "DATABASE_URL", f"postgresql://postgres:postgres@{PG_HOST}:5432/postgres"
)

TEST_URL = URL.replace("@db", f"@{PG_HOST}")
if TEST_URL.endswith("/postgres"):
    TEST_URL = TEST_URL.rsplit("/postgres", 1)[0] + f"/{TEST_DB_NAME}"

os.environ["DATABASE_URL"] = TEST_URL

from backend.main import app  # noqa: E402
from backend.crud.database import get_session  # noqa: E402


def _ensure_db():
    base_url = TEST_URL.rsplit("/", 1)[0] + "/postgres"
    engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{TEST_DB_NAME}'")
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    engine.dispose()


_ensure_db()

engine = create_engine(TEST_URL)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def session():
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection) as session:
            yield session
            transaction.rollback()


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
