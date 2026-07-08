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
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
    UnauthorizedException,
)


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


class TestRegisterUser:
    """Tests for AuthService.register_user."""

    @patch("app.services.auth.auth_service.hash_password")
    @patch("app.services.auth.auth_service.create_access_token")
    @patch("app.services.auth.auth_service.create_refresh_token")
    async def test_register_user_success(
        self,
        mock_create_refresh_token,
        mock_create_access_token,
        mock_hash_password,
        auth_service,
        user_repo,
    ):
        """Test successful user registration returns tokens and user data."""
        # Arrange
        mock_hash_password.return_value = "$2b$12$hashedpassword"
        mock_create_access_token.return_value = "access-token-123"
        mock_create_refresh_token.return_value = "refresh-token-123"

        user_repo.get_by_email = AsyncMock(return_value=None)
        user_repo.create = AsyncMock(
            return_value=User(
                id="user-123",
                name="Test User",
                email="test@example.com",
                password_hash="$2b$12$hashedpassword",
                role="user",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )

        # Act
        result = await auth_service.register_user(
            name="Test User",
            email="test@example.com",
            password="SecurePass123",
        )

        # Assert
        assert isinstance(result, TokenResponse)
        assert result.access_token == "access-token-123"
        assert result.refresh_token == "refresh-token-123"
        assert result.token_type == "bearer"
        assert result.user.email == "test@example.com"
        assert result.user.name == "Test User"
        assert result.user.role == "user"
        assert result.user.is_active is True

        user_repo.get_by_email.assert_awaited_once_with("test@example.com")
        user_repo.create.assert_awaited_once()
        mock_hash_password.assert_called_once_with("SecurePass123")

    async def test_register_user_duplicate_email(
        self,
        auth_service,
        user_repo,
        sample_user,
    ):
        """Test registration with an existing email raises DuplicateException."""
        # Arrange
        user_repo.get_by_email = AsyncMock(return_value=sample_user)

        # Act & Assert
        with pytest.raises(DuplicateException) as exc_info:
            await auth_service.register_user(
                name="Test User",
                email="test@example.com",
                password="SecurePass123",
            )

        assert "already exists" in str(exc_info.value.detail)
        user_repo.get_by_email.assert_awaited_once_with("test@example.com")
        user_repo.create.assert_not_awaited()


class TestAuthenticateUser:
    """Tests for AuthService.authenticate_user."""

    @patch("app.services.auth.auth_service.verify_password")
    @patch("app.services.auth.auth_service.create_access_token")
    @patch("app.services.auth.auth_service.create_refresh_token")
    async def test_authenticate_user_success(
        self,
        mock_create_refresh_token,
        mock_create_access_token,
        mock_verify_password,
        auth_service,
        user_repo,
        sample_user,
    ):
        """Test successful authentication returns tokens."""
        # Arrange
        mock_verify_password.return_value = True
        mock_create_access_token.return_value = "access-token-456"
        mock_create_refresh_token.return_value = "refresh-token-456"

        user_repo.get_by_email = AsyncMock(return_value=sample_user)
        user_repo.update_last_login = AsyncMock(return_value=sample_user)

        # Act
        result = await auth_service.authenticate_user(
            email="test@example.com",
            password="SecurePass123",
        )

        # Assert
        assert isinstance(result, TokenResponse)
        assert result.access_token == "access-token-456"
        assert result.refresh_token == "refresh-token-456"
        assert result.user.email == "test@example.com"
        assert result.user.is_active is True

        user_repo.get_by_email.assert_awaited_once_with("test@example.com")
        mock_verify_password.assert_called_once_with(
            "SecurePass123", sample_user.password_hash
        )
        user_repo.update_last_login.assert_awaited_once_with(sample_user.id)

    async def test_authenticate_user_invalid_password(
        self,
        auth_service,
        user_repo,
        sample_user,
    ):
        """Test authentication with wrong password raises UnauthorizedException."""
        # Arrange
        user_repo.get_by_email = AsyncMock(return_value=sample_user)

        # Act & Assert
        with pytest.raises(UnauthorizedException) as exc_info:
            await auth_service.authenticate_user(
                email="test@example.com",
                password="WrongPassword123",
            )

        assert "Invalid" in str(exc_info.value.detail)
        user_repo.get_by_email.assert_awaited_once_with("test@example.com")

    async def test_authenticate_user_inactive(
        self,
        auth_service,
        user_repo,
        sample_user,
    ):
        """Test authentication for an inactive user raises UnauthorizedException."""
        # Arrange
        sample_user.is_active = False
        user_repo.get_by_email = AsyncMock(return_value=sample_user)

        # Act & Assert
        with pytest.raises(UnauthorizedException) as exc_info:
            await auth_service.authenticate_user(
                email="test@example.com",
                password="SecurePass123",
            )

        assert "deactivated" in str(exc_info.value.detail).lower()


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


class TestChangePassword:
    """Tests for AuthService.change_password."""

    @patch("app.services.auth.auth_service.verify_password")
    @patch("app.services.auth.auth_service.hash_password")
    async def test_change_password(
        self,
        mock_hash_password,
        mock_verify_password,
        auth_service,
        user_repo,
        sample_user,
    ):
        """Test successful password change."""
        # Arrange
        mock_verify_password.return_value = True
        mock_hash_password.return_value = "$2b$12$newhashedpassword"

        user_repo.get_or_raise = AsyncMock(return_value=sample_user)
        user_repo.update = AsyncMock(return_value=sample_user)

        # Act
        await auth_service.change_password(
            user_id="user-123",
            current_password="OldPass123",
            new_password="NewPass456",
        )

        # Assert
        user_repo.get_or_raise.assert_awaited_once_with("user-123")
        mock_verify_password.assert_called_once_with(
            "OldPass123", sample_user.password_hash
        )
        mock_hash_password.assert_called_once_with("NewPass456")
        user_repo.update.assert_awaited_once_with(
            "user-123", password_hash="$2b$12$newhashedpassword"
        )


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


class TestListUsers:
    """Tests for AuthService.list_users."""

    async def test_list_users(
        self,
        auth_service,
        user_repo,
        sample_user,
        another_user,
    ):
        """Test listing users returns paginated results."""
        # Arrange
        user_repo.get_all = AsyncMock(return_value=([sample_user, another_user], 2))

        # Act
        users, total = await auth_service.list_users(page=1, page_size=20)

        # Assert
        assert len(users) == 2
        assert total == 2
        user_repo.get_all.assert_awaited_once_with(
            skip=0, limit=20
        )

    async def test_list_users_with_role_filter(
        self,
        auth_service,
        user_repo,
        sample_user,
    ):
        """Test listing users filtered by role."""
        # Arrange
        user_repo.get_all = AsyncMock(return_value=([sample_user], 1))

        # Act
        users, total = await auth_service.list_users(page=1, page_size=10, role="user")

        # Assert
        assert len(users) == 1
        assert total == 1
        user_repo.get_all.assert_awaited_once_with(
            skip=0, limit=10, role="user"
        )
