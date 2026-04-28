from fastapi import FastAPI
import os

from app.core.config import settings
from app.core.database import engine
from app.models.post import Base
from app.services.scheduler import start_scheduler
from app.routers import health, test_discord
from app.routers.sync import router as sync_router

app = FastAPI(title="Pokémon GO Discord Feed", version="1.0.0")

app.include_router(health.router)
app.include_router(test_discord.router)
app.include_router(sync_router)

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    start_scheduler()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
