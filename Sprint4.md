# Sprint 4: LLM Integration & RAG Chain

## Summary
Successfully integrated Google Gemini to transform raw search results into a conversational AI experience. The system now functions as a true RAG (Retrieval-Augmented Generation) pipeline, capable of "reasoning" over the movie database to provide personalized recommendations.

## Key Accomplishments
- **LLM Selection:** Successfully navigated API quota and model naming challenges to implement **Gemini 1.5 Flash** (`gemini-flash-latest`) via LangChain.
- **RAG Chain Implementation:** Utilized **LCEL (LangChain Expression Language)** to build a seamless pipeline:
    1.  Receive user query.
    2.  Retrieve top 5 semantically similar movies from `pgvector`.
    3.  Format movies into a context block.
    4.  Feed context + query into Gemini with a specialized persona prompt.
- **Persona Design:** Created the "CinemaRAG" persona—an enthusiastic, helpful assistant that explains the "why" behind its recommendations.
- **Error Handling & Diagnostics:** Implemented a logging-based diagnostic system to identify available Gemini models and troubleshoot 429/404 API errors.

## Technical Decisions
- **Gemini 1.5 Flash:** Chosen for its high speed, generous free-tier quota, and ability to handle the "context stuffing" required for RAG.
- **LCEL Chains:** Used the pipe (`|`) operator for the chain to make the code readable and easy to debug or extend (e.g., adding memory/history later).
- **Prompt Engineering:** Optimized the prompt to ensure the model stays "grounded" in the provided context and avoids making up movies that aren't in the database.

## 🧪 Verification (Unit & Integration Testing)
- **Prompt Construction:** `test_format_docs` and `test_prompt_template` verify that the RAG context is built correctly and the "CinemaRAG" persona is preserved.
- **Mocked LLM API:** `test_generate_chat_response` utilizes `unittest.mock` to simulate Gemini API responses, ensuring the RAG chain logic is tested without external costs or connectivity issues.
- **"No-Results" Robustness:** `test_generate_chat_response_no_docs` confirms the assistant handles cases with no relevant movies gracefully, as per the persona instructions.
- **Chat Endpoint:** `test_chat_endpoint_success` provides an integration check for the FastAPI `/chat` endpoint, ensuring seamless communication between the API and the RAG engine.

## Observations
- The system successfully maps abstract requests (e.g., "dark action") to specific characters and plot points (e.g., *The Punisher*) found in the vector store.
- Free-tier rate limits (429) require careful model selection; "latest" aliases are more stable than specific version strings.
