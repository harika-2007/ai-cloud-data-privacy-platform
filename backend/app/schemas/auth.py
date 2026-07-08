"""Pydantic schemas for authentication module.

Defines request/response models for user registration, login,
Google OAuth, token management, and role-based access control.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str
    role: str = "user"
    exp: int
    type: str = "access"
    iat: Optional[int] = None


class UserRegisterRequest(BaseModel):
    """Request schema for local user registration."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    """Request schema for local user login."""
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    """Request schema for Google Sign-In authentication."""
    credential: str = Field(
        ...,
        description="Google ID token credential from Google Identity Services",
    )


class UserResponse(BaseModel):
    """Response schema for user data (safe, no password)."""
    id: str
    name: str
    email: EmailStr
    role: str
    is_active: bool
    provider: str = "LOCAL"
    profile_picture: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    email_verified: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing an access token."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Request schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
