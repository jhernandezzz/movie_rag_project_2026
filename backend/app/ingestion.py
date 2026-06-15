from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from app.tmdb import tmdb_client
from app.config import settings
from app.database import init_db, get_db_connection

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)

# Connection string for PGVector
CONNECTION_STRING = settings.DATABASE_URL
COLLECTION_NAME = "movie_embeddings"

def get_existing_tmdb_ids():
    """Fetch all TMDB IDs already present in the vector store."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # langchain_pg_embedding is the default table name for pgvector in LangChain
        cur.execute("SELECT (cmetadata->>'tmdb_id')::int FROM langchain_pg_embedding;")
        return {row[0] for row in cur.fetchall() if row[0] is not None}
    except Exception:
        return set()
    finally:
        cur.close()
        conn.close()

async def ingest_movies(pages: int = 1, reset: bool = False):
    """Fetch movies from TMDB and store them in pgvector."""
    # Ensure extension is enabled
    init_db()
    
    if reset:
        # This will wipe the specific collection before starting
        vector_store = PGVector(
            connection_string=CONNECTION_STRING,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
            use_jsonb=True,
        )
        vector_store.delete_collection()
        print(f"Collection {COLLECTION_NAME} cleared.")
        existing_ids = set()
    else:
        existing_ids = get_existing_tmdb_ids()
    
    all_movies = []
    for page in range(1, pages + 1):
        movies = await tmdb_client.fetch_popular_movies(page=page)
        all_movies.extend(movies)
    
    documents = []
    for movie in all_movies:
        if movie["id"] in existing_ids:
            continue
            
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
    
    if not documents:
        print("No new movies to ingest.")
        return 0

    # Store in pgvector
    vector_store = PGVector.from_documents(
        embedding=embeddings,
        documents=documents,
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
        pre_delete_collection=False,
        use_jsonb=True,
    )
    
    print(f"Successfully ingested {len(documents)} NEW movies into pgvector.")
    return len(documents)
