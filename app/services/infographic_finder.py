import html
import logging
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import quote_plus, urljoin

import httpx

logger = logging.getLogger(__name__)


class InfographicFinder:
    REDDIT_SEARCH_URL = "https://www.reddit.com/r/TheSilphRoad/search.json"
    IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
    INFOGRAPHIC_TERMS = ("g47ix", "g47onik", "infographic", "guide")

    async def find_for_post(self, post: Dict) -> Optional[Dict]:
        queries = self.build_queries(post)
        for query in queries:
            match = await self.search_reddit(query)
            if match:
                return match
        return None

    async def fetch_recent_infographics(self) -> list[Dict]:
        posts_by_url = {}
        for query in ("G47IX", "g47onik", "infographic pokemon go", '"Infographic - Event"'):
            for post in await self.search_reddit_posts(query, limit=25):
                image_url = self.extract_image_url(post)
                if not image_url or not self.is_infographic_candidate(post):
                    continue

                reddit_url = urljoin("https://www.reddit.com", post.get("permalink", ""))
                posts_by_url[reddit_url] = {
                    "title": post.get("title", "Pokemon GO infographic"),
                    "url": reddit_url,
                    "date": self.datetime_from_utc(post.get("created_utc")),
                    "image_url": image_url,
                    "summary": self.build_infographic_summary(post),
                    "source": "Reddit / r/TheSilphRoad",
                    "category": "INFOGRAFIA",
                    "infographic": {
                        "image_url": image_url,
                        "title": post.get("title", ""),
                        "source": "Reddit / r/TheSilphRoad",
                        "author": post.get("author"),
                        "url": reddit_url,
                        "score": post.get("score", 0),
                        "created_utc": post.get("created_utc"),
                    },
                    "keywords": {},
                }

        return sorted(
            posts_by_url.values(),
            key=lambda item: item.get("date") or datetime.min,
            reverse=True,
        )

    def build_queries(self, post: Dict) -> list[str]:
        title = post.get("title", "")
        keywords = self.extract_keywords(title)
        queries = []

        if keywords:
            queries.append(" ".join(keywords[:5] + ["G47IX"]))
            queries.append(" ".join(keywords[:5] + ["infographic"]))
            queries.append(" ".join(keywords[:4]))

        if post.get("category") in {"RAID", "EVENTO", "COMMUNITY_DAY"}:
            queries.append(f"{post['category']} G47IX")

        return list(dict.fromkeys(query for query in queries if query.strip()))

    def extract_keywords(self, title: str) -> list[str]:
        normalized_title = unicodedata.normalize("NFKD", title)
        normalized_title = normalized_title.encode("ascii", "ignore").decode("ascii")
        words = re.findall(r"[A-Za-z0-9]+", normalized_title.lower())
        stopwords = {
            "and", "the", "for", "with", "more", "during", "pokemon",
            "go", "your", "into", "from", "this", "that", "are", "you", "will",
            "a", "an", "to", "of", "in", "on", "at", "is",
        }
        return [word for word in words if len(word) > 2 and word not in stopwords]

    async def search_reddit(self, query: str) -> Optional[Dict]:
        candidates = await self.search_reddit_posts(query, limit=10)

        for candidate in sorted(candidates, key=self.score_candidate, reverse=True):
            image_url = self.extract_image_url(candidate)
            if image_url and self.is_infographic_candidate(candidate):
                return {
                    "image_url": image_url,
                    "title": candidate.get("title", ""),
                    "source": "Reddit / r/TheSilphRoad",
                    "author": candidate.get("author"),
                    "url": urljoin("https://www.reddit.com", candidate.get("permalink", "")),
                    "score": candidate.get("score", 0),
                    "created_utc": candidate.get("created_utc"),
                }

        return None

    async def search_reddit_posts(self, query: str, limit: int = 10) -> list[Dict]:
        params = f"?q={quote_plus(query)}&restrict_sr=1&sort=new&t=month&limit={limit}"
        headers = {"User-Agent": "PokemonGoDiscordFeed/1.0"}

        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=12.0) as client:
            try:
                response = await client.get(f"{self.REDDIT_SEARCH_URL}{params}")
                response.raise_for_status()
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning("Reddit infographic search failed for %r: %s", query, exc)
                return []

        data = response.json()
        return [
            child.get("data", {})
            for child in data.get("data", {}).get("children", [])
        ]

    def score_candidate(self, candidate: Dict) -> int:
        text = " ".join(
            str(candidate.get(field, ""))
            for field in ("title", "link_flair_text", "author", "author_flair_text")
        ).lower()

        score = 0
        if any(term in text for term in self.INFOGRAPHIC_TERMS):
            score += 5
        if "infographic" in text:
            score += 4
        if candidate.get("post_hint") == "image":
            score += 3
        if candidate.get("domain") in {"i.redd.it", "preview.redd.it"}:
            score += 3
        if candidate.get("over_18"):
            score -= 20

        created_utc = candidate.get("created_utc")
        if created_utc:
            created_at = datetime.utcfromtimestamp(created_utc)
            if created_at >= datetime.utcnow() - timedelta(days=3):
                score += 2

        return score

    def is_infographic_candidate(self, candidate: Dict) -> bool:
        text = " ".join(
            str(candidate.get(field, ""))
            for field in ("title", "link_flair_text", "author", "author_flair_text")
        ).lower()
        return any(term in text for term in self.INFOGRAPHIC_TERMS)

    def extract_image_url(self, candidate: Dict) -> Optional[str]:
        direct_url = candidate.get("url_overridden_by_dest") or candidate.get("url")
        if direct_url and self.is_image_url(direct_url):
            return direct_url

        images = candidate.get("preview", {}).get("images", [])
        if images:
            source_url = images[0].get("source", {}).get("url")
            if source_url:
                return html.unescape(source_url)

        return None

    def is_image_url(self, value: str) -> bool:
        clean_value = value.lower().split("?")[0]
        return clean_value.endswith(self.IMAGE_EXTENSIONS)

    def datetime_from_utc(self, value) -> Optional[datetime]:
        if not value:
            return None
        return datetime.utcfromtimestamp(value)

    def build_infographic_summary(self, post: Dict) -> str:
        author = post.get("author", "unknown")
        flair = post.get("link_flair_text")
        score = post.get("score", 0)
        parts = [f"Infografia publicada en r/TheSilphRoad por {author}."]
        if flair:
            parts.append(f"Tipo: {flair}.")
        parts.append(f"Score en Reddit: {score}.")
        return " ".join(parts)
