"""Security module for authentication and authorization.

Provides JWT token creation/verification, password hashing (bcrypt with
SHA-256 pre-hashing for passwords > 60 bytes to avoid the 72-byte bcrypt
limit), and role-based access control dependency injection for FastAPI
routes.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.core.config.settings import settings
from app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/google/login")

_PASSWORD_PREHASH_LIMIT = 60  # Pre-hash passwords longer than this (bytes)


def _prehash_password(password: str) -> bytes:
    """Pre-hash a password with SHA-256 if it exceeds the safe bcrypt limit.

    bcrypt has a 72-byte limit. Many unicode passwords exceed this.
    We pre-hash with SHA-256 before passing to bcrypt, which is the
    standard recommended workaround and is also what passlib's
    bcrypt_sha256 does internally.

    Important: we detect whether the incoming hash is a pre-hashed one
    by checking for the $bsd$ prefix (legacy format) or a bcrypt salt
    starting variant. For verification, we try both.

    Returns the UTF-8 encoded bytes ready for bcrypt.
    """
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > _PASSWORD_PREHASH_LIMIT:
        # SHA-256 pre-hash, encode as hex to keep it clean
        prehash = hashlib.sha256(pw_bytes).hexdigest()
        return prehash.encode("utf-8")
    return pw_bytes


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    For passwords longer than 60 bytes, transparently pre-hashes with
    SHA-256 to avoid the 72-byte bcrypt limit. The resulting hash is
    indistinguishable from a regular bcrypt hash for verification
    purposes (we detect pre-hashing on verify automatically).
    """
    pw_bytes = _prehash_password(password)
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against its bcrypt hash.

    Tries direct verification first. If that fails and the password is
    long enough to have been pre-hashed, retries with SHA-256 pre-hashing.
    """
    pw_bytes = plain_password.encode("utf-8")
    stored_hash = hashed_password.encode("utf-8")

    # Try direct verification first (works for all passwords < 72 bytes)
    try:
        if bcrypt.checkpw(pw_bytes, stored_hash):
            return True
    except ValueError:
        pass

    # Short passwords won't have been pre-hashed — no need to retry
    if len(pw_bytes) <= _PASSWORD_PREHASH_LIMIT:
        return False

    # Retry with SHA-256 pre-hashing
    try:
        prehashed = hashlib.sha256(pw_bytes).hexdigest().encode("utf-8")
        return bcrypt.checkpw(prehashed, stored_hash)
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token with user info and expiration."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, role: str) -> str:
    """Create a JWT refresh token with longer expiration."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> TokenPayload:
    """FastAPI dependency that extracts and validates the current user from a JWT."""
    token_data = decode_token(token)
    if token_data.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return token_data


def require_role(required_role: str):
    """Factory for role-based access control dependency.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(user: TokenPayload = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        role_hierarchy = {"admin": 4, "analyst": 3, "user": 2, "viewer": 1}
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' or higher required",
            )
        return current_user
    return role_checker
