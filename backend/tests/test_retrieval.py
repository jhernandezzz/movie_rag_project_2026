import pytest
from unittest.mock import MagicMock, patch
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.retrieval import search_movies
from langchain_core.documents import Document

# --- Unit Tests for Retrieval Logic ---

@pytest.mark.asyncio
async def test_search_movies_formatting():
    """Test that search results are correctly formatted and metadata is extracted."""
    # Mock document and score
    mock_doc = Document(
        page_content="A test movie overview.",
        metadata={"title": "Test Movie", "tmdb_id": 999, "vote_average": 8.0}
    )
    mock_results = [(mock_doc, 0.15)]
    
    with patch("app.retrieval.get_vector_store") as mock_get_store:
        mock_store = MagicMock()
        mock_store.similarity_search_with_score.return_value = mock_results
        mock_get_store.return_value = mock_store
        
        results = await search_movies("query", k=1)
        
        assert len(results) == 1
        assert results[0]["title"] == "Test Movie"
        assert results[0]["score"] == 0.15
        assert results[0]["tmdb_id"] == 999
        assert results[0]["overview"] == "A test movie overview."

# --- Integration Tests for FastAPI Endpoints ---

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test that the health check endpoint returns 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "CinemaRAG"}

@pytest.mark.asyncio
async def test_search_endpoint_success():
    """Test the /search endpoint with a mocked retrieval response."""
    mock_results = [{
        "title": "Mocked Movie",
        "overview": "Overview here",
        "score": 0.1,
        "tmdb_id": 1,
        "release_date": "2024-01-01",
        "vote_average": 9.0
    }]
    
    with patch("app.main.search_movies", return_value=mock_results):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/search?query=scifi")
            
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["results"][0]["title"] == "Mocked Movie"
    assert data["query"] == "scifi"

@pytest.mark.asyncio
async def test_search_endpoint_validation():
    """Test that the /search endpoint requires a query parameter."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/search") # No query
    assert response.status_code == 422 # Validation error
