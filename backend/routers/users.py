from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from backend.application.users.change_password import (
    ChangePassword,
    ChangePasswordCommand,
)
from backend.application.users.get_current_user_profile import (
    GetCurrentUserProfile,
    GetCurrentUserProfileCommand,
)
from backend.application.users.login_user import LoginUser, LoginUserCommand
from backend.application.users.register_user import RegisterUser, RegisterUserCommand
from backend.application.users.request_password_reset import RequestPasswordReset
from backend.application.users.reset_password import ResetPassword, ResetPasswordCommand
from backend.application.users.user_accounts import (
    IncorrectCurrentPassword,
    InvalidLoginCredentials,
    InvalidPasswordResetToken,
    UserAlreadyExists,
    UserProfileRecord,
)
from backend.application.users.verify_password_reset import VerifyPasswordReset
from backend.crud.database import get_session
from backend.infrastructure.users.kafka_user_event_publisher import (
    KafkaUserEventPublisher,
)
from backend.infrastructure.users.security_user_credentials import (
    JwtAccessTokenProvider,
    SecurityPasswordService,
)
from backend.infrastructure.users.sqlmodel_user_repository import (
    SqlModelUserRepository,
)
from backend.models.users import UserInDB
from backend.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    ForgotPasswordRequest,
    GroupRead,
    PermissionRead,
    ResetPasswordRequest,
    ResetPasswordResponse,
    Token,
    UserInfo,
    VerifyResetTokenResponse,
)
from backend.schemas.users import UserCreate, UserRead
from backend.utils.cookies import get_cookie_domain, get_cookie_settings, is_production
from backend.utils.kafka import kafka_producer
from backend.utils.log_manager import get_app_logger
from backend.utils.security import get_current_user


router = APIRouter()

logger = get_app_logger(__name__)


def get_register_user_use_case(
    session: Session = Depends(get_session),
) -> RegisterUser:
    return RegisterUser(
        user_repository=SqlModelUserRepository(session),
        password_service=SecurityPasswordService(),
        event_publisher=KafkaUserEventPublisher(kafka_producer),
    )


def get_login_user_use_case(
    session: Session = Depends(get_session),
) -> LoginUser:
    return LoginUser(
        user_repository=SqlModelUserRepository(session),
        password_service=SecurityPasswordService(),
        access_token_provider=JwtAccessTokenProvider(),
    )


def get_request_password_reset_use_case(
    session: Session = Depends(get_session),
) -> RequestPasswordReset:
    return RequestPasswordReset(
        user_repository=SqlModelUserRepository(session),
        password_service=SecurityPasswordService(),
        event_publisher=KafkaUserEventPublisher(kafka_producer),
    )


def get_verify_password_reset_use_case(
    session: Session = Depends(get_session),
) -> VerifyPasswordReset:
    return VerifyPasswordReset(
        user_repository=SqlModelUserRepository(session),
        password_service=SecurityPasswordService(),
    )


def get_reset_password_use_case(
    session: Session = Depends(get_session),
) -> ResetPassword:
    return ResetPassword(
        user_repository=SqlModelUserRepository(session),
        password_service=SecurityPasswordService(),
    )


def get_current_user_profile_use_case() -> GetCurrentUserProfile:
    return GetCurrentUserProfile()


def get_change_password_use_case(
    session: Session = Depends(get_session),
) -> ChangePassword:
    return ChangePassword(
        user_repository=SqlModelUserRepository(session),
        password_service=SecurityPasswordService(),
        event_publisher=KafkaUserEventPublisher(kafka_producer),
    )


def _to_user_info(user_profile: UserProfileRecord) -> UserInfo:
    return UserInfo(
        id=user_profile.id,
        email=user_profile.email,
        auth_provider=user_profile.auth_provider,
        groups=[
            GroupRead(
                name=group.name,
                description=group.description,
                permissions=[
                    PermissionRead(
                        name=permission.name,
                        codename=permission.codename,
                        description=permission.description,
                    )
                    for permission in group.permissions
                ],
            )
            for group in user_profile.groups
        ],
    )


@router.post("/register/", response_model=UserRead)
async def register(
    user_in: UserCreate,
    register_user_use_case: RegisterUser = Depends(get_register_user_use_case),
):
    try:
        user = register_user_use_case.execute(
            command=RegisterUserCommand(
                email=str(user_in.email),
                password=user_in.password,
            )
        )
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    return UserRead(id=user.id, email=user.email)


@router.post("/token")
async def login(
    response: Response,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    login_user_use_case: LoginUser = Depends(get_login_user_use_case),
) -> Token:
    try:
        logged_in_user = login_user_use_case.execute(
            command=LoginUserCommand(
                email=form_data.username,
                password=form_data.password,
            )
        )
    except InvalidLoginCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    cookie_settings = get_cookie_settings()
    response.set_cookie(
        key="access_token",
        value=logged_in_user.access_token,
        httponly=cookie_settings["httponly"],
        secure=cookie_settings["secure"],
        samesite=cookie_settings["samesite"],
        max_age=cookie_settings["max_age"],
        domain=get_cookie_domain(),
    )

    return Token(token_type="bearer", user=_to_user_info(logged_in_user.user))


@router.post("/logout")
async def logout(response: Response):
    """
    Clear the authentication cookie.
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=is_production(),
        samesite="lax",
        domain=get_cookie_domain(),
    )
    return {"message": "Successfully logged out"}


@router.post("/forgot-password/", response_model=ResetPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    request_password_reset_use_case: RequestPasswordReset = Depends(
        get_request_password_reset_use_case
    ),
):
    """
    Request a password reset. Sends an email with reset token if user exists.
    Always returns success to prevent email enumeration attacks.
    """
    try:
        result = request_password_reset_use_case.execute(email=str(request.email))
        if result.reset_token:
            logger.info(f"Password reset email event sent for {request.email}")
        else:
            logger.warning(
                f"Password reset attempt for non-existent email: {request.email}"
            )
    except Exception as exc:
        logger.error(f"Error in forgot_password: {str(exc)}")

    return ResetPasswordResponse(
        success=True,
        message="If your email is registered, you will receive a password reset link shortly.",
    )


@router.get("/verify-reset-token/{token}", response_model=VerifyResetTokenResponse)
async def verify_reset_token(
    token: str,
    verify_password_reset_use_case: VerifyPasswordReset = Depends(
        get_verify_password_reset_use_case
    ),
):
    """
    Verify if a password reset token is valid and not expired.
    """
    result = verify_password_reset_use_case.execute(token=token)
    if result.valid:
        return VerifyResetTokenResponse(valid=True, message="Token is valid")

    return VerifyResetTokenResponse(
        valid=False,
        message="Token is invalid or has expired",
    )


@router.post("/reset-password/", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    reset_password_use_case: ResetPassword = Depends(get_reset_password_use_case),
):
    """
    Reset password using a valid reset token.
    """
    try:
        reset_password_use_case.execute(
            command=ResetPasswordCommand(
                token=request.token,
                new_password=request.new_password,
            )
        )
    except InvalidPasswordResetToken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    logger.info("Password successfully reset for a user")
    return ResetPasswordResponse(
        success=True,
        message="Password has been reset successfully",
    )


@router.get("/me/", response_model=UserInfo)
async def fetch_current_user(
    current_user: UserInDB = Depends(get_current_user),
    current_user_profile_use_case: GetCurrentUserProfile = Depends(
        get_current_user_profile_use_case
    ),
):
    """
    Get current authenticated user's information.

    This endpoint is used by the frontend to check authentication status
    and retrieve user info (since HTTP-only cookies can't be read by JavaScript).
    """
    user_profile = current_user_profile_use_case.execute(
        command=GetCurrentUserProfileCommand(
            user_profile=SqlModelUserRepository.to_user_profile_record(current_user)
        )
    )
    return _to_user_info(user_profile)


@router.post("/change-password/", response_model=ChangePasswordResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    response: Response,
    user: UserInDB = Depends(get_current_user),
    change_password_use_case: ChangePassword = Depends(get_change_password_use_case),
):
    try:
        change_password_use_case.execute(
            command=ChangePasswordCommand(
                user_id=user.id,
                email=str(user.email),
                current_password_hash=user.password,
                current_password=password_data.old_password,
                new_password=password_data.new_password,
            )
        )
    except IncorrectCurrentPassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )

    cookie_settings = get_cookie_settings()
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=get_cookie_domain() if is_production() else None,
        secure=cookie_settings["secure"],
        httponly=cookie_settings["httponly"],
        samesite=cookie_settings["samesite"],
    )

    return ChangePasswordResponse(
        success=True,
        message="Password has been changed successfully. Please log in again.",
    )
