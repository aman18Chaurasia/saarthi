"""Knowledge Base query endpoints for RAG chatbot."""
from __future__ import annotations

import os
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llm_client import get_chat_provider
from rag.retriever import retrieve_context

router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])


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
        # Retrieve context using Qdrant-based RAG
        context = await retrieve_context(
            query=request.query,
            product=None,  # Could extract from call_id
            top_k=request.top_k,
            use_reranking=True,
        )

        if not context:
            raise HTTPException(
                status_code=404,
                detail="No relevant information found in knowledge base"
            )

        # Add live transcript if call_id provided
        if request.call_id:
            # TODO: Fetch live transcript from DB
            context = f"[Live Call Context: {request.call_id}]\n\n{context}"

        # Generate answer with LLM
        if request.stream:
            return StreamingResponse(
                _stream_answer(request.query, context),
                media_type="text/event-stream",
            )
        else:
            answer = await _generate_answer(request.query, context)
            return KBQueryResponse(
                answer=answer,
                sources=[],  # retrieve_context doesn't return individual chunks
                confidence=0.8,  # Placeholder
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


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


async def _stream_answer(query: str, context: str) -> AsyncIterator[str]:
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

    yield "data: [DONE]\n\n"


@router.get("/health")
async def health_check():
    """Check if Qdrant KB is accessible."""
    try:
        from qdrant_client import QdrantClient

        qdrant_url = os.environ.get("QDRANT_URL")
        qdrant_api_key = os.environ.get("QDRANT_API_KEY")

        if not qdrant_url:
            return {"status": "error", "detail": "QDRANT_URL not configured"}

        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        info = client.get_collection("saarthi_knowledge")

        return {
            "status": "ok",
            "collection": "saarthi_knowledge",
            "num_points": info.points_count,
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
        }
