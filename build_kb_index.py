"""Build Qdrant collection from chatbot_kb markdown files."""
import asyncio
import os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

load_dotenv()

# Import from rag package
import sys
sys.path.insert(0, str(Path(__file__).parent))
from packages.rag.rag.embedder import embed_batch


async def main():
    """Ingest chatbot_kb into Qdrant."""
    # Connect to Qdrant
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)
    collection_name = "saarthi_knowledge"

    # Recreate collection
    try:
        client.delete_collection(collection_name)
        print(f"[OK] Deleted old collection: {collection_name}")
    except Exception:
        pass

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
    )
    print(f"[OK] Created collection: {collection_name}")

    # Load all markdown files from chatbot_kb
    kb_dir = Path("chatbot_kb")
    all_chunks = []
    all_metadata = []

    for md_file in kb_dir.glob("*.md"):
        if md_file.name.startswith("README"):
            continue

        print(f"Reading {md_file.name}...")
        content = md_file.read_text(encoding="utf-8")

        # Simple chunking by sections (split on ## headers)
        sections = content.split("\n##")

        for idx, section in enumerate(sections):
            section = section.strip()
            if not section or len(section) < 50:
                continue

            # Extract product name from filename
            product = md_file.stem.replace("_kb", "").replace("_", " ")

            all_chunks.append(section)
            all_metadata.append({
                "source": md_file.name,
                "product": product,
                "section_idx": idx,
                "doc_type": "kb"
            })

    print(f"\n[OK] Loaded {len(all_chunks)} chunks from {len(list(kb_dir.glob('*.md')))} files")

    # Embed in batches
    print("\nEmbedding chunks...")
    batch_size = 50
    all_embeddings = []

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        embeddings = await embed_batch(batch)
        all_embeddings.extend(embeddings)
        print(f"  Embedded {min(i + batch_size, len(all_chunks))}/{len(all_chunks)}")

    # Upload to Qdrant
    print("\nUploading to Qdrant...")
    points = []
    for idx, (chunk, embedding, metadata) in enumerate(zip(all_chunks, all_embeddings, all_metadata)):
        points.append(
            PointStruct(
                id=idx,
                vector=embedding,
                payload={
                    "text": chunk,
                    **metadata
                }
            )
        )

    client.upsert(collection_name=collection_name, points=points)
    print(f"[OK] Uploaded {len(points)} points")

    # Verify
    collection_info = client.get_collection(collection_name)
    print(f"\n[OK] Collection ready: {collection_info.vectors_count} vectors")


if __name__ == "__main__":
    asyncio.run(main())
