"""Query rewriting and expansion for better retrieval."""
from __future__ import annotations

import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()


async def rewrite_query(query: str, product: str) -> list[str]:
    """Rewrite query into multiple variations for better retrieval.

    Uses LLM to generate:
    - Expanded query with domain terms
    - Rephrased variations
    - Keyword extraction

    Args:
        query: Original customer question
        product: Product context

    Returns:
        List of query variations (including original)
    """
    # Import LLM client
    try:
        from llm_client.groq_provider import GroqProvider
        llm = GroqProvider()
    except Exception:
        # Fallback: return original query only
        return [query]

    prompt = f"""You are a financial product expert. A customer asked: "{query}"

Product context: {product}

Generate 2 alternative phrasings of this question that would help retrieve relevant information from a knowledge base.

Requirements:
- Keep financial domain terms
- Add relevant keywords (interest rate, eligibility, documents, etc.)
- Make variations more specific
- Keep under 30 words each

Return only the 2 alternative questions, one per line. No explanations."""

    try:
        messages = [{"role": "user", "content": prompt}]

        # Use LLM to generate variations
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return [query]

        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=200,
        )

        content = response.choices[0].message.content
        if not content:
            return [query]

        # Parse variations
        variations = [line.strip() for line in content.strip().split('\n') if line.strip()]

        # Filter out numbering and cleanup
        cleaned = []
        for var in variations:
            # Remove numbering like "1.", "2."
            var = var.lstrip('0123456789.- ')
            if var and len(var) > 10:
                cleaned.append(var)

        # Return original + variations
        return [query] + cleaned[:2]

    except Exception as e:
        print(f"Query rewriting failed: {e}")
        return [query]


async def expand_with_keywords(query: str) -> str:
    """Expand query with relevant financial keywords.

    Args:
        query: Original query

    Returns:
        Expanded query with keywords
    """
    query_lower = query.lower()

    # Keyword expansion rules
    expansions = []

    if any(word in query_lower for word in ["interest", "rate", "ब्याज"]):
        expansions.extend(["interest rate", "APR", "percentage"])

    if any(word in query_lower for word in ["document", "papers", "required"]):
        expansions.extend(["required documents", "documentation", "KYC"])

    if any(word in query_lower for word in ["eligible", "qualify"]):
        expansions.extend(["eligibility criteria", "qualification", "minimum requirements"])

    if any(word in query_lower for word in ["fee", "charge", "cost"]):
        expansions.extend(["processing fee", "charges", "costs"])

    if any(word in query_lower for word in ["tenure", "duration", "period"]):
        expansions.extend(["repayment tenure", "loan period", "duration"])

    if any(word in query_lower for word in ["amount", "limit"]):
        expansions.extend(["loan amount", "credit limit", "maximum amount"])

    # Combine original query with expansions
    if expansions:
        return f"{query} {' '.join(set(expansions))}"

    return query
