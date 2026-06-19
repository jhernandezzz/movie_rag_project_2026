from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from app.ingestion import ingest_movies
from app.retrieval import search_movies
from app.llm import generate_chat_response

app = FastAPI(title="CinemaRAG API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CinemaRAG"}

@app.get("/")
async def root():
    return {"message": "Welcome to CinemaRAG API"}

@app.post("/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks, pages: int = 1, reset: bool = False, top_rated: bool = False):
    """
    Trigger the ingestion pipeline as a background task.
    'pages' determines how many pages of movies to fetch (20 per page).
    'reset' will wipe the existing collection before ingesting.
    'top_rated' will fetch top-rated movies instead of popular (for diversity).
    """
    endpoint = "top-rated" if top_rated else "popular"
    background_tasks.add_task(ingest_movies, pages, reset, top_rated)
    return {"message": f"Ingestion started for {pages} pages of {endpoint} movies (reset={reset}) in the background."}

@app.get("/search")
async def search(query: str = Query(..., min_length=1), k: int = 5):
    """
    Search for movies using semantic similarity.
    """
    results = await search_movies(query, k=k)
    return {"query": query, "results": results}

@app.get("/chat")
async def chat(query: str = Query(..., min_length=1)):
    """
    Ask a question and get a conversational response based on retrieved movies.
    """
    response = await generate_chat_response(query)
    return {"query": query, "response": response}
