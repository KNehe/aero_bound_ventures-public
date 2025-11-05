from backend.models.users import UserInDB
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from backend.schemas.users import UserCreate, UserRead
from backend.crud.database import get_session
from backend.crud.users import (
    get_user_by_email,
    create_user,
    create_password_reset_token,
    verify_password_reset_token,
    update_password_with_token,
)
from sqlmodel import Session
from backend.external_services.email import send_email_async, send_password_reset_email
from fastapi import BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from backend.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    Token,
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


router = APIRouter()

logger = get_app_logger(__name__)


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


@router.post("/forgot-password/", response_model=ResetPasswordResponse)
async def forgot_password(
    background_tasks: BackgroundTasks,
    request: ForgotPasswordRequest,
    session: Session = Depends(get_session),
):
    """
    Request a password reset. Sends an email with reset token if user exists.
    Always returns success to prevent email enumeration attacks.
    """
    try:
        # Create reset token
        reset_token = create_password_reset_token(session, request.email)

        # Send email only if user exists
        if reset_token:
            background_tasks.add_task(
                send_password_reset_email, request.email, reset_token
            )
            logger.info(f"Password reset email sent to {request.email}")
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


@router.get("/me/", response_model=UserRead)
async def fetch_current_user(current_user: UserInDB = Depends(get_current_user)):
    return current_user


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
