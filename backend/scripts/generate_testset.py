import asyncio
import os
import json
import argparse
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.testset import TestsetGenerator
from ragas.run_config import RunConfig
from ragas.llms.base import LangchainLLMWrapper
from ragas.embeddings.base import LangchainEmbeddingsWrapper
from app.config import settings
from app.database import get_db_connection
from langchain_core.documents import Document

class RateLimitedLangchainLLMWrapper(LangchainLLMWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = asyncio.Lock()

    async def agenerate_text(self, *args, **kwargs):
        async with self.lock:
            # Sleep 6 seconds to stay comfortably below 15 RPM (Google Gemini Free Tier limit)
            await asyncio.sleep(6.0)
            return await super().agenerate_text(*args, **kwargs)

async def generate_testset(testset_size: int = 50):
    print("Fetching documents from pgvector...")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT document, cmetadata FROM langchain_pg_embedding;")
        rows = cur.fetchall()
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return
    finally:
        cur.close()
        conn.close()

    if not rows:
        print("No documents found in the database. Please run ingestion first.")
        return

    # To bypass Ragas' 100-token minimum, we group 4 movie summaries into one "document"
    print(f"Found {len(rows)} movie records. Grouping into larger documents...")
    grouped_documents = []
    chunk_size = 4
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        combined_content = "\n\n---\n\n".join([row[0] for row in chunk])
        
        # Combine titles for the 'filename' metadata as recommended by Ragas docs
        titles = [row[1].get('title', 'Unknown') for row in chunk]
        metadata = {
            "filename": ", ".join(titles),
            "movie_ids": [row[1].get('tmdb_id') for row in chunk]
        }
        grouped_documents.append(Document(page_content=combined_content, metadata=metadata))

    print(f"Created {len(grouped_documents)} grouped documents for generation.")

    # Initialize LLM and Embeddings for generation
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=settings.GOOGLE_API_KEY,
        max_retries=10,
    )
    
    # Wrap models for Ragas with our rate-limited wrapper
    generator_llm = RateLimitedLangchainLLMWrapper(llm)
    generator_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    )

    # Initialize the Generator
    generator = TestsetGenerator(
        llm=generator_llm,
        embedding_model=generator_embeddings
    )

    print(f"Generating synthetic testset of size {testset_size} (throttled at ~10 RPM to prevent rate limits)...")
    try:
        run_config = RunConfig(max_workers=1, timeout=180)
        testset = generator.generate_with_langchain_docs(
            grouped_documents, 
            testset_size=testset_size,
            run_config=run_config
        )
        
        df = testset.to_pandas()
        output_path = "backend/data/eval_testset_raw.json"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_json(output_path, orient="records", indent=4)
        
        print(f"Successfully generated {len(df)} test cases and saved to {output_path}")
    except Exception as e:
        print(f"Error during generation: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic RAGAS testset.")
    parser.add_argument("--size", type=int, default=50, help="Number of questions to generate")
    args = parser.parse_args()
    
    asyncio.run(generate_testset(testset_size=args.size))
