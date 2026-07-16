"""Pydantic schemas for Google OAuth authentication.

Defines request/response models for Google Sign-In, token management,
and role-based access control. Only Google OAuth is supported — no
email/password schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str
    role: str = "user"
    exp: int
    type: str = "access"
    iat: Optional[int] = None


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


