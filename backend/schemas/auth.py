from pydantic import BaseModel, EmailStr, Field, field_validator
import uuid


class PermissionRead(BaseModel):
    """Schema for reading permission data"""

    name: str
    codename: str
    description: str | None = None

    class Config:
        from_attributes = True


class GroupRead(BaseModel):
    """Schema for reading group data with permissions"""

    name: str
    description: str | None = None
    permissions: list[PermissionRead] = []

    class Config:
        from_attributes = True


class GroupResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    """User information included in token response"""

    id: uuid.UUID
    email: str
    auth_provider: str = "email"
    groups: list[GroupRead] = []

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response schema"""

    id: str
    email: str
    is_active: bool
    is_superuser: bool
    auth_provider: str
    groups: list[GroupResponse]

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserInfo


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str


class ChangePasswordResponse(ResetPasswordResponse):
    pass


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class VerifyResetTokenResponse(BaseModel):
    valid: bool
    message: str
