from langchain_community.vectorstores.pgvector import PGVector
from app.config import settings
from app.ingestion import embeddings, CONNECTION_STRING, COLLECTION_NAME

def get_vector_store():
    """Get a connection to the existing vector store."""
    return PGVector(
        connection_string=CONNECTION_STRING,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
        use_jsonb=True,
    )

async def search_movies(query: str, k: int = 5):
    """
    Perform a semantic similarity search for movies.
    Returns the top k most relevant documents.
    """
    vector_store = get_vector_store()
    
    # We use similarity_search_with_score to get the relevance score (distance)
    results = vector_store.similarity_search_with_score(query, k=k)
    
    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "title": doc.metadata.get("title"),
            "overview": doc.page_content,
            "score": score,  # Lower score usually means more similar in pgvector (cosine distance)
            "tmdb_id": doc.metadata.get("tmdb_id"),
            "release_date": doc.metadata.get("release_date"),
            "vote_average": doc.metadata.get("vote_average")
        })
    
    return formatted_results
