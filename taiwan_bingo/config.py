from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Taiwan Bingo Predictor"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/taiwan_bingo"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:password@localhost:5432/taiwan_bingo"

    # ML
    MODEL_ARTIFACTS_DIR: Path = Path("./model_artifacts")
    TORCH_DEVICE: str = "cpu"

    # Scraper
    SCRAPER_ENABLED: bool = True
    BINGO_SCRAPE_INTERVAL_MINUTES: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
