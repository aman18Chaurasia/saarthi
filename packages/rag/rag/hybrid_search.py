"""Hybrid search combining dense vectors + sparse BM25."""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any


def bm25_tokenize(text: str) -> list[str]:
    """Simple tokenizer for BM25."""
    import re
    # Lowercase, remove punctuation, split
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return [token for token in text.split() if len(token) > 2]


def compute_bm25_sparse_vector(text: str, k1: float = 1.5, b: float = 0.75) -> dict[str, float]:
    """Compute BM25 sparse vector for a document.

    Returns term weights as sparse dict {term: weight}.
    Note: IDF computed globally during ingestion.
    """
    tokens = bm25_tokenize(text)

    if not tokens:
        return {}

    # Term frequency
    term_freq = defaultdict(int)
    for token in tokens:
        term_freq[token] += 1

    # Document length
    doc_len = len(tokens)

    # BM25 formula (simplified, assuming avg_doc_len and idf=1 for now)
    # Full IDF will be computed during ingestion with corpus stats
    avg_doc_len = 100  # Placeholder

    sparse_vector = {}
    for term, tf in term_freq.items():
        # BM25 term weight
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
        weight = numerator / denominator

        sparse_vector[term] = weight

    return sparse_vector


def reciprocal_rank_fusion(
    results_list: list[list[tuple[int, float]]],
    k: int = 60
) -> list[tuple[int, float]]:
    """Merge multiple ranked lists using RRF.

    Args:
        results_list: List of ranked results, each is [(doc_id, score), ...]
        k: RRF constant (default 60)

    Returns:
        Merged ranked list [(doc_id, rrf_score), ...]
    """
    rrf_scores = defaultdict(float)

    for ranked_list in results_list:
        for rank, (doc_id, _score) in enumerate(ranked_list, start=1):
            rrf_scores[doc_id] += 1.0 / (k + rank)

    # Sort by RRF score descending
    merged = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return merged


async def hybrid_retrieve(
    dense_client: Any,
    collection_name: str,
    query_vector: list[float],
    query_text: str,
    product_filter: Any | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Perform hybrid search combining dense and sparse retrieval.

    Args:
        dense_client: Qdrant client
        collection_name: Collection name
        query_vector: Dense embedding
        query_text: Raw query text for BM25
        product_filter: Optional Qdrant filter
        top_k: Number of results to return

    Returns:
        List of results with text and metadata
    """
    # 1. Dense vector search
    dense_results = dense_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=product_filter,
        limit=top_k * 2,  # Get more for fusion
    )

    # 2. Sparse BM25 search (using Qdrant sparse vectors if available)
    # For now, we'll simulate with keyword matching
    # In production, use Qdrant sparse vectors feature

    # Create ranked lists for RRF
    dense_ranked = [
        (hit.id, hit.score)
        for hit in dense_results.points
    ]

    # TODO: Add actual sparse search when Qdrant sparse vectors configured
    # For now, return dense results
    # In full implementation:
    # sparse_ranked = [...] from BM25 search
    # merged = reciprocal_rank_fusion([dense_ranked, sparse_ranked])

    # For now, just use dense results
    merged = dense_ranked[:top_k]

    # Fetch full documents for merged IDs
    final_results = []
    for doc_id, score in merged:
        # Find in dense_results
        for hit in dense_results.points:
            if hit.id == doc_id:
                final_results.append({
                    "text": hit.payload.get("text", ""),
                    "score": score,
                    "metadata": {
                        k: v for k, v in hit.payload.items()
                        if k != "text"
                    }
                })
                break

    return final_results
