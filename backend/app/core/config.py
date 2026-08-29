from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "MemeX"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://memex:memex@localhost:5432/memex"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    API_PREFIX: str = "/api"
    
    # Trading
    TRADING_MODE: str = os.getenv("TRADING_MODE", "PAPER")  # PAPER or LIVE
    
    # Market Data
    DEX_SCREENER_API_URL: str = "https://api.dexscreener.com/latest/dex"
    MARKET_DATA_COLLECTION_INTERVAL: int = 10  # seconds
    MARKET_DATA_COLLECTION_BATCH_SIZE: int = 50
    
    # Worker
    ARQ_POOL_SIZE: int = 10
    WORKER_CONCURRENCY: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
