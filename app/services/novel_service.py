"""
Novel service layer - Application Services for novel domain logic
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc, func
import json

from app.models.novel import LightNovel, Chapter
from app.schemas.novel import (
    LightNovelCreate,
    LightNovelUpdate,
    ChapterCreate,
    ChapterUpdate,
    NovelStatus,
)
from app.core.utils import serialize_genres
from app.core.exceptions import (
    NovelNotFoundError,
    ChapterNotFoundError,
    DuplicateNovelError,
    DuplicateChapterError,
    DatabaseError,
)


def search_novels(
    db: Session,
    search_query: Optional[str] = None,
    status: Optional[NovelStatus] = None,
    genre: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "title",
    sort_order: str = "asc",
) -> List[LightNovel]:
    """
    Search and filter novels with pagination and sorting

    Args:
        db: Database session
        search_query: Search text to match against title or author
        status: Filter by novel status
        genre: Filter by genre (exact match)
        limit: Maximum number of results
        offset: Number of results to skip
        sort_by: Field to sort by (title, author, id, status)
        sort_order: Sort direction (asc or desc)

    Returns:
        List of LightNovel models matching the criteria

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        query = db.query(LightNovel)

        # Apply filters
        filters = []

        if search_query:
            search_filter = or_(
                LightNovel.title.ilike(f"%{search_query}%"),
                LightNovel.author.ilike(f"%{search_query}%"),
            )
            filters.append(search_filter)

        if status:
            filters.append(LightNovel.status == status.value)

        if genre:
            # Search for genre in the JSON genres field
            filters.append(LightNovel.genres.like(f'%"{genre}"%'))

        if filters:
            query = query.filter(and_(*filters))

        # Apply sorting
        sort_column = getattr(LightNovel, sort_by, LightNovel.title)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        query = query.offset(offset).limit(limit)

        return query.all()

    except SQLAlchemyError as e:
        raise DatabaseError("search_novels", str(e))


def get_collection_stats(db: Session) -> Dict[str, Any]:
    """
    Get statistics about the novel collection

    Args:
        db: Database session

    Returns:
        Dictionary containing collection statistics

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Total novels count
        total_novels = db.query(func.count(LightNovel.id)).scalar()

        # Count by status
        status_counts = {}
        for status in NovelStatus:
            count = (
                db.query(func.count(LightNovel.id))
                .filter(LightNovel.status == status.value)
                .scalar()
            )
            status_counts[status.value] = count

        # Total chapters count
        total_chapters = db.query(func.count(Chapter.id)).scalar()

        # Genre distribution - extract genres from JSON and count them
        novels_with_genres = (
            db.query(LightNovel.genres)
            .filter(LightNovel.genres.isnot(None), LightNovel.genres != "[]")
            .all()
        )

        genre_counts = {}
        for novel_genres in novels_with_genres:
            if novel_genres[0]:  # Check if genres is not None
                try:
                    genres_list = json.loads(novel_genres[0])
                    for genre in genres_list:
                        if isinstance(genre, str) and genre.strip():
                            genre_counts[genre] = genre_counts.get(genre, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue  # Skip invalid JSON

        # Sort genres by count (most popular first)
        sorted_genres = dict(
            sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        )

        return {
            "total_novels": total_novels,
            "total_chapters": total_chapters,
            "status_distribution": status_counts,
            "genre_distribution": sorted_genres,
            "top_genres": list(sorted_genres.keys())[:10],  # Top 10 genres
        }

    except SQLAlchemyError as e:
        raise DatabaseError("get_collection_stats", str(e))


def get_available_genres(db: Session) -> List[str]:
    """
    Get list of all available genres in the collection

    Args:
        db: Database session

    Returns:
        List of unique genre names sorted by popularity

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Get all novels with genres
        novels_with_genres = (
            db.query(LightNovel.genres)
            .filter(LightNovel.genres.isnot(None), LightNovel.genres != "[]")
            .all()
        )

        genre_counts = {}
        for novel_genres in novels_with_genres:
            if novel_genres[0]:  # Check if genres is not None
                try:
                    genres_list = json.loads(novel_genres[0])
                    for genre in genres_list:
                        if isinstance(genre, str) and genre.strip():
                            genre_counts[genre] = genre_counts.get(genre, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue  # Skip invalid JSON

        # Sort genres by count (most popular first) and return just the names
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        return [genre[0] for genre in sorted_genres]

    except SQLAlchemyError as e:
        raise DatabaseError("get_available_genres", str(e))


def quick_search_novels(
    db: Session, search_query: str, limit: int = 10
) -> List[LightNovel]:
    """
    Quick search for novels - optimized for autocomplete

    Args:
        db: Database session
        search_query: Search text to match against title or author
        limit: Maximum number of results

    Returns:
        List of LightNovel models matching the query

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        search_filter = or_(
            LightNovel.title.ilike(f"%{search_query}%"),
            LightNovel.author.ilike(f"%{search_query}%"),
        )

        return (
            db.query(LightNovel)
            .filter(search_filter)
            .order_by(LightNovel.title)
            .limit(limit)
            .all()
        )

    except SQLAlchemyError as e:
        raise DatabaseError("quick_search_novels", str(e))


def get_novel_summaries(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "title",
    sort_order: str = "asc",
) -> List[Dict[str, Any]]:
    """
    Get novel summaries with chapter counts

    Args:
        db: Database session
        limit: Maximum number of results
        offset: Number of results to skip
        sort_by: Field to sort by
        sort_order: Sort direction

    Returns:
        List of novel summary dictionaries with chapter counts

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Query novels with chapter counts
        novels_query = (
            db.query(LightNovel, func.count(Chapter.id).label("chapter_count"))
            .outerjoin(Chapter)
            .group_by(LightNovel.id)
        )

        # Apply sorting
        sort_column = getattr(LightNovel, sort_by, LightNovel.title)
        if sort_order == "desc":
            novels_query = novels_query.order_by(desc(sort_column))
        else:
            novels_query = novels_query.order_by(asc(sort_column))

        # Apply pagination
        results = novels_query.offset(offset).limit(limit).all()

        # Convert to summary format
        summaries = []
        for novel, chapter_count in results:
            # Parse genres from JSON
            genres = []
            if novel.genres:
                try:
                    genres = json.loads(novel.genres)
                except (json.JSONDecodeError, TypeError):
                    genres = []

            summary = {
                "id": novel.id,
                "title": novel.title,
                "author": novel.author,
                "cover_url": novel.cover_url,
                "status": novel.status,
                "genres": genres,
                "total_chapters": novel.total_chapters or 0,
                "chapter_count": chapter_count or 0,
            }
            summaries.append(summary)

        return summaries

    except SQLAlchemyError as e:
        raise DatabaseError("get_novel_summaries", str(e))


def get_all_novels(db: Session) -> List[LightNovel]:
    """
    Get all novels from database

    Args:
        db: Database session

    Returns:
        List of LightNovel models

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        return db.query(LightNovel).all()
    except SQLAlchemyError as e:
        raise DatabaseError("get_all_novels", str(e))


def get_novel_by_id(db: Session, novel_id: int) -> LightNovel:
    """
    Get a novel by its ID

    Args:
        db: Database session
        novel_id: ID of the novel to retrieve

    Returns:
        LightNovel model

    Raises:
        NovelNotFoundError: If novel is not found
        DatabaseError: If database operation fails
    """
    try:
        novel = db.query(LightNovel).filter(LightNovel.id == novel_id).first()
        if not novel:
            raise NovelNotFoundError(novel_id)
        return novel
    except SQLAlchemyError as e:
        raise DatabaseError("get_novel_by_id", str(e))


def create_novel(db: Session, novel_data: LightNovelCreate) -> LightNovel:
    """
    Create a new novel

    Args:
        db: Database session
        novel_data: Novel creation data

    Returns:
        Created LightNovel model

    Raises:
        DuplicateNovelError: If novel already exists
        DatabaseError: If database operation fails
    """
    try:
        # Check for duplicate novel
        existing_novel = (
            db.query(LightNovel)
            .filter(
                LightNovel.title == novel_data.title,
                LightNovel.author == novel_data.author,
            )
            .first()
        )

        if existing_novel:
            raise DuplicateNovelError(novel_data.title, novel_data.author)

        # Serialize genres for database storage
        novel_dict = novel_data.model_dump()
        novel_dict["genres"] = serialize_genres(novel_dict.get("genres", []))

        db_novel = LightNovel(**novel_dict)
        db.add(db_novel)
        db.commit()
        db.refresh(db_novel)

        return db_novel
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError("create_novel", str(e))


def update_novel(
    db: Session, novel_id: int, novel_data: LightNovelUpdate
) -> LightNovel:
    """
    Update an existing novel

    Args:
        db: Database session
        novel_id: ID of the novel to update
        novel_data: Novel update data

    Returns:
        Updated LightNovel model

    Raises:
        NovelNotFoundError: If novel is not found
        DatabaseError: If database operation fails
    """
    try:
        db_novel = db.query(LightNovel).filter(LightNovel.id == novel_id).first()
        if not db_novel:
            raise NovelNotFoundError(novel_id)

        # Update only provided fields
        update_data = novel_data.model_dump(exclude_unset=True)
        if "genres" in update_data:
            update_data["genres"] = serialize_genres(update_data["genres"])

        for field, value in update_data.items():
            setattr(db_novel, field, value)

        db.commit()
        db.refresh(db_novel)

        return db_novel
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError("update_novel", str(e))


def delete_novel(db: Session, novel_id: int) -> LightNovel:
    """
    Delete a novel by its ID

    Args:
        db: Database session
        novel_id: ID of the novel to delete

    Returns:
        Deleted LightNovel model

    Raises:
        NovelNotFoundError: If novel is not found
        DatabaseError: If database operation fails
    """
    try:
        db_novel = db.query(LightNovel).filter(LightNovel.id == novel_id).first()
        if not db_novel:
            raise NovelNotFoundError(novel_id)

        db.delete(db_novel)
        db.commit()

        return db_novel
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError("delete_novel", str(e))


def get_novel_chapters(db: Session, novel_id: int) -> List[Chapter]:
    """
    Get all chapters for a novel

    Args:
        db: Database session
        novel_id: ID of the novel

    Returns:
        List of Chapter models ordered by chapter number

    Raises:
        NovelNotFoundError: If novel is not found
        DatabaseError: If database operation fails
    """
    try:
        # First check if novel exists
        novel = db.query(LightNovel).filter(LightNovel.id == novel_id).first()
        if not novel:
            raise NovelNotFoundError(novel_id)

        return (
            db.query(Chapter)
            .filter(Chapter.novel_id == novel_id)
            .order_by(Chapter.number)
            .all()
        )
    except SQLAlchemyError as e:
        raise DatabaseError("get_novel_chapters", str(e))


def get_chapter_by_id(db: Session, novel_id: int, chapter_id: int) -> Chapter:
    """
    Get a specific chapter for a novel

    Args:
        db: Database session
        novel_id: ID of the novel
        chapter_id: ID of the chapter

    Returns:
        Chapter model

    Raises:
        ChapterNotFoundError: If chapter is not found
        DatabaseError: If database operation fails
    """
    try:
        chapter = (
            db.query(Chapter)
            .filter(Chapter.id == chapter_id, Chapter.novel_id == novel_id)
            .first()
        )

        if not chapter:
            raise ChapterNotFoundError(chapter_id, novel_id)

        return chapter
    except SQLAlchemyError as e:
        raise DatabaseError("get_chapter_by_id", str(e))


def create_chapter(db: Session, novel_id: int, chapter_data: ChapterCreate) -> Chapter:
    """
    Create a new chapter for a novel

    Args:
        db: Database session
        novel_id: ID of the novel
        chapter_data: Chapter creation data

    Returns:
        Created Chapter model

    Raises:
        NovelNotFoundError: If novel is not found
        DuplicateChapterError: If chapter number already exists
        DatabaseError: If database operation fails
    """
    try:
        # Check if novel exists
        novel = db.query(LightNovel).filter(LightNovel.id == novel_id).first()
        if not novel:
            raise NovelNotFoundError(novel_id)

        # Check if chapter number already exists
        existing_chapter = (
            db.query(Chapter)
            .filter(Chapter.novel_id == novel_id, Chapter.number == chapter_data.number)
            .first()
        )

        if existing_chapter:
            raise DuplicateChapterError(chapter_data.number, novel_id)

        db_chapter = Chapter(
            novel_id=novel_id,
            number=chapter_data.number,
            title=chapter_data.title,
            source_url=chapter_data.source_url,
        )

        db.add(db_chapter)
        db.commit()
        db.refresh(db_chapter)

        return db_chapter
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError("create_chapter", str(e))


def update_chapter(
    db: Session, novel_id: int, chapter_id: int, chapter_data: ChapterUpdate
) -> Chapter:
    """
    Update a chapter

    Args:
        db: Database session
        novel_id: ID of the novel
        chapter_id: ID of the chapter to update
        chapter_data: Chapter update data

    Returns:
        Updated Chapter model

    Raises:
        ChapterNotFoundError: If chapter is not found
        DuplicateChapterError: If chapter number conflicts with existing chapter
        DatabaseError: If database operation fails
    """
    try:
        db_chapter = (
            db.query(Chapter)
            .filter(Chapter.id == chapter_id, Chapter.novel_id == novel_id)
            .first()
        )

        if not db_chapter:
            raise ChapterNotFoundError(chapter_id, novel_id)

        # Update only provided fields
        update_data = chapter_data.model_dump(exclude_unset=True)

        # Check if number conflicts with existing chapter
        if "number" in update_data:
            existing_chapter = (
                db.query(Chapter)
                .filter(
                    Chapter.novel_id == novel_id,
                    Chapter.number == update_data["number"],
                    Chapter.id != chapter_id,
                )
                .first()
            )

            if existing_chapter:
                raise DuplicateChapterError(update_data["number"], novel_id)

        for field, value in update_data.items():
            setattr(db_chapter, field, value)

        db.commit()
        db.refresh(db_chapter)

        return db_chapter
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError("update_chapter", str(e))


def delete_chapter(db: Session, novel_id: int, chapter_id: int) -> Chapter:
    """
    Delete a chapter

    Args:
        db: Database session
        novel_id: ID of the novel
        chapter_id: ID of the chapter to delete

    Returns:
        Deleted Chapter model

    Raises:
        ChapterNotFoundError: If chapter is not found
        DatabaseError: If database operation fails
    """
    try:
        db_chapter = (
            db.query(Chapter)
            .filter(Chapter.id == chapter_id, Chapter.novel_id == novel_id)
            .first()
        )

        if not db_chapter:
            raise ChapterNotFoundError(chapter_id, novel_id)

        db.delete(db_chapter)
        db.commit()

        return db_chapter
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError("delete_chapter", str(e))
