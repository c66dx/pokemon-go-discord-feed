from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.services.feed_processor import process_feeds

scheduler = AsyncIOScheduler()


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        process_feeds,
        trigger=IntervalTrigger(minutes=settings.check_interval_minutes),
        id="check_feeds",
        name="Check Pokemon GO feeds",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
