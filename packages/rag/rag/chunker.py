"""Text chunking utilities for RAG pipeline."""
from __future__ import annotations

import re
from typing import Any


def semantic_chunk(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks at sentence boundaries.

    Args:
        text: Source text to chunk
        max_chars: Maximum characters per chunk
        overlap: Overlap characters between chunks

    Returns:
        List of text chunks
    """
    # Split on sentence boundaries
    sentences = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Split on period followed by space or newline
        parts = line.replace('. ', '.|').split('|')
        sentences.extend([p.strip() for p in parts if p.strip()])

    # Group sentences into chunks
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_length + sentence_len > max_chars and current_chunk:
            # Finalize current chunk
            chunks.append(' '.join(current_chunk))

            # Start new chunk with overlap
            overlap_text = ' '.join(current_chunk)
            if len(overlap_text) > overlap:
                # Keep last few sentences for overlap
                current_chunk = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk = []
                current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_len

    # Add final chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def recursive_chunk(
    text: str,
    max_chars: int = 800,
    overlap: int = 100,
    doc_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Recursively chunk text with hierarchy preservation.

    Chunking strategy:
    1. Split by double newlines (paragraphs/sections)
    2. If chunk > max_chars, split by sentences
    3. If sentence > max_chars, split by tokens
    4. Maintain overlap between chunks
    5. Preserve metadata about parent chunks

    Args:
        text: Source text to chunk
        max_chars: Maximum characters per chunk
        overlap: Overlap characters between chunks
        doc_metadata: Document-level metadata to attach

    Returns:
        List of chunk dicts with {text, metadata}
    """
    doc_metadata = doc_metadata or {}
    chunks: list[dict[str, Any]] = []
    chunk_id = 0

    # Level 1: Split by paragraphs/sections (double newline)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    for para_idx, paragraph in enumerate(paragraphs):
        if len(paragraph) <= max_chars:
            # Paragraph fits, add as single chunk
            chunks.append({
                "text": paragraph,
                "metadata": {
                    **doc_metadata,
                    "chunk_id": chunk_id,
                    "para_index": para_idx,
                    "hierarchy_level": "paragraph",
                }
            })
            chunk_id += 1
        else:
            # Level 2: Split by sentences
            sentences = _split_sentences(paragraph)
            current_chunk = []
            current_length = 0

            for sent_idx, sentence in enumerate(sentences):
                sent_len = len(sentence)

                if sent_len > max_chars:
                    # Level 3: Sentence too large, split by tokens
                    if current_chunk:
                        # Flush current chunk first
                        chunks.append({
                            "text": ' '.join(current_chunk),
                            "metadata": {
                                **doc_metadata,
                                "chunk_id": chunk_id,
                                "para_index": para_idx,
                                "hierarchy_level": "sentence_group",
                            }
                        })
                        chunk_id += 1
                        current_chunk = []
                        current_length = 0

                    # Split long sentence by tokens
                    token_chunks = _split_by_tokens(sentence, max_chars, overlap)
                    for token_chunk in token_chunks:
                        chunks.append({
                            "text": token_chunk,
                            "metadata": {
                                **doc_metadata,
                                "chunk_id": chunk_id,
                                "para_index": para_idx,
                                "sent_index": sent_idx,
                                "hierarchy_level": "token_split",
                            }
                        })
                        chunk_id += 1

                elif current_length + sent_len > max_chars and current_chunk:
                    # Flush current chunk
                    chunks.append({
                        "text": ' '.join(current_chunk),
                        "metadata": {
                            **doc_metadata,
                            "chunk_id": chunk_id,
                            "para_index": para_idx,
                            "hierarchy_level": "sentence_group",
                        }
                    })
                    chunk_id += 1

                    # Start new chunk with overlap
                    if len(current_chunk) > 1:
                        current_chunk = current_chunk[-1:]  # Keep last sentence for overlap
                        current_length = len(current_chunk[0])
                    else:
                        current_chunk = []
                        current_length = 0

                    current_chunk.append(sentence)
                    current_length += sent_len
                else:
                    current_chunk.append(sentence)
                    current_length += sent_len

            # Flush remaining sentences
            if current_chunk:
                chunks.append({
                    "text": ' '.join(current_chunk),
                    "metadata": {
                        **doc_metadata,
                        "chunk_id": chunk_id,
                        "para_index": para_idx,
                        "hierarchy_level": "sentence_group",
                    }
                })
                chunk_id += 1

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    # Split on . ! ? followed by space or newline
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _split_by_tokens(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split text by tokens (words) with overlap."""
    tokens = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for token in tokens:
        token_len = len(token) + 1  # +1 for space

        if current_length + token_len > max_chars and current_chunk:
            # Flush current chunk
            chunks.append(' '.join(current_chunk))

            # Overlap: keep last few tokens
            overlap_tokens = int(overlap / 5)  # Rough estimate
            current_chunk = current_chunk[-overlap_tokens:] if len(current_chunk) > overlap_tokens else []
            current_length = sum(len(t) + 1 for t in current_chunk)

        current_chunk.append(token)
        current_length += token_len

    # Flush remaining
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks
