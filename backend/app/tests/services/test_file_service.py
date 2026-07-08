"""Tests for the FileService class.

Uses mocked database sessions and repositories to verify business-logic
behaviour such as validation, persistence, and error handling without
touching a real database or filesystem.
"""

import io
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app.models.file import File
from app.services.file.file_service import FileService

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Return an AsyncMock that can stand in for an AsyncSession."""
    return AsyncMock()


@pytest.fixture
def file_service(mock_db):
    """Return a FileService wired to the mock database session."""
    return FileService(mock_db)


@pytest.fixture
def sample_file_record():
    """Return a File model instance representing a stored file."""
    return File(
        id="file-001",
        user_id="user-001",
        original_name="report.pdf",
        stored_name="abc123.pdf",
        file_type="pdf",
        file_size=10240,
        storage_path="/tmp/uploads/abc123.pdf",
        scan_status="pending",
    )


def _make_upload_file(filename: str, content: bytes) -> UploadFile:
    """Build a minimal UploadFile for testing without real HTTP request."""
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestUploadFile:
    """Tests for FileService.upload_file()."""

    async def test_upload_file_success(self, file_service, mock_db):
        """Should successfully upload a valid file and create a DB record."""
        content = b"%PDF-1.4 fake pdf content"
        upload_file = _make_upload_file("invoice.pdf", content)

        # Mock repository.create to return a File instance
        fake_record = File(
            id="new-id",
            user_id="user-001",
            original_name="invoice.pdf",
            stored_name="some-uuid.pdf",
            file_type="pdf",
            file_size=len(content),
            storage_path=os.path.join("uploads", "some-uuid.pdf"),
            scan_status="pending",
        )
        file_service.repository.create = AsyncMock(return_value=fake_record)

        # Patch disk operations to verify they are called without actually writing
        with (
            patch("os.makedirs") as mock_makedirs,
            patch("app.services.file.file_service.open", new_callable=MagicMock()),
        ):
            result = await file_service.upload_file(user_id="user-001", file=upload_file)

        assert result.id == "new-id"
        assert result.original_name == "invoice.pdf"
        assert result.file_type == "pdf"
        assert result.file_size == len(content)
        assert result.scan_status == "pending"
        mock_makedirs.assert_any_call("uploads", exist_ok=True)

    async def test_upload_invalid_type(self, file_service, mock_db):
        """Should reject a file whose extension is not in the allowed list."""
        upload_file = _make_upload_file("script.exe", b"some content")

        with pytest.raises(HTTPException) as exc:
            await file_service.upload_file(user_id="user-001", file=upload_file)

        assert exc.value.status_code == 400
        assert "not supported" in exc.value.detail.lower()

    async def test_upload_oversized_file(self, file_service, mock_db):
        """Should reject a file that exceeds the maximum upload size."""
        # Generate content larger than the default 50 MB limit
        oversized = b"x" * (51 * 1024 * 1024)
        upload_file = _make_upload_file("large.csv", oversized)

        with pytest.raises(HTTPException) as exc:
            await file_service.upload_file(user_id="user-001", file=upload_file)

        assert exc.value.status_code == 400
        assert "exceeds" in exc.value.detail.lower()

    async def test_upload_wrong_magic_bytes(self, file_service, mock_db):
        """Should reject a file whose content header doesn't match its extension."""
        # .pdf magic is b"%PDF" but we send plain text
        content = b"This is not a PDF file"
        upload_file = _make_upload_file("fake.pdf", content)

        with pytest.raises(HTTPException) as exc:
            await file_service.upload_file(user_id="user-001", file=upload_file)

        assert exc.value.status_code == 400
        assert "does not match" in exc.value.detail.lower()

    async def test_upload_empty_filename(self, file_service, mock_db):
        """Should reject a file with no filename."""
        upload_file = _make_upload_file("", b"content")

        with pytest.raises(HTTPException) as exc:
            await file_service.upload_file(user_id="user-001", file=upload_file)

        assert exc.value.status_code == 400
        assert "missing" in exc.value.detail.lower()

    async def test_upload_no_extension(self, file_service, mock_db):
        """Should reject a file with a name but no extension."""
        upload_file = _make_upload_file("README", b"content")

        with pytest.raises(HTTPException) as exc:
            await file_service.upload_file(user_id="user-001", file=upload_file)

        assert exc.value.status_code == 400
        assert "no extension" in exc.value.detail.lower()


class TestGetFile:
    """Tests for FileService.get_file()."""

    async def test_get_file_success(self, file_service, mock_db, sample_file_record):
        """Should return the file record when it exists."""
        file_service.repository.get_or_raise = AsyncMock(return_value=sample_file_record)

        result = await file_service.get_file("file-001")

        assert result.id == "file-001"
        assert result.original_name == "report.pdf"

    async def test_file_not_found(self, file_service, mock_db):
        """Should propagate NotFoundException when the file does not exist."""
        from app.utils.exceptions import NotFoundException

        file_service.repository.get_or_raise = AsyncMock(side_effect=NotFoundException("File", "missing-id"))

        with pytest.raises(NotFoundException) as exc:
            await file_service.get_file("missing-id")

        assert "missing-id" in exc.value.detail


class TestGetUserFiles:
    """Tests for FileService.get_user_files()."""

    async def test_get_user_files_with_data(self, file_service, mock_db):
        """Should return a paginated list of files for the user."""
        files = [
            File(id="f1", user_id="user-001", original_name="a.pdf", file_type="pdf", file_size=100),
            File(id="f2", user_id="user-001", original_name="b.csv", file_type="csv", file_size=200),
        ]
        file_service.repository.get_by_user_id = AsyncMock(return_value=(files, 2))

        result_files, total = await file_service.get_user_files(user_id="user-001", page=1, page_size=20)

        assert total == 2
        assert len(result_files) == 2
        assert result_files[0].id == "f1"
        file_service.repository.get_by_user_id.assert_called_once_with(
            "user-001", skip=0, limit=20
        )

    async def test_get_user_files_empty(self, file_service, mock_db):
        """Should return an empty list when the user has no files."""
        file_service.repository.get_by_user_id = AsyncMock(return_value=([], 0))

        result_files, total = await file_service.get_user_files(user_id="user-001", page=1, page_size=20)

        assert total == 0
        assert result_files == []

    async def test_get_user_files_pagination(self, file_service, mock_db):
        """Should compute correct skip/limit values for pagination."""
        file_service.repository.get_by_user_id = AsyncMock(return_value=([], 0))

        await file_service.get_user_files(user_id="user-001", page=3, page_size=10)

        file_service.repository.get_by_user_id.assert_called_once_with(
            "user-001", skip=20, limit=10
        )


class TestDeleteFile:
    """Tests for FileService.delete_file()."""

    async def test_delete_file(self, file_service, mock_db, sample_file_record):
        """Should delete the file from disk and the database."""
        file_service.repository.get_or_raise = AsyncMock(return_value=sample_file_record)
        file_service.repository.delete = AsyncMock(return_value=True)

        with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:
            result = await file_service.delete_file("file-001")

        assert result is True
        mock_remove.assert_called_once_with("/tmp/uploads/abc123.pdf")
        file_service.repository.delete.assert_called_once_with("file-001")

    async def test_delete_file_not_on_disk(self, file_service, mock_db, sample_file_record):
        """Should still succeed when the file record exists but the disk copy is gone."""
        file_service.repository.get_or_raise = AsyncMock(return_value=sample_file_record)
        file_service.repository.delete = AsyncMock(return_value=True)

        with patch("os.path.exists", return_value=False), patch("os.remove") as mock_remove:
            result = await file_service.delete_file("file-001")

        assert result is True
        mock_remove.assert_not_called()

    async def test_delete_file_not_found(self, file_service, mock_db):
        """Should raise when the file record does not exist."""
        from app.utils.exceptions import NotFoundException

        file_service.repository.get_or_raise = AsyncMock(side_effect=NotFoundException("File", "missing"))

        with pytest.raises(NotFoundException):
            await file_service.delete_file("missing")


class TestGetFileStats:
    """Tests for FileService.get_file_stats()."""

    async def test_get_file_stats(self, file_service, mock_db):
        """Should return file statistics aggregated by the repository."""
        expected_stats = {
            "count_by_type": {"pdf": 3, "csv": 5},
            "total_size": 1048576,
        }
        file_service.repository.get_file_stats = AsyncMock(return_value=expected_stats)

        stats = await file_service.get_file_stats(user_id="user-001")

        assert stats["count_by_type"]["pdf"] == 3
        assert stats["total_size"] == 1048576
        file_service.repository.get_file_stats.assert_called_once_with("user-001")

    async def test_get_file_stats_empty(self, file_service, mock_db):
        """Should return zero counts when the user has no files."""
        empty_stats = {"count_by_type": {}, "total_size": 0}
        file_service.repository.get_file_stats = AsyncMock(return_value=empty_stats)

        stats = await file_service.get_file_stats(user_id="user-002")

        assert stats["count_by_type"] == {}
        assert stats["total_size"] == 0
