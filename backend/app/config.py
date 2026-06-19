import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "CinemaRAG"

    _raw_database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@db:5432/cinemarag"
    )
    if _raw_database_url.startswith("postgresql+asyncpg://"):
        DATABASE_URL: str = _raw_database_url.replace(
            "postgresql+asyncpg://", "postgresql://", 1
        )
        DATABASE_URL_ASYNC: str = _raw_database_url
    else:
        DATABASE_URL: str = _raw_database_url
        DATABASE_URL_ASYNC: str = _raw_database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
    
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    TMDB_READ_ACCESS_TOKEN: str = os.getenv("TMDB_READ_ACCESS_TOKEN")
    
    # Embedding Model Name (HuggingFace)
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

settings = Settings()
