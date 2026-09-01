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
        "postgresql://memex:memex@localhost:15487/memex"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:16721/0")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    API_PREFIX: str = "/api"
    
    # Trading
    TRADING_MODE: str = os.getenv("TRADING_MODE", "PAPER")  # PAPER or LIVE
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")
    PAPER_INITIAL_BALANCE: float = float(os.getenv("PAPER_INITIAL_BALANCE", os.getenv("INITIAL_BALANCE", "100")))
    
    # Market Data
    DEX_SCREENER_API_URL: str = "https://api.dexscreener.com/latest/dex"
    GECKO_TERMINAL_API_URL: str = os.getenv("GECKO_TERMINAL_API_URL", "https://api.geckoterminal.com/api/v2")
    MARKET_DATA_COLLECTION_INTERVAL: int = 10  # seconds
    MARKET_DATA_COLLECTION_BATCH_SIZE: int = 50
    
    # Worker
    ARQ_POOL_SIZE: int = 10
    WORKER_CONCURRENCY: int = 5

    # Observability
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    AUTO_CREATE_TABLES: bool = os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true"

    # Blockchain / Jupiter
    JUPITER_API_URL: str = os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag/v6")
    SOLANA_RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    DEFAULT_SLIPPAGE_BPS: int = int(os.getenv("DEFAULT_SLIPPAGE_BPS", "50"))
    WALLET_PRIVATE_KEY: Optional[str] = os.getenv("WALLET_PRIVATE_KEY")
    MAX_LIVE_TRADE_USD: float = float(os.getenv("MAX_LIVE_TRADE_USD", "100"))

    # ML
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "models/artifacts/momentum_scalp_v1.pkl")
    ML_PREDICTION_THRESHOLD: float = float(os.getenv("ML_PREDICTION_THRESHOLD", "0.65"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
