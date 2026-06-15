# Architecture Decisions: CinemaRAG

## Project Structure
- **Monorepo Split:** Using `/backend` (FastAPI) and `/frontend` (Next.js) for clear separation of concerns. This allows independent scaling and deployment of the AI microservice.

## Backend Stack
- **FastAPI:** Chosen for its high performance, native async support, and automatic OpenAPI documentation.
- **pgvector:** Used for vector storage. This allows us to keep relational metadata and embeddings in the same PostgreSQL database, simplifying the architecture and enabling complex relational/vector hybrid queries.
- **Google Gemini (LLM):** Using Gemini 1.5 Flash via Google AI Studio. It provides a generous free tier for prototyping and high-quality responses.
- **Hugging Face (Embeddings):** Using local `sentence-transformers` for embeddings. This removes the cost and latency of API-based embeddings while keeping the project "free-to-run."
- **LangChain (LCEL):** Using the modern LangChain Expression Language for building the RAG pipeline. This provides better observability and composability compared to legacy syntax.

## Infrastructure
- **Docker Compose:** Used to orchestrate the backend and database during development, ensuring environment parity across different machines.
