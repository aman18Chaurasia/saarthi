"""RAG-based real-time nudge generation from customer transcript chunks."""
from __future__ import annotations

import logging
import re
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from .models.nudge import Nudge

logger = logging.getLogger(__name__)


def _extract_question_keywords(text: str) -> list[str]:
    """Extract potential question/topic keywords from customer speech."""
    text_lower = text.lower()

    # Common question keywords
    keywords = []

    # Interest/rate related
    if any(word in text_lower for word in ["interest", "rate", "percentage", "ब्याज", "रेट"]):
        keywords.append("interest rate")

    # Tenure/duration
    if any(word in text_lower for word in ["tenure", "duration", "period", "time", "kitne"]):
        keywords.append("repayment tenure")

    # Documents
    if any(word in text_lower for word in ["document", "papers", "required", "need", "डॉक्यूमेंट"]):
        keywords.append("required documents")

    # Eligibility
    if any(word in text_lower for word in ["eligible", "qualify", "criteria", "minimum"]):
        keywords.append("eligibility criteria")

    # Amount/limit
    if any(word in text_lower for word in ["amount", "limit", "maximum", "minimum", "kitna"]):
        keywords.append("loan amount")

    # Processing/fees
    if any(word in text_lower for word in ["fee", "charge", "cost", "processing", "फीस"]):
        keywords.append("fees and charges")

    # Benefits/features
    if any(word in text_lower for word in ["benefit", "feature", "advantage", "offer"]):
        keywords.append("benefits")

    # Approval/timeline
    if any(word in text_lower for word in ["approval", "time", "when", "how long", "कब"]):
        keywords.append("approval process")

    return keywords


def _looks_like_question(text: str) -> bool:
    """Check if transcript looks like a customer question."""
    text_lower = text.lower()

    # Question markers
    if "?" in text:
        return True

    # Question words
    question_words = [
        "what", "how", "when", "where", "why", "which",
        "kya", "kaise", "kab", "kitna", "kitni",
        "क्या", "कैसे", "कब", "कितना", "کیا", "کیسے"
    ]

    if any(text_lower.startswith(word) for word in question_words):
        return True

    # Interest/feature inquiry
    if any(word in text_lower for word in ["interest", "rate", "document", "eligible", "benefit", "fee"]):
        return True

    return False


def _generate_suggestion_from_context(query: str, context: str) -> str:
    """Extract concise suggestion from RAG context."""
    # Try to find relevant sentences
    sentences = re.split(r'[.!?\n]+', context)
    relevant = []

    query_lower = query.lower()

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 20:
            continue

        # Check if sentence relevant to query
        if any(word in sentence.lower() for word in query_lower.split()):
            relevant.append(sentence)

    if relevant:
        # Take first 2 relevant sentences
        suggestion = ". ".join(relevant[:2])
        if not suggestion.endswith("."):
            suggestion += "."
        return suggestion

    # Fallback: take first substantial sentence
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 30:
            if not sentence.endswith("."):
                sentence += "."
            return sentence

    return context[:200]  # Last resort


async def generate_nudge(
    session: AsyncSession,
    call_id: str,
    product: str,
    transcript_chunk: str,
    speaker: str = "customer",
) -> Nudge | None:
    """Generate nudge from customer speech using RAG retrieval.

    Args:
        session: DB session
        call_id: Current call ID
        product: Product type (personal_loan, home_loan, etc)
        transcript_chunk: Customer speech text
        speaker: Who spoke (default: customer)

    Returns:
        Created Nudge or None if no match
    """
    if speaker != "customer":
        return None  # Only generate nudges from customer speech

    # Skip very short utterances
    if len(transcript_chunk.strip()) < 10:
        return None

    # Check if this looks like a question/inquiry
    if not _looks_like_question(transcript_chunk):
        logger.debug(f"Transcript doesn't look like question: {transcript_chunk}")
        return None

    # Extract keywords for better retrieval
    keywords = _extract_question_keywords(transcript_chunk)

    # Build query - use transcript + keywords for better RAG matching
    query = transcript_chunk
    if keywords:
        query = f"{transcript_chunk} {' '.join(keywords)}"

    logger.info(f"Querying RAG for nudge: query='{transcript_chunk}', keywords={keywords}")

    # Retrieve context from RAG
    try:
        from rag.retriever import retrieve_context

        context = await retrieve_context(
            query=query,
            product=product,
            top_k=3
        )

        if not context or len(context.strip()) < 50:
            logger.debug("RAG returned insufficient context")
            return None

        logger.info(f"RAG context retrieved: {len(context)} chars")

    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return None

    # Determine route based on keywords
    route = "PRODUCT_FACT"
    if any(word in transcript_chunk.lower() for word in ["expensive", "costly", "high", "think", "discuss"]):
        route = "OBJECTION"
    elif any(word in transcript_chunk.lower() for word in ["eligible", "qualify", "criteria"]):
        route = "ELIGIBILITY"

    # Determine title from keywords
    if keywords:
        title = keywords[0].title()
    else:
        title = "Product Information"

    # Generate suggestion from context
    suggestion = _generate_suggestion_from_context(transcript_chunk, context)

    # Priority based on route
    priority_map = {"OBJECTION": "high", "ELIGIBILITY": "medium", "PRODUCT_FACT": "medium"}
    priority = priority_map.get(route, "medium")

    priority_score_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
    priority_score = priority_score_map.get(priority, 0.5)

    # Confidence based on context quality
    confidence = min(0.95, 0.6 + (len(context) / 500))

    # Policy checks
    policy_checks = {
        "rag_retrieved": True,
        "context_sufficient": len(context) >= 50,
        "looks_like_question": True,
    }

    # Create nudge
    nudge = Nudge(
        call_id=call_id,
        template_id=None,  # RAG-based, no template
        product=product,
        route=route,
        title=title,
        suggestion=suggestion,
        priority=priority,
        priority_score=priority_score,
        confidence=confidence,
        transcript_chunk=transcript_chunk,
        speaker=speaker,
        emitted=True,
        suppression_reason=None,
        policy_checks=policy_checks,
    )

    session.add(nudge)
    await session.commit()
    await session.refresh(nudge)

    # Create history entry
    from .models.nudge import NudgeHistory
    history = NudgeHistory(nudge_id=nudge.id, call_id=call_id)
    session.add(history)
    await session.commit()

    logger.info(
        f"Generated RAG-based nudge {nudge.id} for call {call_id}: "
        f"{title} (confidence={confidence:.2f}, route={route})"
    )

    return nudge
