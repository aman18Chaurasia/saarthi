"""Embedding provider wrapper for RAG pipeline."""
from __future__ import annotations

import os
import httpx
from dotenv import load_dotenv

load_dotenv()


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using Jina AI embeddings.

    Falls back to simple zero vectors if API fails (for testing).

    Args:
        texts: List of text strings to embed

    Returns:
        List of 1024-dimensional embedding vectors
    """
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        # Fallback: return zero vectors for testing
        return [[0.0] * 1024 for _ in texts]

    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "jina-embeddings-v3",
        "input": texts,
        "task": "retrieval.passage"  # For document chunks
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
    except Exception as e:
        print(f"Embedding API error: {e}. Using fallback zero vectors.")
        return [[0.0] * 1024 for _ in texts]


async def embed_query(query: str) -> list[float]:
    """Embed a single query string.

    Args:
        query: Query text

    Returns:
        1024-dimensional embedding vector
    """
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        return [0.0] * 1024

    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "jina-embeddings-v3",
        "input": [query],
        "task": "retrieval.query"  # For search queries
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    except Exception as e:
        print(f"Query embedding error: {e}. Using fallback zero vector.")
        return [0.0] * 1024
