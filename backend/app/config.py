import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "CinemaRAG"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/cinemarag")
    
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    TMDB_READ_ACCESS_TOKEN: str = os.getenv("TMDB_READ_ACCESS_TOKEN")
    
    # Embedding Model Name (HuggingFace)
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

settings = Settings()
