import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.tmdb import tmdb_client

# --- Unit Tests for TMDB Client ---

@pytest.mark.asyncio
async def test_fetch_popular_movies():
    """Test that fetch_popular_movies returns movie data."""
    mock_response_data = {
        "results": [
            {
                "id": 1,
                "title": "Popular Movie 1",
                "overview": "A popular movie",
                "release_date": "2024-01-01",
                "vote_average": 7.5
            }
        ]
    }
    
    # Create a mock response with synchronous json() method
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    
    # Create a mock client that returns our mock response
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    
    with patch("app.tmdb.httpx.AsyncClient") as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        result = await tmdb_client.fetch_popular_movies(page=1)
        
        assert len(result) == 1
        assert result[0]["title"] == "Popular Movie 1"
        assert result[0]["id"] == 1


@pytest.mark.asyncio
async def test_fetch_top_rated_movies():
    """Test that fetch_top_rated_movies returns high-quality movie data."""
    mock_response_data = {
        "results": [
            {
                "id": 2,
                "title": "Top Rated Movie",
                "overview": "A critically acclaimed movie",
                "release_date": "2023-06-15",
                "vote_average": 9.2
            }
        ]
    }
    
    # Create a mock response with synchronous json() method
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    
    # Create a mock client that returns our mock response
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    
    with patch("app.tmdb.httpx.AsyncClient") as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        result = await tmdb_client.fetch_top_rated_movies(page=1)
        
        assert len(result) == 1
        assert result[0]["title"] == "Top Rated Movie"
        assert result[0]["vote_average"] == 9.2


# --- Integration Tests for /ingest Endpoint ---

@pytest.mark.asyncio
async def test_ingest_endpoint_popular():
    """Test the /ingest endpoint with default popular movies."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/ingest?pages=1&reset=false")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "popular" in data["message"].lower()


@pytest.mark.asyncio
async def test_ingest_endpoint_top_rated():
    """Test the /ingest endpoint with top_rated=true parameter."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/ingest?pages=1&top_rated=true&reset=false")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "top-rated" in data["message"].lower()


@pytest.mark.asyncio
async def test_ingest_endpoint_with_reset():
    """Test the /ingest endpoint with reset=true to clear collection."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/ingest?pages=1&reset=true")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "reset=True" in data["message"]


@pytest.mark.asyncio
async def test_ingest_endpoint_multiple_pages():
    """Test the /ingest endpoint with multiple pages."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/ingest?pages=5&reset=false")
    
    assert response.status_code == 200
    data = response.json()
    assert "5 pages" in data["message"]
