# CinemaRAG 🎬

An intelligent, full-stack movie discovery engine powered by **Retrieval-Augmented Generation (RAG)**. CinemaRAG uses the Gemini API, LangChain, and PGVector to provide conversational recommendations based on a high-quality movie database.

## 🚀 Features (v3)

- **AI Discovery Engine:** Powered by `gemini-3.1-flash-lite` for fast, intelligent, and stable responses (30 RPM free tier).
- **Polished UI:** A modern, full-width Next.js 14 interface with advanced typography and responsive design.
- **Semantic Search:** Uses PGVector and HuggingFace embeddings (`all-MiniLM-L6-v2`) to find movies based on meaning, not just keywords.
- **Real-time Ingestion:** Background tasks to sync popular movies directly from the TMDB API.
- **Dark Mode Support:** Native system-aware dark mode for comfortable late-night movie browsing.

## 🛠️ Tech Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons.
- **Backend:** FastAPI, Python 3.11, LangChain (LCEL).
- **Database:** PostgreSQL + PGVector for high-performance vector similarity search.
- **LLM:** Google Gemini API (Flash-Lite family).
- **Embeddings:** HuggingFace Sentence Transformers.

## 📁 Project Structure

- `/backend`: FastAPI service handling ingestion, RAG logic, and API endpoints.
- `/frontend`: Next.js web application with a polished "chat-bubble" interface.
- `docker-compose.yml`: Local infrastructure orchestration (Database + Backend + Frontend).

## 🏁 Getting Started

### 1. Prerequisites
- Docker & Docker Compose
- Google Gemini API Key ([Get it here](https://aistudio.google.com/))
- TMDB Read Access Token ([Get it here](https://www.themoviedb.org/settings/api))

### 2. Setup Environment
```bash
cp .env.example .env
```
Update the `.env` file with your specific API keys.

### 3. Launch Application
```bash
docker-compose up --build
```
- **Frontend:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`
- **API Docs:** `http://localhost:8000/docs`

### 4. Data Ingestion
To populate your local movie database, trigger the ingestion endpoint:
```bash
# Ingest 5 pages of popular movies (Background task)
curl -X POST "http://localhost:8000/ingest?pages=5"
```

## 🧪 Testing

The project includes comprehensive test suites for both the backend and frontend.

### Running Backend Tests
From the project root:
```bash
# Set PYTHONPATH so Python can find the 'app' module
export PYTHONPATH=backend

# Run all tests
python3 -m pytest backend/tests/
```

### Running Frontend Tests
From the `frontend` directory:
```bash
npm test
```

### Test Coverage
- **Data Pipeline:** Validates TMDB data transformation, embedding dimensions, and malformed data handling.
- **Retrieval:** Tests semantic search accuracy, result formatting, and API status codes.
- **LLM Logic:** Mocks the Gemini API to test prompt construction, persona consistency, and "no-results" handling.
- **UI/Frontend:** Uses Vitest and React Testing Library to verify component rendering, loading states, and API integration.

## 📈 Roadmap

- [x] **Sprint 5:** Functional Next.js Chat Interface.
- [x] **Sprint 6 (UI):** Full-width v3 Layout & Typography Polish.
- [ ] **Sprint 6 (Eval):** RAGAS Evaluation Layer for accuracy metrics.
- [ ] **Sprint 6 (Deploy):** Production containerization and Cloud deployment.
