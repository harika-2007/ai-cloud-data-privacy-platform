"""Authentication service implementing Google OAuth 2.0 business logic.

Provides Google Sign-In authentication, token refresh, and user lookup
operations. Only Google OAuth is supported — no email/password auth.
All database access is handled through UserRepository.
"""

import logging
from datetime import datetime, timezone

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserResponse
from app.utils.exceptions import NotFoundException, UnauthorizedException

logger = logging.getLogger(__name__)


class AuthService:
    """Service layer for authentication and user management.

    Encapsulates business logic for user registration, authentication,
    Google OAuth, token management, and password changes.
    """

    def __init__(self, user_repository: UserRepository):
        """Initialize the auth service with a user repository.

        Args:
            user_repository: Repository instance for User data access.
        """
        self.user_repo = user_repository

    # ------------------------------------------------------------------
    # Google OAuth 2.0 authentication
    # ------------------------------------------------------------------

    async def authenticate_google_user(self, id_token: dict) -> TokenResponse:
        """Authenticate or register a user via Google Sign-In.

        Verifies the Google ID token payload, looks up an existing user by
        Google ID or email, and creates a new account if one does not exist.

        Args:
            id_token: The decoded Google ID token payload containing:
                - sub: Google account ID
                - email: Verified email address
                - name: Display name
                - picture: Profile photo URL
                - email_verified: Whether Google has verified the email

        Returns:
            TokenResponse containing access token, refresh token, and user data.

        Raises:
            UnauthorizedException: If required fields are missing.
        """
        google_id = id_token.get("sub")
        email = id_token.get("email", "")
        name = id_token.get("name", email.split("@")[0])
        picture = id_token.get("picture", "")
        email_verified = id_token.get("email_verified", False)

        if not google_id or not email:
            raise UnauthorizedException("Invalid Google token: missing required fields")

        # 1. Try to find existing user by Google ID
        user = await self.user_repo.get_by_google_id(google_id)

        # 2. Try by email (link Google account to existing local user)
        if not user:
            user = await self.user_repo.get_by_email(email)

        # 3. Create a new user
        if not user:
            user = await self.user_repo.create(
                name=name,
                email=email,
                google_id=google_id,
                profile_picture=picture,
                avatar_url=picture,
                email_verified=email_verified,
                provider="GOOGLE",
                role="user",
                is_active=True,
                last_login=datetime.now(timezone.utc),
            )
            logger.info("New Google user created: %s (%s)", email, user.id)
        else:
            # Update existing user with Google info
            update_fields: dict = {
                "google_id": google_id,
                "provider": "GOOGLE",
                "profile_picture": picture,
                "avatar_url": picture,
                "email_verified": email_verified,
            }
            if name:
                update_fields["name"] = name
            user = await self.user_repo.update(user.id, **update_fields)
            logger.info("Google user authenticated: %s (%s)", email, user.id)

        # Update last login
        await self.user_repo.update_last_login(user.id)

        return await self._build_token_response(user)

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def create_token(self, subject: str, role: str, token_type: str) -> str:
        """Create a JWT token (access or refresh).

        Args:
            subject: The user ID to embed in the token.
            role: The user's role.
            token_type: "access" or "refresh".

        Returns:
            A signed JWT token string.
        """
        if token_type == "refresh":
            return create_refresh_token(subject=subject, role=role)
        return create_access_token(subject=subject, role=role)

    async def refresh_token(self, token: str) -> TokenResponse:
        """Refresh an access token using a valid refresh token.

        Decodes and validates the refresh token, then issues a new
        access token (and refresh token) for the user.

        Args:
            token: The JWT refresh token.

        Returns:
            TokenResponse containing new access token, refresh token, and user data.

        Raises:
            UnauthorizedException: If the token is invalid, expired, or not a refresh token.
            NotFoundException: If the user referenced in the token no longer exists.
        """
        token_data = decode_token(token)

        if token_data.type != "refresh":
            logger.warning("Refresh attempted with non-refresh token")
            raise UnauthorizedException("Invalid token type")

        user = await self.user_repo.get(token_data.sub)
        if not user:
            logger.warning(
                "Refresh attempted for non-existent user: %s", token_data.sub
            )
            raise NotFoundException("User", token_data.sub)

        if not user.is_active:
            logger.warning("Refresh attempted for inactive user: %s", user.email)
            raise UnauthorizedException("Account is deactivated")

        logger.info("Token refreshed for user: %s", user.email)

        return await self._build_token_response(user)

    async def get_user_by_id(self, user_id: str) -> User:
        """Retrieve a user by their ID.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            The User instance.

        Raises:
            NotFoundException: If no user with the given ID exists.
        """
        return await self.user_repo.get_or_raise(user_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _build_token_response(self, user: User) -> TokenResponse:
        """Build a token response from a user instance.

        Creates access and refresh tokens and assembles the full response.

        Args:
            user: The authenticated user.

        Returns:
            A TokenResponse with tokens and user data.
        """
        access_token = create_access_token(subject=user.id, role=user.role)
        refresh_token = create_refresh_token(subject=user.id, role=user.role)

        user_response = UserResponse.model_validate(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_response,
        )
