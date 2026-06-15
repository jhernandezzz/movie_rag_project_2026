from fastapi import FastAPI, BackgroundTasks
from app.ingestion import ingest_movies

app = FastAPI(title="CinemaRAG API")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CinemaRAG"}

@app.get("/")
async def root():
    return {"message": "Welcome to CinemaRAG API"}

@app.post("/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks, pages: int = 1):
    """
    Trigger the ingestion pipeline as a background task.
    'pages' determines how many pages of popular movies to fetch from TMDB.
    """
    background_tasks.add_task(ingest_movies, pages)
    return {"message": f"Ingestion started for {pages} pages of movies in the background."}
