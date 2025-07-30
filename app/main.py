"""
Light Novel Bookmarks API - Main FastAPI application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.exceptions import LightNovelBookmarksException
from app.db.session import create_tables
from app.api.novels import router as novels_router
from app.api.scraper import router as scraper_router
from app.api.demo import router as demo_router

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Light Novel Bookmarks API")
    logger.info(f"Environment: {settings.app.environment}")
    logger.info(f"Version: {settings.app.version}")
    create_tables()
    logger.info("Database tables created/verified")

    yield

    # Shutdown
    logger.info("Shutting down Light Novel Bookmarks API")


# Create FastAPI application with enhanced configuration
app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    debug=settings.app.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.app.environment != "production" else None,
    redoc_url="/redoc" if settings.app.environment != "production" else None,
    openapi_tags=[
        {
            "name": "novels",
            "description": "Operations for managing light novels and chapters. Create, read, update, and delete novels and their associated chapters.",
        },
        {
            "name": "scraper",
            "description": "Web scraping operations for importing novels from NovelUpdates. Includes preview, import, and background processing capabilities.",
        },
        {
            "name": "demo",
            "description": "Demo data creation and testing endpoints. Used for development and testing purposes.",
        },
        {"name": "system", "description": "System health and information endpoints."},
    ],
    contact={
        "name": "Light Novel Bookmarks API",
        "url": "https://github.com/your-repo/lightnovel-bookmarks-backend",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins,
    allow_credentials=settings.cors.credentials,
    allow_methods=settings.cors.methods,
    allow_headers=settings.cors.headers,
)


# Global exception handler for custom exceptions
@app.exception_handler(LightNovelBookmarksException)
async def custom_exception_handler(request: Request, exc: LightNovelBookmarksException):
    """Handle custom application exceptions"""
    logger.error(f"Application error: {exc.message}", extra={"details": exc.details})

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": exc.error_code or "INTERNAL_ERROR",
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


# Include API routers
app.include_router(novels_router, prefix="/api", tags=["novels"])
app.include_router(scraper_router, prefix="/api", tags=["scraper"])
app.include_router(demo_router, prefix="/api", tags=["demo"])


@app.get("/", tags=["system"])
def read_root():
    """
    Root endpoint

    Returns basic API information and health status.

    Returns:
        dict: API information including name, version, and status
    """
    return {
        "name": settings.app.title,
        "version": settings.app.version,
        "status": "operational",
        "environment": settings.app.environment,
        "docs_url": "/docs" if settings.app.environment != "production" else "disabled",
        "description": settings.app.description,
    }


@app.get("/health", tags=["system"])
def health_check():
    """
    Health check endpoint

    Returns the current health status of the API. This endpoint can be used
    by monitoring systems and load balancers to verify the service is running.

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "version": settings.app.version,
        "environment": settings.app.environment,
        "timestamp": "2024-01-01T00:00:00Z",  # In production, use actual timestamp
    }


@app.get("/api", tags=["system"])
def api_info():
    """
    API information endpoint

    Provides detailed information about the API capabilities and available endpoints.

    Returns:
        dict: Comprehensive API information and feature overview
    """
    return {
        "name": settings.app.title,
        "version": settings.app.version,
        "description": settings.app.description,
        "features": {
            "novel_management": "Create, read, update, and delete light novels with metadata",
            "chapter_management": "Manage individual chapters with decimal numbering support",
            "web_scraping": "Import novels from NovelUpdates with automatic metadata extraction",
            "background_processing": "Asynchronous import for large novels with many chapters",
            "search_and_filter": "Query novels by various criteria",
            "demo_data": "Pre-built demo novels for testing and development",
        },
        "data_sources": [
            "NovelUpdates.com - Primary source for novel metadata and chapter information"
        ],
        "supported_formats": {
            "chapter_numbering": "Integer and decimal chapters (e.g., 1, 1.5, 2.1)",
            "genres": "Multiple genre tags per novel",
            "status_tracking": "Novel publication status (ongoing, completed, hiatus, etc.)",
            "content_types": "Chapters, volumes, or mixed content organization",
        },
        "api_documentation": {
            "openapi_spec": "/openapi.json",
            "interactive_docs": "/docs",
            "redoc_docs": "/redoc",
        },
    }
