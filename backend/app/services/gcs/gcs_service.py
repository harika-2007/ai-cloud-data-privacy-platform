"""Google Cloud Storage Service.

Handles file upload to GCS, signed URL generation, and file management.
Gracefully degrades when GCS is not configured.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class GCSService:
    """Service for Google Cloud Storage operations."""

    def __init__(self):
        self.bucket_name = settings.GCS_BUCKET_NAME
        self.enabled = bool(settings.GOOGLE_CLOUD_PROJECT and settings.GCS_BUCKET_NAME)
        self._client = None
        self._bucket = None

    @property
    def client(self):
        """Lazy-init GCS client."""
        if self._client is None and self.enabled:
            try:
                from google.cloud import storage
                self._client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {e}")
                self.enabled = False
        return self._client

    @property
    def bucket(self):
        """Lazy-init GCS bucket."""
        if self._bucket is None and self.client:
            try:
                self._bucket = self.client.bucket(self.bucket_name)
            except Exception as e:
                logger.error(f"Failed to get GCS bucket: {e}")
                self.enabled = False
        return self._bucket

    async def upload_file(self, local_path: str, destination_blob_name: str) -> Optional[str]:
        """Upload a file to GCS. Returns the GCS path or None."""
        if not self.enabled:
            logger.info(f"GCS not configured. File stored locally: {local_path}")
            return None

        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(local_path)
            gcs_path = f"gs://{self.bucket_name}/{destination_blob_name}"
            logger.info(f"Uploaded to GCS: {gcs_path}")
            return gcs_path
        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
            return None

    async def generate_signed_url(
        self, blob_name: str, expiration_hours: int = 1
    ) -> Optional[str]:
        """Generate a signed URL for temporary file access."""
        if not self.enabled:
            return None

        try:
            blob = self.bucket.blob(blob_name)
            url = blob.generate_signed_url(
                expiration=timedelta(hours=expiration_hours),
                method="GET",
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return None

    async def delete_file(self, blob_name: str) -> bool:
        """Delete a file from GCS."""
        if not self.enabled:
            return False

        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Deleted from GCS: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"GCS delete failed: {e}")
            return False

    async def list_files(self, prefix: str = "") -> list[str]:
        """List files in GCS bucket with given prefix."""
        if not self.enabled:
            return []

        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"GCS list failed: {e}")
            return []
