import psycopg2
from app.config import settings

def get_db_connection():
    return psycopg2.connect(settings.DATABASE_URL)

def init_db():
    """Initialize the database by enabling the pgvector extension."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        print("pgvector extension enabled.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
