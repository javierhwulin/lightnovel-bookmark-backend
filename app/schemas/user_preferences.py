"""
Pydantic schemas for User Preferences API data validation and serialization
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, List
from datetime import datetime, date
from enum import Enum


class UserStatus(str, Enum):
    """Valid user status values for reading progress"""
    READING = "reading"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    DROPPED = "dropped"
    PLAN_TO_READ = "plan_to_read"


class DeviceType(str, Enum):
    """Valid device types for reading sessions"""
    WEB = "web"
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"


# User Preferences Schemas
class UserPreferencesBase(BaseModel):
    """Base schema for user preferences"""
    user_status: Optional[UserStatus] = Field(
        default=None,
        description="Current reading status for this novel",
        examples=["reading", "completed", "on_hold"]
    )
    is_favorite: bool = Field(
        default=False,
        description="Whether this novel is marked as favorite"
    )
    current_chapter: Optional[Union[int, float]] = Field(
        default=None,
        ge=0,
        description="Current chapter being read (supports decimal values)",
        examples=[1, 1.5, 2.1]
    )
    rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="User rating for the novel (1-5 stars)",
        examples=[4, 5]
    )
    personal_notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Personal notes about the novel",
        examples=["Great story, love the character development"]
    )
    date_started: Optional[date] = Field(
        default=None,
        description="Date when user started reading this novel"
    )
    date_completed: Optional[date] = Field(
        default=None,
        description="Date when user completed this novel"
    )

    @field_validator("personal_notes")
    @classmethod
    def validate_personal_notes(cls, v):
        if v is not None and v.strip() == "":
            return None
        return v


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences"""
    pass


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences (partial updates allowed)"""
    user_status: Optional[UserStatus] = None
    is_favorite: Optional[bool] = None
    current_chapter: Optional[Union[int, float]] = Field(default=None, ge=0)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    personal_notes: Optional[str] = Field(default=None, max_length=2000)
    date_started: Optional[date] = None
    date_completed: Optional[date] = None

    @field_validator("personal_notes")
    @classmethod
    def validate_personal_notes(cls, v):
        if v is not None and v.strip() == "":
            return None
        return v


class UserPreferences(UserPreferencesBase):
    """Schema for returning user preferences (includes DB fields)"""
    id: int
    novel_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Status Update Schemas
class StatusUpdate(BaseModel):
    """Schema for updating only the user status"""
    user_status: UserStatus = Field(
        ...,
        description="New reading status for the novel"
    )


class ProgressUpdate(BaseModel):
    """Schema for updating reading progress"""
    current_chapter: Union[int, float] = Field(
        ...,
        ge=0,
        description="Current chapter number (supports decimal values)"
    )
    user_status: Optional[UserStatus] = Field(
        default=None,
        description="Optional status update along with progress"
    )


# Reading Session Schemas
class ReadingSessionBase(BaseModel):
    """Base schema for reading sessions"""
    chapter_number: Union[int, float] = Field(
        ...,
        ge=0,
        description="Chapter number being read (supports decimal values)"
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Reading session duration in minutes"
    )
    device_type: Optional[DeviceType] = Field(
        default=DeviceType.WEB,
        description="Device used for reading"
    )


class ReadingSessionCreate(ReadingSessionBase):
    """Schema for creating a reading session"""
    pass


class ReadingSessionEnd(BaseModel):
    """Schema for ending a reading session"""
    duration_minutes: int = Field(
        ...,
        ge=0,
        description="Total reading session duration in minutes"
    )


class ReadingSession(ReadingSessionBase):
    """Schema for returning reading sessions (includes DB fields)"""
    id: int
    novel_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Response Schemas
class UserPreferencesResponse(BaseModel):
    """Response schema that includes novel information with user preferences"""
    novel_id: int
    novel_title: str
    preferences: Optional[UserPreferences] = None


class ReadingStatsResponse(BaseModel):
    """Response schema for reading statistics"""
    total_reading_time_minutes: int
    average_session_minutes: float
    total_sessions: int
    current_streak_days: int
    chapters_read_today: int
    favorite_reading_time: Optional[str] = None  # e.g., "morning", "evening"


# Error Response Schema
class ErrorResponse(BaseModel):
    """Error response schema"""
    error: dict = Field(
        ...,
        description="Error details including code, message, and additional info"
    ) 