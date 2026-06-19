# Architecture Decisions: CinemaRAG

## Project Structure

- **Monorepo Split:** Using `/backend` (FastAPI) and `/frontend` (Next.js) for clear separation of concerns. This allows independent scaling and deployment of the AI microservice.

## Backend Stack

- **FastAPI:** Chosen for its high performance, native async support, and automatic OpenAPI documentation.
- **pgvector:** Used for vector storage. This allows us to keep relational metadata and embeddings in the same PostgreSQL database, simplifying the architecture and enabling complex relational/vector hybrid queries.
- **langchain-postgres v2:** Adopted the newer `langchain-postgres` table-based `PGVectorStore` API and added compatibility with legacy `langchain_pg_embedding` collections. This avoids older collection-schema assumptions and makes the backend more future-proof.
- **Python 3.11 target:** The backend is intended to run under Python 3.11 to avoid runtime warnings from Google libraries, urllib3/OpenSSL, and other transitive dependencies during testing and development.
- **Google Gemini (LLM):** Using Gemini 1.5 Flash via Google AI Studio. It provides a generous free tier for prototyping and high-quality responses.
- **Hugging Face (Embeddings):** Using local `sentence-transformers` for embeddings. This removes the cost and latency of API-based embeddings while keeping the project "free-to-run."
- **LangChain (LCEL):** Using the modern LangChain Expression Language for building the RAG pipeline. This provides better observability and composability compared to legacy syntax.
- **FastAPI/Starlette version pinning:** The backend now pins `fastapi` and `starlette` to newer, compatible versions in order to avoid deprecated `httpx` test warnings and maintain stable ASGI transport behavior.

## Frontend Stack

- **Next.js (App Router):** Provides a modern React framework with excellent performance, SEO, and developer experience.
- **TypeScript:** Ensures type safety across the frontend, reducing bugs and improving maintainability.
- **Tailwind CSS:** Chosen for rapid, consistent UI development and easy responsive design.
- **React Markdown:** Used to render the rich text (bolding, lists) returned by the LLM in a user-friendly way.

## Infrastructure

- **Docker Compose:** Used to orchestrate the backend and database during development, ensuring environment parity across different machines.
