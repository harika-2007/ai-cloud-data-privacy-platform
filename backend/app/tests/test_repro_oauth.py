"""Reproduce the Google OAuth callback failure.

Exercises the EXACT database operations from google_callback
to capture any exception, its type, and exact line of code.
"""

import logging
import sys
import traceback
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


@pytest.mark.asyncio
async def test_repro_google_callback_user_creation(app, client, db_session):
    """Reproduce the database operations from google_callback exactly.

    Tests the EXACT code path for creating a NEW user from Google data.
    This is the create() path in the callback.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.auth.auth_service import AuthService
    from app.utils.exceptions import AppException

    # --- Step 1: Build the callback's database block EXACTLY as it runs ---
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo)

    # --- Step 2: Simulate Google ID token payload ---
    google_info = {
        "sub": "google-id-12345",
        "email": "googleuser@example.com",
        "name": "Google User",
        "picture": "https://lh3.googleusercontent.com/a/photo",
        "email_verified": True,
    }
    google_id = google_info.get("sub") or google_info.get("id")
    email = google_info.get("email", "")
    name = google_info.get("name", email.split("@")[0])
    picture = google_info.get("picture", "")

    print(f"\n=== REPRO: Creating new Google user ===")
    print(f"google_id={google_id!r}, email={email!r}, name={name!r}, picture={picture!r}")

    try:
        # Find existing user
        user = await user_repo.get_by_google_id(google_id)
        print(f"User by google_id: {user.id if user else 'None'}")

        if not user:
            user = await user_repo.get_by_email(email)
            print(f"User by email: {user.id if user else 'None'}")

        # --- Step 3: CREATE new user ---
        if not user:
            print("Creating new user...")
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
            print(f"Created user ID: {user.id!r} (type: {type(user.id).__name__})")

        # --- Step 4: Generate JWT ---
        access_token = auth_service.create_token(user.id, user.role, "access")
        refresh_token = auth_service.create_token(user.id, user.role, "refresh")
        print(f"Tokens generated: access={access_token[:20]}..., refresh={refresh_token[:20]}...")
        print("=== SUCCESS ===")

    except AppException:
        raise
    except Exception as e:
        print(f"\n!!! EXCEPTION CAUGHT !!!")
        print(f"Type: {type(e).__name__}")
        print(f"Args: {e.args}")
        print(f"Repr: {e!r}")
        traceback.print_exc()
        pytest.fail(f"Exception raised: {type(e).__name__}: {e}")


@pytest.mark.asyncio
async def test_repro_google_callback_existing_user(client, app, db_session):
    """Test the UPDATE path - when a user already exists by email.

    This simulates a Google user whose email matches an existing LOCAL user.
    """
    from app.models.user import User
    from app.repositories.user_repository import UserRepository
    from app.services.auth.auth_service import AuthService

    # Create an existing LOCAL user first
    existing_user = User(
        id="00000000-0000-0000-0000-000000000010",
        name="Existing User",
        email="existing@example.com",
        provider="LOCAL",
        role="user",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(existing_user)
    await db_session.flush()

    print(f"\n=== REPRO: Updating existing user with Google ID ===")
    print(f"Pre-created user: id={existing_user.id!r}")

    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo)

    google_info = {
        "sub": "google-id-existing",
        "email": "existing@example.com",
        "name": "Existing User",
        "picture": "https://lh3.googleusercontent.com/a/photo",
        "email_verified": True,
    }
    google_id = google_info.get("sub") or google_info.get("id")
    email = google_info.get("email", "")
    name = google_info.get("name", email.split("@")[0])
    picture = google_info.get("picture", "")

    try:
        user = await user_repo.get_by_google_id(google_id)
        print(f"User by google_id: {user.id if user else 'None'}")

        if not user:
            user = await user_repo.get_by_email(email)
            print(f"User by email: {user.id if user else 'None'}")

        if user:
            print(f"Updating user {user.id}...")
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
            print(f"update_data: {update_data}")
            user = await user_repo.update(user.id, **update_data)
            print(f"Updated user ID: {user.id!r}")

        access_token = auth_service.create_token(user.id, user.role, "access")
        refresh_token = auth_service.create_token(user.id, user.role, "refresh")
        print(f"Tokens generated")
        print("=== SUCCESS ===")

    except Exception as e:
        print(f"\n!!! EXCEPTION CAUGHT !!!")
        print(f"Type: {type(e).__name__}")
        print(f"Args: {e.args}")
        print(f"Repr: {e!r}")
        traceback.print_exc()
        pytest.fail(f"Exception raised: {type(e).__name__}: {e}")


@pytest.mark.asyncio
async def test_repro_google_callback_no_name(client, app, db_session):
    """Test the CREATE path when Google returns no name or picture.

    This simulates edge cases that might trigger type/format issues.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.auth.auth_service import AuthService

    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo)

    # Simulate Google returning MINIMAL data (some providers return no name/picture)
    google_info = {
        "sub": "google-id-minimal",
        "email": "minimal@example.com",
        # No "name", no "picture" keys
    }
    google_id = google_info.get("sub") or google_info.get("id")
    email = google_info.get("email", "")
    name = google_info.get("name", email.split("@")[0])
    picture = google_info.get("picture", "")

    print(f"\n=== REPRO: Creating user with MINIMAL Google data ===")
    print(f"google_id={google_id!r}, email={email!r}, name={name!r}, picture={picture!r}")

    try:
        user = await user_repo.get_by_google_id(google_id)
        if not user:
            user = await user_repo.get_by_email(email)

        if user:
            print("Found existing user (unexpected)")
        else:
            print("Creating user with minimal data...")
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
            print(f"Created user ID: {user.id!r}")

        access_token = auth_service.create_token(user.id, user.role, "access")
        refresh_token = auth_service.create_token(user.id, user.role, "refresh")
        print("=== SUCCESS ===")

    except Exception as e:
        print(f"\n!!! EXCEPTION CAUGHT !!!")
        print(f"Type: {type(e).__name__}")
        print(f"Args: {e.args}")
        print(f"Repr: {e!r}")
        traceback.print_exc()
        pytest.fail(f"Exception raised: {type(e).__name__}: {e}")


@pytest.mark.asyncio
async def test_repro_google_callback_duplicate_ids(app, client, db_session):
    """Test what happens when a duplicate google_id or email is used.

    This might reveal constraint violation paths.
    """
    from app.models.user import User
    from app.repositories.user_repository import UserRepository
    from app.services.auth.auth_service import AuthService

    # Create a user that already has a google_id
    existing = User(
        id="00000000-0000-0000-0000-000000000011",
        name="Existing Google User",
        email="existinggoogle@example.com",
        provider="GOOGLE",
        google_id="google-id-taken",
        role="user",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(existing)
    await db_session.flush()

    print(f"\n=== REPRO: Trying to link another user with already-used google_id ===")
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo)

    try:
        # First user with this google_id - should find existing
        user = await user_repo.get_by_google_id("google-id-taken")
        print(f"User by google_id: {user.id if user else 'None'}")
        assert user is not None, "Should have found the existing user by google_id"
        print("=== SUCCESS - duplicate ID correctly detected ===")

    except Exception as e:
        print(f"\n!!! EXCEPTION CAUGHT !!!")
        print(f"Type: {type(e).__name__}")
        print(f"Args: {e.args}")
        print(f"Repr: {e!r}")
        traceback.print_exc()
        pytest.fail(f"Exception raised: {type(e).__name__}: {e}")


@pytest.mark.asyncio
async def test_repro_google_callback_same_email_new_google(client, app, db_session):
    """Test: existing LOCAL user signs in with a NEW Google account.

    The user has email X but NO google_id. Google returns google_id Y with email X.
    The callback should find the user by email and link the google_id.
    This is the most common real-world scenario.
    """
    from app.models.user import User
    from app.repositories.user_repository import UserRepository
    from app.services.auth.auth_service import AuthService

    # Create a LOCAL user (no google_id) with a specific email
    existing_user = User(
        id="00000000-0000-0000-0000-000000000012",
        name="Local User",
        email="local@example.com",
        provider="LOCAL",
        role="user",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(existing_user)
    await db_session.flush()
    print(f"\n=== REPRO: Linking local user with new Google account ===")

    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo)

    google_info = {
        "sub": "brand-new-google-id",
        "email": "local@example.com",
        "name": "Local User",
        "picture": "https://lh3.googleusercontent.com/photo.jpg",
        "email_verified": True,
    }
    google_id = google_info.get("sub") or google_info.get("id")
    email = google_info.get("email", "")
    name = google_info.get("name", email.split("@")[0])
    picture = google_info.get("picture", "")

    try:
        print(f"Looking up google_id={google_id!r} (should be None)...")
        user = await user_repo.get_by_google_id(google_id)
        print(f"Result: {user.id if user else 'None'}")

        if not user:
            print(f"Looking up by email={email!r} (should find existing)...")
            user = await user_repo.get_by_email(email)
            print(f"Result: {user.id if user else 'None'}")

        if user:
            print(f"Updating user {user.id} with Google info...")
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
            print(f"update_data: {update_data}")
            user = await user_repo.update(user.id, **update_data)
            print(f"Updated successfully. google_id now: {user.google_id!r}")

        access_token = auth_service.create_token(user.id, user.role, "access")
        refresh_token = auth_service.create_token(user.id, user.role, "refresh")
        print("=== SUCCESS - local user linked to Google ===")

    except Exception as e:
        print(f"\n!!! EXCEPTION CAUGHT !!!")
        print(f"Type: {type(e).__name__}")
        print(f"Args: {e.args}")
        print(f"Repr: {e!r}")
        traceback.print_exc()
        pytest.fail(f"Exception raised: {type(e).__name__}: {e}")
