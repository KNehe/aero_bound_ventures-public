from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from backend.schemas.users import UserCreate, UserRead
from backend.crud.database import get_session
from backend.crud.users import get_user_by_email, create_user
from sqlmodel import Session
from backend.external_services.email import send_email_async
from fastapi import BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from backend.schemas.auth import Token
from backend.utils.security import authenticate_user
from backend.utils.security import create_access_token

router = APIRouter()


@router.post("/register/", response_model=UserRead)
async def register(
    background_tasks: BackgroundTasks,
    user_in: UserCreate,
    session: Session = Depends(get_session),
):
    user = get_user_by_email(session, user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = create_user(session, email=user_in.email, password=user_in.password)

    subject = "Welcome to Aero Bound Ventures!"
    recipients = [user_in.email]
    body_text = f"Hello {user_in.email}, thank you for registering with us. We are excited to have you on board!"
    background_tasks.add_task(send_email_async, subject, recipients, body_text)

    return user


@router.post("/token")
async def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    session: Session = Depends(get_session),
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})

    return Token(access_token=access_token, token_type="bearer")
