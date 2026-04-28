from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.post import Post
import hashlib

class PostRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_post_exists(self, url: str) -> bool:
        result = await self.db.execute(select(Post).where(Post.url == url))
        return result.scalar_one_or_none() is not None

    async def count_posts(self) -> int:
        result = await self.db.execute(select(func.count(Post.id)))
        return result.scalar_one()

    async def save_post(self, post_data: dict):
        hash_value = hashlib.md5(post_data['url'].encode()).hexdigest()
        post = Post(
            title=post_data['title'],
            url=post_data['url'],
            date=post_data.get('date'),
            image_url=post_data.get('image_url'),
            summary=post_data.get('summary'),
            category=post_data.get('category'),
            source=post_data.get('source'),
            hash_value=hash_value
        )
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post
