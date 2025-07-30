"""
Novels API endpoints - Primary Adapters for novel operations
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import novel as schemas
from app.services import novel_service
from app.core.utils import convert_novel_model_to_schema
from app.core.exceptions import (
    LightNovelBookmarksException,
    NovelNotFoundError,
    ChapterNotFoundError,
    DuplicateNovelError,
    DuplicateChapterError,
)

router = APIRouter()


def _handle_service_exception(e: LightNovelBookmarksException):
    """Convert service exceptions to HTTP exceptions"""
    if isinstance(e, (NovelNotFoundError, ChapterNotFoundError)):
        raise HTTPException(status_code=404, detail=e.message)
    elif isinstance(e, (DuplicateNovelError, DuplicateChapterError)):
        raise HTTPException(status_code=409, detail=e.message)
    else:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/novels", response_model=List[schemas.LightNovel])
def get_novels(db: Session = Depends(get_db)) -> List[schemas.LightNovel]:
    """
    Get all novels

    Returns a list of all novels in the database with their basic information.
    Chapters are not included in this endpoint for performance reasons.

    Returns:
        List[LightNovel]: A list of novels with their metadata

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        db_novels = novel_service.get_all_novels(db)
        return [convert_novel_model_to_schema(novel) for novel in db_novels]
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.post("/novels", response_model=schemas.LightNovel, status_code=201)
def create_novel(
    novel: schemas.LightNovelCreate, db: Session = Depends(get_db)
) -> schemas.LightNovel:
    """
    Create a new novel

    Creates a new novel with the provided information. The novel title and author
    combination must be unique in the database.

    Args:
        novel: The novel data to create

    Returns:
        LightNovel: The created novel with generated ID

    Raises:
        HTTPException: 409 if novel already exists, 500 if database error occurs
    """
    try:
        db_novel = novel_service.create_novel(db, novel)
        return convert_novel_model_to_schema(db_novel)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.get("/novels/{novel_id}", response_model=schemas.LightNovel)
def get_novel(novel_id: int, db: Session = Depends(get_db)) -> schemas.LightNovel:
    """
    Get a novel by its ID

    Retrieves a specific novel by its unique identifier. Chapters are not
    included in this response; use the chapters endpoint for chapter data.

    Args:
        novel_id: The unique ID of the novel to retrieve

    Returns:
        LightNovel: The novel with the specified ID

    Raises:
        HTTPException: 404 if novel not found, 500 if database error occurs
    """
    try:
        db_novel = novel_service.get_novel_by_id(db, novel_id)
        return convert_novel_model_to_schema(db_novel)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.patch("/novels/{novel_id}", response_model=schemas.LightNovel)
def update_novel(
    novel_id: int, novel: schemas.LightNovelUpdate, db: Session = Depends(get_db)
) -> schemas.LightNovel:
    """
    Update a novel

    Updates an existing novel with the provided information. Only the fields
    specified in the request will be updated; unspecified fields remain unchanged.

    Args:
        novel_id: The unique ID of the novel to update
        novel: The novel data to update (only specified fields will be updated)

    Returns:
        LightNovel: The updated novel

    Raises:
        HTTPException: 404 if novel not found, 500 if database error occurs
    """
    try:
        db_novel = novel_service.update_novel(db, novel_id, novel)
        return convert_novel_model_to_schema(db_novel)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.delete("/novels/{novel_id}", status_code=204)
def delete_novel(novel_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a novel

    Permanently deletes a novel and all its associated chapters from the database.
    This operation cannot be undone.

    Args:
        novel_id: The unique ID of the novel to delete

    Raises:
        HTTPException: 404 if novel not found, 500 if database error occurs
    """
    try:
        novel_service.delete_novel(db, novel_id)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.get("/novels/{novel_id}/chapters", response_model=List[schemas.Chapter])
def get_novel_chapters(
    novel_id: int, db: Session = Depends(get_db)
) -> List[schemas.Chapter]:
    """
    Get all chapters for a novel

    Retrieves all chapters for the specified novel, ordered by chapter number.
    This includes both integer and decimal chapter numbers (e.g., 1, 1.5, 2).

    Args:
        novel_id: The unique ID of the novel to get chapters for

    Returns:
        List[Chapter]: A list of chapters ordered by chapter number

    Raises:
        HTTPException: 404 if novel not found, 500 if database error occurs
    """
    try:
        chapters = novel_service.get_novel_chapters(db, novel_id)
        return [schemas.Chapter.model_validate(chapter) for chapter in chapters]
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.post(
    "/novels/{novel_id}/chapters", response_model=schemas.Chapter, status_code=201
)
def create_chapter(
    novel_id: int, chapter: schemas.ChapterCreate, db: Session = Depends(get_db)
) -> schemas.Chapter:
    """
    Create a new chapter for a novel

    Creates a new chapter for the specified novel. The chapter number must be
    unique within the novel. Decimal chapter numbers are supported (e.g., 1.5).

    Args:
        novel_id: The unique ID of the novel to add the chapter to
        chapter: The chapter data to create

    Returns:
        Chapter: The created chapter with generated ID

    Raises:
        HTTPException: 404 if novel not found, 409 if chapter number already exists, 500 if database error occurs
    """
    try:
        db_chapter = novel_service.create_chapter(db, novel_id, chapter)
        return schemas.Chapter.model_validate(db_chapter)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.get("/novels/{novel_id}/chapters/{chapter_id}", response_model=schemas.Chapter)
def get_chapter(
    novel_id: int, chapter_id: int, db: Session = Depends(get_db)
) -> schemas.Chapter:
    """
    Get a specific chapter

    Retrieves a specific chapter by its unique ID within the context of a novel.

    Args:
        novel_id: The unique ID of the novel
        chapter_id: The unique ID of the chapter to retrieve

    Returns:
        Chapter: The chapter with the specified ID

    Raises:
        HTTPException: 404 if chapter or novel not found, 500 if database error occurs
    """
    try:
        chapter = novel_service.get_chapter_by_id(db, novel_id, chapter_id)
        return schemas.Chapter.model_validate(chapter)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.patch(
    "/novels/{novel_id}/chapters/{chapter_id}", response_model=schemas.Chapter
)
def update_chapter(
    novel_id: int,
    chapter_id: int,
    chapter: schemas.ChapterUpdate,
    db: Session = Depends(get_db),
) -> schemas.Chapter:
    """
    Update a chapter

    Updates an existing chapter with the provided information. Only the fields
    specified in the request will be updated; unspecified fields remain unchanged.
    If updating the chapter number, it must not conflict with existing chapters.

    Args:
        novel_id: The unique ID of the novel
        chapter_id: The unique ID of the chapter to update
        chapter: The chapter data to update (only specified fields will be updated)

    Returns:
        Chapter: The updated chapter

    Raises:
        HTTPException: 404 if chapter not found, 409 if chapter number conflicts, 500 if database error occurs
    """
    try:
        db_chapter = novel_service.update_chapter(db, novel_id, chapter_id, chapter)
        return schemas.Chapter.model_validate(db_chapter)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)


@router.delete("/novels/{novel_id}/chapters/{chapter_id}", status_code=204)
def delete_chapter(
    novel_id: int, chapter_id: int, db: Session = Depends(get_db)
) -> None:
    """
    Delete a chapter

    Permanently deletes a chapter from the database. This operation cannot be undone.

    Args:
        novel_id: The unique ID of the novel
        chapter_id: The unique ID of the chapter to delete

    Raises:
        HTTPException: 404 if chapter not found, 500 if database error occurs
    """
    try:
        novel_service.delete_chapter(db, novel_id, chapter_id)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)
