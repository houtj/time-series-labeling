"""
Hill Sequence Backend V2 - Main Application Entry Point

This is a refactored version of the Hill Sequence backend with:
- Clean layered architecture (routes -> services -> repositories)
- Proper dependency injection
- Configuration management
- Comprehensive error handling
- Type safety throughout
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import (
    download,
    files,
    folders,
    labels,
    projects,
    templates,
    users,
    websockets,
)
from app.core.config import get_settings
from app.core.database import db_manager
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.logging import setup_logging

# Get settings
settings = get_settings()

# Setup logging
setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown"""
    # Startup
    logger.info("Starting Hill Sequence Backend V2...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Connect to database
    await db_manager.connect_async()
    db_manager.connect_sync()

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await db_manager.disconnect_async()
    db_manager.disconnect_sync()
    logger.info("Application shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="Hill Sequence Backend V2",
    description="Time series data labeling and analysis platform",
    version="2.0.0",
    lifespan=lifespan,
    debug=settings.debug,
)


# ============================================================================
# Middleware Configuration
# ============================================================================


class LargeFileMiddleware(BaseHTTPMiddleware):
    """Middleware to handle large file uploads"""

    async def dispatch(self, request: Request, call_next):
        request.scope["max_content_size"] = settings.max_upload_size_bytes
        response = await call_next(request)
        return response


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add large file middleware
app.add_middleware(LargeFileMiddleware)


# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions"""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions"""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    """Handle unauthorized exceptions"""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    """Handle forbidden exceptions"""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    """Handle conflict exceptions"""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(InternalServerException)
async def internal_server_exception_handler(request: Request, exc: InternalServerException):
    """Handle internal server exceptions"""
    logger.error(f"Internal server error: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred. Please try again later."},
    )


# ============================================================================
# Route Registration
# ============================================================================

# Root endpoint
@app.get("/", tags=["health"])
async def root():
    """Health check endpoint"""
    return {"hello": "world", "version": "2.0.0", "status": "healthy"}


# Include all routers
app.include_router(projects.router)
app.include_router(templates.router)
app.include_router(folders.router)
app.include_router(files.router)
app.include_router(labels.router)
app.include_router(users.router)
app.include_router(download.router)
app.include_router(websockets.router)


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )

