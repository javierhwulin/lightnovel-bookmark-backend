"""
Novel service layer - Application Services for novel domain logic
"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.novel import LightNovel, Chapter
from app.schemas.novel import (
    LightNovelCreate,
    LightNovelUpdate,
    ChapterCreate,
    ChapterUpdate,
)
from app.core.utils import serialize_genres
from app.core.exceptions import (
    NovelNotFoundError,
    ChapterNotFoundError,
    DuplicateNovelError,
    DuplicateChapterError,
    DatabaseError,
)


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
