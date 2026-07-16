"""Integration tests for the authentication API endpoints.

Tests cover token refresh, profile retrieval, and protected route access.
Only Google OAuth authentication is supported — no email/password auth.
"""

import pytest
from httpx import AsyncClient

from app.core.security import create_refresh_token, create_access_token


pytestmark = pytest.mark.asyncio


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


