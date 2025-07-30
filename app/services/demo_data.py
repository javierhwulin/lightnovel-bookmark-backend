from sqlalchemy.orm import Session
import json
from app.models.novel import LightNovel, Chapter


def create_demo_slime_novel(db: Session) -> LightNovel:
    """
    Create demo data for 'That Time I Got Reincarnated as a Slime'
    mimicking what would be scraped from NovelUpdates with proper author extraction
    """

    # Check if novel already exists
    existing_novel = (
        db.query(LightNovel)
        .filter(LightNovel.title == "Tensei Shitara Slime Datta Ken (WN)")
        .first()
    )

    if existing_novel:
        return existing_novel

    # Create the novel with multiple authors as would be extracted from showauthors div
    genres = ["Action", "Adventure", "Comedy", "Fantasy", "Shounen"]

    db_novel = LightNovel(
        title="Tensei Shitara Slime Datta Ken (WN)",
        author="Fuse & 伏瀬",  # Multiple authors as extracted from showauthors div
        description="A man is stabbed by a robber on the run after pushing his coworker and his coworker's new fiance out of the way. As he lays dying, bleeding on the ground, he hears a voice. This voice is strange and interprets his dying regret of being a virgin by giving him the [Great Sage] unique skill! Is he being made fun of? !",
        status="ongoing",
        genres=json.dumps(genres),
        source_url="https://www.novelupdates.com/series/tensei-shitara-slime-datta-ken/",
        cover_url=None,
    )

    db.add(db_novel)
    db.flush()

    # Create chapters directly under the novel
    sample_chapters = [
        {"ch": 1, "title": "The Dragon Veldora", "url": "https://example.com/ch1"},
        {
            "ch": 2,
            "title": "Coexistence with Monsters",
            "url": "https://example.com/ch2",
        },
        {
            "ch": 3,
            "title": "Battle with the Direwolves",
            "url": "https://example.com/ch3",
        },
        {"ch": 4, "title": "Orc Lord", "url": "https://example.com/ch4"},
        {"ch": 5, "title": "The Meeting", "url": "https://example.com/ch5"},
        {"ch": 6, "title": "The Dwarf Kingdom", "url": "https://example.com/ch6"},
        {
            "ch": 7,
            "title": "Kaijin and the Magistrate",
            "url": "https://example.com/ch7",
        },
        {"ch": 8, "title": "Flames of War", "url": "https://example.com/ch8"},
        {"ch": 9, "title": "The Orc Disaster", "url": "https://example.com/ch9"},
        {"ch": 10, "title": "Harvest Festival", "url": "https://example.com/ch10"},
        {"ch": 11, "title": "The Demon Lord", "url": "https://example.com/ch11"},
        {"ch": 12, "title": "Walpurgis", "url": "https://example.com/ch12"},
        {"ch": 13, "title": "The Eastern Empire", "url": "https://example.com/ch13"},
        {"ch": 14, "title": "The Masked Hero", "url": "https://example.com/ch14"},
        {"ch": 15, "title": "Return to Jura", "url": "https://example.com/ch15"},
        {"ch": 16, "title": "Tempest's Growth", "url": "https://example.com/ch16"},
        {"ch": 17, "title": "New Allies", "url": "https://example.com/ch17"},
        {"ch": 18, "title": "The Sky Dragon", "url": "https://example.com/ch18"},
        {"ch": 19, "title": "Ancient Secrets", "url": "https://example.com/ch19"},
        {"ch": 20, "title": "Evolution", "url": "https://example.com/ch20"},
    ]

    # Create chapters
    for chapter_data in sample_chapters:
        db_chapter = Chapter(
            novel_id=db_novel.id,
            number=chapter_data["ch"],
            title=chapter_data["title"],
            source_url=chapter_data["url"],
        )
        db.add(db_chapter)

    db.commit()
    db.refresh(db_novel)

    return db_novel


def create_demo_overlord_novel(db: Session) -> LightNovel:
    """Create demo data for Overlord to showcase multiple novels with proper author extraction"""

    existing_novel = (
        db.query(LightNovel).filter(LightNovel.title == "Overlord (LN)").first()
    )

    if existing_novel:
        return existing_novel

    genres = ["Action", "Adventure", "Drama", "Fantasy", "Supernatural", "Seinen"]

    db_novel = LightNovel(
        title="Overlord (LN)",
        author="Kugane Maruyama",  # Single author as would be extracted
        description="The story begins with Yggdrasil, a popular online game which is quietly shut down one day. However, the protagonist Momonga decides not to log out. Momonga is then transformed into the image of a skeleton as 'the most powerful wizard.' The world continues to change, with non-player characters (NPCs) beginning to feel emotion.",
        status="ongoing",
        genres=json.dumps(genres),
        source_url="https://www.novelupdates.com/series/overlord/",
        cover_url=None,
    )

    db.add(db_novel)
    db.flush()

    # Create some sample chapters
    sample_chapters = [
        {
            "ch": 1,
            "title": "The End and the Beginning",
            "url": "https://example.com/overlord-ch1",
        },
        {
            "ch": 2,
            "title": "Floor Guardians",
            "url": "https://example.com/overlord-ch2",
        },
        {
            "ch": 3,
            "title": "Battle of Carne Village",
            "url": "https://example.com/overlord-ch3",
        },
        {"ch": 4, "title": "Ruler of Death", "url": "https://example.com/overlord-ch4"},
        {
            "ch": 5,
            "title": "Two Adventurers",
            "url": "https://example.com/overlord-ch5",
        },
        {"ch": 6, "title": "Journey", "url": "https://example.com/overlord-ch6"},
        {
            "ch": 7,
            "title": "Wise King of the Forest",
            "url": "https://example.com/overlord-ch7",
        },
        {"ch": 8, "title": "Twin Swords", "url": "https://example.com/overlord-ch8"},
        {"ch": 9, "title": "Dark Warrior", "url": "https://example.com/overlord-ch9"},
        {
            "ch": 10,
            "title": "The Bloody Valkyrie",
            "url": "https://example.com/overlord-ch10",
        },
    ]

    # Create chapters
    for chapter_data in sample_chapters:
        db_chapter = Chapter(
            novel_id=db_novel.id,
            number=chapter_data["ch"],
            title=chapter_data["title"],
            source_url=chapter_data["url"],
        )
        db.add(db_chapter)

    db.commit()
    db.refresh(db_novel)

    return db_novel
