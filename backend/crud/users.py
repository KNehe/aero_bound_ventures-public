from sqlmodel import Session, select
from backend.models.users import UserInDB
from backend.models.permissions import Group, UserGroup
from backend.models.constants import ADMIN_GROUP_NAME
from backend.utils.security import (
    hash_password,
    generate_reset_token,
    hash_reset_token,
    verify_reset_token,
)
from datetime import datetime, timedelta, timezone
from typing import Optional, List


def get_user_by_email(session: Session, email: str):
    return session.exec(select(UserInDB).where(UserInDB.email == email)).first()


def create_user(session: Session, email: str, password: str):
    hashed_password = hash_password(password)
    user = UserInDB(email=email, password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_password_reset_token(session: Session, email: str) -> Optional[str]:
    """
    Create a password reset token for a user.
    Returns the plain token if user exists, None otherwise.
    """
    user = get_user_by_email(session, email)
    if not user:
        return None

    # Generate token and hash it
    plain_token = generate_reset_token()
    hashed_token = hash_reset_token(plain_token)

    # Set expiration to 1 hour from now
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # Update user with reset token
    user.reset_token = hashed_token
    user.reset_token_expires = expires_at
    session.add(user)
    session.commit()

    return plain_token


def verify_password_reset_token(session: Session, token: str) -> Optional[UserInDB]:
    """
    Verify a password reset token and return the user if valid.
    Returns None if token is invalid or expired.
    """
    # Get all users with a reset token set
    users = session.exec(
        select(UserInDB).where(UserInDB.reset_token.is_not(None))
    ).all()

    for user in users:
        # Check if token matches and hasn't expired
        if user.reset_token and verify_reset_token(token, user.reset_token):
            if user.reset_token_expires and user.reset_token_expires > datetime.now(
                timezone.utc
            ):
                return user

    return None


def update_password_with_token(session: Session, token: str, new_password: str) -> bool:
    """
    Update user password using reset token.
    Returns True if successful, False otherwise.
    """
    user = verify_password_reset_token(session, token)
    if not user:
        return False

    # Update password
    user.password = hash_password(new_password)

    # Invalidate reset token
    user.reset_token = None
    user.reset_token_expires = None

    session.add(user)
    session.commit()

    return True


def invalidate_reset_token(session: Session, user_id: str):
    """Invalidate a user's reset token."""
    user = session.get(UserInDB, user_id)
    if user:
        user.reset_token = None
        user.reset_token_expires = None
        session.add(user)
        session.commit()


def get_admin_emails(session: Session) -> List[str]:
    """Return a list of emails for all users in the admin group."""
    admin_group = session.exec(
        select(Group).where(Group.name == ADMIN_GROUP_NAME)
    ).first()
    if not admin_group:
        return []
    return [user.email for user in admin_group.users if user.is_active]


def get_admin_users(session: Session):
    """Get all users who belong to the admin group"""
    statement = (
        select(UserInDB)
        .join(UserGroup)
        .join(Group)
        .where(Group.name == ADMIN_GROUP_NAME)
    )
    return session.exec(statement).all()


def get_user_by_google_id(session: Session, google_id: str) -> Optional[UserInDB]:
    """Find a user by their Google ID."""
    return session.exec(select(UserInDB).where(UserInDB.google_id == google_id)).first()


def create_google_user(session: Session, email: str, google_id: str) -> UserInDB:
    """Create a new user from Google OAuth."""
    user = UserInDB(
        email=email,
        google_id=google_id,
        auth_provider="google",
        password=None,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def link_google_account(session: Session, user: UserInDB, google_id: str) -> UserInDB:
    """Link a Google account to an existing user."""
    user.google_id = google_id
    if user.auth_provider == "email":
        user.auth_provider = "google"
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
