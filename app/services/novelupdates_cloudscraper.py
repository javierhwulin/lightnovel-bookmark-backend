import re
import time
import json
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple, Union
from urllib.parse import urljoin, urlparse

import cloudscraper
from bs4 import BeautifulSoup

@dataclass
class ChapterInfo:
    title: str
    chapter_number: Union[int, float]
    source_url: str
    release_date: Optional[str] = None

class NovelUpdatesScraperError(Exception):
    """Custom exception for scraper errors"""
    pass

class NovelUpdatesCloudScraper:
    """Enhanced NovelUpdates scraper using cloudscraper to bypass Cloudflare protection"""
    
    def __init__(self, delay: int = 6):
        self.scraper = cloudscraper.create_scraper(delay=delay)
        self.base_url = "https://www.novelupdates.com"
        self.delay = delay



    def _extract_novel_info(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Extract basic novel information from a series page"""
        novel_info = {}
        
        # Extract title
        title_elem = soup.find("div", class_="seriestitlenu")
        if title_elem:
            novel_info['title'] = title_elem.get_text(strip=True)
        
        # Extract author from showauthors div
        authors_elem = soup.find("div", id="showauthors")
        if authors_elem:
            author_links = authors_elem.find_all("a", class_="genre", id="authtag")
            if author_links:
                authors = []
                for link in author_links:
                    author_name = link.get_text(strip=True)
                    if author_name:
                        authors.append(author_name)
                novel_info['author'] = " & ".join(authors) if authors else "Unknown Author"
            else:
                novel_info['author'] = "Unknown Author"
        else:
            novel_info['author'] = "Unknown Author"
        
        # Extract description
        desc_elem = soup.find("div", id="editdescription")
        if desc_elem:
            # Clean up description text
            desc_parts = []
            for element in desc_elem.children:
                if hasattr(element, 'get_text'):
                    text = element.get_text(strip=True)
                    if text:
                        desc_parts.append(text)
                elif isinstance(element, str):
                    text = element.strip()
                    if text and text != '\n':
                        desc_parts.append(text)
            
            novel_info['description'] = ' '.join(desc_parts)[:1000]  # Limit length
        
        # Extract genres
        genre_elem = soup.find("div", id="seriesgenre")
        if genre_elem:
            genres = []
            for genre_link in genre_elem.findAll("a"):
                if genre_link.string:
                    genres.append(genre_link.string.strip())
            novel_info['genres'] = genres
        
        # Extract rating
        rating_elem = soup.find("span", class_="uvotes")
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            novel_info['rating'] = rating_text.replace("(", "").replace(")", "")
        
        # Extract status and total chapters/volumes from editstatus div (Status in COO)
        status_elem = soup.find("div", id="editstatus")
        if status_elem:
            status_text = status_elem.get_text(strip=True)
            
            # Store the raw status text for the payload
            novel_info['raw_status'] = status_text
            
            # Extract total chapters from text like "355 Chapters (Completed)"
            import re
            chapter_match = re.search(r'(\d+)\s+chapters?', status_text, re.IGNORECASE)
            volume_match = re.search(r'(\d+)\s+volumes?', status_text, re.IGNORECASE)
            
            if chapter_match:
                novel_info['total_chapters'] = int(chapter_match.group(1))
                novel_info['content_type'] = 'chapters'
            elif volume_match:
                novel_info['total_volumes'] = int(volume_match.group(1))
                novel_info['total_chapters'] = 0  # No chapter count available
                novel_info['content_type'] = 'volumes'
            else:
                novel_info['total_chapters'] = 0
                novel_info['content_type'] = 'unknown'
            
            # Extract status from the same text
            status_text_lower = status_text.lower()
            if 'completed' in status_text_lower or 'complete' in status_text_lower:
                novel_info['status'] = 'completed'
            elif 'ongoing' in status_text_lower:
                novel_info['status'] = 'ongoing'
            elif 'hiatus' in status_text_lower:
                novel_info['status'] = 'hiatus'
            elif 'dropped' in status_text_lower:
                novel_info['status'] = 'dropped'
            else:
                novel_info['status'] = 'unknown'
        else:
            novel_info['total_chapters'] = 0
            novel_info['content_type'] = 'unknown'
            novel_info['status'] = 'unknown'
            novel_info['raw_status'] = None
        
        # Extract translation status
        trans_elem = soup.find("div", id="showtranslated")
        if trans_elem:
            trans_link = trans_elem.find('a')
            if trans_link:
                novel_info['translation_status'] = trans_link.get_text(strip=True)
            else:
                novel_info['translation_status'] = trans_elem.get_text(strip=True)
        
        # Extract cover image URL
        cover_img = None
        
        # Look for image with cover URL patterns
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            if src and ('cdn.novelupdates.com/images' in src or 'cover' in src.lower() or 'hardcover' in src.lower()):
                # Found a potential cover image
                if src.startswith('//'):
                    # Handle protocol-relative URLs
                    cover_img = 'https:' + src
                elif src.startswith('/'):
                    # Handle relative URLs
                    cover_img = urljoin(self.base_url, src)
                elif src.startswith('http'):
                    # Handle absolute URLs
                    cover_img = src
                break  # Take the first matching image
        
        novel_info['cover_url'] = cover_img
        
        return novel_info

    def _extract_chapters_from_page(self, soup: BeautifulSoup) -> List[ChapterInfo]:
        """Extract chapter information from a series page"""
        chapters = []
        
        # Look for the chapter table
        table = soup.find('table', id='myTable')
        if not table:
            return chapters
        
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue
            
            # Extract chapter link and title
            chapter_link = cells[0].find('a')
            if not chapter_link:
                continue
            
            chapter_title = chapter_link.get_text(strip=True)
            chapter_url = chapter_link.get('href', '')
            
            if not chapter_title or len(chapter_title) < 3:
                continue
            
            # Parse chapter number from title
            chapter_num = self._parse_chapter_number(chapter_title)
            clean_title = self._clean_chapter_title(chapter_title)
            
            # Extract release date
            release_date = None
            if len(cells) > 1:
                date_cell = cells[1]
                release_date = date_cell.get_text(strip=True)
            
            chapter_info = ChapterInfo(
                title=clean_title,
                chapter_number=chapter_num,
                source_url=chapter_url,
                release_date=release_date
            )
            
            chapters.append(chapter_info)
        
        return chapters

    def _parse_chapter_number(self, title: str) -> Union[int, float]:
        """Extract chapter number from title"""
        patterns = [
            r'c(\d+(?:\.\d+)?)',  # c123, c123.5
            r'ch\.?\s*(\d+(?:\.\d+)?)',  # ch 123, ch. 123.5
            r'chapter\s*(\d+(?:\.\d+)?)',  # chapter 123
            r'(\d+(?:\.\d+)?)(?:\s*-|\s*$)',  # 123, 123.5
        ]
        
        title_lower = title.lower()
        
        for pattern in patterns:
            match = re.search(pattern, title_lower)
            if match:
                num_str = match.group(1)
                try:
                    if '.' in num_str:
                        return float(num_str)
                    else:
                        return int(num_str)
                except ValueError:
                    continue
        
        return 1  # Default if no number found

    def _clean_chapter_title(self, title: str) -> str:
        """Clean chapter title by removing chapter numbers"""
        patterns = [
            r'^c\d+(?:\.\d+)?\s*[-:]?\s*',
            r'^ch\.?\s*\d+(?:\.\d+)?\s*[-:]?\s*',
            r'^chapter\s*\d+(?:\.\d+)?\s*[-:]?\s*',
            r'^\d+(?:\.\d+)?\s*[-:]?\s*',
        ]
        
        clean_title = title
        for pattern in patterns:
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
        
        clean_title = clean_title.strip()
        return clean_title or f"Chapter {self._parse_chapter_number(title)}"

    def scrape_novel_by_url(self, novel_url: str, scrape_chapters: bool = True) -> Dict:
        """
        Scrape complete novel information from a NovelUpdates URL
        
        Args:
            novel_url: Direct URL to the novel page
            scrape_chapters: Whether to scrape individual chapters (slower) or just get total count
            
        Returns:
            Dictionary with novel information and optionally chapters
        """
        try:
            # Ensure we have a full URL
            if not novel_url.startswith('http'):
                novel_url = urljoin(self.base_url, novel_url)
            
            # Get the main page
            response = self.scraper.get(novel_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract novel information (including total_chapters from status)
            novel_info = self._extract_novel_info(soup)
            novel_info['source_url'] = novel_url
            
            # Set defaults
            novel_info.setdefault('title', 'Unknown Title')
            novel_info.setdefault('description', 'No description available')
            novel_info.setdefault('genres', [])
            novel_info.setdefault('status', 'unknown')
            novel_info.setdefault('total_chapters', 0)
            novel_info.setdefault('total_volumes', 0)
            novel_info.setdefault('content_type', 'unknown')
            novel_info.setdefault('raw_status', None)
            novel_info.setdefault('cover_url', None)
            
            if scrape_chapters:
                # Extract chapters from the current page
                all_chapters = self._extract_chapters_from_page(soup)
                
                # Check for additional pages
                max_page = self._find_max_page(soup)
                
                # Scrape additional pages (limit to first 5 pages for performance)
                max_page = min(max_page, 5)
                
                for page in range(2, max_page + 1):
                    try:
                        page_url = f"{novel_url}?pg={page}"
                        page_response = self.scraper.get(page_url)
                        page_response.raise_for_status()
                        
                        page_soup = BeautifulSoup(page_response.content, "html.parser")
                        page_chapters = self._extract_chapters_from_page(page_soup)
                        all_chapters.extend(page_chapters)
                        
                        # Add delay to be respectful
                        time.sleep(self.delay / 2)
                        
                    except Exception as e:
                        print(f"Warning: Failed to scrape page {page}: {str(e)}")
                        break
                
                # Sort chapters by number
                all_chapters.sort(key=lambda x: x.chapter_number)
                
                novel_info['chapters'] = all_chapters
                # Update total_chapters with actual scraped count if we have chapters
                if all_chapters:
                    novel_info['total_chapters'] = len(all_chapters)
            else:
                # Just provide empty chapters list, use total_chapters from status
                novel_info['chapters'] = []
            
            return novel_info
            
        except Exception as e:
            raise NovelUpdatesScraperError(f"Failed to scrape novel: {str(e)}")

    def _find_max_page(self, soup: BeautifulSoup) -> int:
        """Find the maximum page number for pagination"""
        max_page = 1
        
        # Look for pagination links
        page_links = soup.find_all('a', href=lambda x: x and 'pg=' in x)
        
        for link in page_links:
            href = link.get('href', '')
            page_match = re.search(r'pg=(\d+)', href)
            if page_match:
                page_num = int(page_match.group(1))
                max_page = max(max_page, page_num)
        
        return max_page



    def close(self):
        """Close the scraper session"""
        # cloudscraper doesn't need explicit closing
        pass 