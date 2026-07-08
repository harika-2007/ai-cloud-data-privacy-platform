"""Integration tests for the health check API endpoint.

Tests verify the health endpoint returns correct status information
about the application and its dependencies.
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestHealthCheck:
    """Tests for GET /api/v1/health."""

    async def test_health_check(self, client: AsyncClient):
        """Test that the health endpoint returns a 200 status."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_health_check_response_format(self, client: AsyncClient):
        """Test that the health response has the correct structure and fields."""
        response = await client.get("/api/v1/health")
        data = response.json()

        # Verify top-level fields exist
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "database" in data
        assert "ai" in data
        assert "dlp" in data
        assert "gcs" in data

        # Verify status is one of the expected values
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

        # Verify version is a string
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

        # Verify environment is a string
        assert isinstance(data["environment"], str)

    async def test_health_check_database_status(self, client: AsyncClient):
        """Test that the database status field is present in the response."""
        response = await client.get("/api/v1/health")
        data = response.json()
        assert data["database"] in ["healthy", "unhealthy", "degraded"]

    async def test_health_check_no_auth_required(self, client: AsyncClient):
        """Test that the health endpoint is publicly accessible without auth."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_health_check_ai_service_status(self, client: AsyncClient):
        """Test that the AI service status field is properly structured."""
        response = await client.get("/api/v1/health")
        data = response.json()

        assert "ai" in data
        ai = data["ai"]
        assert "status" in ai
        assert ai["status"] in ["configured", "disabled"]

    async def test_health_check_dlp_service_status(self, client: AsyncClient):
        """Test that the DLP service status field is properly structured."""
        response = await client.get("/api/v1/health")
        data = response.json()

        assert "dlp" in data
        dlp = data["dlp"]
        assert "status" in dlp
        assert "enabled" in dlp
        assert isinstance(dlp["enabled"], bool)

    async def test_health_check_gcs_service_status(self, client: AsyncClient):
        """Test that the GCS service status field is properly structured."""
        response = await client.get("/api/v1/health")
        data = response.json()

        assert "gcs" in data
        gcs = data["gcs"]
        assert "status" in gcs
        assert "enabled" in gcs
        assert isinstance(gcs["enabled"], bool)

    async def test_health_check_version_matches_settings(self, client: AsyncClient):
        """Test that the version field in health matches the app version."""
        from app.core.config.settings import settings

        response = await client.get("/api/v1/health")
        data = response.json()
        assert data["version"] == settings.APP_VERSION
