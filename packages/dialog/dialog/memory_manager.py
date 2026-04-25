"""Conversation Memory Manager with semantic retrieval.

Manages both short-term (recent turns) and long-term (embeddings) memory
for better context awareness across entire conversation.
"""
from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel


class ConversationTurn(BaseModel):
    """Single turn in conversation."""
    speaker: str  # "agent" | "customer"
    text: str
    timestamp: float
    node_name: str
    turn_index: int
    embedding: list[float] | None = None


class KeyFact(BaseModel):
    """Important fact extracted from conversation."""
    fact_type: str  # "objection", "interest", "concern", "preference"
    content: str
    mentioned_at_turn: int
    importance: float  # 0.0 - 1.0


class ConversationMemory:
    """Manages conversation memory with semantic retrieval.

    Short-term: Last 10 turns (recent context)
    Long-term: All turns with embeddings (semantic search)
    Key facts: Extracted important information
    """

    def __init__(self, embed_fn: Any = None):
        """Initialize memory.

        Args:
            embed_fn: Optional async function to generate embeddings
                     If None, falls back to simple text matching
        """
        self.short_term: list[ConversationTurn] = []
        self.long_term: list[ConversationTurn] = []
        self.key_facts: dict[str, KeyFact] = {}
        self.embed_fn = embed_fn

    async def add_turn(
        self,
        speaker: str,
        text: str,
        node_name: str,
        turn_index: int,
    ) -> None:
        """Add a conversation turn to memory."""
        turn = ConversationTurn(
            speaker=speaker,
            text=text,
            timestamp=time.time(),
            node_name=node_name,
            turn_index=turn_index,
        )

        # Generate embedding if function provided
        if self.embed_fn and text.strip():
            turn.embedding = await self.embed_fn(text)

        # Add to both memories
        self.short_term.append(turn)
        self.long_term.append(turn)

        # Keep only last 10 in short-term
        if len(self.short_term) > 10:
            self.short_term.pop(0)

        # Extract key facts from customer turns
        if speaker == "customer":
            await self._extract_key_facts(turn)

    async def _extract_key_facts(self, turn: ConversationTurn) -> None:
        """Extract important facts from customer utterance."""
        text_lower = turn.text.lower()

        # Detect objections
        objection_keywords = [
            "expensive", "costly", "high interest", "better rate",
            "too much", "afford", "budget", "cheaper", "discount"
        ]
        for keyword in objection_keywords:
            if keyword in text_lower:
                fact = KeyFact(
                    fact_type="objection",
                    content=f"Concerned about: {keyword}",
                    mentioned_at_turn=turn.turn_index,
                    importance=0.9,
                )
                self.key_facts[f"objection_{turn.turn_index}"] = fact

        # Detect interests
        interest_keywords = [
            "interested", "want", "need", "looking for", "chahiye",
            "chahta", "future", "family", "security", "investment"
        ]
        for keyword in interest_keywords:
            if keyword in text_lower:
                fact = KeyFact(
                    fact_type="interest",
                    content=f"Interested in: {keyword}",
                    mentioned_at_turn=turn.turn_index,
                    importance=0.7,
                )
                self.key_facts[f"interest_{turn.turn_index}"] = fact

        # Detect product mentions (different product interest)
        product_keywords = {
            "home loan": "home_loan",
            "housing loan": "home_loan",
            "car loan": "four_wheeler",
            "education loan": "education_loan",
            "gold loan": "gold_loan",
            "credit card": "credit_card",
        }
        for keyword, product in product_keywords.items():
            if keyword in text_lower:
                fact = KeyFact(
                    fact_type="preference",
                    content=f"Mentioned interest in: {product}",
                    mentioned_at_turn=turn.turn_index,
                    importance=0.8,
                )
                self.key_facts[f"product_{turn.turn_index}"] = fact

    async def retrieve_relevant_context(
        self,
        query: str,
        max_turns: int = 3,
    ) -> str:
        """Retrieve semantically relevant past turns.

        Args:
            query: Current query/context
            max_turns: Max number of relevant turns to retrieve

        Returns:
            Formatted context string
        """
        if not self.long_term:
            return ""

        # If we have embedding function, do semantic search
        if self.embed_fn:
            query_embedding = await self.embed_fn(query)
            scored_turns = []

            for turn in self.long_term:
                if turn.embedding:
                    # Cosine similarity
                    score = self._cosine_similarity(query_embedding, turn.embedding)
                    scored_turns.append((score, turn))

            # Sort by relevance
            scored_turns.sort(reverse=True, key=lambda x: x[0])
            relevant_turns = [turn for _, turn in scored_turns[:max_turns]]
        else:
            # Fallback: keyword matching
            relevant_turns = self._keyword_match(query, max_turns)

        # Format as context
        if not relevant_turns:
            return ""

        context_lines = ["[Earlier in conversation:]"]
        for turn in relevant_turns:
            context_lines.append(f"{turn.speaker}: {turn.text}")

        return "\n".join(context_lines)

    def _keyword_match(self, query: str, max_turns: int) -> list[ConversationTurn]:
        """Fallback: simple keyword matching."""
        query_words = set(query.lower().split())
        scored = []

        for turn in self.long_term:
            turn_words = set(turn.text.lower().split())
            overlap = len(query_words & turn_words)
            if overlap > 0:
                scored.append((overlap, turn))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [turn for _, turn in scored[:max_turns]]

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def get_key_facts_summary(self) -> str:
        """Get summary of extracted key facts."""
        if not self.key_facts:
            return ""

        # Group by type
        by_type: dict[str, list[str]] = {}
        for fact in self.key_facts.values():
            if fact.fact_type not in by_type:
                by_type[fact.fact_type] = []
            by_type[fact.fact_type].append(fact.content)

        # Format
        lines = ["[Key facts:]"]
        for fact_type, contents in by_type.items():
            lines.append(f"{fact_type}: {', '.join(contents)}")

        return "\n".join(lines)

    def get_recent_context(self, num_turns: int = 4) -> list[dict[str, str]]:
        """Get recent conversation turns as message list.

        Returns format suitable for LLM messages.
        """
        recent = self.short_term[-num_turns:] if len(self.short_term) > num_turns else self.short_term

        messages = []
        for turn in recent:
            role = "assistant" if turn.speaker == "agent" else "user"
            messages.append({"role": role, "content": turn.text})

        return messages

    def has_customer_asked_question(self) -> bool:
        """Check if customer recently asked a question."""
        for turn in self.short_term[-3:]:
            if turn.speaker == "customer" and ("?" in turn.text or any(
                q in turn.text.lower() for q in ["kya", "kaise", "kyun", "kab", "what", "how", "why"]
            )):
                return True
        return False

    def get_last_customer_question(self) -> str | None:
        """Get the last question customer asked."""
        for turn in reversed(self.short_term):
            if turn.speaker == "customer" and ("?" in turn.text or any(
                q in turn.text.lower() for q in ["kya", "kaise", "kyun", "kab", "what", "how", "why"]
            )):
                return turn.text
        return None

    def clear(self) -> None:
        """Clear all memory (for new conversation)."""
        self.short_term.clear()
        self.long_term.clear()
        self.key_facts.clear()
