"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import Optional, Dict, List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    database_url: str = "postgresql://postgres:postgres@localhost:5432/paragraphs_db"
    metaphorpsum_url: str = "http://metaphorpsum.com/paragraphs/1/50"
    dictionary_api_url: str = "https://api.dictionaryapi.dev/api/v2/entries/en"
    
    # Redis configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Cache TTL settings (in seconds)
    cache_ttl_word_definitions: int = 86400  # 24 hours
    cache_ttl_top_words: int = 3600  # 1 hour
    cache_ttl_word_frequencies: int = 1800  # 30 minutes
    
    # Celery configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Dictionary API settings
    dictionary_api_timeout: int = 10
    dictionary_api_max_retries: int = 3
    dictionary_api_parallel_requests: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

