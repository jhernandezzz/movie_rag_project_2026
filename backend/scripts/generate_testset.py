import asyncio
import os
import json
import argparse
import pandas as pd
import logging
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.testset import TestsetGenerator
from ragas.run_config import RunConfig
from ragas.llms.base import LangchainLLMWrapper
from ragas.embeddings.base import LangchainEmbeddingsWrapper
from app.config import settings
from app.database import get_db_connection
from app.retrieval import search_movies
from app.llm import generate_chat_response
from langchain_core.documents import Document

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimitedLangchainLLMWrapper(LangchainLLMWrapper):
    """Simple rate limiting with conservative sleep intervals."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = asyncio.Lock()

    async def agenerate_text(self, *args, **kwargs):
        async with self.lock:
            # Sleep 15 seconds to stay well below the 15 RPM free tier limit (1 call per min)
            await asyncio.sleep(15.0)
            return await super().agenerate_text(*args, **kwargs)


async def generate_testset(testset_size: int = 50):
    """Generate synthetic test cases using RAGAS."""
    print("Fetching documents from pgvector...")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT document, cmetadata FROM langchain_pg_embedding;")
        rows = cur.fetchall()
    except Exception as e:
        # Try the new table name from langchain_postgres
        try:
            cur.execute(
                "SELECT langchain_content, langchain_metadata FROM langchain_pg_collection_documents WHERE collection_id = (SELECT uuid FROM langchain_pg_collections LIMIT 1);"
            )
            rows = cur.fetchall()
        except Exception as e2:
            logger.error(f"Error fetching documents: {e}, {e2}")
            return None
    finally:
        cur.close()
        conn.close()

    if not rows:
        print("No documents found in the database. Please run ingestion first.")
        return None

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
        model="gemini-3.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        max_retries=3,
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

    print(f"Generating synthetic testset of size {testset_size}...")
    print(f"(Rate limited to 1 call per 15 seconds = ~4 RPM, well below 15 RPM quota)")
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
        
        print(f"✓ Successfully generated {len(df)} test cases and saved to {output_path}")
        return df
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        raise


async def evaluate_testset(testset_df: pd.DataFrame):
    """Evaluate the RAG system using the generated testset."""
    print("\n" + "="*60)
    print("STARTING EVALUATION PHASE")
    print("="*60)
    
    if testset_df is None or len(testset_df) == 0:
        print("No testset to evaluate. Load a testset first.")
        return None

    evaluation_results = []
    total_tests = len(testset_df)
    
    print(f"Running {total_tests} test cases through the RAG pipeline...")
    print("(Rate limited to 10 seconds between calls)\n")
    
    for idx, row in testset_df.iterrows():
        question = row.get('question') or row.get('user_input')
        ground_truth = row.get('ground_truth_context') or row.get('ground_truth')
        
        print(f"[{idx + 1}/{total_tests}] Q: {question[:70]}{'...' if len(question) > 70 else ''}")
        
        try:
            # Get retrieved context from the RAG system
            search_results = await search_movies(question, k=5)
            retrieved_context = "\n\n".join([
                f"Title: {r['title']}\nOverview: {r['overview']}"
                for r in search_results
            ])
            
            # Get the RAG response
            response = await generate_chat_response(question)
            
            result = {
                "question": question,
                "ground_truth": ground_truth,
                "retrieved_context": retrieved_context,
                "answer": response,
                "search_results": search_results
            }
            evaluation_results.append(result)
            print(f"  → ✓ Completed")
            
            # Sleep between requests to avoid rate limiting
            await asyncio.sleep(10.0)
            
        except Exception as e:
            logger.error(f"Error processing test case {idx}: {e}")
            result = {
                "question": question,
                "ground_truth": ground_truth,
                "retrieved_context": "",
                "answer": f"ERROR: {str(e)[:100]}",
                "search_results": []
            }
            evaluation_results.append(result)
            print(f"  → ✗ Error: {str(e)[:50]}")
    
    # Save raw evaluation results
    eval_results_df = pd.DataFrame(evaluation_results)
    eval_output_path = "backend/data/eval_results_raw.json"
    os.makedirs(os.path.dirname(eval_output_path), exist_ok=True)
    eval_results_df.to_json(eval_output_path, orient="records", indent=4)
    print(f"\n✓ Saved raw evaluation results to {eval_output_path}")
    
    return eval_results_df


def generate_evaluation_report(
    testset_df: pd.DataFrame, 
    eval_results_df: pd.DataFrame
):
    """Generate a comprehensive evaluation report."""
    print("\n" + "="*60)
    print("GENERATING EVALUATION REPORT")
    print("="*60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "testset_size": len(testset_df),
        "evaluation_count": len(eval_results_df),
    }
    
    # Basic statistics
    errors = sum(1 for ans in eval_results_df["answer"] if ans.startswith("ERROR"))
    report["errors"] = errors
    report["success_rate"] = f"{((len(eval_results_df) - errors) / len(eval_results_df) * 100):.1f}%"
    
    # Sample results
    sample_indices = min(3, len(eval_results_df))
    report["sample_results"] = []
    for i in range(sample_indices):
        row = eval_results_df.iloc[i]
        report["sample_results"].append({
            "question": row["question"],
            "answer": row["answer"][:200] + "..." if len(row["answer"]) > 200 else row["answer"],
            "retrieved_context": row["retrieved_context"][:150] + "..." if len(row["retrieved_context"]) > 150 else row["retrieved_context"],
        })
    
    # Save report
    report_output_path = "backend/data/eval_report.json"
    os.makedirs(os.path.dirname(report_output_path), exist_ok=True)
    with open(report_output_path, "w") as f:
        json.dump(report, f, indent=4)
    
    print(f"\n✓ Saved evaluation report to {report_output_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Testset Size: {report['testset_size']}")
    print(f"Evaluated: {report['evaluation_count']}")
    print(f"Errors: {report['errors']}")
    print(f"Success Rate: {report['success_rate']}")
    print("="*60 + "\n")
    
    return report


async def main():
    parser = argparse.ArgumentParser(description="Generate and evaluate RAGAS testset.")
    parser.add_argument("--size", type=int, default=50, help="Number of questions to generate")
    parser.add_argument("--generate-only", action="store_true", help="Only generate testset, don't evaluate")
    parser.add_argument("--evaluate-only", action="store_true", help="Only evaluate existing testset")
    parser.add_argument("--testset-path", type=str, default="backend/data/eval_testset_raw.json", 
                       help="Path to testset JSON file for evaluation")
    args = parser.parse_args()
    
    try:
        testset_df = None
        eval_results_df = None
        
        # Generation phase
        if not args.evaluate_only:
            print("="*60)
            print("STARTING GENERATION PHASE")
            print("="*60)
            testset_df = await generate_testset(testset_size=args.size)
        else:
            # Load existing testset
            if os.path.exists(args.testset_path):
                testset_df = pd.read_json(args.testset_path)
                print(f"✓ Loaded existing testset from {args.testset_path}")
            else:
                print(f"Error: Testset not found at {args.testset_path}")
                return
        
        # Evaluation phase
        if testset_df is not None and not args.generate_only:
            eval_results_df = await evaluate_testset(testset_df)
            
            # Generate report
            if eval_results_df is not None:
                generate_evaluation_report(testset_df, eval_results_df)
        
        print("\n✓ Evaluation pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in evaluation pipeline: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())


async def evaluate_testset(testset_df: pd.DataFrame):
    """Evaluate the RAG system using the generated testset."""
    print("\n" + "="*60)
    print("STARTING EVALUATION PHASE")
    print("="*60)
    
    if testset_df is None or len(testset_df) == 0:
        print("No testset to evaluate. Load a testset first.")
        return None

    evaluation_results = []
    total_tests = len(testset_df)
    
    print(f"Running {total_tests} test cases through the RAG pipeline...")
    print("Note: Requests are rate-limited to ~10 RPM to avoid quota exhaustion\n")
    
    for idx, row in testset_df.iterrows():
        question = row.get('question') or row.get('user_input')
        ground_truth = row.get('ground_truth_context') or row.get('ground_truth')
        
        print(f"[{idx + 1}/{total_tests}] Q: {question[:70]}{'...' if len(question) > 70 else ''}")
        
        try:
            # Get retrieved context from the RAG system
            search_results = await search_movies(question, k=5)
            retrieved_context = "\n\n".join([
                f"Title: {r['title']}\nOverview: {r['overview']}"
                for r in search_results
            ])
            
            # Get the RAG response with retries for rate limiting
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = await generate_chat_response(question)
                    break
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        wait_time = (attempt + 1) * 10  # Exponential backoff: 10, 20, 30 seconds
                        if attempt < max_retries - 1:
                            print(f"  → Rate limited. Waiting {wait_time}s before retry...")
                            await asyncio.sleep(wait_time)
                        else:
                            response = f"ERROR: {str(e)[:100]}"
                    else:
                        raise
            
            result = {
                "question": question,
                "ground_truth": ground_truth,
                "retrieved_context": retrieved_context,
                "answer": response if response else "ERROR: Unknown error",
                "search_results": search_results
            }
            evaluation_results.append(result)
            print(f"  → ✓ Completed")
            
        except Exception as e:
            logger.error(f"Error processing test case {idx}: {e}")
            result = {
                "question": question,
                "ground_truth": ground_truth,
                "retrieved_context": "",
                "answer": f"ERROR: {str(e)[:100]}",
                "search_results": []
            }
            evaluation_results.append(result)
            print(f"  → ✗ Error: {str(e)[:50]}")
    
    # Save raw evaluation results
    eval_results_df = pd.DataFrame(evaluation_results)
    eval_output_path = "backend/data/eval_results_raw.json"
    os.makedirs(os.path.dirname(eval_output_path), exist_ok=True)
    eval_results_df.to_json(eval_output_path, orient="records", indent=4)
    print(f"\n✓ Saved raw evaluation results to {eval_output_path}")
    
    return eval_results_df


async def calculate_metrics(testset_df: pd.DataFrame, eval_results_df: pd.DataFrame):
    """Calculate RAGAS metrics to assess hallucinations, relevance, and faithfulness."""
    print("\n" + "="*60)
    print("CALCULATING METRICS USING RAGAS")
    print("="*60)
    
    # Check for too many errors in evaluation results
    errors = sum(1 for ans in eval_results_df["answer"] if ans.startswith("ERROR"))
    if errors > len(eval_results_df) * 0.5:  # More than 50% errors
        print(f"\n⚠ High error rate detected ({errors}/{len(eval_results_df)}).")
        print("⚠ Skipping metric calculation due to API rate limits.")
        print("⚠ Please run evaluation again later or increase rate limit delays.\n")
        return None
    
    try:
        # Filter out error responses for metric calculation
        valid_results = eval_results_df[~eval_results_df["answer"].str.startswith("ERROR")].reset_index(drop=True)
        
        if len(valid_results) == 0:
            print("⚠ No valid results to evaluate. Skipping metrics.\n")
            return None
        
        print(f"Calculating metrics for {len(valid_results)} valid responses...")
        
        # Prepare data for RAGAS evaluation
        ragas_dataset_dict = {
            "question": valid_results["question"].tolist(),
            "contexts": [[ctx] if ctx else ["No context retrieved"] for ctx in valid_results["retrieved_context"].tolist()],
            "answer": valid_results["answer"].tolist(),
            "ground_truth": valid_results["ground_truth"].tolist(),
        }
        
        dataset = Dataset.from_dict(ragas_dataset_dict)
        
        # Initialize LLM for metric calculations
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            max_retries=3,
            temperature=0.0,  # Deterministic for evaluation
        )
        
        metrics = [
            Faithfulness(),
            ContextRelevance(),
            AnswerRelevancy(),
            ContextRecall(),
        ]
        
        print(f"Evaluating with {len(metrics)} metrics...")
        print("(This may take 5-10 minutes due to LLM rate limits)\n")
        
        # Run RAGAS evaluation with conservative rate limiting
        run_config = RunConfig(max_workers=1, timeout=120)
        results = evaluate(
            dataset,
            metrics=metrics,
            llm=llm,
            run_config=run_config
        )
        
        metrics_df = results.to_pandas()
        metrics_output_path = "backend/data/eval_metrics.json"
        os.makedirs(os.path.dirname(metrics_output_path), exist_ok=True)
        metrics_df.to_json(metrics_output_path, orient="records", indent=4)
        
        print(f"\n✓ Saved detailed metrics to {metrics_output_path}")
        return metrics_df
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            print(f"\n⚠ Rate limited during metrics calculation.")
            print("⚠ Skipping metrics. Evaluation results are still available.\n")
        else:
            logger.warning(f"Metrics calculation failed: {e}")
            print(f"⚠ Could not calculate RAGAS metrics: {e}")
            print("  Continuing with summary statistics...\n")
        return None


def generate_evaluation_report(
    testset_df: pd.DataFrame, 
    eval_results_df: pd.DataFrame, 
    metrics_df: pd.DataFrame = None
):
    """Generate a comprehensive evaluation report."""
    print("\n" + "="*60)
    print("GENERATING EVALUATION REPORT")
    print("="*60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "testset_size": len(testset_df),
        "evaluation_count": len(eval_results_df),
    }
    
    # Basic statistics
    errors = sum(1 for ans in eval_results_df["answer"] if ans.startswith("ERROR"))
    report["errors"] = errors
    report["success_rate"] = f"{((len(eval_results_df) - errors) / len(eval_results_df) * 100):.1f}%"
    
    # Calculate metrics if available
    if metrics_df is not None and len(metrics_df) > 0:
        report["metrics"] = {
            "faithfulness": {
                "mean": float(metrics_df.get("faithfulness", [0]).mean()),
                "std": float(metrics_df.get("faithfulness", [0]).std()),
            },
            "context_relevance": {
                "mean": float(metrics_df.get("context_relevance", [0]).mean()),
                "std": float(metrics_df.get("context_relevance", [0]).std()),
            },
            "answer_relevancy": {
                "mean": float(metrics_df.get("answer_relevancy", [0]).mean()),
                "std": float(metrics_df.get("answer_relevancy", [0]).std()),
            },
            "context_recall": {
                "mean": float(metrics_df.get("context_recall", [0]).mean()),
                "std": float(metrics_df.get("context_recall", [0]).std()),
            },
        }
    
    # Sample results
    sample_indices = min(3, len(eval_results_df))
    report["sample_results"] = []
    for i in range(sample_indices):
        row = eval_results_df.iloc[i]
        report["sample_results"].append({
            "question": row["question"],
            "answer": row["answer"][:200] + "..." if len(row["answer"]) > 200 else row["answer"],
            "retrieved_context": row["retrieved_context"][:150] + "..." if len(row["retrieved_context"]) > 150 else row["retrieved_context"],
        })
    
    # Save report
    report_output_path = "backend/data/eval_report.json"
    os.makedirs(os.path.dirname(report_output_path), exist_ok=True)
    with open(report_output_path, "w") as f:
        json.dump(report, f, indent=4)
    
    print(f"\n✓ Saved evaluation report to {report_output_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Testset Size: {report['testset_size']}")
    print(f"Evaluated: {report['evaluation_count']}")
    print(f"Errors: {report['errors']}")
    print(f"Success Rate: {report['success_rate']}")
    
    if metrics_df is not None and len(metrics_df) > 0:
        print("\nMetrics (0-1 scale, higher is better):")
        print(f"  Faithfulness (no hallucinations): {report['metrics']['faithfulness']['mean']:.3f} ± {report['metrics']['faithfulness']['std']:.3f}")
        print(f"  Context Relevance (context relevance): {report['metrics']['context_relevance']['mean']:.3f} ± {report['metrics']['context_relevance']['std']:.3f}")
        print(f"  Answer Relevancy: {report['metrics']['answer_relevancy']['mean']:.3f} ± {report['metrics']['answer_relevancy']['std']:.3f}")
        print(f"  Context Recall: {report['metrics']['context_recall']['mean']:.3f} ± {report['metrics']['context_recall']['std']:.3f}")
    
    print("="*60 + "\n")
    return report


async def main():
    parser = argparse.ArgumentParser(description="Generate and evaluate RAGAS testset.")
    parser.add_argument("--size", type=int, default=50, help="Number of questions to generate")
    parser.add_argument("--generate-only", action="store_true", help="Only generate testset, don't evaluate")
    parser.add_argument("--evaluate-only", action="store_true", help="Only evaluate existing testset")
    parser.add_argument("--testset-path", type=str, default="backend/data/eval_testset_raw.json", 
                       help="Path to testset JSON file for evaluation")
    args = parser.parse_args()
    
    try:
        testset_df = None
        eval_results_df = None
        metrics_df = None
        
        # Generation phase
        if not args.evaluate_only:
            print("="*60)
            print("STARTING GENERATION PHASE")
            print("="*60)
            testset_df = await generate_testset(testset_size=args.size)
        else:
            # Load existing testset
            if os.path.exists(args.testset_path):
                testset_df = pd.read_json(args.testset_path)
                print(f"✓ Loaded existing testset from {args.testset_path}")
            else:
                print(f"Error: Testset not found at {args.testset_path}")
                return
        
        # Evaluation phase
        if testset_df is not None and not args.generate_only:
            eval_results_df = await evaluate_testset(testset_df)
            
            # Metrics calculation
            if eval_results_df is not None:
                try:
                    metrics_df = await calculate_metrics(testset_df, eval_results_df)
                except Exception as e:
                    logger.warning(f"Metrics calculation failed: {e}")
                    print("Continuing with report generation...")
            
            # Generate report
            if eval_results_df is not None:
                generate_evaluation_report(testset_df, eval_results_df, metrics_df)
        
        print("\n✓ Evaluation pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in evaluation pipeline: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
