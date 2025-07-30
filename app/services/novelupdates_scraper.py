import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Tuple
from urllib.parse import urljoin, urlparse
import time
import random
from dataclasses import dataclass

@dataclass
class ChapterInfo:
    title: str
    chapter_number: int
    volume_number: Optional[int]
    release_date: Optional[str]
    source_url: str

@dataclass
class VolumeInfo:
    volume_number: int
    title: str
    chapters: List[ChapterInfo]

class NovelUpdatesScraperError(Exception):
    """Custom exception for scraper errors"""
    pass

class NovelUpdatesScraper:
    """Enhanced scraper for NovelUpdates.com with anti-bot protection bypass"""
    
    def __init__(self, delay_between_requests: float = 2.0):
        self.session = requests.Session()
        
        # More realistic headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        self.delay = delay_between_requests
        self.base_url = "https://www.novelupdates.com"
        self._setup_session()

    def _setup_session(self):
        """Initialize session by visiting the homepage first"""
        try:
            # Visit homepage to get cookies and establish session
            homepage_response = self.session.get(self.base_url, timeout=15)
            if homepage_response.status_code == 200:
                # Update referer for subsequent requests
                self.session.headers.update({'Referer': self.base_url})
        except requests.RequestException:
            # If homepage fails, continue anyway
            pass

    def _make_request(self, url: str, retries: int = 3) -> BeautifulSoup:
        """Make a request with error handling, rate limiting, and retries"""
        for attempt in range(retries):
            try:
                # Add random delay to appear more human-like
                delay = self.delay + random.uniform(0.5, 1.5)
                time.sleep(delay)
                
                # Update referer to the current page
                if hasattr(self, '_last_url'):
                    self.session.headers.update({'Referer': self._last_url})
                
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 403:
                    if attempt < retries - 1:
                        # Exponential backoff on 403
                        time.sleep((attempt + 1) * 5)
                        continue
                    else:
                        raise NovelUpdatesScraperError(f"Access denied (403) after {retries} attempts. NovelUpdates may be blocking automated requests.")
                
                response.raise_for_status()
                self._last_url = url
                
                return BeautifulSoup(response.content, 'lxml')
                
            except requests.RequestException as e:
                if attempt < retries - 1:
                    time.sleep((attempt + 1) * 2)
                    continue
                else:
                    raise NovelUpdatesScraperError(f"Failed to fetch {url} after {retries} attempts: {str(e)}")

    def _extract_novel_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract basic novel information from the series page"""
        novel_info = {}
        
        # Extract title - try multiple selectors
        title_selectors = [
            'h4.seriestitle',
            '.seriestitle',
            'h1.entry-title',
            '.entry-title',
            'h1'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                novel_info['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract author - try multiple approaches
        author_selectors = [
            'a[href*="/nauthor/"]',
            '.author a',
            '.series-author a'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                novel_info['author'] = author_elem.get_text(strip=True)
                break
        
        # Extract description
        desc_selectors = [
            '#editdescription',
            '.description',
            '.series-description',
            '.entry-content'
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                # Clean up the description
                desc_text = desc_elem.get_text(strip=True)
                # Remove common NovelUpdates specific text
                desc_text = re.sub(r'Show more.*$', '', desc_text, flags=re.IGNORECASE)
                novel_info['description'] = desc_text[:1000]  # Limit length
                break
        
        # Extract status
        status_selectors = [
            '.seriesstat',
            '.series-status',
            '.status'
        ]
        
        for selector in status_selectors:
            status_elem = soup.select_one(selector)
            if status_elem:
                status_text = status_elem.get_text(strip=True).lower()
                if 'complete' in status_text:
                    novel_info['status'] = 'completed'
                elif 'ongoing' in status_text:
                    novel_info['status'] = 'ongoing'
                else:
                    novel_info['status'] = 'unknown'
                break
        
        # Extract genres
        genre_selectors = [
            'a[href*="/genre/"]',
            '.genre a',
            '.series-genre a'
        ]
        
        for selector in genre_selectors:
            genre_elements = soup.select(selector)
            if genre_elements:
                novel_info['genres'] = [elem.get_text(strip=True) for elem in genre_elements]
                break
        
        return novel_info

    def _parse_chapter_title(self, title: str) -> Tuple[Optional[int], int, str]:
        """Parse chapter title to extract volume number, chapter number, and clean title"""
        # Common patterns for volume and chapter numbering
        patterns = [
            r'v(\d+)c(\d+(?:\.\d+)?)',  # v1c1, v1c1.5
            r'volume\s*(\d+)\s*chapter\s*(\d+(?:\.\d+)?)',  # Volume 1 Chapter 1
            r'vol\.?\s*(\d+)\s*ch\.?\s*(\d+(?:\.\d+)?)',  # Vol. 1 Ch. 1
            r'chapter\s*(\d+(?:\.\d+)?)',  # Chapter 1 (no volume)
            r'c(\d+(?:\.\d+)?)',  # c1, c1.5
        ]
        
        volume_num = None
        chapter_num = 1
        clean_title = title
        
        title_lower = title.lower()
        
        for pattern in patterns:
            match = re.search(pattern, title_lower)
            if match:
                if len(match.groups()) == 2:  # Volume and chapter
                    volume_num = int(match.group(1))
                    chapter_num = float(match.group(2))
                elif len(match.groups()) == 1:  # Only chapter
                    chapter_num = float(match.group(1))
                
                # Remove the matched pattern from title
                clean_title = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
                clean_title = re.sub(r'^[-\s:]+|[-\s:]+$', '', clean_title)  # Clean up dashes, spaces, colons
                break
        
        # Convert float chapter number to int if it's a whole number
        if isinstance(chapter_num, float) and chapter_num.is_integer():
            chapter_num = int(chapter_num)
        
        return volume_num, chapter_num, clean_title or f"Chapter {chapter_num}"

    def _extract_chapters_from_table(self, soup: BeautifulSoup) -> List[ChapterInfo]:
        """Extract chapter information from the releases table"""
        chapters = []
        
        # Look for the chapter table with various selectors
        table_selectors = [
            'table#myTable',
            'table.tablesorter',
            '.chapter-table table',
            'table'
        ]
        
        table = None
        for selector in table_selectors:
            table = soup.select_one(selector)
            if table:
                break
        
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
            
            # Skip if this is not actually a chapter (sometimes there are other links)
            if not chapter_title or len(chapter_title) < 3:
                continue
            
            # Parse volume and chapter numbers from title
            volume_num, chapter_num, clean_title = self._parse_chapter_title(chapter_title)
            
            # Extract release date
            date_cell = cells[1] if len(cells) > 1 else None
            release_date = date_cell.get_text(strip=True) if date_cell else None
            
            chapter_info = ChapterInfo(
                title=clean_title,
                chapter_number=chapter_num,
                volume_number=volume_num,
                release_date=release_date,
                source_url=chapter_url
            )
            
            chapters.append(chapter_info)
        
        return chapters

    def scrape_novel(self, novel_url: str) -> Dict:
        """Scrape a complete novel from NovelUpdates"""
        if not novel_url.startswith('http'):
            novel_url = urljoin(self.base_url, novel_url)
        
        # Parse URL to get series identifier  
        parsed_url = urlparse(novel_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        # Remove page parameter and fragment for consistency
        if '?' in base_url:
            base_url = base_url.split('?')[0]
        
        soup = self._make_request(novel_url)
        
        # Extract novel information
        novel_info = self._extract_novel_info(soup)
        novel_info['source_url'] = base_url
        
        # Set defaults if extraction failed
        if 'title' not in novel_info:
            novel_info['title'] = 'Unknown Title'
        if 'author' not in novel_info:
            novel_info['author'] = 'Unknown Author'
        if 'description' not in novel_info:
            novel_info['description'] = 'No description available'
        if 'status' not in novel_info:
            novel_info['status'] = 'unknown'
        if 'genres' not in novel_info:
            novel_info['genres'] = []
        
        # Extract chapters from first page
        all_chapters = self._extract_chapters_from_table(soup)
        
        # Check if there are multiple pages
        page_links = soup.find_all('a', href=lambda x: x and 'pg=' in x)
        max_page = 1
        
        for link in page_links:
            href = link.get('href', '')
            page_match = re.search(r'pg=(\d+)', href)
            if page_match:
                page_num = int(page_match.group(1))
                max_page = max(max_page, page_num)
        
        # Limit to first 5 pages for initial testing
        max_page = min(max_page, 5)
        
        # Scrape additional pages if they exist
        for page in range(2, max_page + 1):
            page_url = f"{base_url}?pg={page}#myTable"
            try:
                page_soup = self._make_request(page_url)
                page_chapters = self._extract_chapters_from_table(page_soup)
                all_chapters.extend(page_chapters)
            except NovelUpdatesScraperError as e:
                print(f"Warning: Failed to scrape page {page}: {e}")
                break  # Stop on first failure to avoid getting blocked
        
        # Organize chapters by volume
        volumes_dict = {}
        
        for chapter in all_chapters:
            vol_num = chapter.volume_number or 1  # Default to volume 1 if not specified
            
            if vol_num not in volumes_dict:
                volumes_dict[vol_num] = VolumeInfo(
                    volume_number=vol_num,
                    title=f"Volume {vol_num}",
                    chapters=[]
                )
            
            volumes_dict[vol_num].chapters.append(chapter)
        
        # Sort volumes and chapters
        volumes = list(volumes_dict.values())
        volumes.sort(key=lambda v: v.volume_number)
        
        for volume in volumes:
            volume.chapters.sort(key=lambda c: c.chapter_number)
        
        novel_info['volumes'] = volumes
        novel_info['total_chapters'] = len(all_chapters)
        
        return novel_info

    def close(self):
        """Close the session"""
        self.session.close() 