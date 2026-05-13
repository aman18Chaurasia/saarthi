"""RAGAS evaluation for hybrid RAG system."""
from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np
from datasets import Dataset
from dotenv import load_dotenv

# Load .env from repo root (4 levels up from packages/rag/rag)
_env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(_env_path)

# Will import ragas after install completes
# from ragas import evaluate
# from ragas.metrics import context_precision, faithfulness, answer_relevancy

from .faiss_hybrid import FAISSHybridRetriever


# Test dataset: questions about insurance products in KB
TEST_QUESTIONS = [
    {
        "question": "What is a term plan?",
        "ground_truth": "A term plan is a life insurance policy that provides pure risk coverage for a specified period. It pays a death benefit if the insured dies during the term.",
        "expected_sources": ["term_plan", "life_insurance"],
    },
    {
        "question": "What happens if I stop paying premiums?",
        "ground_truth": "If you stop paying premiums, the policy may lapse or provide reduced benefits depending on the policy terms and whether there is any paid-up value.",
        "expected_sources": ["premium", "lapse"],
    },
    {
        "question": "What are the benefits of life insurance?",
        "ground_truth": "Life insurance provides financial protection to your family in case of death, and some plans offer maturity benefits, tax benefits, and riders for additional coverage.",
        "expected_sources": ["benefits", "life_insurance"],
    },
    {
        "question": "What is the minimum sum assured?",
        "ground_truth": "The minimum sum assured varies by product, but many plans require at least 5-10 times the annual premium or a minimum amount like 25 lakh rupees.",
        "expected_sources": ["sum_assured", "eligibility"],
    },
    {
        "question": "Can I surrender my policy?",
        "ground_truth": "Yes, you can surrender your policy after paying premiums for a minimum period (usually 2-3 years). You will receive the surrender value as per policy terms.",
        "expected_sources": ["surrender", "policy_servicing"],
    },
]


async def run_rag_query(
    retriever: FAISSHybridRetriever,
    question: str,
    top_k: int = 5,
) -> dict:
    """Run single RAG query and collect results.

    Args:
        retriever: FAISS hybrid retriever
        question: User question
        top_k: Number of sources to retrieve

    Returns:
        Dict with question, contexts, and answer
    """
    # Generate embedding for question
    from llm_client import get_embed_provider, get_chat_provider

    embed_provider = get_embed_provider()
    embeddings = await embed_provider.embed([question])
    query_embedding = np.array(embeddings[0], dtype=np.float32)

    # Hybrid search
    results = retriever.hybrid_search(
        query_text=question,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    # Build context from retrieved chunks
    contexts = [r["text"] for r in results]
    context_str = "\n\n---\n\n".join(contexts)

    # Generate answer with LLM
    chat_provider = get_chat_provider()
    prompt = f"""You are a helpful assistant for SAARTHI, an insurance advisory platform.

Answer the user's question using ONLY the information from the provided context.
If the answer is not in the context, say "I don't have information about that in the knowledge base."

Context:
{context_str}

User Question: {question}

Answer (be concise and accurate):"""

    response = await chat_provider.ainvoke(prompt)
    answer = response.content

    return {
        "question": question,
        "contexts": contexts,
        "answer": answer,
    }


async def evaluate_rag(
    index_path: Path = Path("D:/Major Project/saarthi/kb_indices"),
    output_path: Path | None = None,
) -> dict:
    """Run RAGAS evaluation on test dataset.

    Args:
        index_path: Path to FAISS indices
        output_path: Optional path to save results JSON

    Returns:
        Dict with RAGAS metrics and results
    """
    # Load retriever
    retriever = FAISSHybridRetriever(index_path=index_path)
    retriever.load()

    # Run queries
    print(f"Running {len(TEST_QUESTIONS)} test queries...")
    results = []
    for i, test_case in enumerate(TEST_QUESTIONS, 1):
        print(f"  [{i}/{len(TEST_QUESTIONS)}] {test_case['question'][:60]}...")
        result = await run_rag_query(retriever, test_case["question"])
        result["ground_truth"] = test_case["ground_truth"]
        results.append(result)

    # Create RAGAS dataset
    dataset_dict = {
        "question": [r["question"] for r in results],
        "answer": [r["answer"] for r in results],
        "contexts": [r["contexts"] for r in results],
        "ground_truth": [r["ground_truth"] for r in results],
    }
    dataset = Dataset.from_dict(dataset_dict)

    print("\nRunning RAGAS evaluation...")
    try:
        from ragas import evaluate
        from ragas.metrics import (
            context_precision,
            faithfulness,
            answer_relevancy,
            context_recall,
        )

        # Run evaluation
        eval_result = evaluate(
            dataset,
            metrics=[
                context_precision,
                context_recall,
                faithfulness,
                answer_relevancy,
            ],
        )

        print("\n" + "="*60)
        print("RAGAS Evaluation Results")
        print("="*60)
        for metric, score in eval_result.items():
            print(f"{metric:25s}: {score:.3f}")
        print("="*60)

        # Save results if output path provided
        if output_path:
            import json
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump({
                    "metrics": dict(eval_result),
                    "results": results,
                }, f, indent=2)
            print(f"\nResults saved to {output_path}")

        return dict(eval_result)

    except ImportError as e:
        print(f"\n⚠ RAGAS not installed yet. Run 'uv sync' first.")
        print(f"Error: {e}")
        return {}


def main():
    """CLI entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(description="Run RAGAS evaluation on RAG system")
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=Path("D:/Major Project/saarthi/kb_indices"),
        help="Path to FAISS indices",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("D:/Major Project/saarthi/evals/rag/ragas_results.json"),
        help="Path to save results JSON",
    )

    args = parser.parse_args()

    asyncio.run(evaluate_rag(
        index_path=args.index_dir,
        output_path=args.output,
    ))


if __name__ == "__main__":
    main()
