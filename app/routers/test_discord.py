from fastapi import APIRouter, HTTPException
from app.services.discord_webhook import send_test_embed, send_embed
from app.services.fetcher import Fetcher
from app.services.parser import Parser
from app.services.classifier import Classifier
from app.services.infographic_finder import InfographicFinder

router = APIRouter()

@router.post("/test-discord")
async def test_discord_webhook():
    try:
        await send_test_embed()
        return {"message": "Test embed sent to Discord"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview-latest-discord")
async def preview_latest_discord_embed():
    try:
        fetcher = Fetcher()
        posts = await fetcher.fetch_all_sources()
        if not posts:
            raise HTTPException(status_code=404, detail="No posts found")

        post = await fetcher.enrich_post_details(posts[0])
        post = Parser.parse_post(post)
        post['category'] = Classifier.classify_post(post, post.get('keywords', {}))
        infographic = await InfographicFinder().find_for_post(post)
        if infographic:
            post['official_image_url'] = post.get('image_url')
            post['image_url'] = infographic['image_url']
            post['infographic'] = infographic

        await send_embed(post)
        return {
            "message": "Latest post preview sent to Discord",
            "title": post['title'],
            "category": post['category'],
            "infographic": post.get('infographic'),
            "sections": post.get('sections', []),
            "highlights": post.get('highlights', [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview-infographics")
async def preview_infographics():
    try:
        posts = await InfographicFinder().fetch_recent_infographics()
        return {
            "count": len(posts),
            "items": [
                {
                    "title": post["title"],
                    "url": post["url"],
                    "image_url": post["image_url"],
                    "date": post.get("date"),
                    "author": post.get("infographic", {}).get("author"),
                    "score": post.get("infographic", {}).get("score"),
                }
                for post in posts[:20]
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview-latest-infographic-discord")
async def preview_latest_infographic_discord_embed():
    try:
        posts = await InfographicFinder().fetch_recent_infographics()
        if not posts:
            raise HTTPException(status_code=404, detail="No infographic posts found")

        post = posts[0]
        await send_embed(post)
        return {
            "message": "Latest infographic preview sent to Discord",
            "title": post["title"],
            "url": post["url"],
            "image_url": post["image_url"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
