#!/usr/bin/env python
"""Test script to verify feed synchronization works correctly."""
import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())

# Set UTF-8 encoding
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.services.fetcher import Fetcher
from app.services.parser import Parser
from app.services.classifier import Classifier

async def test_feeds():
    print("=" * 70)
    print("[TEST] POKEMON GO DISCORD FEED")
    print("=" * 70)
    
    fetcher = Fetcher()
    print(f"\n[OK] Sources loaded: {len(fetcher.sources)}")
    for source in fetcher.sources:
        print(f"     - {source['name']} ({source['type']})")
    
    print("\n[INFO] Fetching posts from all sources...")
    try:
        all_posts = await fetcher.fetch_all_sources()
        print(f"[OK] Total posts fetched: {len(all_posts)}")
        
        if all_posts:
            print("\n[SAMPLES] First 3 posts:")
            for i, post in enumerate(all_posts[:3], 1):
                title = post.get('title', 'NO TITLE')[:60]
                print(f"\n{i}. {title}...")
                print(f"   URL: {post.get('url', 'NO URL')}")
                print(f"   Date (raw): {post.get('date', 'NO DATE')}")
                
                # Parse the post
                parsed = Parser.parse_post(post.copy())
                print(f"   Date (parsed): {parsed.get('date', 'FAILED TO PARSE')}")
                print(f"   Source: {post.get('source', 'NO SOURCE')}")
        else:
            print("[WARN] No posts were fetched")
    except Exception as e:
        print(f"[ERROR] During fetch: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(test_feeds())
