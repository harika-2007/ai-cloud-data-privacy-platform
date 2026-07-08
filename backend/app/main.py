"""Application entry point."""
import logging
from app.core.config.settings import settings
from app.utils.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

from server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
