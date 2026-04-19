"""RAG retrieval interface for SAARTHI knowledge base."""
from __future__ import annotations

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv

from .embedder import embed_query

load_dotenv()


async def retrieve_context(
    query: str,
    product: str | None = None,
    top_k: int = 3
) -> str:
    """Retrieve relevant context from Qdrant knowledge base.

    Args:
        query: Search query (e.g., "benefits of personal loan")
        product: Optional product filter (e.g., "personal_loan")
        top_k: Number of chunks to retrieve

    Returns:
        Concatenated context string from top-k chunks
    """
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)
    collection_name = "saarthi_knowledge"

    # Embed query
    query_vector = await embed_query(query)

    # Build filter
    query_filter = None
    if product:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="product",
                    match=MatchValue(value=product)
                )
            ]
        )

    try:
        # Search
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=top_k
        )

        # Extract text from results
        contexts = [hit.payload["text"] for hit in results]
        return "\n\n".join(contexts)

    except Exception as e:
        print(f"Qdrant retrieval error: {e}")
        return ""  # Return empty string on error
