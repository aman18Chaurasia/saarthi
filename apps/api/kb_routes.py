"""Knowledge Base query endpoints for RAG chatbot."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator

import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llm_client import get_embed_provider, get_chat_provider
from rag.faiss_hybrid import FAISSHybridRetriever

router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])

# Global retriever instance (loaded once at startup)
_retriever: FAISSHybridRetriever | None = None
_INDEX_DIR = Path("kb_indices")


def get_retriever() -> FAISSHybridRetriever:
    """Get or initialize the FAISS retriever."""
    global _retriever
    if _retriever is None:
        if not _INDEX_DIR.exists():
            raise HTTPException(
                status_code=503,
                detail=f"KB indices not found at {_INDEX_DIR}. Run build_indices first."
            )
        _retriever = FAISSHybridRetriever(index_path=_INDEX_DIR)
        _retriever.load()
    return _retriever


class KBQueryRequest(BaseModel):
    """Request body for KB query."""
    query: str
    call_id: str | None = None  # Optional: include live transcript
    top_k: int = 5
    stream: bool = True  # Stream response for fast first token


class KBQueryResponse(BaseModel):
    """Response for KB query."""
    answer: str
    sources: list[dict]
    confidence: float


@router.post("/query")
async def query_kb(request: KBQueryRequest):
    """Query knowledge base with hybrid RAG.

    Args:
        request: Query request with text and optional call_id

    Returns:
        Streaming response with answer + sources
    """
    try:
        retriever = get_retriever()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Generate query embedding
    embed_provider = get_embed_provider()
    embeddings = await embed_provider.embed([request.query])
    query_embedding = np.array(embeddings[0], dtype=np.float32)  # First embedding

    # Hybrid search
    results = await asyncio.to_thread(
        retriever.hybrid_search,
        query_text=request.query,
        query_embedding=query_embedding,
        top_k=request.top_k,
    )

    # Build context from retrieved chunks
    context_parts = []
    for idx, result in enumerate(results, 1):
        source_info = f"[{idx}] {result['metadata'].get('source', 'Unknown')}"
        context_parts.append(f"{source_info}\n{result['text']}")

    context = "\n\n---\n\n".join(context_parts)

    # Add live transcript if call_id provided
    if request.call_id:
        # TODO: Fetch live transcript from DB
        # For now, just note it in context
        context = f"[Live Call Context: {request.call_id}]\n\n{context}"

    # Generate answer with LLM
    if request.stream:
        return StreamingResponse(
            _stream_answer(request.query, context, results),
            media_type="text/event-stream",
        )
    else:
        answer = await _generate_answer(request.query, context)
        return KBQueryResponse(
            answer=answer,
            sources=[
                {
                    "text": r["text"][:200] + "...",
                    "source": r["metadata"].get("source", "Unknown"),
                    "score": r["score"],
                }
                for r in results
            ],
            confidence=results[0]["score"] if results else 0.0,
        )


async def _generate_answer(query: str, context: str) -> str:
    """Generate answer from context using LLM."""
    chat_provider = get_chat_provider()

    prompt = f"""You are a helpful assistant for SAARTHI, an insurance and loan advisory platform.

Answer the user's question using ONLY the information from the provided context.
If the answer is not in the context, say "I don't have information about that in the knowledge base."

Context:
{context}

User Question: {query}

Answer (be concise and accurate):"""

    response = await chat_provider.ainvoke(prompt)
    return response.content


async def _stream_answer(
    query: str,
    context: str,
    sources: list[dict],
) -> AsyncIterator[str]:
    """Stream answer token by token for fast first response."""
    chat_provider = get_chat_provider()

    prompt = f"""You are a helpful assistant for SAARTHI, an insurance and loan advisory platform.

Answer the user's question using ONLY the information from the provided context.
If the answer is not in the context, say "I don't have information about that in the knowledge base."

Context:
{context}

User Question: {query}

Answer (be concise and accurate):"""

    # Stream LLM response
    async for chunk in chat_provider.astream(prompt):
        if hasattr(chunk, 'content') and chunk.content:
            yield f"data: {chunk.content}\n\n"

    # Send sources at end
    sources_json = [
        {
            "text": r["text"][:200] + "...",
            "source": r["metadata"].get("source", "Unknown"),
            "score": float(r["score"]),
        }
        for r in sources
    ]

    import json
    yield f"data: [SOURCES]{json.dumps(sources_json)}\n\n"
    yield "data: [DONE]\n\n"


@router.get("/health")
async def health_check():
    """Check if KB indices are loaded."""
    try:
        retriever = get_retriever()
        return {
            "status": "ok",
            "num_documents": retriever.faiss_index.ntotal if retriever.faiss_index else 0,
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
        }
