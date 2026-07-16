"""Tests for the AuthService.

Uses mocked repository and database to verify authentication business
logic independently of the database layer.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.services.auth.auth_service import AuthService
from app.utils.exceptions import NotFoundException


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def user_repo(mock_db):
    """Create a UserRepository with a mocked database session."""
    return UserRepository(mock_db)


@pytest.fixture
def auth_service(user_repo):
    """Create an AuthService with a mocked repository."""
    return AuthService(user_repo)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id="user-123",
        name="Test User",
        email="test@example.com",
        password_hash="$2b$12$hashedpassword1234567890abcdefghijklmnopqrstuvwxyz",
        role="user",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def another_user():
    """Create another sample user for testing."""
    return User(
        id="user-456",
        name="Another User",
        email="another@example.com",
        password_hash="$2b$12$differenthash1234567890abcdefghijklmnopqrstuvwxyz",
        role="analyst",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestRefreshToken:
    """Tests for AuthService.refresh_token."""

    @patch("app.services.auth.auth_service.decode_token")
    @patch("app.services.auth.auth_service.create_access_token")
    @patch("app.services.auth.auth_service.create_refresh_token")
    async def test_refresh_token(
        self,
        mock_create_refresh_token,
        mock_create_access_token,
        mock_decode_token,
        auth_service,
        user_repo,
        sample_user,
    ):
        """Test successful token refresh returns a new access token."""
        # Arrange
        mock_decode_token.return_value = MagicMock(
            sub="user-123",
            type="refresh",
        )
        mock_create_access_token.return_value = "new-access-token"
        mock_create_refresh_token.return_value = "new-refresh-token"

        user_repo.get = AsyncMock(return_value=sample_user)

        # Act
        result = await auth_service.refresh_token(token="valid-refresh-token")

        # Assert
        assert isinstance(result, TokenResponse)
        assert result.access_token == "new-access-token"
        assert result.refresh_token == "new-refresh-token"
        assert result.user.email == "test@example.com"

        mock_decode_token.assert_called_once_with("valid-refresh-token")
        user_repo.get.assert_awaited_once_with("user-123")


class TestGetUserById:
    """Tests for AuthService.get_user_by_id."""

    async def test_get_user_by_id(
        self,
        auth_service,
        user_repo,
        sample_user,
    ):
        """Test retrieving a user by ID returns the user."""
        # Arrange
        user_repo.get_or_raise = AsyncMock(return_value=sample_user)

        # Act
        result = await auth_service.get_user_by_id("user-123")

        # Assert
        assert result.id == "user-123"
        assert result.email == "test@example.com"
        user_repo.get_or_raise.assert_awaited_once_with("user-123")

    async def test_get_user_by_id_not_found(
        self,
        auth_service,
        user_repo,
    ):
        """Test retrieving a non-existent user raises NotFoundException."""
        # Arrange
        from app.utils.exceptions import NotFoundException

        user_repo.get_or_raise = AsyncMock(
            side_effect=NotFoundException("User", "nonexistent")
        )

        # Act & Assert
        with pytest.raises(NotFoundException):
            await auth_service.get_user_by_id("nonexistent")
