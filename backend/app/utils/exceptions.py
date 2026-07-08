"""Application exception classes and error handling."""

from typing import Any, Optional

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with error details."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        errors: Optional[dict[str, list[str]]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.errors = errors


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, resource: str = "Resource", resource_id: str = ""):
        detail = f"{resource} not found" + (f": {resource_id}" if resource_id else "")
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
        )


class DuplicateException(AppException):
    """Duplicate resource exception."""

    def __init__(self, resource: str = "Resource", value: str = ""):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} already exists: {value}",
            error_code="DUPLICATE",
        )


class UnauthorizedException(AppException):
    """Authentication/authorization exception."""

    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(AppException):
    """Permission denied exception."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
        )


class ValidationException(AppException):
    """Input validation exception."""

    def __init__(self, errors: dict[str, list[str]]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation failed",
            error_code="VALIDATION_ERROR",
            errors=errors,
        )


class ServiceUnavailableException(AppException):
    """External service unavailable exception."""

    def __init__(self, service: str = "Service"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} is temporarily unavailable",
            error_code="SERVICE_UNAVAILABLE",
        )
