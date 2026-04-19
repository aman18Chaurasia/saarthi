"""Tests for text chunking utilities."""
from rag.chunker import semantic_chunk


def test_chunker_splits_long_text():
    """Test chunker splits text into reasonable chunks."""
    text = """
    This is the first sentence. This is the second sentence.
    This is the third sentence. This is the fourth sentence.
    This is the fifth sentence. This is the sixth sentence.
    This is the seventh sentence. This is the eighth sentence.
    """ * 10  # Repeat to make it long

    chunks = semantic_chunk(text, max_chars=200, overlap=50)

    assert len(chunks) > 1
    assert all(len(chunk) <= 300 for chunk in chunks)  # Allow some buffer


def test_chunker_preserves_short_text():
    """Test chunker doesn't split very short text."""
    text = "This is a short sentence."

    chunks = semantic_chunk(text, max_chars=800)

    assert len(chunks) == 1
    assert chunks[0].strip() == text.strip()


def test_chunker_handles_empty_text():
    """Test chunker handles empty input gracefully."""
    chunks = semantic_chunk("")

    assert chunks == []


def test_chunker_removes_empty_lines():
    """Test chunker filters out empty lines."""
    text = """
    First line.

    Second line.


    Third line.
    """

    chunks = semantic_chunk(text, max_chars=800)

    assert len(chunks) == 1
    # Should have all three lines
    result = chunks[0]
    assert "First line" in result
    assert "Second line" in result
    assert "Third line" in result
