from fastapi import FastAPI, BackgroundTasks, Query
from app.ingestion import ingest_movies
from app.retrieval import search_movies

app = FastAPI(title="CinemaRAG API")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CinemaRAG"}

@app.get("/")
async def root():
    return {"message": "Welcome to CinemaRAG API"}

@app.post("/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks, pages: int = 1, reset: bool = False):
    """
    Trigger the ingestion pipeline as a background task.
    'pages' determines how many pages of popular movies to fetch from TMDB.
    'reset' will wipe the existing collection before ingesting.
    """
    background_tasks.add_task(ingest_movies, pages, reset)
    return {"message": f"Ingestion started for {pages} pages of movies (reset={reset}) in the background."}

@app.get("/search")
async def search(query: str = Query(..., min_length=1), k: int = 5):
    """
    Search for movies using semantic similarity.
    """
    results = await search_movies(query, k=k)
    return {"query": query, "results": results}
