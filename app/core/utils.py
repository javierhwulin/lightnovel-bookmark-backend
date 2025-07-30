"""
Utility functions for the Light Novel Bookmarks API
"""
import json
from typing import List
from app.models.novel import LightNovel as LightNovelModel
from app.schemas.novel import LightNovel as LightNovelSchema


def serialize_genres(genres: List[str]) -> str:
    """
    Serialize genres list to JSON string for database storage
    
    Args:
        genres: List of genre strings
        
    Returns:
        JSON string representation of genres
    """
    return json.dumps(genres) if genres else "[]"


def deserialize_genres(genres_json: str) -> List[str]:
    """
    Deserialize genres JSON string to list
    
    Args:
        genres_json: JSON string representation of genres
        
    Returns:
        List of genre strings
    """
    try:
        return json.loads(genres_json) if genres_json else []
    except json.JSONDecodeError:
        return []


def convert_novel_model_to_schema(db_novel: LightNovelModel) -> LightNovelSchema:
    """
    Convert SQLAlchemy novel model to Pydantic schema with deserialized genres
    
    Args:
        db_novel: SQLAlchemy LightNovel model instance
        
    Returns:
        Pydantic LightNovel schema instance
    """
    genres = deserialize_genres(db_novel.genres)
    
    return LightNovelSchema(
        id=db_novel.id,
        title=db_novel.title,
        author=db_novel.author,
        cover_url=db_novel.cover_url,
        description=db_novel.description,
        status=db_novel.status,
        genres=genres,
        source_url=db_novel.source_url,
        total_chapters=db_novel.total_chapters or 0,
        total_volumes=db_novel.total_volumes or 0,
        content_type=db_novel.content_type or 'unknown',
        raw_status=db_novel.raw_status,
        chapters=[]  # Will be populated if needed
    )


def validate_url(url: str) -> bool:
    """
    Validate if a URL is a valid NovelUpdates URL
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    return url.startswith('http') and 'novelupdates.com' in url.lower()


def format_error_response(error_code: str, message: str, details: dict = None) -> dict:
    """
    Format a consistent error response structure
    
    Args:
        error_code: Error code identifier
        message: Human-readable error message
        details: Optional additional error details
        
    Returns:
        Formatted error response dictionary
    """
    response = {
        "error": {
            "code": error_code,
            "message": message
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return response 