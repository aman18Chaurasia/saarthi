"""Advanced RAG retrieval with hybrid search, reranking, and query rewriting."""
from __future__ import annotations

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv

from .embedder import embed_query
from .query_rewriter import rewrite_query, expand_with_keywords
from .reranker import rerank_and_filter

load_dotenv()


async def retrieve_context(
    query: str,
    product: str | None = None,
    top_k: int = 3,
    use_reranking: bool = True,
    use_query_expansion: bool = False,  # Disabled - breaks Hindi/Urdu queries
) -> str:
    """Retrieve relevant context using advanced RAG techniques.

    Pipeline:
    1. Query expansion/rewriting (optional)
    2. Multi-query retrieval
    3. Hybrid search (dense + sparse)
    4. Reranking with cross-encoder (optional)
    5. Context fusion

    Args:
        query: Search query (e.g., "benefits of personal loan")
        product: Optional product filter (e.g., "personal_loan")
        top_k: Number of final chunks to return
        use_reranking: Enable reranking (default True)
        use_query_expansion: Enable query expansion (default True)

    Returns:
        Concatenated context string from top-k chunks
    """
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    collection_name = "saarthi_knowledge"

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
        # Step 1: Query expansion/rewriting
        queries = [query]
        if use_query_expansion and product:
            try:
                # Expand with keywords
                expanded = await expand_with_keywords(query)
                if expanded != query:
                    queries.append(expanded)

                # Generate alternative phrasings
                variations = await rewrite_query(query, product)
                queries.extend([v for v in variations if v not in queries])

                print(f"Query variations: {len(queries)}")
            except Exception as e:
                print(f"Query expansion failed: {e}")

        # Step 2: Multi-query retrieval
        all_results = []
        seen_ids = set()

        for q in queries[:3]:  # Limit to 3 queries max
            query_vector = await embed_query(q)

            # Dense vector search
            response = client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k * 3,  # Get more for reranking
            )

            # Collect results
            for hit in response.points:
                if hit.id not in seen_ids:
                    seen_ids.add(hit.id)
                    all_results.append({
                        "text": hit.payload.get("text", ""),
                        "score": hit.score,
                        "metadata": {
                            k: v for k, v in hit.payload.items()
                            if k not in ["text", "sparse_vector"]
                        }
                    })

        if not all_results:
            print(f"[RAG] No results found for query='{query}' product={product}")
            return ""

        print(f"[RAG] Retrieved {len(all_results)} candidates for query='{query}' product={product}")
        print(f"[RAG] Top result score: {all_results[0]['score']:.3f}")

        # Step 3: Reranking (if enabled)
        if use_reranking and len(all_results) > top_k:
            try:
                all_results = await rerank_and_filter(
                    query=query,
                    results=all_results,
                    top_k=top_k,
                    min_score=0.3,
                )
                print(f"Reranked to {len(all_results)} results")
            except Exception as e:
                print(f"Reranking failed: {e}, using original ranking")
                all_results = all_results[:top_k]
        else:
            all_results = all_results[:top_k]

        # Step 4: Extract and fuse context
        contexts = [r["text"] for r in all_results if r["text"]]
        final_context = "\n\n".join(contexts)
        print(f"[RAG] Returning {len(contexts)} chunks, total {len(final_context)} chars")
        return final_context

    except Exception as e:
        print(f"Retrieval error: {e}")
        return ""
