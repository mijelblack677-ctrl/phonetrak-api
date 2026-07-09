from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = "sqlite:///./phonetrak.db"
    secret_key: str = "dev-secret-change-in-production"
    api_base_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
