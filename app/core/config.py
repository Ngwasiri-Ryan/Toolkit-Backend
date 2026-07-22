from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ToolKit API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "60/minute"
    
    # Database
    DATABASE_URL: str = "sqlite:///./toolkit.db"
    
    # Auth
    SUPABASE_JWT_SECRET: str = "mock_secret"
    
    # Celery & Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage (S3 / local fallback)
    STORAGE_BUCKET: str = "toolkit-uploads"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_ENDPOINT_URL: str = ""
    
    # Billing & Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PRO_PRICE_ID: str = "price_pro_monthly"
    FREE_DAILY_CONVERSION_LIMIT: int = 5
    
    # Email & Security
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@toolkit.dev"
    MAX_FILE_SIZE_MB: int = 50
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
