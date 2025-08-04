"""
User Preferences service layer - Application Services for user preferences domain logic
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from datetime import datetime, date

from app.models.user_preferences import UserPreferences, ReadingSession
from app.models.novel import LightNovel
from app.schemas.user_preferences import (
    UserPreferencesCreate,
    UserPreferencesUpdate,
    StatusUpdate,
    ProgressUpdate,
    ReadingSessionCreate,
    ReadingSessionEnd,
    UserStatus,
)
from app.core.exceptions import (
    NovelNotFoundError,
    DatabaseError,
)


def get_user_preferences(db: Session, novel_id: int) -> Optional[UserPreferences]:
    """
    Get user preferences for a specific novel

    Args:
        db: Database session
        novel_id: ID of the novel

    Returns:
        UserPreferences model or None if not found

    Raises:
        NovelNotFoundError: If novel doesn't exist
        DatabaseError: If database operation fails
    """
    try:
        # Verify novel exists
        novel = db.query(LightNovel).filter(LightNovel.id == novel_id).first()
        if not novel:
            raise NovelNotFoundError(f"Novel with ID {novel_id} not found")

        # Get user preferences
        preferences = (
            db.query(UserPreferences)
            .filter(UserPreferences.novel_id == novel_id)
            .first()
        )

        return preferences

    except SQLAlchemyError as e:
        raise DatabaseError(
            f"Database error while retrieving user preferences: {str(e)}"
        )


def create_or_update_user_preferences(
    db: Session, novel_id: int, preferences_data: UserPreferencesCreate
) -> UserPreferences:
    """
    Create or update user preferences for a novel

    Args:
        db: Database session
        novel_id: ID of the novel
        preferences_data: User preferences data

    Returns:
        Created or updated UserPreferences model

    Raises:
        NovelNotFoundError: If novel doesn't exist
        DatabaseError: If database operation fails
    """
    try:
        # Verify novel exists
        novel = db.query(LightNovel).filter(LightNovel.id == novel_id).first()
        if not novel:
            raise NovelNotFoundError(f"Novel with ID {novel_id} not found")

        # Check if preferences already exist
        existing_preferences = (
            db.query(UserPreferences)
            .filter(UserPreferences.novel_id == novel_id)
            .first()
        )

        if existing_preferences:
            # Update existing preferences
            for field, value in preferences_data.model_dump(exclude_unset=True).items():
                setattr(existing_preferences, field, value)
            existing_preferences.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_preferences)
            return existing_preferences
        else:
            # Create new preferences
            db_preferences = UserPreferences(
                novel_id=novel_id, **preferences_data.model_dump(exclude_unset=True)
            )
            db.add(db_preferences)
            db.commit()
            db.refresh(db_preferences)
            return db_preferences

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(
            f"Database error while creating/updating user preferences: {str(e)}"
        )


def update_user_preferences(
    db: Session, novel_id: int, preferences_data: UserPreferencesUpdate
) -> UserPreferences:
    """
    Update existing user preferences for a novel

    Args:
        db: Database session
        novel_id: ID of the novel
        preferences_data: Updated preferences data

    Returns:
        Updated UserPreferences model

    Raises:
        NovelNotFoundError: If novel or preferences don't exist
        DatabaseError: If database operation fails
    """
    try:
        preferences = get_user_preferences(db, novel_id)
        if not preferences:
            raise NovelNotFoundError(f"User preferences for novel {novel_id} not found")

        # Update only provided fields
        update_data = preferences_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)

        preferences.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(preferences)
        return preferences

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Database error while updating user preferences: {str(e)}")


def update_reading_status(
    db: Session, novel_id: int, status_data: StatusUpdate
) -> UserPreferences:
    """
    Update only the reading status for a novel

    Args:
        db: Database session
        novel_id: ID of the novel
        status_data: New status data

    Returns:
        Updated UserPreferences model

    Raises:
        NovelNotFoundError: If novel doesn't exist
        DatabaseError: If database operation fails
    """
    try:
        # Get or create preferences
        preferences = get_user_preferences(db, novel_id)

        if not preferences:
            # Create new preferences with just the status
            preferences_create = UserPreferencesCreate(
                user_status=status_data.user_status
            )
            return create_or_update_user_preferences(db, novel_id, preferences_create)

        # Update existing preferences
        preferences.user_status = status_data.user_status

        # Auto-set dates based on status
        if (
            status_data.user_status == UserStatus.READING
            and not preferences.date_started
        ):
            preferences.date_started = date.today()
        elif (
            status_data.user_status == UserStatus.COMPLETED
            and not preferences.date_completed
        ):
            preferences.date_completed = date.today()

        preferences.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(preferences)
        return preferences

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Database error while updating reading status: {str(e)}")


def update_reading_progress(
    db: Session, novel_id: int, progress_data: ProgressUpdate
) -> UserPreferences:
    """
    Update reading progress for a novel

    Args:
        db: Database session
        novel_id: ID of the novel
        progress_data: Progress update data

    Returns:
        Updated UserPreferences model

    Raises:
        NovelNotFoundError: If novel doesn't exist
        DatabaseError: If database operation fails
    """
    try:
        # Get or create preferences
        preferences = get_user_preferences(db, novel_id)

        if not preferences:
            # Create new preferences with progress
            preferences_create = UserPreferencesCreate(
                current_chapter=progress_data.current_chapter,
                user_status=progress_data.user_status,
                date_started=date.today(),
            )
            return create_or_update_user_preferences(db, novel_id, preferences_create)

        # Update existing preferences
        preferences.current_chapter = progress_data.current_chapter

        if progress_data.user_status:
            preferences.user_status = progress_data.user_status

        # Auto-set date_started if not set and we're tracking progress
        if not preferences.date_started:
            preferences.date_started = date.today()

        preferences.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(preferences)
        return preferences

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Database error while updating reading progress: {str(e)}")


def delete_user_preferences(db: Session, novel_id: int) -> bool:
    """
    Delete user preferences for a novel

    Args:
        db: Database session
        novel_id: ID of the novel

    Returns:
        True if deleted, False if not found

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        preferences = (
            db.query(UserPreferences)
            .filter(UserPreferences.novel_id == novel_id)
            .first()
        )

        if preferences:
            db.delete(preferences)
            db.commit()
            return True
        return False

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Database error while deleting user preferences: {str(e)}")


# Reading Session Functions
def start_reading_session(
    db: Session, novel_id: int, session_data: ReadingSessionCreate
) -> ReadingSession:
    """
    Start a new reading session

    Args:
        db: Database session
        novel_id: ID of the novel
        session_data: Reading session data

    Returns:
        Created ReadingSession model

    Raises:
        NovelNotFoundError: If novel doesn't exist
        DatabaseError: If database operation fails
    """
    try:
        # Verify novel exists
        novel = db.query(LightNovel).filter(LightNovel.id == novel_id).first()
        if not novel:
            raise NovelNotFoundError(f"Novel with ID {novel_id} not found")

        # Create reading session
        db_session = ReadingSession(novel_id=novel_id, **session_data.model_dump())
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Database error while creating reading session: {str(e)}")


def end_reading_session(
    db: Session, session_id: int, end_data: ReadingSessionEnd
) -> ReadingSession:
    """
    End a reading session

    Args:
        db: Database session
        session_id: ID of the reading session
        end_data: Session end data

    Returns:
        Updated ReadingSession model

    Raises:
        NovelNotFoundError: If session doesn't exist
        DatabaseError: If database operation fails
    """
    try:
        session = (
            db.query(ReadingSession).filter(ReadingSession.id == session_id).first()
        )
        if not session:
            raise NovelNotFoundError(f"Reading session with ID {session_id} not found")

        session.ended_at = datetime.utcnow()
        session.duration_minutes = end_data.duration_minutes

        db.commit()
        db.refresh(session)
        return session

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Database error while ending reading session: {str(e)}")


def get_reading_sessions(
    db: Session, novel_id: Optional[int] = None, limit: int = 50, offset: int = 0
) -> List[ReadingSession]:
    """
    Get reading sessions with optional filtering

    Args:
        db: Database session
        novel_id: Optional novel ID to filter by
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of ReadingSession models

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        query = db.query(ReadingSession)

        if novel_id:
            query = query.filter(ReadingSession.novel_id == novel_id)

        sessions = (
            query.order_by(desc(ReadingSession.started_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
        return sessions

    except SQLAlchemyError as e:
        raise DatabaseError(
            f"Database error while retrieving reading sessions: {str(e)}"
        )


def get_reading_statistics(
    db: Session, novel_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get reading statistics for all novels or a specific novel

    Args:
        db: Database session
        novel_id: Optional novel ID to get stats for

    Returns:
        Dictionary with reading statistics

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        query = db.query(ReadingSession)

        if novel_id:
            query = query.filter(ReadingSession.novel_id == novel_id)

        # Filter to sessions with duration data
        query = query.filter(ReadingSession.duration_minutes.isnot(None))

        sessions = query.all()

        if not sessions:
            return {
                "total_reading_time_minutes": 0,
                "average_session_minutes": 0.0,
                "total_sessions": 0,
                "current_streak_days": 0,
                "chapters_read_today": 0,
            }

        total_time = sum(session.duration_minutes or 0 for session in sessions)
        total_sessions = len(sessions)
        average_time = total_time / total_sessions if total_sessions > 0 else 0.0

        # Calculate today's stats
        today = date.today()
        today_sessions = [s for s in sessions if s.started_at.date() == today]
        chapters_read_today = len(set(s.chapter_number for s in today_sessions))

        # Calculate reading streak (simplified)
        unique_dates = sorted(set(s.started_at.date() for s in sessions), reverse=True)
        current_streak = 0
        if unique_dates and unique_dates[0] == today:
            current_streak = 1
            for i in range(1, len(unique_dates)):
                if (unique_dates[i - 1] - unique_dates[i]).days == 1:
                    current_streak += 1
                else:
                    break

        return {
            "total_reading_time_minutes": total_time,
            "average_session_minutes": round(average_time, 2),
            "total_sessions": total_sessions,
            "current_streak_days": current_streak,
            "chapters_read_today": chapters_read_today,
        }

    except SQLAlchemyError as e:
        raise DatabaseError(
            f"Database error while calculating reading statistics: {str(e)}"
        )


def get_all_user_preferences(
    db: Session,
    status: Optional[UserStatus] = None,
    is_favorite: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[UserPreferences]:
    """
    Get all user preferences with optional filtering

    Args:
        db: Database session
        status: Optional status filter
        is_favorite: Optional favorite filter
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of UserPreferences models

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        query = db.query(UserPreferences)

        if status:
            query = query.filter(UserPreferences.user_status == status)

        if is_favorite is not None:
            query = query.filter(UserPreferences.is_favorite == is_favorite)

        preferences = (
            query.order_by(desc(UserPreferences.updated_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
        return preferences

    except SQLAlchemyError as e:
        raise DatabaseError(
            f"Database error while retrieving user preferences: {str(e)}"
        )
