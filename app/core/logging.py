"""
Logging configuration for the Light Novel Bookmarks API
"""
import logging
import sys
from typing import Dict, Any
from app.core.config import settings


def configure_logging() -> None:
    """
    Configure application logging based on environment settings
    """
    # Configure root logger
    log_level = logging.DEBUG if settings.app.debug else logging.INFO
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if settings.app.debug:
        console_handler.setFormatter(detailed_formatter)
    else:
        console_handler.setFormatter(simple_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_app_loggers()
    configure_third_party_loggers()


def configure_app_loggers() -> None:
    """Configure application-specific loggers"""
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if settings.app.debug else logging.INFO)
    
    # Service loggers
    service_logger = logging.getLogger("app.services")
    service_logger.setLevel(logging.INFO)
    
    # API loggers
    api_logger = logging.getLogger("app.api")
    api_logger.setLevel(logging.INFO)
    
    # Scraper logger
    scraper_logger = logging.getLogger("app.services.scraper")
    scraper_logger.setLevel(logging.INFO)


def configure_third_party_loggers() -> None:
    """Configure third-party library loggers"""
    # SQLAlchemy
    if settings.database.echo:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # FastAPI/Uvicorn
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # HTTP libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    # Cloudscraper
    logging.getLogger("cloudscraper").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Convenience loggers for common use cases
app_logger = get_logger("app")
api_logger = get_logger("app.api")
service_logger = get_logger("app.services")
scraper_logger = get_logger("app.services.scraper") 