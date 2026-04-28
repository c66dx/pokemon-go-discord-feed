from fastapi import APIRouter, HTTPException, Query
from app.services.feed_processor import process_feeds, publish_recent_infographics

router = APIRouter()

@router.post("/sync-feeds")
async def sync_feeds():
    try:
        stats = await process_feeds()
        return {"message": "Feed sync completed", **stats}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/seed-feeds")
async def seed_feeds():
    try:
        stats = await process_feeds(notify=False, seed_if_empty=False)
        return {"message": "Feed seed completed without Discord notifications", **stats}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/publish-recent-infographics")
async def publish_recent_infographics_endpoint(
    days: int = Query(default=14, ge=1, le=60),
    limit: int = Query(default=10, ge=1, le=25),
    dry_run: bool = False,
    force: bool = False,
):
    try:
        stats = await publish_recent_infographics(
            days=days,
            limit=limit,
            dry_run=dry_run,
            force=force,
        )
        return {"message": "Recent infographic publish completed", **stats}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
