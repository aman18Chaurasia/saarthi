"""Document ingestion CLI for SAARTHI knowledge base.

Usage:
    python -m rag.ingest
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

from .chunker import semantic_chunk
from .embedder import embed_batch

load_dotenv()


async def ingest_documents():
    """Load all documents from fixtures and upload to Qdrant."""
    # Initialize Qdrant client
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)

    collection_name = "saarthi_knowledge"

    # Recreate collection
    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except Exception:
        pass

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
    )
    print(f"Created collection: {collection_name}")

    # Load documents
    docs_dir = Path(__file__).parents[3] / "fixtures" / "documents"
    brochures_dir = docs_dir / "brochures"
    faqs_dir = docs_dir / "rbi_faqs"

    all_chunks = []
    chunk_metadata = []

    # Process brochures
    if brochures_dir.exists():
        for brochure_file in brochures_dir.glob("*.txt"):
            product = brochure_file.stem  # e.g., "personal_loan"
            content = brochure_file.read_text(encoding="utf-8")
            chunks = semantic_chunk(content, max_chars=800)

            print(f"Loaded {len(chunks)} chunks from {brochure_file.name}")

            for chunk in chunks:
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "product": product,
                    "source": str(brochure_file.name),
                    "doc_type": "brochure"
                })

    # Process RBI FAQs
    if faqs_dir.exists():
        for faq_file in faqs_dir.glob("*.txt"):
            content = faq_file.read_text(encoding="utf-8")
            chunks = semantic_chunk(content, max_chars=800)

            print(f"Loaded {len(chunks)} chunks from {faq_file.name}")

            for chunk in chunks:
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "product": "general",
                    "source": str(faq_file.name),
                    "doc_type": "rbi_faq"
                })

    if not all_chunks:
        print("No documents found to ingest!")
        return

    print(f"\nTotal chunks to embed: {len(all_chunks)}")

    # Embed in batches
    batch_size = 10
    all_embeddings = []

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        embeddings = await embed_batch(batch)
        all_embeddings.extend(embeddings)
        print(f"Embedded batch {i//batch_size + 1}/{(len(all_chunks) + batch_size - 1)//batch_size}")

    # Upload to Qdrant
    points = [
        PointStruct(
            id=idx,
            vector=emb,
            payload={
                "text": chunk,
                **metadata
            }
        )
        for idx, (chunk, emb, metadata) in enumerate(zip(all_chunks, all_embeddings, chunk_metadata))
    ]

    client.upsert(collection_name=collection_name, points=points)
    print(f"\nUploaded {len(points)} points to Qdrant collection '{collection_name}'")

    # Verify
    collection_info = client.get_collection(collection_name)
    print(f"Collection size: {collection_info.points_count} points")


if __name__ == "__main__":
    asyncio.run(ingest_documents())
