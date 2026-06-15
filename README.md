# CinemaRAG

An intelligent movie discovery chatbot built with FastAPI, LangChain, and pgvector.

## Project Structure

- `/backend`: FastAPI service, LangChain logic, and data ingestion.
- `/frontend`: Next.js chat interface.
- `docker-compose.yml`: Local infrastructure (Postgres + pgvector).

## Getting Started (Sprint 1)

1. **Clone the repository.**
2. **Setup environment variables:**
   ```bash
   cp .env.example .env
   ```
   Fill in your `OPENAI_API_KEY` and `TMDB_API_KEY`.
3. **Start the infrastructure:**
   ```bash
   docker-compose up --build
   ```
4. **Verify the backend:**
   Visit `http://localhost:8000/health` or `http://localhost:8000/docs` for the Swagger UI.
