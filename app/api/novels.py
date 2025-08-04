"""
Novels API endpoints - Primary Adapters for novel operations
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/novels/search", response_model=List[schemas.LightNovel])
def search_novels(
    q: Optional[str] = Query(None, description="Search query for title or author"),
    status: Optional[schemas.NovelStatus] = Query(None, description="Filter by novel status"),
    genre: Optional[str] = Query(None, description="Filter by genre (exact match)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip for pagination"),
    sort_by: str = Query("title", description="Sort field: title, author, id, or status"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> List[schemas.LightNovel]:
    """
    Search and filter novels with pagination
    
    Provides comprehensive search and filtering capabilities for the frontend:
    - Search by title or author (case-insensitive partial match)
    - Filter by status (ongoing, completed, hiatus, dropped, unknown)
    - Filter by genre (exact match)
    - Pagination support with limit and offset
    - Sorting by various fields
    
    Args:
        q: Search query to match against title or author
        status: Filter novels by their publication status
        genre: Filter novels containing the specified genre
        limit: Maximum number of novels to return (1-100)
        offset: Number of novels to skip for pagination
        sort_by: Field to sort by (title, author, id, status)
        sort_order: Sort direction (asc or desc)
    
    Returns:
        List[LightNovel]: Filtered and sorted list of novels
    
    Raises:
        HTTPException: 400 for invalid parameters, 500 for server errors
    """
    try:
        # Validate sort parameters
        valid_sort_fields = {"title", "author", "id", "status"}
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"
            )
        
        if sort_order not in {"asc", "desc"}:
            raise HTTPException(
                status_code=400, 
                detail="Invalid sort_order. Must be 'asc' or 'desc'"
            )
        
        db_novels = novel_service.search_novels(
            db, 
            search_query=q,
            status=status,
            genre=genre,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return [convert_novel_model_to_schema(novel) for novel in db_novels]
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/novels/stats", response_model=schemas.CollectionStats)
def get_novels_stats(db: Session = Depends(get_db)) -> schemas.CollectionStats:
    """
    Get statistics about the novel collection
    
    Provides useful statistics for frontend dashboards:
    - Total novel count
    - Count by status
    - Count by genre
    - Total chapters count
    
    Returns:
        CollectionStats: Collection statistics including counts by status and genre
    
    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        stats = novel_service.get_collection_stats(db)
        return schemas.CollectionStats(**stats)
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/novels/genres", response_model=schemas.GenreList)
def get_available_genres(db: Session = Depends(get_db)) -> schemas.GenreList:
    """
    Get list of all available genres in the collection
    
    Provides a list of unique genres for frontend filter dropdowns and tags.
    Genres are sorted by popularity (most used first).
    
    Returns:
        GenreList: List of available genres with count
    
    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        genres = novel_service.get_available_genres(db)
        return schemas.GenreList(genres=genres, count=len(genres))
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get genres: {str(e)}")


@router.get("/novels/quick-search", response_model=List[schemas.QuickSearchResult])
def quick_search_novels(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of results"),
    db: Session = Depends(get_db),
) -> List[schemas.QuickSearchResult]:
    """
    Quick search for novels - optimized for autocomplete
    
    Provides fast search results for frontend autocomplete/typeahead components.
    Returns minimal data for performance.
    
    Args:
        q: Search query (required, minimum 1 character)
        limit: Maximum number of results (1-20, default 10)
    
    Returns:
        List[QuickSearchResult]: Lightweight novel results for autocomplete
    
    Raises:
        HTTPException: 400 for invalid parameters, 500 for server errors
    """
    try:
        novels = novel_service.quick_search_novels(db, q, limit)
        return [
            schemas.QuickSearchResult(
                id=novel.id,
                title=novel.title,
                author=novel.author,
                cover_url=novel.cover_url
            )
            for novel in novels
        ]
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick search failed: {str(e)}")


@router.get("/novels/summaries", response_model=List[schemas.NovelSummary])
def get_novel_summaries(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    sort_by: str = Query("title", description="Sort field: title, author, id, or status"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> List[schemas.NovelSummary]:
    """
    Get novel summaries - lightweight novel data for lists
    
    Provides lightweight novel data optimized for frontend lists and grids.
    Includes actual chapter counts from the database.
    
    Args:
        limit: Maximum number of novels to return (1-100)
        offset: Number of novels to skip for pagination
        sort_by: Field to sort by (title, author, id, status)
        sort_order: Sort direction (asc or desc)
    
    Returns:
        List[NovelSummary]: Lightweight novel summaries with chapter counts
    
    Raises:
        HTTPException: 400 for invalid parameters, 500 for server errors
    """
    try:
        # Validate sort parameters
        valid_sort_fields = {"title", "author", "id", "status"}
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"
            )
        
        if sort_order not in {"asc", "desc"}:
            raise HTTPException(
                status_code=400, 
                detail="Invalid sort_order. Must be 'asc' or 'desc'"
            )
        
        novels_with_counts = novel_service.get_novel_summaries(
            db, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )
        
        return novels_with_counts
    except LightNovelBookmarksException as e:
        _handle_service_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get novel summaries: {str(e)}")


@router.get("/novels", response_model=List[schemas.LightNovel])
def get_novels(db: Session = Depends(get_db)) -> List[schemas.LightNovel]:
    """
    Get all novels
    
    Returns a list of all novels in the database with their basic information.
    Chapters are not included in this endpoint for performance reasons.
    For search and filtering, use the /novels/search endpoint instead.
    
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
