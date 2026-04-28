import httpx
import feedparser
from bs4 import BeautifulSoup
import yaml
import logging
import re
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class Fetcher:
    def __init__(self):
        self.sources = self.load_sources()

    def load_sources(self) -> List[Dict]:
        config_path = Path(__file__).parent.parent.parent / "config" / "sources.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('sources', [])

    async def fetch_source(self, source: Dict) -> List[Dict]:
        posts = []
        if source['type'] == 'rss':
            posts = await self.fetch_rss(source)
        elif source['type'] == 'html':
            posts = await self.fetch_html(source)
        else:
            logger.warning("Source type %s not supported for %s", source.get('type'), source.get('name'))

        for post in posts:
            post['keywords'] = source.get('category_keywords', {})
        return posts

    async def fetch_rss(self, source: Dict) -> List[Dict]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PokemonGoFeed/1.0"}
        async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
            try:
                response = await client.get(source['url'], timeout=15.0)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.warning("RSS source %s returned HTTP %s", source['url'], exc.response.status_code)
                return []
            except httpx.RequestError as exc:
                logger.warning("RSS source %s request failed: %s", source['url'], exc)
                return []

            feed = feedparser.parse(response.text)
            posts = []
            for entry in feed.entries:
                published = None
                if getattr(entry, 'published_parsed', None):
                    published = datetime(*entry.published_parsed[:6])
                elif 'published' in entry:
                    published = entry.published
                post = {
                    'title': getattr(entry, 'title', '') or '',
                    'url': getattr(entry, 'link', '') or '',
                    'date': published,
                    'summary': getattr(entry, 'summary', '') or None,
                    'source': source['name']
                }
                posts.append(post)
            return posts

    async def fetch_html(self, source: Dict) -> List[Dict]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PokemonGoFeed/1.0"}
        async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
            try:
                response = await client.get(source['url'], timeout=15.0)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.warning("HTML source %s returned HTTP %s", source['url'], exc.response.status_code)
                return []
            except httpx.RequestError as exc:
                logger.warning("HTML source %s request failed: %s", source['url'], exc)
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select(source['selector'])
            posts = []
            
            for item in items:
                raw_url = self.extract_url(item, source.get('url_selector'))
                url = urljoin(source['url'], raw_url) if raw_url else ''

                date_value = self.extract_date(item)

                # Get all direct children that have text
                all_text = item.get_text(separator='|', strip=True)
                parts = [p.strip() for p in all_text.split('|') if p.strip()]
                
                # Typically: [date, title, ...]
                date_str = None
                title_str = None
                
                if len(parts) >= 2:
                    # Heuristic: first part looks like a date if it contains numbers/month names
                    first_part = parts[0]
                    if any(char.isdigit() for char in first_part) and len(first_part) < 50:
                        date_str = first_part
                        title_str = parts[1]
                    else:
                        title_str = first_part
                elif len(parts) == 1:
                    title_str = parts[0]

                if date_value is None and date_str:
                    date_value = date_str

                # Try to extract additional fields
                image = self.extract_image(item, source.get('image_selector'))
                image = urljoin(source['url'], image) if image else None
                summary = self.extract_text(item, source.get('summary_selector'))

                post = {
                    'title': title_str or '',
                    'url': url,
                    'date': date_value,
                    'image_url': image,
                    'summary': summary or title_str,
                    'source': source['name']
                }
                if post['url']:  # Only add if we have a URL
                    posts.append(post)
            return posts

    def extract_text(self, item, selector: Optional[str]) -> Optional[str]:
        if not selector:
            return item.get_text(separator=' ', strip=True)
        element = item.select_one(selector)
        return element.get_text(strip=True) if element else None

    def extract_url(self, item, selector: Optional[str]) -> str:
        if selector:
            element = item.select_one(selector)
        else:
            element = item if item.name == 'a' else None
        if element and element.has_attr('href'):
            return element['href']
        return ''

    def extract_image(self, item, selector: Optional[str]) -> Optional[str]:
        element = item.select_one(selector) if selector else item.select_one('img')
        if element and element.has_attr('src'):
            return element['src']
        return None

    def extract_date(self, item) -> Optional[datetime]:
        element = item.select_one('pg-date-format[timestamp]')
        if not element:
            return None

        try:
            timestamp_ms = int(element['timestamp'])
        except (TypeError, ValueError):
            return None

        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).replace(tzinfo=None)

    def extract_date_title(self, text: str) -> Tuple[Optional[str], str]:
        """Extract date from combined text like 'Apr 27, 2026 Title here'"""
        if not text:
            return None, text

        text = text.strip()
        # Try patterns for English and Spanish dates
        patterns = [
            r'^([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})\s+(.+)$',  # Apr 27, 2026 Title
            r'^(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\s+(.+)$',   # 27 abr 2026 Title
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 4:
                    # English: Apr 27, 2026 Title
                    month, day, year, title = match.groups()
                    date_str = f"{month} {day}, {year}"
                    return date_str, title.strip()
        
        # If no date pattern found, return None as date and full text as title
        return None, text

    async def fetch_all_sources(self) -> List[Dict]:
        all_posts = []
        for source in self.sources:
            posts = await self.fetch_source(source)
            all_posts.extend(posts)
        return all_posts

    async def enrich_post_details(self, post: Dict) -> Dict:
        url = post.get('url')
        if not url:
            return post

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PokemonGoFeed/1.0"}
        async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
            try:
                response = await client.get(url, timeout=15.0)
                response.raise_for_status()
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning("Could not enrich post %s: %s", url, exc)
                return post

        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.select_one('article') or soup

        metadata = self.extract_article_metadata(soup)
        paragraphs = self.extract_article_paragraphs(article)
        sections = self.extract_article_sections(article)
        highlights = self.extract_article_highlights(article)

        enriched = post.copy()
        if metadata.get('image'):
            enriched['image_url'] = metadata['image']
        if metadata.get('date_published') and not enriched.get('date'):
            enriched['date'] = metadata['date_published']
        if metadata.get('date_modified'):
            enriched['date_modified'] = metadata['date_modified']

        if paragraphs:
            enriched['summary'] = ' '.join(paragraphs[:2])
            enriched['article_preview'] = paragraphs[:4]
        if sections:
            enriched['sections'] = sections[:6]
        if highlights:
            enriched['highlights'] = highlights[:5]

        return enriched

    def extract_article_metadata(self, soup) -> Dict:
        metadata = {}
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or '{}')
            except json.JSONDecodeError:
                continue

            if isinstance(data, dict) and data.get('@type') in {'NewsArticle', 'Article', 'BlogPosting'}:
                metadata['image'] = data.get('image')
                metadata['date_published'] = ParserCompat.parse_datetime(data.get('datePublished'))
                metadata['date_modified'] = ParserCompat.parse_datetime(data.get('dateModified'))
                return metadata

        image = soup.select_one('meta[property="og:image"]')
        if image and image.has_attr('content'):
            metadata['image'] = image['content']
        return metadata

    def extract_article_paragraphs(self, article) -> List[str]:
        paragraphs = []
        for element in article.select('p'):
            text = self.clean_article_text(element.get_text(' ', strip=True))
            if len(text) >= 25 and text not in paragraphs:
                paragraphs.append(text)
        return paragraphs

    def extract_article_sections(self, article) -> List[str]:
        sections = []
        for element in article.select('h2, h3'):
            text = self.clean_article_text(element.get_text(' ', strip=True))
            if text and text not in sections:
                sections.append(text)
        return sections

    def extract_article_highlights(self, article) -> List[str]:
        highlights = []
        for element in article.select('li'):
            text = self.clean_article_text(element.get_text(' ', strip=True))
            if 20 <= len(text) <= 220 and text not in highlights:
                highlights.append(text)
        return highlights

    def clean_article_text(self, value: str) -> str:
        return re.sub(r'\s+', ' ', value).strip()


class ParserCompat:
    @staticmethod
    def parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        normalized = value.replace('Z', '+00:00')
        try:
            return datetime.fromisoformat(normalized).replace(tzinfo=None)
        except ValueError:
            return None
