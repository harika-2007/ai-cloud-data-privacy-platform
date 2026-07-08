"""Integration tests for the authentication API endpoints.

Tests cover user registration, login, token refresh, profile retrieval,
and protected route access. Uses the test client and database fixtures
from conftest.py.
"""

import pytest
from httpx import AsyncClient

from app.core.security import create_refresh_token, create_access_token


pytestmark = pytest.mark.asyncio


class TestRegister:
    """Tests for POST /api/v1/auth/register."""

    async def test_register_success(self, client: AsyncClient, db_session):
        """Test successful user registration returns tokens and user data."""
        payload = {
            "name": "New User",
            "email": "newuser@example.com",
            "password": "SecurePass123",
        }
        response = await client.post(
            "/api/v1/auth/register",
            json=payload,
        )
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["name"] == "New User"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["role"] == "user"
        assert data["user"]["is_active"] is True
        assert "id" in data["user"]

        # Verify tokens are not empty
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user
    ):
        """Test registration with an existing email returns 409."""
        payload = {
            "name": "Duplicate User",
            "email": "testuser@example.com",  # test_user's email
            "password": "SecurePass123",
        }
        response = await client.post(
            "/api/v1/auth/register",
            json=payload,
        )
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()
        assert data["error_code"] == "DUPLICATE"

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with a weak password returns 422."""
        payload = {
            "name": "Weak Password",
            "email": "weakpass@example.com",
            "password": "short",  # Too short and no uppercase/digit
        }
        response = await client.post(
            "/api/v1/auth/register",
            json=payload,
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with an invalid email returns 422."""
        payload = {
            "name": "Invalid Email",
            "email": "not-an-email",
            "password": "SecurePass123",
        }
        response = await client.post(
            "/api/v1/auth/register",
            json=payload,
        )
        assert response.status_code == 422

    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"name": "Missing Fields"},
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login returns tokens and user data."""
        payload = {
            "email": "testuser@example.com",
            "password": "TestPass123",
        }
        response = await client.post(
            "/api/v1/auth/login",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "testuser@example.com"
        assert data["user"]["name"] == "Test User"
        assert data["user"]["is_active"] is True

    async def test_login_invalid_password(self, client: AsyncClient, test_user):
        """Test login with wrong password returns 401."""
        payload = {
            "email": "testuser@example.com",
            "password": "WrongPassword123",
        }
        response = await client.post(
            "/api/v1/auth/login",
            json=payload,
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"

    async def test_login_nonexistent_email(self, client: AsyncClient):
        """Test login with an unregistered email returns 401."""
        payload = {
            "email": "nobody@example.com",
            "password": "SomePassword123",
        }
        response = await client.post(
            "/api/v1/auth/login",
            json=payload,
        )
        assert response.status_code == 401

    async def test_login_inactive_user(self, client: AsyncClient, inactive_user):
        """Test login for a deactivated user returns 401."""
        payload = {
            "email": "inactive@example.com",
            "password": "InactivePass123",
        }
        response = await client.post(
            "/api/v1/auth/login",
            json=payload,
        )
        assert response.status_code == 401
        data = response.json()
        assert "deactivated" in data["detail"].lower()

    async def test_login_empty_fields(self, client: AsyncClient):
        """Test login with empty fields returns 422."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "", "password": ""},
        )
        assert response.status_code == 422


class TestRefreshToken:
    """Tests for POST /api/v1/auth/refresh."""

    async def test_refresh_success(self, client: AsyncClient, test_user):
        """Test successful token refresh returns new tokens."""
        refresh_token = create_refresh_token(
            subject=test_user.id, role=test_user.role
        )
        payload = {"refresh_token": refresh_token}
        response = await client.post(
            "/api/v1/auth/refresh",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "testuser@example.com"

        # New tokens should be different from the old one
        assert data["refresh_token"] != refresh_token

    async def test_refresh_with_access_token(self, client: AsyncClient, test_user):
        """Test refreshing with an access token instead of refresh token returns 401."""
        access_token = create_access_token(
            subject=test_user.id, role=test_user.role
        )
        payload = {"refresh_token": access_token}
        response = await client.post(
            "/api/v1/auth/refresh",
            json=payload,
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with a garbage token returns 401."""
        payload = {"refresh_token": "not-a-valid-jwt-token"}
        response = await client.post(
            "/api/v1/auth/refresh",
            json=payload,
        )
        assert response.status_code == 401

    async def test_refresh_expired_token(self, client: AsyncClient):
        """Test refresh with an expired token returns 401."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNTAwMDAwMDAwfQ.signature"},
        )
        assert response.status_code == 401


class TestMeEndpoint:
    """Tests for GET /api/v1/auth/me."""

    async def test_me_success(self, client: AsyncClient, user_auth_headers, test_user):
        """Test getting the current user profile returns user data."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=user_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        assert data["email"] == "testuser@example.com"
        assert data["name"] == "Test User"
        assert data["role"] == "user"
        assert data["is_active"] is True

    async def test_me_no_token(self, client: AsyncClient):
        """Test accessing /me without a token returns 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED" or "detail" in data

    async def test_me_invalid_token(self, client: AsyncClient):
        """Test accessing /me with an invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid-token-here"}
        response = await client.get(
            "/api/v1/auth/me",
            headers=headers,
        )
        assert response.status_code == 401

    async def test_me_expired_token(self, client: AsyncClient, test_user):
        """Test accessing /me with an expired token returns 401."""
        # Create a token that expired in the past
        expired_token = create_access_token(
            subject=test_user.id,
            role=test_user.role,
            expires_delta=-1,  # negative timedelta = expired
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.get(
            "/api/v1/auth/me",
            headers=headers,
        )
        assert response.status_code == 401


class TestProtectedRoutes:
    """Tests that various protected routes reject unauthenticated requests."""

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/files"),
        ("POST", "/api/v1/files/upload"),
        ("POST", "/api/v1/scans/start/some-file-id"),
        ("GET", "/api/v1/scans/file/some-file-id"),
        ("GET", "/api/v1/dashboard/stats"),
        ("GET", "/api/v1/alerts"),
        ("GET", "/api/v1/reports"),
        ("GET", "/api/v1/users/"),
    ]

    @pytest.mark.parametrize("method, endpoint", PROTECTED_ENDPOINTS)
    async def test_protected_route_no_token(
        self, client: AsyncClient, method: str, endpoint: str
    ):
        """Test that all protected routes return 401 when no token is provided."""
        response = await client.request(method, endpoint)
        assert response.status_code == 401, (
            f"Expected 401 for {method} {endpoint}, got {response.status_code}"
        )


class TestChangePassword:
    """Tests for POST /api/v1/auth/change-password."""

    async def test_change_password_success(
        self, client: AsyncClient, user_auth_headers, test_user
    ):
        """Test successful password change returns 204."""
        payload = {
            "current_password": "TestPass123",
            "new_password": "NewSecurePass456",
        }
        response = await client.post(
            "/api/v1/auth/change-password",
            json=payload,
            headers=user_auth_headers,
        )
        assert response.status_code == 204

        # Verify we can login with the new password
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "NewSecurePass456",
            },
        )
        assert login_response.status_code == 200

    async def test_change_password_wrong_current(
        self, client: AsyncClient, user_auth_headers
    ):
        """Test changing password with wrong current password returns 401."""
        payload = {
            "current_password": "WrongCurrentPass",
            "new_password": "NewSecurePass456",
        }
        response = await client.post(
            "/api/v1/auth/change-password",
            json=payload,
            headers=user_auth_headers,
        )
        assert response.status_code == 401

    async def test_change_password_no_auth(self, client: AsyncClient):
        """Test changing password without authentication returns 401."""
        payload = {
            "current_password": "TestPass123",
            "new_password": "NewSecurePass456",
        }
        response = await client.post(
            "/api/v1/auth/change-password",
            json=payload,
        )
        assert response.status_code == 401
