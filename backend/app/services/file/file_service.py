"""File management service for upload, retrieval, deletion, and statistics.

Validates file types and sizes against application settings, performs
magic-byte verification for binary formats, persists files to disk, and
manages metadata records in the database through FileRepository.
"""

import logging
import os
import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.models.file import File
from app.repositories.file_repository import FileRepository

logger = logging.getLogger(__name__)

# Mapping of file extensions to known magic byte signatures.
# Each entry lists one or more byte sequences that must appear at the
# start of the file for it to be considered valid for that extension.
# Text-based formats (csv, txt) are exempted from this check.
FILE_MAGIC_BYTES: dict[str, list[bytes]] = {
    ".pdf": [b"%PDF"],
    ".xlsx": [b"PK\x03\x04"],
}


class FileService:
    """Business logic for file management operations."""

    def __init__(self, db: AsyncSession):
        self.repository = FileRepository(db)

    async def upload_file(self, user_id: str, file: UploadFile) -> File:
        """Validate, persist, and register an uploaded file.

        Steps performed:
            1. Validate the file extension against allowed types.
            2. Read the full content into memory.
            3. Validate file size against the configured maximum.
            4. Validate magic bytes for binary formats (pdf, xlsx).
            5. Write the file to the upload directory with a UUID name.
            6. Create a database record via FileRepository.

        Args:
            user_id: UUID string of the uploading user.
            file: The incoming UploadFile from FastAPI.

        Returns:
            The newly created File record.

        Raises:
            HTTPException 400: For unsupported types, oversized files,
                               or content/format mismatches.
        """
        # --- Extension validation ---
        original_name = file.filename or "unnamed"
        ext = self._get_extension(original_name)
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File type '{ext}' is not supported. "
                    f"Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                ),
            )

        # --- Content and size validation ---
        content = await file.read()
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File exceeds the maximum allowed size of "
                    f"{settings.MAX_UPLOAD_SIZE_MB} MB"
                ),
            )

        self._validate_magic_bytes(content, ext)

        # --- Persist to disk ---
        stored_name = f"{uuid.uuid4()}{ext}"
        storage_path = os.path.join(settings.UPLOAD_DIR, stored_name)
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(content)

        logger.info("File saved to disk: %s (%d bytes)", storage_path, len(content))

        # --- Create DB record ---
        file_type = ext.lstrip(".")
        file_record = await self.repository.create(
            user_id=user_id,
            original_name=original_name,
            stored_name=stored_name,
            file_type=file_type,
            file_size=len(content),
            storage_path=storage_path,
            scan_status="pending",
        )

        logger.info("File uploaded: id=%s user=%s name=%s", file_record.id, user_id, original_name)
        return file_record

    async def get_file(self, file_id: str) -> File:
        """Retrieve a single file record by ID.

        Args:
            file_id: The file's UUID string.

        Returns:
            The File record.

        Raises:
            NotFoundException: If no file with the given ID exists.
        """
        return await self.repository.get_or_raise(file_id)

    async def get_user_files(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[File], int]:
        """Get a paginated list of files belonging to a user.

        Args:
            user_id: The user's UUID string.
            page: The page number (1-based).
            page_size: Number of items per page.

        Returns:
            A tuple of (list of File records, total count).
        """
        skip = (page - 1) * page_size
        return await self.repository.get_by_user_id(user_id, skip=skip, limit=page_size)

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file record and its on-disk artifact.

        Args:
            file_id: The file's UUID string.

        Returns:
            True if the record was deleted.

        Raises:
            NotFoundException: If no file with the given ID exists.
        """
        file_record = await self.repository.get_or_raise(file_id)

        # Remove from disk
        if os.path.exists(file_record.storage_path):
            os.remove(file_record.storage_path)
            logger.info("File deleted from disk: %s", file_record.storage_path)

        # Remove from database
        deleted = await self.repository.delete(file_id)
        logger.info("File record deleted: id=%s", file_id)
        return deleted

    async def get_file_stats(self, user_id: str) -> dict:
        """Get file statistics for a user.

        Args:
            user_id: The user's UUID string.

        Returns:
            A dict with count_by_type (dict) and total_size (int).
        """
        return await self.repository.get_file_stats(user_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_extension(filename: Optional[str]) -> str:
        """Extract the lower-cased file extension from a filename.

        Raises HTTPException 400 if the filename is missing or has no
        extension.
        """
        if not filename or "." not in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is missing or has no extension",
            )
        _, ext = os.path.splitext(filename)
        return ext.lower()

    @staticmethod
    def _validate_magic_bytes(content: bytes, ext: str) -> None:
        """Check that the file content's header matches known signatures.

        Text-based types (csv, txt) are accepted without a signature check.
        Binary types (pdf, xlsx) must match their expected magic bytes.
        """
        expected_signatures = FILE_MAGIC_BYTES.get(ext)
        if expected_signatures is None:
            # No signature check defined for this type (e.g. .csv, .txt) --
            # accept as-is.
            return

        for magic in expected_signatures:
            if content[: len(magic)] == magic:
                return

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File content does not match the expected format for '{ext}' files",
        )
