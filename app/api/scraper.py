"""
Scraper API endpoints - Web scraping operations for importing novels from NovelUpdates
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict

from app.db.session import get_db
from app.schemas.novel import ScrapeRequest, PreviewResponse, LightNovel, ErrorResponse
from app.services.scraper_integration import (
    scrape_and_create_novel,
    update_novel_chapters,
    get_novel_info_preview
)
from app.services.novelupdates_cloudscraper import NovelUpdatesScraperError
from app.core.utils import convert_novel_model_to_schema, validate_url
from app.core.exceptions import (
    LightNovelBookmarksException,
    InvalidUrlError,
    ScrapingError,
    DuplicateNovelError
)

router = APIRouter()


def _handle_scraper_exception(e: Exception, url: str):
    """Convert scraper exceptions to HTTP exceptions"""
    if isinstance(e, NovelUpdatesScraperError):
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to scrape from {url}: {str(e)}"
        )
    elif isinstance(e, ValueError) and "already exists" in str(e):
        raise HTTPException(status_code=409, detail=str(e))
    elif isinstance(e, ValueError):
        raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error while processing {url}: {str(e)}"
        )


@router.post("/scraper/preview", response_model=PreviewResponse, responses={
    400: {"model": ErrorResponse, "description": "Invalid URL or scraping failed"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def preview_novel(request: ScrapeRequest) -> PreviewResponse:
    """
    Preview novel information from NovelUpdates without saving to database
    
    This endpoint provides a fast preview of novel metadata by extracting information
    from the NovelUpdates page without scraping individual chapter pages. It's useful
    for verifying novel information before importing.
    
    Args:
        request: Contains the NovelUpdates URL to preview
        
    Returns:
        PreviewResponse: Novel information preview including title, author, description,
                        status, genres, and chapter count extracted from the "Status in COO" section
        
    Raises:
        HTTPException: 
            - 400 if the URL is invalid or scraping fails
            - 500 if an unexpected server error occurs
            
    Example:
        ```
        POST /api/scraper/preview
        {
            "url": "https://www.novelupdates.com/series/tensei-shitara-slime-datta-ken/"
        }
        ```
    """
    if not validate_url(request.url):
        raise HTTPException(
            status_code=400, 
            detail="Invalid URL. Only NovelUpdates URLs are supported."
        )
    
    try:
        preview_data = get_novel_info_preview(request.url)
        return PreviewResponse(**preview_data)
    except Exception as e:
        _handle_scraper_exception(e, request.url)


@router.post("/scraper/import", response_model=LightNovel, status_code=201, responses={
    400: {"model": ErrorResponse, "description": "Invalid URL or scraping failed"},
    409: {"model": ErrorResponse, "description": "Novel already exists"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def import_novel(request: ScrapeRequest, db: Session = Depends(get_db)) -> LightNovel:
    """
    Import a novel from NovelUpdates and save it to the database
    
    This endpoint scrapes a complete novel from NovelUpdates, including all available
    chapters, and saves it to the database. The operation may take some time for novels
    with many chapters. For large novels, consider using the background import endpoint.
    
    Args:
        request: Contains the NovelUpdates URL to import
        db: Database session (injected dependency)
        
    Returns:
        LightNovel: The imported novel with complete metadata and chapter information
        
    Raises:
        HTTPException:
            - 400 if the URL is invalid or scraping fails
            - 409 if a novel with the same title and author already exists
            - 500 if an unexpected server error occurs
            
    Example:
        ```
        POST /api/scraper/import
        {
            "url": "https://www.novelupdates.com/series/overlord-ln/"
        }
        ```
    """
    if not validate_url(request.url):
        raise HTTPException(
            status_code=400, 
            detail="Invalid URL. Only NovelUpdates URLs are supported."
        )
    
    try:
        db_novel = scrape_and_create_novel(db, request.url)
        return convert_novel_model_to_schema(db_novel)
    except Exception as e:
        _handle_scraper_exception(e, request.url)


@router.post("/scraper/update/{novel_id}", response_model=LightNovel, responses={
    400: {"model": ErrorResponse, "description": "Invalid URL or scraping failed"},
    404: {"model": ErrorResponse, "description": "Novel not found"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def update_novel_from_source(
    novel_id: int, 
    request: ScrapeRequest, 
    db: Session = Depends(get_db)
) -> LightNovel:
    """
    Update an existing novel with new chapters from NovelUpdates
    
    This endpoint scrapes the latest chapter information from NovelUpdates and adds
    any new chapters to an existing novel in the database. Existing chapters are
    not modified, only new chapters are added.
    
    Args:
        novel_id: Unique ID of the existing novel to update
        request: Contains the NovelUpdates URL to scrape updates from
        db: Database session (injected dependency)
        
    Returns:
        LightNovel: The updated novel with any new chapters added
        
    Raises:
        HTTPException:
            - 400 if the URL is invalid or scraping fails
            - 404 if the novel with the specified ID does not exist
            - 500 if an unexpected server error occurs
            
    Example:
        ```
        POST /api/scraper/update/123
        {
            "url": "https://www.novelupdates.com/series/overlord-ln/"
        }
        ```
    """
    if not validate_url(request.url):
        raise HTTPException(
            status_code=400, 
            detail="Invalid URL. Only NovelUpdates URLs are supported."
        )
    
    try:
        db_novel = update_novel_chapters(db, novel_id, request.url)
        return convert_novel_model_to_schema(db_novel)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _handle_scraper_exception(e, request.url)


@router.post("/scraper/import-background", response_model=Dict[str, str], responses={
    400: {"model": ErrorResponse, "description": "Invalid URL"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def import_novel_background(
    request: ScrapeRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Import a novel from NovelUpdates in the background
    
    This endpoint initiates a background import process for novels with many chapters
    or when you don't want to wait for the import to complete. The import will continue
    processing after the API response is returned.
    
    Use this endpoint for:
    - Large novels with hundreds of chapters
    - When you want to start multiple imports simultaneously
    - When the client doesn't need to wait for completion
    
    Args:
        request: Contains the NovelUpdates URL to import
        background_tasks: FastAPI background tasks manager (injected dependency)
        db: Database session (injected dependency)
        
    Returns:
        Dict: Success message and status indicating background processing has started
        
    Raises:
        HTTPException:
            - 400 if the URL is invalid
            - 500 if an unexpected server error occurs
            
    Note:
        Check the novels list after a few minutes to see the imported novel.
        Background import errors are logged but not returned to the client.
        
    Example:
        ```
        POST /api/scraper/import-background
        {
            "url": "https://www.novelupdates.com/series/martial-god-asura/"
        }
        ```
    """
    if not validate_url(request.url):
        raise HTTPException(
            status_code=400, 
            detail="Invalid URL. Only NovelUpdates URLs are supported."
        )
    
    def background_import_task(url: str):
        """Background task for importing novels"""
        try:
            # Create a new database session for the background task
            from app.db.session import SessionLocal
            bg_db = SessionLocal()
            try:
                scrape_and_create_novel(bg_db, url)
                print(f"✅ Successfully imported novel from {url}")
            finally:
                bg_db.close()
        except Exception as e:
            print(f"❌ Background import failed for {url}: {str(e)}")
    
    # Add the task to background processing
    background_tasks.add_task(background_import_task, request.url)
    
    return {
        "message": "Novel import started in background. Check the novels list in a few minutes to see the imported novel.",
        "status": "processing",
        "url": request.url
    } 