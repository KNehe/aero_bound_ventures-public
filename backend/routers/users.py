from backend.models.users import UserInDB
from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import Annotated
from backend.schemas.users import UserCreate, UserRead
from backend.crud.database import get_session
from backend.utils.cookies import get_cookie_settings, get_cookie_domain, is_production
from backend.crud.users import (
    get_user_by_email,
    create_user,
    create_password_reset_token,
    verify_password_reset_token,
    update_password_with_token,
)
from sqlmodel import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    Token,
    UserInfo,
    GroupRead,
    PermissionRead,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    VerifyResetTokenResponse,
)
from backend.utils.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.utils.log_manager import get_app_logger
from backend.utils.kafka import kafka_producer
from backend.utils.constants import KafkaTopics, KafkaEventTypes


router = APIRouter()

logger = get_app_logger(__name__)


@router.post("/register/", response_model=UserRead)
async def register(
    user_in: UserCreate,
    session: Session = Depends(get_session),
):
    user = get_user_by_email(session, user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = create_user(session, email=user_in.email, password=user_in.password)

    kafka_producer.send(
        KafkaTopics.USER_EVENTS,
        {
            "event_type": KafkaEventTypes.USER_REGISTERED,
            "email": user.email,
            "user_id": str(user.id),
        },
    )

    return user


@router.post("/token")
async def login(
    response: Response,
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

    # Set HTTP-only cookie
    cookie_settings = get_cookie_settings()
    cookie_domain = get_cookie_domain()
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=cookie_settings["httponly"],
        secure=cookie_settings["secure"],
        samesite=cookie_settings["samesite"],
        max_age=cookie_settings["max_age"],
        domain=cookie_domain,
    )

    # Build user info with groups and permissions
    groups_with_permissions = [
        GroupRead(
            name=group.name,
            description=group.description,
            permissions=[
                PermissionRead(
                    name=perm.name,
                    codename=perm.codename,
                    description=perm.description,
                )
                for perm in group.permissions
            ],
        )
        for group in user.groups
    ]

    user_info = UserInfo(
        id=user.id,
        email=user.email,
        groups=groups_with_permissions,
    )

    return Token(token_type="bearer", user=user_info)


@router.post("/logout")
async def logout(response: Response):
    """
    Clear the authentication cookie.
    """
    cookie_domain = get_cookie_domain()
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=is_production(),
        samesite="lax",
        domain=cookie_domain,
    )
    return {"message": "Successfully logged out"}


@router.post("/forgot-password/", response_model=ResetPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    session: Session = Depends(get_session),
):
    """
    Request a password reset. Sends an email with reset token if user exists.
    Always returns success to prevent email enumeration attacks.
    """
    try:
        reset_token = create_password_reset_token(session, request.email)

        if reset_token:
            kafka_producer.send(
                KafkaTopics.USER_EVENTS,
                {
                    "event_type": KafkaEventTypes.PASSWORD_RESET_REQUESTED,
                    "email": request.email,
                    "reset_token": reset_token,
                },
            )
            logger.info(f"Password reset email event sent for {request.email}")
        else:
            # Log attempt for non-existent email but don't reveal this to user
            logger.warning(
                f"Password reset attempt for non-existent email: {request.email}"
            )

    except Exception as e:
        # Log the error but don't expose it to the user
        logger.error(f"Error in forgot_password: {str(e)}")

    # Always return success to prevent email enumeration
    return ResetPasswordResponse(
        success=True,
        message="If your email is registered, you will receive a password reset link shortly.",
    )


@router.get("/verify-reset-token/{token}", response_model=VerifyResetTokenResponse)
async def verify_reset_token(
    token: str,
    session: Session = Depends(get_session),
):
    """
    Verify if a password reset token is valid and not expired.
    """
    user = verify_password_reset_token(session, token)

    if user:
        return VerifyResetTokenResponse(valid=True, message="Token is valid")
    else:
        return VerifyResetTokenResponse(
            valid=False, message="Token is invalid or has expired"
        )


@router.post("/reset-password/", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    session: Session = Depends(get_session),
):
    """
    Reset password using a valid reset token.
    """
    # Verify token and update password
    success = update_password_with_token(session, request.token, request.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    logger.info("Password successfully reset for a user")

    return ResetPasswordResponse(
        success=True, message="Password has been reset successfully"
    )


@router.get("/me/", response_model=UserInfo)
async def fetch_current_user(
    current_user: UserInDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get current authenticated user's information.
    
    This endpoint is used by the frontend to check authentication status
    and retrieve user info (since HTTP-only cookies can't be read by JavaScript).
    """
    # Build groups with permissions
    groups_with_permissions = [
        GroupRead(
            name=group.name,
            description=group.description,
            permissions=[
                PermissionRead(
                    name=perm.name,
                    codename=perm.codename,
                    description=perm.description,
                )
                for perm in group.permissions
            ],
        )
        for group in current_user.groups
    ]
    
    return UserInfo(
        id=current_user.id,
        email=current_user.email,
        auth_provider=current_user.auth_provider or "email",
        groups=groups_with_permissions,
    )


@router.post("/change-password/", response_model=ChangePasswordResponse)
def change_password(
    password_data: ChangePasswordRequest,
    user: UserInDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not verify_password(password_data.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect"
        )

    user.password = hash_password(password_data.new_password)
    session.add(user)
    session.commit()

    return ChangePasswordResponse(
        success=True, message="Password has been changed successfully"
    )
