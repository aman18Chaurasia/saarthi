"""FAISS-based hybrid RAG with BM25 + semantic search + reranking."""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from rank_bm25 import BM25Okapi


class FAISSHybridRetriever:
    """Hybrid retriever combining FAISS (dense) + BM25 (sparse) + optional reranking."""

    def __init__(
        self,
        index_path: Path | str,
        embedding_dim: int = 768,
    ):
        """Initialize hybrid retriever.

        Args:
            index_path: Directory containing index files
            embedding_dim: Dimension of embeddings (768 for Jina v3)
        """
        self.index_path = Path(index_path)
        self.embedding_dim = embedding_dim

        # FAISS index for dense vectors
        self.faiss_index: faiss.IndexFlatIP | None = None  # Inner product (cosine sim)

        # BM25 index for keyword search
        self.bm25_index: BM25Okapi | None = None
        self.bm25_corpus: list[list[str]] = []  # Tokenized documents

        # Document store
        self.documents: list[dict[str, Any]] = []
        self.doc_ids: list[str] = []

    def build_index(
        self,
        documents: list[dict[str, Any]],
        embeddings: np.ndarray,
    ) -> None:
        """Build FAISS + BM25 indices from documents and embeddings.

        Args:
            documents: List of dicts with {id, text, metadata}
            embeddings: np.ndarray of shape (n_docs, embedding_dim)
        """
        assert len(documents) == len(embeddings), "Mismatch documents/embeddings"

        self.documents = documents
        self.doc_ids = [doc["id"] for doc in documents]

        # Build FAISS index
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
        self.faiss_index.add(embeddings.astype(np.float32))

        # Build BM25 index
        self.bm25_corpus = [self._tokenize(doc["text"]) for doc in documents]
        self.bm25_index = BM25Okapi(self.bm25_corpus)

        print(f"Built FAISS index: {self.faiss_index.ntotal} vectors")
        print(f"Built BM25 index: {len(self.bm25_corpus)} documents")

    def save(self) -> None:
        """Save indices to disk."""
        self.index_path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        if self.faiss_index:
            faiss.write_index(
                self.faiss_index,
                str(self.index_path / "faiss.index")
            )

        # Save BM25 + documents
        with open(self.index_path / "metadata.pkl", "wb") as f:
            pickle.dump({
                "bm25_corpus": self.bm25_corpus,
                "documents": self.documents,
                "doc_ids": self.doc_ids,
            }, f)

        print(f"Saved indices to {self.index_path}")

    def load(self) -> None:
        """Load indices from disk."""
        # Load FAISS
        faiss_path = self.index_path / "faiss.index"
        if faiss_path.exists():
            self.faiss_index = faiss.read_index(str(faiss_path))
        else:
            raise FileNotFoundError(f"FAISS index not found: {faiss_path}")

        # Load BM25 + documents
        metadata_path = self.index_path / "metadata.pkl"
        if metadata_path.exists():
            with open(metadata_path, "rb") as f:
                data = pickle.load(f)
                self.bm25_corpus = data["bm25_corpus"]
                self.documents = data["documents"]
                self.doc_ids = data["doc_ids"]
                self.bm25_index = BM25Okapi(self.bm25_corpus)
        else:
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")

        print(f"Loaded indices from {self.index_path}")
        print(f"  FAISS: {self.faiss_index.ntotal} vectors")
        print(f"  BM25: {len(self.bm25_corpus)} documents")

    def hybrid_search(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        alpha: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Perform hybrid search combining FAISS + BM25.

        Args:
            query_text: Raw query text for BM25
            query_embedding: Dense embedding for FAISS
            top_k: Number of results to return
            alpha: Weight for dense vs sparse (1.0 = dense only, 0.0 = sparse only)

        Returns:
            List of retrieved documents with scores
        """
        if not self.faiss_index or not self.bm25_index:
            raise ValueError("Indices not loaded. Call load() or build_index() first.")

        # 1. Dense search (FAISS)
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_embedding)
        dense_scores, dense_ids = self.faiss_index.search(query_embedding, top_k * 2)
        dense_scores = dense_scores[0]  # Shape: (top_k*2,)
        dense_ids = dense_ids[0]

        # 2. Sparse search (BM25)
        query_tokens = self._tokenize(query_text)
        bm25_scores = self.bm25_index.get_scores(query_tokens)
        sparse_top_indices = np.argsort(bm25_scores)[::-1][:top_k * 2]
        sparse_scores = bm25_scores[sparse_top_indices]

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores = self._reciprocal_rank_fusion(
            dense_ids=dense_ids,
            dense_scores=dense_scores,
            sparse_ids=sparse_top_indices,
            sparse_scores=sparse_scores,
            alpha=alpha,
        )

        # 4. Get top-k after fusion
        top_doc_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]

        # 5. Build results with normalized scores
        results = []
        # Normalize RRF scores to 0-100 range for better UX
        # Max theoretical RRF score: 2 * (1 / (k + 1)) when doc ranks #1 in both
        max_rrf_score = 2.0 / (60 + 1)  # ~0.0328
        for doc_id in top_doc_ids:
            doc = self.documents[doc_id]
            # Convert to percentage (0-100)
            normalized_score = min(100.0, (rrf_scores[doc_id] / max_rrf_score) * 100.0)
            results.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
                "score": normalized_score,
            })

        return results

    def _reciprocal_rank_fusion(
        self,
        dense_ids: np.ndarray,
        dense_scores: np.ndarray,
        sparse_ids: np.ndarray,
        sparse_scores: np.ndarray,
        alpha: float = 0.5,
        k: int = 60,
    ) -> dict[int, float]:
        """Merge dense + sparse results using RRF.

        Args:
            dense_ids: Document IDs from FAISS
            dense_scores: Scores from FAISS
            sparse_ids: Document IDs from BM25
            sparse_scores: Scores from BM25
            alpha: Weight for dense (1-alpha for sparse)
            k: RRF constant

        Returns:
            Dict mapping doc_id -> rrf_score
        """
        rrf_scores: dict[int, float] = {}

        # Dense results (weighted by alpha)
        for rank, (doc_id, score) in enumerate(zip(dense_ids, dense_scores), start=1):
            if doc_id < 0:  # FAISS returns -1 for invalid IDs
                continue
            rrf_scores[int(doc_id)] = rrf_scores.get(int(doc_id), 0.0) + alpha * (1.0 / (k + rank))

        # Sparse results (weighted by 1-alpha)
        for rank, (doc_id, score) in enumerate(zip(sparse_ids, sparse_scores), start=1):
            rrf_scores[int(doc_id)] = rrf_scores.get(int(doc_id), 0.0) + (1 - alpha) * (1.0 / (k + rank))

        return rrf_scores

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple tokenizer for BM25."""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return [token for token in text.split() if len(token) > 2]
