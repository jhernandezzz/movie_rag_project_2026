# Sprint 2: Data Ingestion Pipeline

## Summary
Successfully implemented the core RAG data pipeline. This sprint involved fetching movie metadata from TMDB, processing it into searchable documents, and generating vector embeddings locally for storage in `pgvector`.

## Key Accomplishments
- **TMDB Integration:** Built an async `TMDBClient` using the API Read Access Token (Bearer) to securely fetch popular movie data.
- **Local Embedding Pipeline:** Integrated `langchain-huggingface` to run the `all-MiniLM-L6-v2` model locally within the Docker container. This ensures zero API costs and lower latency for vector generation.
- **Vector Storage:** 
    - Automated the initialization of the `vector` extension in PostgreSQL.
    - Implemented a background ingestion task to prevent blocking the API during heavy processing.
    - Utilized `JSONB` for metadata storage in `pgvector` for optimized filtering.
- **Background Processing:** Added an `/ingest` endpoint that leverages FastAPI's `BackgroundTasks` to handle data fetching and embedding asynchronously.

## Technical Decisions
- **Async HTTPX:** Used `httpx` instead of `requests` for the TMDB client to maintain non-blocking I/O within FastAPI's async event loop.
- **Content Formatting:** Designed a specific template for embeddings (`Title: ... \n Overview: ...`) to ensure the vector representation captures both the name and the narrative context of the movie.
- **Metadata Preservation:** Stored TMDB IDs, titles, and vote averages alongside vectors to enable rich metadata filtering in future sprints.
