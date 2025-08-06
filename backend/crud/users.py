from sqlmodel import Session, select
from backend.models.users import UserInDB
from backend.utils.security import hash_password


def get_user_by_email(session: Session, email: str):
    return session.exec(select(UserInDB).where(UserInDB.email == email)).first()


def create_user(session: Session, email: str, password: str):
    hashed_password = hash_password(password)
    user = UserInDB(email=email, password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
