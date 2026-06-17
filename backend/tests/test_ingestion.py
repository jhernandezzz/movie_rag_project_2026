import pytest
from app.ingestion import prepare_movie_documents, embeddings

def test_prepare_movie_documents():
    """Test that TMDB data is correctly transformed into LangChain Documents."""
    mock_movies = [
        {
            "id": 1,
            "title": "Inception",
            "overview": "A thief who steals corporate secrets through the use of dream-sharing technology.",
            "release_date": "2010-07-16",
            "vote_average": 8.3
        },
        {
            "id": 2,
            "title": "Interstellar",
            "overview": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
            "release_date": "2014-11-05",
            "vote_average": 8.4
        }
    ]
    
    docs = prepare_movie_documents(mock_movies)
    
    assert len(docs) == 2
    assert docs[0].metadata["tmdb_id"] == 1
    assert docs[0].metadata["title"] == "Inception"
    assert "Title: Inception" in docs[0].page_content
    assert "Overview:" in docs[0].page_content
    
    # Test filtering existing IDs
    docs_filtered = prepare_movie_documents(mock_movies, existing_ids={1})
    assert len(docs_filtered) == 1
    assert docs_filtered[0].metadata["tmdb_id"] == 2

def test_prepare_movie_documents_malformed_data():
    """Test that missing optional fields are handled gracefully."""
    malformed_movies = [
        {
            "id": 3,
            "title": "Missing Info Movie",
            "overview": "This movie has no release date or vote average."
            # release_date and vote_average missing
        }
    ]
    
    docs = prepare_movie_documents(malformed_movies)
    assert len(docs) == 1
    assert docs[0].metadata["release_date"] == ""
    assert docs[0].metadata["vote_average"] == 0

def test_embedding_dimensions():
    """Test that the embedding model returns the expected dimensions (384 for all-MiniLM-L6-v2)."""
    text = "CinemaRAG is a great movie discovery engine."
    embedding = embeddings.embed_query(text)
    
    # all-MiniLM-L6-v2 produces 384-dimensional vectors
    assert len(embedding) == 384
