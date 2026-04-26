"""Reranking with cross-encoder for better relevance."""
from __future__ import annotations

import os
import httpx
from typing import Any
from dotenv import load_dotenv

load_dotenv()


async def rerank_results(
    query: str,
    documents: list[str],
    top_k: int = 5,
) -> list[tuple[int, float]]:
    """Rerank documents using Jina Reranker API.

    Args:
        query: Search query
        documents: List of candidate documents
        top_k: Number of top results to return

    Returns:
        List of (original_index, relevance_score) tuples, sorted by score
    """
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        # Fallback: return original order
        return [(i, 1.0 - (i * 0.1)) for i in range(min(top_k, len(documents)))]

    url = "https://api.jina.ai/v1/rerank"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "jina-reranker-v2-base-multilingual",
        "query": query,
        "documents": documents,
        "top_n": top_k
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Extract reranked results
            results = [
                (item["index"], item["relevance_score"])
                for item in data["results"]
            ]
            return results

    except Exception as e:
        print(f"Reranker API error: {e}. Using original order.")
        # Fallback: return original order
        return [(i, 1.0 - (i * 0.1)) for i in range(min(top_k, len(documents)))]


async def rerank_and_filter(
    query: str,
    results: list[dict[str, Any]],
    top_k: int = 5,
    min_score: float = 0.3,
) -> list[dict[str, Any]]:
    """Rerank results and filter by minimum relevance score.

    Args:
        query: Search query
        results: List of result dicts with 'text' field
        top_k: Number of top results
        min_score: Minimum relevance score threshold

    Returns:
        Filtered and reranked results
    """
    if not results:
        return []

    # Extract texts
    documents = [r["text"] for r in results]

    # Rerank
    reranked_indices = await rerank_results(query, documents, top_k=len(results))

    # Rebuild results in reranked order
    reranked_results = []
    for idx, score in reranked_indices:
        if score < min_score:
            continue

        result = results[idx].copy()
        result["rerank_score"] = score
        reranked_results.append(result)

        if len(reranked_results) >= top_k:
            break

    return reranked_results
