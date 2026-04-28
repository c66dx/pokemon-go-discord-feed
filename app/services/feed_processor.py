from app.services.fetcher import Fetcher
from app.services.parser import Parser
from app.services.classifier import Classifier
from app.services.discord_webhook import send_embed
from app.services.infographic_finder import InfographicFinder
from app.repositories.post_repository import PostRepository
from app.core.database import async_session
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def process_feeds(notify: bool = True, seed_if_empty: bool = True) -> dict:
    logger.info("Starting feed processing...")
    fetcher = Fetcher()
    infographic_finder = InfographicFinder()
    posts = await fetcher.fetch_all_sources()
    infographic_posts = await infographic_finder.fetch_recent_infographics()
    posts.extend(infographic_posts)
    stats = {"fetched": len(posts), "saved": 0, "notified": 0, "skipped": 0}

    async with async_session() as db:
        repo = PostRepository(db)
        should_notify = notify
        if seed_if_empty and await repo.count_posts() == 0:
            should_notify = False
            logger.info("No existing posts found; seeding current feed without Discord notifications.")

        for post in posts:
            if await repo.is_post_exists(post['url']):
                stats["skipped"] += 1
                continue

            if should_notify:
                post = await fetcher.enrich_post_details(post)

            parsed_post = Parser.parse_post(post)
            keywords = post.get('keywords', {})
            category = post.get('category') or Classifier.classify_post(parsed_post, keywords)
            parsed_post['category'] = category
            if should_notify and not parsed_post.get('infographic'):
                infographic = await infographic_finder.find_for_post(parsed_post)
                if infographic:
                    parsed_post['official_image_url'] = parsed_post.get('image_url')
                    parsed_post['image_url'] = infographic['image_url']
                    parsed_post['infographic'] = infographic

            await repo.save_post(parsed_post)
            stats["saved"] += 1

            if should_notify:
                try:
                    await send_embed(parsed_post)
                    stats["notified"] += 1
                except Exception as exc:
                    logger.warning("Discord webhook failed for %s: %s", parsed_post['url'], exc)
                logger.info(f"Posted: {parsed_post['title']}")
            else:
                logger.info(f"Seeded without notification: {parsed_post['title']}")

    logger.info("Feed processing completed.")
    return stats

async def publish_recent_infographics(
    days: int = 14,
    limit: int = 10,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    infographic_finder = InfographicFinder()
    cutoff = datetime.utcnow() - timedelta(days=days)
    posts = [
        post
        for post in await infographic_finder.fetch_recent_infographics()
        if post.get('date') and post['date'] >= cutoff
    ][:limit]

    stats = {
        "found": len(posts),
        "published": 0,
        "saved": 0,
        "skipped": 0,
        "dry_run": dry_run,
        "items": [],
    }

    async with async_session() as db:
        repo = PostRepository(db)
        for post in posts:
            exists = await repo.is_post_exists(post['url'])
            item = {
                "title": post['title'],
                "url": post['url'],
                "image_url": post.get('image_url'),
                "date": post.get('date'),
                "already_saved": exists,
            }

            if exists and not force:
                stats["skipped"] += 1
                item["action"] = "skipped_existing"
                stats["items"].append(item)
                continue

            if dry_run:
                item["action"] = "would_publish"
                stats["items"].append(item)
                continue

            try:
                await send_embed(post)
                stats["published"] += 1
                item["action"] = "published"
            except Exception as exc:
                logger.warning("Discord webhook failed for infographic %s: %s", post['url'], exc)
                item["action"] = "failed"
                item["error"] = str(exc)
                stats["items"].append(item)
                continue

            if not exists:
                await repo.save_post(post)
                stats["saved"] += 1

            stats["items"].append(item)

    return stats
