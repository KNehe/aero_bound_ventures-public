from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
import jwt
from sqlmodel import Session, select
from backend.models.users import UserInDB
from backend.models.permissions import Group
import os
from fastapi import Depends, HTTPException, status, Request
from jwt.exceptions import InvalidTokenError
from backend.crud.database import get_session
import secrets
from sqlalchemy.orm import selectinload


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_reset_token() -> str:
    """Generate a cryptographically secure random token for password reset."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """Hash the reset token before storing in database."""
    return pwd_context.hash(token)


def verify_reset_token(plain_token: str, hashed_token: str) -> bool:
    """Verify a reset token against its hash."""
    return pwd_context.verify(plain_token, hashed_token)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    data_to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    data_to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(session: Session, email: str, password: str):
    # Eager load groups and their permissions
    statement = (
        select(UserInDB)
        .where(UserInDB.email == email)
        .options(selectinload(UserInDB.groups).selectinload(Group.permissions))
    )
    user = session.exec(statement).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
):
    """
    Get current authenticated user from JWT token.
    
    Tries to get token from:
    1. Authorization header (Bearer token)
    2. HTTP-only cookie (access_token)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from Authorization header first, then from cookie
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = session.exec(select(UserInDB).where(UserInDB.email == email)).first()
        if user is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    return user


def get_user_from_token(
    token: str | None,
    session: Session,
    request: Request | None = None,
) -> UserInDB:
    """
    Validate a JWT token and return the user.
    Used for SSE endpoints where token may be passed as query param or via cookie.
    
    Args:
        token: JWT access token (from query param)
        session: Database session
        request: Optional request object to read cookie from
        
    Returns:
        UserInDB if valid
        
    Raises:
        HTTPException 401 if token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    # Try query param token first, then cookie
    if not token and request:
        token = request.cookies.get("access_token")
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = session.exec(select(UserInDB).where(UserInDB.email == email)).first()
        if user is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    return user
