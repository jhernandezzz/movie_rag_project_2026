# Sprint 5: Next.js Chat Frontend

## Summary
Successfully built a functional, responsive web interface for CinemaRAG. This sprint transformed the project from a set of API endpoints into a user-facing application, enabling real-time conversational interaction with the movie discovery AI.

## Key Accomplishments
- **Frontend Architecture:** Initialized a Next.js 14 project using the App Router and TypeScript, following a modular component structure.
- **Modern Styling:** Integrated **Tailwind CSS** to build a clean "chat-bubble" interface that supports both light and dark modes natively.
- **Conversational UI Components:**
    - `ChatInterface`: Manages message state, loading states, and automatic scrolling.
    - `MessageBubble`: Distinguishes between User and AI messages with tailored styling.
    - `ChatInput`: A sleek, responsive input area with validation and sending logic.
- **Rich Text Support:** Integrated `react-markdown` to render the structured data (bolding, movie lists) returned by the Gemini RAG pipeline.
- **Backend Bridge:** Updated the FastAPI service with **CORS Middleware** to allow secure cross-origin requests from the frontend.

## Technical Decisions
- **Next.js + Tailwind:** Chosen for rapid development and a professional "out-of-the-box" look.
- **Path Aliasing:** Configured `@/` imports in `tsconfig.json` for cleaner, more maintainable code.
- **Version Pinning:** Reverted to React 18 and Next.js 14.2.x to maintain compatibility with existing peer dependencies (Lucide-React).
- **Client-Side Fetching:** Implemented a clean API client in `frontend/lib/api.ts` to keep business logic separate from UI components.

## 🧪 Verification (UI Testing)
- **Component Rendering:** Tests verify that the `ChatInterface` correctly displays the "Welcome" state and individual `MessageBubble` components based on the message role.
- **Interaction & State:** Verified that user input updates the local state and triggers the appropriate loading animations while waiting for the LLM.
- **Mocked API Integration:** Used Vitest to mock the `chat` API call, ensuring the frontend correctly processes and displays the JSON response from the backend.
- **Error Resilience:** Confirms that the UI displays a user-friendly error message if the backend service is unavailable or returns an error.

## Observations
- The interface handles long LLM responses gracefully with an auto-scrolling chat window.
- The use of `lucide-react` icons provides intuitive visual cues for the user.
- Aesthetic "polishing" (advanced animations, custom themes) is deferred to Sprint 6 to maintain focus on functionality.
