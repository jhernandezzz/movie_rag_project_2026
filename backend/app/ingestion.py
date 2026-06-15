from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from app.tmdb import tmdb_client
from app.config import settings
from app.database import init_db

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)

# Connection string for PGVector
CONNECTION_STRING = settings.DATABASE_URL
COLLECTION_NAME = "movie_embeddings"

async def ingest_movies(pages: int = 1):
    """Fetch movies from TMDB and store them in pgvector."""
    # Ensure extension is enabled
    init_db()
    
    all_movies = []
    for page in range(1, pages + 1):
        movies = await tmdb_client.fetch_popular_movies(page=page)
        all_movies.extend(movies)
    
    documents = []
    for movie in all_movies:
        # Create a rich text representation for embedding
        content = f"Title: {movie['title']}\nOverview: {movie['overview']}"
        
        # Metadata for filtering later
        metadata = {
            "tmdb_id": movie["id"],
            "title": movie["title"],
            "release_date": movie.get("release_date", ""),
            "vote_average": movie.get("vote_average", 0),
        }
        
        doc = Document(page_content=content, metadata=metadata)
        documents.append(doc)
    
    # Store in pgvector
    vector_store = PGVector.from_documents(
        embedding=embeddings,
        documents=documents,
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
        pre_delete_collection=False, # Set to True if you want to wipe existing data
        use_jsonb=True,
    )
    
    print(f"Successfully ingested {len(documents)} movies into pgvector.")
    return len(documents)
