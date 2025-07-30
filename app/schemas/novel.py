"""
Pydantic schemas for Light Novel API data validation and serialization
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, List
from enum import Enum


class NovelStatus(str, Enum):
    """Valid status values for novels"""

    ONGOING = "ongoing"
    COMPLETED = "completed"
    HIATUS = "hiatus"
    DROPPED = "dropped"
    UNKNOWN = "unknown"


class ContentType(str, Enum):
    """Valid content type values for novels"""

    CHAPTERS = "chapters"
    VOLUMES = "volumes"
    UNKNOWN = "unknown"


# Base schemas
class ChapterBase(BaseModel):
    """Base schema for chapter data"""

    number: Union[int, float] = Field(
        ...,
        ge=0,
        description="Chapter number (supports decimal values like 1.5)",
        examples=[1, 1.5, 2.1],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Chapter title",
        examples=["Prologue", "Chapter 1: The Beginning", "Chapter 1.5: Side Story"],
    )
    source_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="URL to the original chapter source",
        examples=["https://example-translator.com/novel/chapter-1"],
    )

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v):
        if v is not None and v.strip() == "":
            return None
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("Source URL must start with http:// or https://")
        return v


class ChapterCreate(ChapterBase):
    """Schema for creating a new chapter"""

    pass


class ChapterUpdate(BaseModel):
    """Schema for updating an existing chapter"""

    number: Optional[Union[int, float]] = Field(
        default=None,
        ge=0,
        description="Chapter number (supports decimal values like 1.5)",
    )
    title: Optional[str] = Field(
        default=None, min_length=1, max_length=500, description="Chapter title"
    )
    source_url: Optional[str] = Field(
        default=None, max_length=2000, description="URL to the original chapter source"
    )

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v):
        if v is not None and v.strip() == "":
            return None
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("Source URL must start with http:// or https://")
        return v


class Chapter(ChapterBase):
    """Complete chapter schema with database fields"""

    id: int = Field(..., description="Unique chapter identifier")
    novel_id: int = Field(..., description="ID of the novel this chapter belongs to")

    model_config = {"from_attributes": True}


class LightNovelBase(BaseModel):
    """Base schema for light novel data"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Novel title",
        examples=["That Time I Got Reincarnated as a Slime", "Overlord"],
    )
    author: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Novel author (multiple authors separated by ' & ')",
        examples=["Fuse", "Kugane Maruyama", "Fuse & 伏瀬"],
    )
    cover_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="URL to the novel cover image",
        examples=["https://www.novelupdates.com/img/cover.jpg"],
    )
    description: Optional[str] = Field(
        default=None, max_length=5000, description="Novel description or synopsis"
    )
    status: NovelStatus = Field(
        default=NovelStatus.ONGOING,
        description="Current publication status of the novel",
    )
    genres: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="List of genre tags",
        examples=[
            ["Fantasy", "Adventure", "Comedy"],
            ["Action", "Drama", "Supernatural"],
        ],
    )
    source_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="URL to the original novel source (e.g., NovelUpdates page)",
        examples=[
            "https://www.novelupdates.com/series/tensei-shitara-slime-datta-ken/"
        ],
    )

    # Chapter/volume tracking and raw status fields
    total_chapters: Optional[int] = Field(
        default=0, ge=0, description="Total number of chapters (extracted from source)"
    )
    total_volumes: Optional[int] = Field(
        default=0, ge=0, description="Total number of volumes (if applicable)"
    )
    content_type: ContentType = Field(
        default=ContentType.UNKNOWN, description="Type of content organization"
    )
    raw_status: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Raw status text from the source (e.g., '355 Chapters (Completed)')",
    )

    @field_validator("genres")
    @classmethod
    def validate_genres(cls, v):
        if v is None:
            return []
        # Remove empty strings and limit genre name length
        valid_genres = []
        for genre in v:
            if isinstance(genre, str) and genre.strip():
                if len(genre.strip()) > 50:
                    raise ValueError("Genre names must be 50 characters or less")
                valid_genres.append(genre.strip())
        return valid_genres

    @field_validator("cover_url", "source_url")
    @classmethod
    def validate_urls(cls, v):
        if v is not None and v.strip() == "":
            return None
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URLs must start with http:// or https://")
        return v


class LightNovelCreate(LightNovelBase):
    """Schema for creating a new light novel"""

    pass


class LightNovelUpdate(BaseModel):
    """Schema for updating an existing light novel"""

    title: Optional[str] = Field(
        default=None, min_length=1, max_length=500, description="Novel title"
    )
    author: Optional[str] = Field(
        default=None, min_length=1, max_length=200, description="Novel author"
    )
    cover_url: Optional[str] = Field(
        default=None, max_length=2000, description="URL to the novel cover image"
    )
    description: Optional[str] = Field(
        default=None, max_length=5000, description="Novel description or synopsis"
    )
    status: Optional[NovelStatus] = Field(
        default=None, description="Current publication status of the novel"
    )
    genres: Optional[List[str]] = Field(
        default=None, max_length=20, description="List of genre tags"
    )
    source_url: Optional[str] = Field(
        default=None, max_length=2000, description="URL to the original novel source"
    )

    # Chapter/volume tracking and raw status fields
    total_chapters: Optional[int] = Field(
        default=None, ge=0, description="Total number of chapters"
    )
    total_volumes: Optional[int] = Field(
        default=None, ge=0, description="Total number of volumes"
    )
    content_type: Optional[ContentType] = Field(
        default=None, description="Type of content organization"
    )
    raw_status: Optional[str] = Field(
        default=None, max_length=1000, description="Raw status text from the source"
    )

    @field_validator("genres")
    @classmethod
    def validate_genres(cls, v):
        if v is None:
            return None
        # Remove empty strings and limit genre name length
        valid_genres = []
        for genre in v:
            if isinstance(genre, str) and genre.strip():
                if len(genre.strip()) > 50:
                    raise ValueError("Genre names must be 50 characters or less")
                valid_genres.append(genre.strip())
        return valid_genres

    @field_validator("cover_url", "source_url")
    @classmethod
    def validate_urls(cls, v):
        if v is not None and v.strip() == "":
            return None
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URLs must start with http:// or https://")
        return v


class LightNovel(LightNovelBase):
    """Complete light novel schema with database fields"""

    id: int = Field(..., description="Unique novel identifier")
    chapters: List[Chapter] = Field(
        default_factory=list,
        description="List of chapters (may be empty for performance reasons)",
    )

    model_config = {"from_attributes": True}


# Scraper-specific schemas
class ScrapeRequest(BaseModel):
    """Schema for scraping requests"""

    url: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="NovelUpdates URL to scrape",
        examples=[
            "https://www.novelupdates.com/series/tensei-shitara-slime-datta-ken/"
        ],
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        if "novelupdates.com" not in v.lower():
            raise ValueError("Only NovelUpdates URLs are supported")
        return v


class PreviewResponse(BaseModel):
    """Schema for novel preview responses"""

    title: str = Field(..., description="Novel title")
    author: str = Field(..., description="Novel author(s)")
    description: str = Field(..., description="Novel description (may be truncated)")
    status: str = Field(..., description="Publication status")
    genres: List[str] = Field(..., description="List of genre tags")
    total_chapters: int = Field(
        default=0, description="Total chapter count from source"
    )
    total_volumes: int = Field(default=0, description="Total volume count from source")
    content_type: str = Field(
        default="unknown", description="Content organization type"
    )
    raw_status: Optional[str] = Field(
        default=None, description="Raw status text from source"
    )
    cover_url: Optional[str] = Field(default=None, description="Cover image URL")
    source_url: str = Field(..., description="Source URL")
    rating: str = Field(default="Not available", description="Novel rating from source")
    translation_status: str = Field(default="Unknown", description="Translation status")


class ErrorResponse(BaseModel):
    """Schema for error responses"""

    error: dict = Field(
        ...,
        description="Error information",
        examples=[
            {
                "code": "NOVEL_NOT_FOUND",
                "message": "Novel with ID 123 not found",
                "details": {"novel_id": 123},
            }
        ],
    )
