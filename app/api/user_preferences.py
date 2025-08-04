"""
User Preferences API endpoints - Operations for managing user reading preferences and sessions
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import user_preferences as schemas
from app.services import user_preferences_service as service
from app.core.exceptions import (
    LightNovelBookmarksException,
    NovelNotFoundError,
    DatabaseError,
)

router = APIRouter()


def _handle_service_exception(e: LightNovelBookmarksException):
    """Convert service exceptions to HTTP exceptions"""
    if isinstance(e, NovelNotFoundError):
        raise HTTPException(status_code=404, detail=e.message)
    elif isinstance(e, DatabaseError):
        raise HTTPException(status_code=500, detail="Internal server error")
    else:
        raise HTTPException(status_code=500, detail="Internal server error")


# User Preferences Endpoints
@router.get(
    "/user-preferences/{novel_id}", response_model=Optional[schemas.UserPreferences]
)
def get_user_preferences(
    novel_id: int,
    db: Session = Depends(get_db),
):
    """
    Get user preferences for a specific novel

    Retrieves the user's reading preferences, status, progress, and notes for a novel.
    Returns null if no preferences have been set for this novel.

    Args:
        novel_id: ID of the novel to get preferences for

    Returns:
        UserPreferences: User's preferences for the novel, or null if none exist

    Raises:
        HTTPException:
            - 404 if novel doesn't exist
            - 500 if an unexpected server error occurs
    """
    try:
        preferences = service.get_user_preferences(db, novel_id)
        return preferences
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.post(
    "/user-preferences/{novel_id}",
    response_model=schemas.UserPreferences,
    status_code=201,
)
def create_or_update_user_preferences(
    novel_id: int,
    preferences_data: schemas.UserPreferencesCreate,
    db: Session = Depends(get_db),
):
    """
    Create or update user preferences for a novel

    Creates new user preferences or updates existing ones for a novel.
    This endpoint handles both creation and full updates of user preferences.

    Args:
        novel_id: ID of the novel to set preferences for
        preferences_data: User preferences data including status, rating, notes, etc.

    Returns:
        UserPreferences: Created or updated user preferences

    Raises:
        HTTPException:
            - 404 if novel doesn't exist
            - 422 if validation fails
            - 500 if an unexpected server error occurs

    Example:
        ```
        POST /api/user-preferences/1
        {
            "user_status": "reading",
            "is_favorite": true,
            "current_chapter": 15.5,
            "rating": 5,
            "personal_notes": "Amazing story with great character development!"
        }
        ```
    """
    try:
        preferences = service.create_or_update_user_preferences(
            db, novel_id, preferences_data
        )
        return preferences
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.patch("/user-preferences/{novel_id}", response_model=schemas.UserPreferences)
def update_user_preferences(
    novel_id: int,
    preferences_data: schemas.UserPreferencesUpdate,
    db: Session = Depends(get_db),
):
    """
    Partially update user preferences for a novel

    Updates specific fields of existing user preferences. Only provided fields will be updated.

    Args:
        novel_id: ID of the novel to update preferences for
        preferences_data: Partial user preferences data to update

    Returns:
        UserPreferences: Updated user preferences

    Raises:
        HTTPException:
            - 404 if novel or preferences don't exist
            - 422 if validation fails
            - 500 if an unexpected server error occurs
    """
    try:
        preferences = service.update_user_preferences(db, novel_id, preferences_data)
        return preferences
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.patch(
    "/user-preferences/{novel_id}/status", response_model=schemas.UserPreferences
)
def update_reading_status(
    novel_id: int,
    status_data: schemas.StatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Update only the reading status for a novel

    Quick endpoint to update just the reading status. Automatically sets relevant dates
    (date_started when status becomes "reading", date_completed when status becomes "completed").

    Args:
        novel_id: ID of the novel to update status for
        status_data: New reading status

    Returns:
        UserPreferences: Updated user preferences

    Raises:
        HTTPException:
            - 404 if novel doesn't exist
            - 422 if validation fails
            - 500 if an unexpected server error occurs

    Example:
        ```
        PATCH /api/user-preferences/1/status
        {
            "user_status": "completed"
        }
        ```
    """
    try:
        preferences = service.update_reading_status(db, novel_id, status_data)
        return preferences
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.patch(
    "/user-preferences/{novel_id}/progress", response_model=schemas.UserPreferences
)
def update_reading_progress(
    novel_id: int,
    progress_data: schemas.ProgressUpdate,
    db: Session = Depends(get_db),
):
    """
    Update reading progress for a novel

    Updates the current chapter being read and optionally the reading status.
    Automatically sets date_started if not already set.

    Args:
        novel_id: ID of the novel to update progress for
        progress_data: Progress update data including chapter number and optional status

    Returns:
        UserPreferences: Updated user preferences

    Raises:
        HTTPException:
            - 404 if novel doesn't exist
            - 422 if validation fails
            - 500 if an unexpected server error occurs

    Example:
        ```
        PATCH /api/user-preferences/1/progress
        {
            "current_chapter": 23.5,
            "user_status": "reading"
        }
        ```
    """
    try:
        preferences = service.update_reading_progress(db, novel_id, progress_data)
        return preferences
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.delete("/user-preferences/{novel_id}", status_code=204)
def delete_user_preferences(
    novel_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete user preferences for a novel

    Removes all user preferences and reading data for the specified novel.

    Args:
        novel_id: ID of the novel to delete preferences for

    Raises:
        HTTPException:
            - 500 if an unexpected server error occurs
    """
    try:
        service.delete_user_preferences(db, novel_id)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


# Reading Session Endpoints
@router.post(
    "/reading-sessions/{novel_id}/start",
    response_model=schemas.ReadingSession,
    status_code=201,
)
def start_reading_session(
    novel_id: int,
    session_data: schemas.ReadingSessionCreate,
    db: Session = Depends(get_db),
):
    """
    Start a new reading session

    Begins tracking a reading session for time analytics and progress monitoring.

    Args:
        novel_id: ID of the novel being read
        session_data: Reading session data including chapter and device type

    Returns:
        ReadingSession: Created reading session

    Raises:
        HTTPException:
            - 404 if novel doesn't exist
            - 422 if validation fails
            - 500 if an unexpected server error occurs

    Example:
        ```
        POST /api/reading-sessions/1/start
        {
            "chapter_number": 15.5,
            "device_type": "web"
        }
        ```
    """
    try:
        session = service.start_reading_session(db, novel_id, session_data)
        return session
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.patch(
    "/reading-sessions/{session_id}/end", response_model=schemas.ReadingSession
)
def end_reading_session(
    session_id: int,
    end_data: schemas.ReadingSessionEnd,
    db: Session = Depends(get_db),
):
    """
    End a reading session

    Marks a reading session as complete with the total duration.

    Args:
        session_id: ID of the reading session to end
        end_data: Session end data including duration

    Returns:
        ReadingSession: Updated reading session

    Raises:
        HTTPException:
            - 404 if session doesn't exist
            - 422 if validation fails
            - 500 if an unexpected server error occurs

    Example:
        ```
        PATCH /api/reading-sessions/123/end
        {
            "duration_minutes": 45
        }
        ```
    """
    try:
        session = service.end_reading_session(db, session_id, end_data)
        return session
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.get("/reading-sessions", response_model=List[schemas.ReadingSession])
def get_reading_sessions(
    novel_id: Optional[int] = Query(None, description="Filter by novel ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(
        0, ge=0, description="Number of results to skip for pagination"
    ),
    db: Session = Depends(get_db),
):
    """
    Get reading sessions with optional filtering

    Retrieves reading sessions with pagination and optional filtering by novel.
    Sessions are ordered by start time (most recent first).

    Args:
        novel_id: Optional novel ID to filter sessions by
        limit: Maximum number of sessions to return (1-100)
        offset: Number of sessions to skip for pagination

    Returns:
        List[ReadingSession]: List of reading sessions

    Raises:
        HTTPException:
            - 500 if an unexpected server error occurs
    """
    try:
        sessions = service.get_reading_sessions(db, novel_id, limit, offset)
        return sessions
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.get("/reading-statistics", response_model=schemas.ReadingStatsResponse)
def get_reading_statistics(
    novel_id: Optional[int] = Query(
        None, description="Get stats for specific novel only"
    ),
    db: Session = Depends(get_db),
):
    """
    Get reading statistics and analytics

    Provides comprehensive reading statistics including total time, session averages,
    reading streaks, and daily progress.

    Args:
        novel_id: Optional novel ID to get statistics for (omit for global stats)

    Returns:
        ReadingStatsResponse: Reading statistics and analytics

    Raises:
        HTTPException:
            - 500 if an unexpected server error occurs

    Example Response:
        ```
        {
            "total_reading_time_minutes": 1250,
            "average_session_minutes": 42.5,
            "total_sessions": 29,
            "current_streak_days": 7,
            "chapters_read_today": 3
        }
        ```
    """
    try:
        stats = service.get_reading_statistics(db, novel_id)
        return schemas.ReadingStatsResponse(**stats)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.get("/user-preferences", response_model=List[schemas.UserPreferences])
def get_all_user_preferences(
    status: Optional[schemas.UserStatus] = Query(
        None, description="Filter by reading status"
    ),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(
        0, ge=0, description="Number of results to skip for pagination"
    ),
    db: Session = Depends(get_db),
):
    """
    Get all user preferences with optional filtering

    Retrieves all user preferences with pagination and optional filtering by status or favorite.
    Useful for building reading lists, favorites pages, etc.

    Args:
        status: Optional status filter (reading, completed, on_hold, dropped, plan_to_read)
        is_favorite: Optional favorite filter (true/false)
        limit: Maximum number of preferences to return (1-100)
        offset: Number of preferences to skip for pagination

    Returns:
        List[UserPreferences]: List of user preferences

    Raises:
        HTTPException:
            - 500 if an unexpected server error occurs
    """
    try:
        preferences = service.get_all_user_preferences(
            db, status, is_favorite, limit, offset
        )
        return preferences
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)
