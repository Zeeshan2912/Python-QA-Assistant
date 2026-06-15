import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # Cerebras Configuration
    CEREBRAS_API_KEY: str
    
    # Qdrant Configuration
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_IN_MEMORY: bool = True
    
    # RAG Settings
    TOP_K_RETRIEVAL: int = 5
    RERANK_THRESHOLD: float = 0.3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings(_env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
