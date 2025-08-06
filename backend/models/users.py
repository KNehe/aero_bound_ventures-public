from pydantic import EmailStr
import uuid
from sqlmodel import SQLModel, Field


class UserInDB(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    email: EmailStr = Field(index=True, unique=True)
    password: str
