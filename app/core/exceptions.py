"""
Custom exception classes for the Light Novel Bookmarks API
"""
from typing import Optional, Dict, Any


class LightNovelBookmarksException(Exception):
    """Base exception class for Light Novel Bookmarks API"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NovelNotFoundError(LightNovelBookmarksException):
    """Raised when a novel is not found"""
    
    def __init__(self, novel_id: int):
        super().__init__(
            message=f"Novel with ID {novel_id} not found",
            error_code="NOVEL_NOT_FOUND",
            details={"novel_id": novel_id}
        )


class ChapterNotFoundError(LightNovelBookmarksException):
    """Raised when a chapter is not found"""
    
    def __init__(self, chapter_id: int, novel_id: Optional[int] = None):
        message = f"Chapter with ID {chapter_id} not found"
        if novel_id:
            message += f" for novel {novel_id}"
        
        super().__init__(
            message=message,
            error_code="CHAPTER_NOT_FOUND",
            details={"chapter_id": chapter_id, "novel_id": novel_id}
        )


class DuplicateNovelError(LightNovelBookmarksException):
    """Raised when attempting to create a duplicate novel"""
    
    def __init__(self, title: str, author: str):
        super().__init__(
            message=f"Novel '{title}' by {author} already exists",
            error_code="DUPLICATE_NOVEL",
            details={"title": title, "author": author}
        )


class DuplicateChapterError(LightNovelBookmarksException):
    """Raised when attempting to create a duplicate chapter"""
    
    def __init__(self, chapter_number: float, novel_id: int):
        super().__init__(
            message=f"Chapter {chapter_number} already exists for novel {novel_id}",
            error_code="DUPLICATE_CHAPTER",
            details={"chapter_number": chapter_number, "novel_id": novel_id}
        )


class ScrapingError(LightNovelBookmarksException):
    """Raised when web scraping fails"""
    
    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"Failed to scrape from {url}: {reason}",
            error_code="SCRAPING_FAILED",
            details={"url": url, "reason": reason}
        )


class InvalidUrlError(LightNovelBookmarksException):
    """Raised when an invalid URL is provided"""
    
    def __init__(self, url: str):
        super().__init__(
            message=f"Invalid URL provided: {url}",
            error_code="INVALID_URL",
            details={"url": url}
        )


class DatabaseError(LightNovelBookmarksException):
    """Raised when database operations fail"""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Database operation '{operation}' failed: {reason}",
            error_code="DATABASE_ERROR",
            details={"operation": operation, "reason": reason}
        )


class ValidationError(LightNovelBookmarksException):
    """Raised when input validation fails"""
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            message=f"Validation failed for field '{field}': {reason}",
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": value, "reason": reason}
        ) 