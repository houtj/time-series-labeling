"""Custom exceptions for the application"""

from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """Raised when a resource is not found"""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' not found",
        )


class ValidationException(HTTPException):
    """Raised when validation fails"""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


class UnauthorizedException(HTTPException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )


class ForbiddenException(HTTPException):
    """Raised when access is forbidden"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        )


class ConflictException(HTTPException):
    """Raised when there's a conflict (e.g., duplicate resource)"""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )


class InternalServerException(HTTPException):
    """Raised for internal server errors"""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        )

