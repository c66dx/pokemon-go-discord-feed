import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    discord_webhook_url: str | None = os.getenv("DISCORD_WEBHOOK_URL")
    check_interval_minutes: int = int(os.getenv("CHECK_INTERVAL_MINUTES", 30))
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./pokemon_go_feed.db")

    class Config:
        env_file = ".env"

settings = Settings()