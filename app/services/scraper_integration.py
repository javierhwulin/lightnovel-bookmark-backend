from sqlalchemy.orm import Session
from typing import Dict
import json

from app.services.novelupdates_cloudscraper import (
    NovelUpdatesCloudScraper,
)
from app.models.novel import LightNovel, Chapter


def scrape_and_create_novel(db: Session, novelupdates_url: str) -> LightNovel:
    """
    Scrape a novel from NovelUpdates and create it in the database with chapters

    Args:
        db: Database session
        novelupdates_url: URL to the NovelUpdates series page

    Returns:
        LightNovel: The created novel with chapters

    Raises:
        NovelUpdatesScraperError: If scraping fails
        ValueError: If novel already exists or data is invalid
    """
    scraper = NovelUpdatesCloudScraper(delay=6)

    try:
        # Scrape the novel data - only URLs are supported now
        if not novelupdates_url.startswith("http"):
            raise ValueError(
                "Only NovelUpdates URLs are supported. Search functionality has been removed."
            )

        scraped_data = scraper.scrape_novel_by_url(novelupdates_url)

        # Check if novel already exists by title and author
        title = scraped_data.get("title", "Unknown Title")
        author = scraped_data.get("author", "Unknown Author")

        existing_novel = (
            db.query(LightNovel)
            .filter(LightNovel.title == title, LightNovel.author == author)
            .first()
        )

        if existing_novel:
            raise ValueError(f"Novel '{title}' by {author} already exists")

        # Serialize genres
        genres_json = json.dumps(scraped_data.get("genres", []))

        # Create the novel
        db_novel = LightNovel(
            title=title,
            author=author,
            description=scraped_data.get("description", ""),
            status=scraped_data.get("status", "unknown"),
            genres=genres_json,
            source_url=scraped_data.get("source_url", novelupdates_url),
            cover_url=scraped_data.get(
                "cover_url", None
            ),  # Now extracts cover images from NovelUpdates
            # New fields for chapter/volume tracking and raw status
            total_chapters=scraped_data.get("total_chapters", 0),
            total_volumes=scraped_data.get("total_volumes", 0),
            content_type=scraped_data.get("content_type", "unknown"),
            raw_status=scraped_data.get("raw_status", None),
        )

        db.add(db_novel)
        db.flush()  # Get the novel ID

        # Create chapters
        chapters_data = scraped_data.get("chapters", [])

        for chapter_info in chapters_data:
            db_chapter = Chapter(
                novel_id=db_novel.id,
                number=chapter_info.chapter_number,
                title=chapter_info.title,
                source_url=chapter_info.source_url,
            )

            db.add(db_chapter)

        db.commit()
        db.refresh(db_novel)

        return db_novel

    finally:
        scraper.close()


def update_novel_chapters(
    db: Session, novel_id: int, novelupdates_url: str
) -> LightNovel:
    """
    Update an existing novel with new chapters from NovelUpdates

    Args:
        db: Database session
        novel_id: ID of the existing novel
        novelupdates_url: URL to the NovelUpdates series page

    Returns:
        LightNovel: The updated novel

    Raises:
        NovelUpdatesScraperError: If scraping fails
        ValueError: If novel doesn't exist
    """
    # Check if novel exists
    db_novel = db.query(LightNovel).filter(LightNovel.id == novel_id).first()
    if not db_novel:
        raise ValueError(f"Novel with ID {novel_id} not found")

    scraper = NovelUpdatesCloudScraper(delay=6)

    try:
        # Scrape the novel data
        scraped_data = scraper.scrape_novel_by_url(novelupdates_url)

        # Get existing chapters to avoid duplicates
        existing_chapters = db.query(Chapter).filter(Chapter.novel_id == novel_id).all()
        existing_chapter_numbers = {chapter.number for chapter in existing_chapters}

        # Process scraped chapters
        chapters_data = scraped_data.get("chapters", [])
        new_chapters_count = 0

        for chapter_info in chapters_data:
            # Skip if chapter already exists
            if chapter_info.chapter_number not in existing_chapter_numbers:
                db_chapter = Chapter(
                    novel_id=novel_id,
                    number=chapter_info.chapter_number,
                    title=chapter_info.title,
                    source_url=chapter_info.source_url,
                )
                db.add(db_chapter)
                new_chapters_count += 1

        # Update novel's source URL if it's different
        if (
            scraped_data.get("source_url")
            and db_novel.source_url != scraped_data["source_url"]
        ):
            db_novel.source_url = scraped_data["source_url"]

        db.commit()
        db.refresh(db_novel)

        print(f"Added {new_chapters_count} new chapters to '{db_novel.title}'")
        return db_novel

    finally:
        scraper.close()


def get_novel_info_preview(novelupdates_url: str) -> Dict:
    """
    Preview novel information without saving to database
    Gets total chapter count from Status in COO section for fast preview

    Args:
        novelupdates_url: URL to the NovelUpdates series page

    Returns:
        Dict: Novel information preview

    Raises:
        NovelUpdatesScraperError: If scraping fails
    """
    scraper = NovelUpdatesCloudScraper(delay=6)

    try:
        # Get novel info without scraping individual chapters (faster preview)
        scraped_data = scraper.scrape_novel_by_url(
            novelupdates_url, scrape_chapters=False
        )

        # Format preview data
        preview = {
            "title": scraped_data.get("title", "Unknown"),
            "author": scraped_data.get("author", "Unknown Author"),
            "description": scraped_data.get("description", "")[:500] + "..."
            if len(scraped_data.get("description", "")) > 500
            else scraped_data.get("description", ""),
            "status": scraped_data.get("status", "unknown"),
            "genres": scraped_data.get("genres", []),
            "total_chapters": scraped_data.get("total_chapters", 0),
            "total_volumes": scraped_data.get("total_volumes", 0),
            "content_type": scraped_data.get("content_type", "unknown"),
            "raw_status": scraped_data.get("raw_status", None),
            "cover_url": scraped_data.get("cover_url", None),
            "source_url": scraped_data.get("source_url", novelupdates_url),
            "rating": scraped_data.get("rating", "Not available"),
            "translation_status": scraped_data.get("translation_status", "Unknown"),
            "chapter_extraction_note": "Total chapters from Status in COO section (faster than individual chapter scraping)",
        }

        return preview

    finally:
        scraper.close()
