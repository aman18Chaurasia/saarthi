"""Text chunking utilities for RAG pipeline."""
from __future__ import annotations


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
