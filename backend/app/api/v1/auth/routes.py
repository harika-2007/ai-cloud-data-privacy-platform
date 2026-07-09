"""Authentication API routes.

Provides endpoints for user registration, login, Google OAuth 2.0
(both popup and server-side redirect flows), token refresh, user
profile retrieval, and password changes.
"""

import logging
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    GoogleLoginRequest,
    RefreshTokenRequest,
    TokenPayload,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth.auth_service import AuthService
from app.utils.exceptions import AppException, UnauthorizedException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency provider for AuthService."""
    user_repo = UserRepository(db)
    return AuthService(user_repo)


# =========================================================================
# Dynamic URL helpers
# =========================================================================


def get_base_url(request: Request) -> str:
    """Determine the base URL of the current request.

    Respects X-Forwarded-Proto and X-Forwarded-Host headers (set by
    nginx/reverse proxies). Falls back to the direct request URL.
    Also checks NGROK_URL and PUBLIC_URL env vars for explicit overrides.
    """
    # 1. Explicit override via env var (highest priority)
    if settings.NGROK_URL:
        return settings.NGROK_URL.rstrip("/")
    if settings.PUBLIC_URL:
        return settings.PUBLIC_URL.rstrip("/")

    # 2. X-Forwarded-* headers (set by nginx reverse proxy)
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
    forwarded_host = request.headers.get("X-Forwarded-Host", "")
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}"

    # 3. Direct Host header
    host = request.headers.get("Host", "localhost:8000")
    # Determine scheme from the request itself
    if forwarded_proto:
        scheme = forwarded_proto
    elif request.url.scheme:
        scheme = request.url.scheme
    else:
        scheme = "http"
    return f"{scheme}://{host}"


def get_google_redirect_uri(request: Request) -> str:
    """Generate the Google OAuth redirect URI dynamically.

    Returns the explicitly configured GOOGLE_REDIRECT_URI if set,
    otherwise constructs it from the request's base URL.
    """
    if settings.GOOGLE_REDIRECT_URI:
        return settings.GOOGLE_REDIRECT_URI
    base = get_base_url(request)
    return f"{base}/api/v1/auth/google/callback"


def should_use_secure_cookie(request: Request) -> bool:
    """Determine if cookies should have the Secure flag.

    Returns True when:
    - The request is over HTTPS
    - The environment is production
    - SECURE_COOKIES is explicitly set to True
    - Running behind ngrok (ngrok forces HTTPS)
    """
    if settings.SECURE_COOKIES:
        return True
    if settings.ENVIRONMENT == "production":
        return True
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
    if forwarded_proto == "https":
        return True
    if request.url.scheme == "https":
        return True
    if settings.NGROK_URL:
        return True
    return False


# =========================================================================
# Server-side Google OAuth redirect flow
# =========================================================================


@router.get(
    "/google/login",
    summary="Google OAuth login (redirect)",
    description="Redirects the user to Google's OAuth 2.0 consent screen. "
    "After authentication, Google redirects back to /auth/google/callback.",
)
async def google_login_redirect(request: Request):
    """Redirect the user to Google's OAuth 2.0 consent screen.

    The redirect_uri is generated dynamically from the current request
    so it works correctly behind ngrok, reverse proxies, and in
    production deployments. The state cookie uses Secure and SameSite
    flags appropriate for the connection.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.warning(
            "Google OAuth is not configured "
            "(GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is empty)"
        )
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Sign-In is not configured on the server",
            error_code="GOOGLE_OAUTH_NOT_CONFIGURED",
        )

    # Generate redirect URI dynamically
    redirect_uri = get_google_redirect_uri(request)
    logger.info("Google OAuth redirect URI: %s", redirect_uri)

    # Generate a state value for CSRF protection
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
        params
    )

    secure = should_use_secure_cookie(request)

    # Store state in a cookie for CSRF validation on callback
    response = RedirectResponse(
        url=google_auth_url,
        status_code=status.HTTP_302_FOUND,
    )
    response.set_cookie(
        key="google_oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=secure,
        samesite="lax",
    )
    return response


@router.get(
    "/google/callback",
    summary="Google OAuth callback",
    description="Handles the OAuth 2.0 callback from Google. Exchanges the "
    "authorization code for tokens, retrieves the user profile, creates or "
    "updates the user in the database, and redirects to the frontend with "
    "JWT tokens.",
)
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle the OAuth 2.0 callback from Google.

    Exchanges the authorization code for an ID token and access token,
    verifies the user's identity, creates or updates the user record,
    and redirects to the frontend with JWT tokens in the URL fragment.
    """
    # Check for error from Google
    if error:
        logger.error("Google OAuth error: %s", error)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error={error}",
            status_code=status.HTTP_302_FOUND,
        )

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.warning("Google OAuth is not configured")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_not_configured",
            status_code=status.HTTP_302_FOUND,
        )

    # Validate state (CSRF protection)
    cookie_state = request.cookies.get("google_oauth_state")
    if not cookie_state or cookie_state != state:
        logger.warning("Google OAuth state mismatch (possible CSRF)")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=invalid_state",
            status_code=status.HTTP_302_FOUND,
        )

    # Exchange authorization code for tokens
    redirect_uri = get_google_redirect_uri(request)
    logger.debug("Using redirect_uri for token exchange: %s", redirect_uri)

    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
                timeout=30,
            )

            if token_response.status_code != 200:
                logger.error(
                    "Google token exchange failed: %s", token_response.text
                )
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/login?error=token_exchange_failed",
                    status_code=status.HTTP_302_FOUND,
                )

            token_data = token_response.json()
            id_token_str = token_data.get("id_token")
            access_token = token_data.get("access_token")

            if not id_token_str and not access_token:
                logger.error("No id_token or access_token in Google response")
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/login?error=no_token",
                    status_code=status.HTTP_302_FOUND,
                )

            # Get user info from Google
            if id_token_str:
                user_info = await verify_google_id_token(id_token_str)
            else:
                user_info_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if user_info_response.status_code != 200:
                    logger.error(
                        "Failed to fetch Google user info: %s",
                        user_info_response.text,
                    )
                    return RedirectResponse(
                        url=f"{settings.FRONTEND_URL}/login?error=userinfo_failed",
                        status_code=status.HTTP_302_FOUND,
                    )
                user_info = user_info_response.json()

    except httpx.RequestError as e:
        logger.error("Google OAuth HTTP request failed: %s", e)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=network_error",
            status_code=status.HTTP_302_FOUND,
        )

    # Create or update the user in the database
    try:
        user_repo = UserRepository(db)
        auth_service = AuthService(user_repo)

        google_id = user_info.get("sub") or user_info.get("id")
        email = user_info.get("email", "")
        name = user_info.get("name", email.split("@")[0])
        picture = user_info.get("picture", "")

        if not google_id or not email:
            logger.error("Google user info missing required fields")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=missing_user_info",
                status_code=status.HTTP_302_FOUND,
            )

        # Find existing user by google_id or email
        user = await user_repo.get_by_google_id(google_id)
        if not user:
            user = await user_repo.get_by_email(email)

        if user:
            update_data = {
                "google_id": google_id,
                "provider": "GOOGLE",
                "profile_picture": picture or user.profile_picture,
                "avatar_url": picture or user.avatar_url,
                "email_verified": True,
                "last_login": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            if name and not user.name.startswith("("):
                update_data["name"] = name
            user = await user_repo.update(user.id, **update_data)
        else:
            user = await user_repo.create(
                name=name or email.split("@")[0],
                email=email,
                google_id=google_id,
                profile_picture=picture,
                avatar_url=picture,
                email_verified=True,
                provider="GOOGLE",
                role="user",
                is_active=True,
                last_login=datetime.now(timezone.utc),
            )

        # Generate JWT tokens
        access_token = auth_service.create_token(user.id, user.role, "access")
        refresh_token = auth_service.create_token(user.id, user.role, "refresh")

        # Redirect to frontend with tokens
        # Using URL fragment (#) instead of query params (?) to prevent
        # tokens from being logged by nginx/reverse proxies or stored
        # in browser history.
        frontend_callback = (
            f"{settings.FRONTEND_URL}/auth/callback"
            f"#access_token={access_token}"
            f"&refresh_token={refresh_token}"
        )
        return RedirectResponse(
            url=frontend_callback,
            status_code=status.HTTP_302_FOUND,
        )

    except AppException:
        raise
    except Exception as e:
        logger.error("Error processing Google OAuth callback: %s", e)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=server_error",
            status_code=status.HTTP_302_FOUND,
        )


async def verify_google_id_token(id_token_str: str) -> dict:
    """Verify a Google ID token and return its payload.

    Validates the JWT signature, expiration, issuer, and audience.
    Falls back to fetching Google's public keys and verifying manually
    when the google-auth library is not available.
    """
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        request = google_requests.Request()
        decoded_token = id_token.verify_oauth2_token(
            id_token_str,
            request,
            settings.GOOGLE_CLIENT_ID,
        )
        return decoded_token
    except ImportError:
        logger.warning(
            "google-auth library not available, using manual verification"
        )
        return await _verify_google_id_token_manual(id_token_str)
    except ValueError as e:
        logger.error("Google token verification failed: %s", e)
        raise


async def _verify_google_id_token_manual(id_token_str: str) -> dict:
    """Fallback Google ID token verification using jose + httpx."""
    from jose import jwk, jwt as jose_jwt
    from jose.utils import base64url_decode

    async with httpx.AsyncClient() as client:
        resp = await client.get("https://www.googleapis.com/oauth2/v3/certs")
        if resp.status_code != 200:
            raise ValueError("Failed to fetch Google public keys")
        certs = resp.json()

    header = jose_jwt.get_unverified_header(id_token_str)
    kid = header.get("kid")
    if not kid:
        raise ValueError("Token header missing 'kid'")

    key_data = None
    for key in certs.get("keys", []):
        if key.get("kid") == kid:
            key_data = key
            break
    if not key_data:
        raise ValueError("Matching public key not found")

    try:
        payload = jose_jwt.decode(
            id_token_str,
            key_data,
            algorithms=["RS256"],
            audience=settings.GOOGLE_CLIENT_ID,
            options={
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "require": ["sub", "email", "aud", "exp"],
            },
        )
    except Exception as e:
        raise ValueError(f"Token verification failed: {e}")

    issuers = ["accounts.google.com", "https://accounts.google.com"]
    if payload.get("iss") not in issuers:
        raise ValueError("Invalid token issuer")

    return payload


# =========================================================================
# Frontend Google Sign-In (popup) flow — receives credential from GIS
# =========================================================================


@router.post(
    "/google-login",
    response_model=TokenResponse,
    summary="Sign in with Google (popup)",
    description="Authenticates or registers a user via Google Sign-In OAuth 2.0 "
    "popup flow. Accepts a Google ID token credential and returns JWT tokens.",
)
async def google_login(
    request: GoogleLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate or register using Google Sign-In (popup flow).

    Verifies the Google ID token from the client-side Google Identity
    Services popup, then either returns JWT tokens for an existing
    Google user or creates a new account.
    """
    try:
        id_token_payload = await verify_google_id_token(request.credential)
        result = await auth_service.authenticate_google_user(id_token_payload)
        logger.info("Google login successful: %s", result.user.email)
        return result
    except ValueError as e:
        raise UnauthorizedException(str(e))
    except AppException:
        raise
    except Exception as e:
        logger.error("Unexpected error during Google login: %s", str(e))
        raise


# =========================================================================
# Email/Password registration & login
# =========================================================================


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with name, email, and password. "
    "Returns JWT tokens on success.",
)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account."""
    try:
        result = await auth_service.register_user(
            name=request.name,
            email=request.email,
            password=request.password,
        )
        logger.info("New user registered: %s", request.email)
        return result
    except AppException:
        raise
    except Exception as e:
        logger.error("Unexpected error during registration: %s", str(e))
        raise


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate a user",
    description="Authenticates a user with email and password. Returns JWT tokens "
    "on success.",
)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate a user and return JWT tokens."""
    try:
        result = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
        )
        logger.info("User logged in: %s", request.email)
        return result
    except AppException:
        raise
    except Exception as e:
        logger.error("Unexpected error during login: %s", str(e))
        raise


# =========================================================================
# Token management
# =========================================================================


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Issues a new access token using a valid refresh token.",
)
async def refresh(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh an expired access token using a refresh token."""
    try:
        result = await auth_service.refresh_token(token=request.refresh_token)
        logger.info("Token refreshed successfully")
        return result
    except AppException:
        raise
    except Exception as e:
        logger.error("Unexpected error during token refresh: %s", str(e))
        raise


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Logs out the user. In a stateless JWT setup, the client discards "
    "the tokens. This endpoint exists for session invalidation if needed.",
)
async def logout(
    current_user: TokenPayload = Depends(get_current_user),
):
    """Logout the current user.

    With stateless JWT tokens, logout is handled client-side by discarding
    tokens. This endpoint can be extended to maintain a token blacklist.
    """
    logger.info("User logged out: %s", current_user.sub)
    return None


# =========================================================================
# User profile
# =========================================================================


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get the profile of the currently authenticated user."""
    user = await auth_service.get_user_by_id(current_user.sub)
    return UserResponse.model_validate(user)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change user password",
    description="Changes the password for the currently authenticated user.",
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: TokenPayload = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Change the password for the authenticated user."""
    try:
        await auth_service.change_password(
            user_id=current_user.sub,
            current_password=request.current_password,
            new_password=request.new_password,
        )
        logger.info("Password changed for user: %s", current_user.sub)
    except AppException:
        raise
    except Exception as e:
        logger.error("Unexpected error during password change: %s", str(e))
        raise
