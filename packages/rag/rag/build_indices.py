"""Build FAISS + BM25 indices from chatbot_kb directory."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from tqdm import tqdm

from .chunker import recursive_chunk
from .faiss_hybrid import FAISSHybridRetriever

# Load .env from repo root (4 levels up from packages/rag/rag)
_env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(_env_path)


def load_documents_from_kb(kb_dir: Path) -> list[dict]:
    """Load all markdown files from KB directory.

    Args:
        kb_dir: Path to chatbot_kb directory

    Returns:
        List of documents with {id, text, metadata}
    """
    documents = []
    doc_id = 0

    # Find all markdown files
    md_files = list(kb_dir.glob("**/*.md"))
    print(f"Found {len(md_files)} markdown files in {kb_dir}")

    for md_file in tqdm(md_files, desc="Loading documents"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract metadata from filename
        relative_path = md_file.relative_to(kb_dir)
        doc_metadata = {
            "source": str(relative_path),
            "filename": md_file.name,
            "doc_type": "kb",
        }

        # Recursive chunk the document
        chunks = recursive_chunk(
            text=content,
            max_chars=800,
            overlap=100,
            doc_metadata=doc_metadata,
        )

        # Add chunks as separate documents
        for chunk in chunks:
            documents.append({
                "id": f"doc_{doc_id}",
                "text": chunk["text"],
                "metadata": chunk["metadata"],
            })
            doc_id += 1

    print(f"Created {len(documents)} chunks from {len(md_files)} documents")
    return documents


async def generate_embeddings(documents: list[dict], batch_size: int = 32) -> np.ndarray:
    """Generate embeddings for documents using Jina AI.

    Args:
        documents: List of documents with text field
        batch_size: Batch size for embedding generation

    Returns:
        np.ndarray of embeddings (n_docs, embedding_dim)
    """
    # Import here to avoid loading if not needed
    from llm_client import get_embed_provider

    embed_provider = get_embed_provider()
    texts = [doc["text"] for doc in documents]

    print(f"Generating embeddings for {len(texts)} chunks...")
    all_embeddings = []

    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
        batch = texts[i:i + batch_size]
        batch_embeddings = await embed_provider.embed(batch)
        all_embeddings.extend(batch_embeddings)

    embeddings = np.array(all_embeddings, dtype=np.float32)
    print(f"Generated embeddings with shape: {embeddings.shape}")
    return embeddings


async def build_and_save_indices(
    kb_dir: Path,
    index_dir: Path,
    embedding_dim: int = 1024,
) -> None:
    """Build FAISS + BM25 indices and save to disk.

    Args:
        kb_dir: Path to chatbot_kb directory
        index_dir: Path to save indices
        embedding_dim: Embedding dimension (1024 for Jina v3)
    """
    # 1. Load documents from KB
    documents = load_documents_from_kb(kb_dir)

    if not documents:
        print("No documents found. Exiting.")
        return

    # 2. Generate embeddings
    embeddings = await generate_embeddings(documents)

    # 3. Build indices
    retriever = FAISSHybridRetriever(
        index_path=index_dir,
        embedding_dim=embedding_dim,
    )

    retriever.build_index(documents=documents, embeddings=embeddings)

    # 4. Save to disk
    retriever.save()

    print(f"\n✓ Indices built and saved to {index_dir}")
    print(f"  Total documents: {len(documents)}")
    print(f"  Embedding dim: {embedding_dim}")


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Build FAISS + BM25 indices from KB directory"
    )
    parser.add_argument(
        "--kb-dir",
        type=Path,
        default=Path("D:/Major Project/saarthi/chatbot_kb"),
        help="Path to chatbot_kb directory",
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=Path("D:/Major Project/saarthi/kb_indices"),
        help="Path to save indices",
    )
    parser.add_argument(
        "--embedding-dim",
        type=int,
        default=1024,
        help="Embedding dimension (1024 for Jina v3)",
    )

    args = parser.parse_args()

    asyncio.run(
        build_and_save_indices(
            kb_dir=args.kb_dir,
            index_dir=args.index_dir,
            embedding_dim=args.embedding_dim,
        )
    )


if __name__ == "__main__":
    main()
