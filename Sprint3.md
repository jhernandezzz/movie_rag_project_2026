# Sprint 3: Semantic Retrieval & Search API

## Summary
Successfully implemented the retrieval layer of the RAG pipeline. This sprint enables the system to understand natural language queries and find semantically relevant movies from the `pgvector` store, moving beyond simple keyword matching.

## Key Accomplishments
- **Vector Store Connection:** Implemented a robust connection logic to the existing `pgvector` collection, ensuring consistent use of local embeddings for both ingestion and retrieval.
- **Semantic Similarity Search:** Leveraged `similarity_search_with_score` to retrieve the most relevant movies based on cosine distance in vector space.
- **Search API Endpoint:** Exposed the retrieval logic via a new `/search` endpoint in FastAPI, allowing users to query the database with parameters like `query` and `k` (number of results).
- **Formatted Results:** Structured the API response to include movie metadata (title, overview, score, TMDB ID, rating) for immediate front-end consumption.

## Technical Decisions
- **Cosine Distance:** Used the default distance metric in `pgvector` which works well with the `all-MiniLM-L6-v2` model for finding conceptual similarity.
- **Score Inclusion:** Included the similarity score in the response to help evaluate the "confidence" of the RAG system's matches.
- **Deduplication Strategy:** Implemented a robust check for existing TMDB IDs before ingestion and added a `reset` parameter to the ingestion endpoint to allow for a clean state.

## 🧪 Verification (Unit & Integration Testing)
- **Search Logic:** `test_search_movies_formatting` ensures that retrieval results are correctly structured and that metadata is accurately extracted from the vector store response.
- **API Status Codes:** Integration tests verify that `/health` and `/search` endpoints return `200 OK` on success and `422 Unprocessable Entity` when required parameters are missing.
- **Response Shape:** `test_search_endpoint_success` validates that the JSON response contains the expected fields (`results`, `query`) and matches the frontend requirements.
- **Relevance Thresholding:** Tests confirm that the system correctly maps vector similarity scores to the API response.

## Observations
- The semantic search successfully identified "Masters of the Universe" for a superhero query, demonstrating that the embedding model understands high-level concepts even when specific keywords might be missing.
