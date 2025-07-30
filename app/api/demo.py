from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any
from app.db.session import get_db
from app.schemas import novel as schemas
from app.services.demo_data import create_demo_slime_novel, create_demo_overlord_novel
import json

router = APIRouter()

def _convert_novel_to_schema(db_novel) -> schemas.LightNovel:
    """Convert SQLAlchemy novel model to Pydantic schema"""
    try:
        genres = json.loads(db_novel.genres) if db_novel.genres else []
    except json.JSONDecodeError:
        genres = []
    
    return schemas.LightNovel(
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
        chapters=[]
    )

@router.post("/demo/create-slime-novel", response_model=schemas.LightNovel)
def create_slime_demo(db: Session = Depends(get_db)) -> schemas.LightNovel:
    """
    Create demo data for 'That Time I Got Reincarnated as a Slime'
    This demonstrates what the scraper would create from NovelUpdates.
    Now creates 20 chapters directly under the novel (no volumes).
    """
    try:
        db_novel = create_demo_slime_novel(db)
        return _convert_novel_to_schema(db_novel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create demo novel: {str(e)}")

@router.post("/demo/create-overlord-novel", response_model=schemas.LightNovel)
def create_overlord_demo(db: Session = Depends(get_db)) -> schemas.LightNovel:
    """
    Create demo data for 'Overlord'
    This demonstrates what the scraper would create from NovelUpdates.
    Now creates 10 chapters directly under the novel (no volumes).
    """
    try:
        db_novel = create_demo_overlord_novel(db)
        return _convert_novel_to_schema(db_novel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create demo novel: {str(e)}")

@router.post("/demo/create-all-demos")
def create_all_demos(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Create all available demo novels with chapter counts"""
    try:
        slime_novel = create_demo_slime_novel(db)
        overlord_novel = create_demo_overlord_novel(db)
        
        return {
            "message": "Successfully created all demo novels",
            "novels": [
                {
                    "title": slime_novel.title,
                    "id": slime_novel.id,
                    "chapter_count": len(slime_novel.chapters)
                },
                {
                    "title": overlord_novel.title, 
                    "id": overlord_novel.id,
                    "chapter_count": len(overlord_novel.chapters)
                }
            ],
            "note": "Volumes have been removed. Chapters are now directly under novels as per NovelUpdates structure."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create demo novels: {str(e)}")

@router.get("/demo/scraper-alternatives")
def get_scraper_alternatives() -> dict:
    """
    Provide information about the updated scraper system using cloudscraper
    """
    return {
        "message": "Updated scraper system now uses cloudscraper to bypass Cloudflare protection",
        "changes": {
            "scraper": "Now uses cloudscraper instead of regular requests for better Cloudflare bypass",
            "data_model": "Removed volumes - chapters are now directly under novels",
            "chapter_numbering": "Supports decimal chapter numbers (e.g., 1.5, 2.1)",
            "author_extraction": "Now properly extracts authors from showauthors div, supports multiple authors",
            "chapter_count": "Fast total chapter extraction from Status in COO section (div#editstatus)"
        },
        "available_endpoints": [
            {
                "method": "POST",
                "endpoint": "/api/scraper/search",
                "description": "Search for novels on NovelUpdates by title",
                "example": {"search_term": "slime", "limit": 10}
            },
            {
                "method": "POST", 
                "endpoint": "/api/scraper/preview",
                "description": "Fast preview with total chapters from Status in COO (no individual chapter scraping)",
                "example": {"url": "https://www.novelupdates.com/series/novel-name/"}
            },
            {
                "method": "POST",
                "endpoint": "/api/scraper/import",
                "description": "Import novel with chapters - uses fast total count from Status in COO section"
            },
            {
                "method": "POST",
                "endpoint": "/api/scraper/import-by-search", 
                "description": "Search for a novel and import the first result"
            }
        ],
        "demo_data": {
            "slime_novel": "20 chapters available - shows multiple author extraction (Fuse & 伏瀬)",
            "overlord_novel": "10 chapters available - shows single author extraction",
            "structure": "Chapters directly under novels, no volume grouping"
        },
        "extraction_features": {
            "author_extraction": {
                "description": "Extracts authors from <div id='showauthors'> containing <a class='genre' id='authtag'> links",
                "examples": ["Single: 'Kugane Maruyama'", "Multiple: 'Fuse & 伏瀬'"]
            },
            "chapter_count": {
                "description": "Fast extraction from Status in COO section <div id='editstatus'>",
                "examples": ["'355 Chapters (Completed)' → 355 chapters, completed status"],
                "benefits": ["Much faster than scraping individual chapters", "More reliable total count", "Includes completion status"]
            }
        },
        "test_endpoints": [
            "GET /api/demo/test-author-extraction - Test author extraction logic",
            "GET /api/demo/test-chapter-extraction - Test chapter count extraction logic"
        ],
        "api_changes": {
            "removed": [
                "GET /api/novels/{id}/volumes",
                "Volume-related endpoints"
            ],
            "added": [
                "GET /api/novels/{id}/chapters",
                "POST /api/novels/{id}/chapters", 
                "GET /api/novels/{id}/chapters/{chapter_id}",
                "PATCH /api/novels/{id}/chapters/{chapter_id}",
                "DELETE /api/novels/{id}/chapters/{chapter_id}"
            ]
        }
    } 

@router.get("/demo/test-author-extraction")
def test_author_extraction() -> dict:
    """
    Test the author extraction logic with sample HTML from NovelUpdates
    """
    from bs4 import BeautifulSoup
    
    # Sample HTML structure as provided by the user
    sample_html = '''
    <div id="showauthors">
    <a class="genre" id="authtag" href="https://www.novelupdates.com/nauthor/fuse/" title="View All Series by Fuse">Fuse</a><br>
    <a class="genre" id="authtag" href="https://www.novelupdates.com/nauthor/%e4%bc%8f%e7%80%ac/" title="View All Series by 伏瀬">伏瀬</a><br>
    </div>
    '''
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    # Extract authors using the same logic as the scraper
    authors_elem = soup.find("div", id="showauthors")
    extracted_authors = []
    
    if authors_elem:
        author_links = authors_elem.find_all("a", class_="genre", id="authtag")
        if author_links:
            for link in author_links:
                author_name = link.get_text(strip=True)
                if author_name:
                    extracted_authors.append(author_name)
    
    result_author = " & ".join(extracted_authors) if extracted_authors else "Unknown Author"
    
    return {
        "test_description": "Testing author extraction logic with sample NovelUpdates HTML",
        "sample_html": sample_html.strip(),
        "extracted_authors": extracted_authors,
        "final_author_string": result_author,
        "extraction_steps": [
            "1. Find <div id='showauthors'>",
            "2. Extract all <a class='genre' id='authtag'> links within it",
            "3. Get text content from each link",
            "4. Join multiple authors with ' & ' separator"
        ],
        "status": "✅ Working correctly" if len(extracted_authors) == 2 and "伏瀬" in extracted_authors else "❌ Issue detected"
    } 

@router.get("/demo/test-chapter-extraction")
def test_chapter_extraction() -> dict:
    """
    Test the total chapter count extraction from Status in COO section
    """
    from bs4 import BeautifulSoup
    import re
    
    # Sample HTML structure as provided by the user
    sample_html = '''
    <h5 class="seriesother" title="Status in Country of Origin">Status in COO</h5>
    <span class="editmsg">Status in Country of Origin. One entry per line</span>
    <div id="editstatus">
    355 Chapters (Completed)
    </div>
    '''
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    # Extract total chapters and status using the same logic as the scraper
    status_elem = soup.find("div", id="editstatus")
    extracted_data = {}
    
    if status_elem:
        status_text = status_elem.get_text(strip=True)
        
        # Extract total chapters
        chapter_match = re.search(r'(\d+)\s+chapters?', status_text, re.IGNORECASE)
        if chapter_match:
            extracted_data['total_chapters'] = int(chapter_match.group(1))
        else:
            extracted_data['total_chapters'] = 0
        
        # Extract status
        status_text_lower = status_text.lower()
        if 'completed' in status_text_lower or 'complete' in status_text_lower:
            extracted_data['status'] = 'completed'
        elif 'ongoing' in status_text_lower:
            extracted_data['status'] = 'ongoing'
        elif 'hiatus' in status_text_lower:
            extracted_data['status'] = 'hiatus'
        elif 'dropped' in status_text_lower:
            extracted_data['status'] = 'dropped'
        else:
            extracted_data['status'] = 'unknown'
        
        extracted_data['raw_status_text'] = status_text
    
    return {
        "test_description": "Testing total chapter count extraction from Status in COO section",
        "sample_html": sample_html.strip(),
        "raw_text": status_elem.get_text(strip=True) if status_elem else "No editstatus found",
        "extracted_data": extracted_data,
        "extraction_logic": [
            "1. Find <div id='editstatus'> containing Status in COO text",
            "2. Use regex to extract chapter count: r'(\\d+)\\s+chapters?' ",
            "3. Parse status from keywords: completed, ongoing, hiatus, dropped",
            "4. Much faster than scraping individual chapter pages"
        ],
        "regex_pattern": r'(\d+)\s+chapters?',
        "status": "✅ Working correctly" if extracted_data.get('total_chapters', 0) == 355 and extracted_data.get('status') == 'completed' else "❌ Issue detected"
    } 