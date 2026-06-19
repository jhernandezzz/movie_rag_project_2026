import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.llm import format_docs, prompt, generate_chat_response
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

def test_format_docs():
    """Test that documents are formatted correctly for the prompt context."""
    docs = [
        Document(page_content="Overview 1", metadata={"title": "Movie 1", "vote_average": 8.0}),
        Document(page_content="Overview 2", metadata={"title": "Movie 2", "vote_average": 7.0}),
    ]
    formatted = format_docs(docs)
    
    assert "Title: Movie 1" in formatted
    assert "Overview: Overview 1" in formatted
    assert "Rating: 8.0/10" in formatted
    assert "Title: Movie 2" in formatted
    assert "Rating: 7.0/10" in formatted

def test_format_docs_missing_metadata():
    """Test that format_docs handles missing metadata gracefully."""
    docs = [
        Document(page_content="Overview 1", metadata={}),  # No title, no rating
    ]
    formatted = format_docs(docs)
    
    assert "Title: None" in formatted
    assert "Overview: Overview 1" in formatted
    assert "Rating: None/10" in formatted

def test_prompt_template():
    """Test that the prompt template has the expected input variables."""
    assert "context" in prompt.input_variables
    assert "question" in prompt.input_variables
    
    # Verify formatting works
    formatted_prompt = prompt.format(context="Test Context", question="Test Question")
    assert "Test Context" in formatted_prompt
    assert "Test Question" in formatted_prompt
    assert "CinemaRAG" in formatted_prompt

@pytest.mark.asyncio
async def test_generate_chat_response():
    """Test the full RAG chain logic with mocked retriever and LLM."""
    mock_docs = [Document(page_content="Sci-fi movie", metadata={"title": "Space", "vote_average": 9.0})]
    
    # Mock the vector store and retriever
    with patch("app.llm.get_vector_store") as mock_get_store:
        mock_store = MagicMock()
        spy_retriever = AsyncMock(return_value=mock_docs)
        mock_retriever = RunnableLambda(spy_retriever)
        mock_store.as_retriever.return_value = mock_retriever
        mock_get_store.return_value = mock_store
        
        # Patch the ainvoke method on the class to avoid Pydantic validation errors on the instance
        with patch("langchain_google_genai.ChatGoogleGenerativeAI.ainvoke", new_callable=AsyncMock) as mock_ainvoke:
            mock_ainvoke.return_value = AIMessage(content="Mocked AI Response")
            
            response = await generate_chat_response("What's a good sci-fi?")
            
            assert response == "Mocked AI Response"
            spy_retriever.assert_called_once()
            mock_ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_generate_chat_response_no_docs():
    """Test the RAG chain when the retriever returns no documents."""
    # Mock the vector store and retriever to return empty list
    with patch("app.llm.get_vector_store") as mock_get_store:
        mock_store = MagicMock()
        spy_retriever = AsyncMock(return_value=[])
        mock_retriever = RunnableLambda(spy_retriever)
        mock_store.as_retriever.return_value = mock_retriever
        mock_get_store.return_value = mock_store
        
        with patch("langchain_google_genai.ChatGoogleGenerativeAI.ainvoke", new_callable=AsyncMock) as mock_ainvoke:
            mock_ainvoke.return_value = AIMessage(content="I'm sorry, I couldn't find any movies.")
            
            response = await generate_chat_response("Something obscure")
            
            assert "couldn't find" in response.lower()
            spy_retriever.assert_called_once()

# --- Integration Tests for FastAPI Endpoints ---

@pytest.mark.asyncio
async def test_chat_endpoint_success():
    """Test the /chat endpoint with a mocked LLM response."""
    with patch("app.main.generate_chat_response", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Mocked LLM Response"
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/chat?query=tell me about batman")
            
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Mocked LLM Response"
    assert data["query"] == "tell me about batman"
