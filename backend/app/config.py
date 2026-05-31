# backend/app/config.py
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: Literal["groq", "openai", "anthropic"] = "groq"
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    assemblyai_api_key: Optional[str] = None

    chroma_mode: Literal["local", "memory"] = "local"
    chroma_persist_dir: str = "./chroma_db"
    data_dir: str = "./data"
    allowed_origins: str = "http://localhost:3000"
    apify_api_token: Optional[str] = None

settings = Settings()
