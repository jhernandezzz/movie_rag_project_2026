from psycopg2 import sql
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.v2.engine import PGEngine
from langchain_postgres.v2.vectorstores import PGVectorStore
from langchain_core.documents import Document
from app.tmdb import tmdb_client
from app.config import settings
from app.database import init_db, get_db_connection

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)

# Connection string for Postgres
CONNECTION_STRING = settings.DATABASE_URL_ASYNC
COLLECTION_NAME = "movie_embeddings"
LEGACY_COLLECTION_TABLE = "langchain_pg_embedding"
EMBEDDING_DIMENSION = 384
BATCH_SIZE = 100

def _table_exists(table_name: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            );
            """,
            (table_name,),
        )
        return cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()


def _table_row_count(table_name: str) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(table_name))
        )
        return cur.fetchone()[0]
    except Exception:
        return 0
    finally:
        cur.close()
        conn.close()


def _migrate_legacy_pgvector_collection(engine: PGEngine) -> None:
    """Copy legacy pgvector rows into the new langchain_postgres table format."""
    if not _table_exists(LEGACY_COLLECTION_TABLE):
        return

    if _table_exists(COLLECTION_NAME) and _table_row_count(COLLECTION_NAME) > 0:
        return

    if not _table_exists(COLLECTION_NAME):
        engine.init_vectorstore_table(
            table_name=COLLECTION_NAME,
            vector_size=EMBEDDING_DIMENSION,
        )

    vector_store = PGVectorStore.create_sync(
        engine,
        embeddings,
        COLLECTION_NAME,
    )

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            sql.SQL("SELECT document, cmetadata FROM {} ORDER BY uuid;").format(
                sql.Identifier(LEGACY_COLLECTION_TABLE)
            )
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    if not rows:
        return

    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]
        documents = [
            Document(page_content=document, metadata=metadata or {})
            for document, metadata in batch
        ]
        vector_store.add_documents(documents)

    print(
        f"Migrated {len(rows)} documents from legacy pgvector collection "
        f"'{LEGACY_COLLECTION_TABLE}' into new table '{COLLECTION_NAME}'."
    )


def _ensure_vectorstore_table(engine: PGEngine) -> None:
    if not _table_exists(COLLECTION_NAME):
        engine.init_vectorstore_table(
            table_name=COLLECTION_NAME,
            vector_size=EMBEDDING_DIMENSION,
        )


def get_vector_store() -> PGVectorStore:
    """Return a ready-to-use PGVectorStore for the current collection."""
    engine = PGEngine.from_connection_string(CONNECTION_STRING)
    _migrate_legacy_pgvector_collection(engine)
    _ensure_vectorstore_table(engine)
    return PGVectorStore.create_sync(engine, embeddings, COLLECTION_NAME)


def get_existing_tmdb_ids():
    """Fetch all TMDB IDs already present in the vector store."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if _table_exists(COLLECTION_NAME):
            cur.execute(
                sql.SQL("SELECT (langchain_metadata->>'tmdb_id')::int FROM {};").format(
                    sql.Identifier(COLLECTION_NAME)
                )
            )
        elif _table_exists(LEGACY_COLLECTION_TABLE):
            cur.execute(
                "SELECT (cmetadata->>'tmdb_id')::int FROM langchain_pg_embedding;"
            )
        else:
            return set()

        return {row[0] for row in cur.fetchall() if row[0] is not None}
    except Exception:
        return set()
    finally:
        cur.close()
        conn.close()


def prepare_movie_documents(movies, existing_ids=None):
    """Transform raw TMDB movie data into LangChain Documents."""
    if existing_ids is None:
        existing_ids = set()
        
    documents = []
    for movie in movies:
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
    return documents

async def ingest_movies(pages: int = 1, reset: bool = False):
    """Fetch movies from TMDB and store them in pgvector."""
    init_db()
    engine = PGEngine.from_connection_string(CONNECTION_STRING)
    _migrate_legacy_pgvector_collection(engine)
    _ensure_vectorstore_table(engine)

    if reset:
        engine.drop_table(COLLECTION_NAME)
        engine.init_vectorstore_table(
            table_name=COLLECTION_NAME,
            vector_size=EMBEDDING_DIMENSION,
        )
        print(f"Collection {COLLECTION_NAME} cleared.")
        existing_ids = set()
    else:
        existing_ids = get_existing_tmdb_ids()

    all_movies = []
    for page in range(1, pages + 1):
        movies = await tmdb_client.fetch_popular_movies(page=page)
        all_movies.extend(movies)

    documents = prepare_movie_documents(all_movies, existing_ids)

    if not documents:
        print("No new movies to ingest.")
        return 0

    vector_store = PGVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        engine=engine,
        table_name=COLLECTION_NAME,
    )

    print(f"Successfully ingested {len(documents)} NEW movies into pgvector.")
    return len(documents)
