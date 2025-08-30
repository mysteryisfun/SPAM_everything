"""
Configuration settings for the Voice Agent
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenAI Configuration
    openai_api_key: str

    # LiveKit Configuration
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str

    # Application Configuration
    app_name: str = "Voice Agent"
    debug: bool = False

    # RAG Configuration
    chroma_persist_directory: str = "./data/chroma_db"
    knowledge_base_path: str = "./data/knowledge_base.txt"

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
