# Sprint 1: Project Scaffolding & Infrastructure

## Summary

Successfully established the foundation for CinemaRAG, a movie discovery AI microservice. This sprint focused on environment parity, containerization, and basic API connectivity using a free-tier AI stack.

## Key Accomplishments

- **Monorepo Structure:** Created `/backend` (FastAPI) and `/frontend` (Next.js) for clean separation of concerns.
- **Docker Orchestration:** Configured `docker-compose.yml` to manage the FastAPI application and a PostgreSQL database with the `pgvector` extension.
- **Backend Setup:**
  - Initialized FastAPI with health check and root endpoints.
  - Configured `requirements.txt` for the free AI stack (Google Gemini LLM + local Hugging Face embeddings).
  - Implemented a multi-stage `Dockerfile` with system dependencies for database drivers.
- **Configuration & Safety:**
  - Set up `.env.example` to manage sensitive API keys and database strings.
  - Configured `.gitignore` to prevent leaking credentials and environment-specific files.
  - Implemented `.venv`-based backend testing guidance and documented `PYTHONPATH=backend` as the reliable local test environment.
  - Initialized `DECISIONS.md` to track architectural rationale.

## Technical Decisions

- **pgvector:** Chosen to keep relational movie metadata and vector embeddings in a single source of truth, avoiding the complexity of multiple databases.
- **Free-Tier AI:** Pivoted from OpenAI to Google Gemini (LLM) and local Hugging Face (Embeddings) to ensure the project remains cost-free during development.
- **Local Embeddings:** Decided to run `sentence-transformers` locally within the container to reduce API latency and cost.
