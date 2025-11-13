from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Template Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/notifications"
    REDIS_URL: str = "redis://localhost:6379/0"
    TEMPLATE_CACHE_TTL: int = 3600
    
    class Config:
        env_file = ".env"


settings = Settings()

