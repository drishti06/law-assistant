from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440
    openai_api_key: str = ""
    use_openai: bool = False
    hf_model_name: str = "google/flan-t5-base"
    embedding_model: str = "all-MiniLM-L6-v2"
    faiss_index_path: str = "data/faiss_index"
    cors_origins: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
