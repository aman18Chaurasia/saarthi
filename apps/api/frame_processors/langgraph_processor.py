"""LangGraph frame processor: drives the product dialog state machine.

On TranscriptionFrame:
  1. Check compliance on customer input (PII detection + redaction)
  2. update_state(config, {"asr_text": text})
  3. ainvoke(None, config) -> new state dict
  4. Extract last agent TurnRecord from history
  5. Agent-output compliance guard (pre-TTS)
  6. Emit TextFrame(text=agent_turn_text) + LatencyFrame(hop="llm")
"""
from __future__ import annotations

import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

from pipecat.frames.frames import Frame, TextFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from ..frames import LatencyFrame

logger = logging.getLogger(__name__)

RAGCallable = Callable[[str, str | None, int], Awaitable[str]]

_QUESTION_TERMS = (
    "?",
    "kya",
    "kiya",
    "what",
    "how",
    "kitna",
    "kitni",
    "kab",
    "kaise",
    "क्या",
    "कितना",
    "कितनी",
    "कब",
    "कैसे",
    "کیا",
    "کتنا",
    "کتنی",
)
_PRODUCT_TERMS = (
    "interest",
    "rate",
    "document",
    "amount",
    "loan",
    "fee",
    "processing",
    "approval",
    "salary",
    "income",
    "tenure",
    "emi",
    "cibil",
    "eligibility",
    "eligible",
    "qualification",
    "qualify",
    "prepayment",
    "ब्याज",
    "इंट्रेस्ट",
    "रेट",
    "डॉक्यूमेंट",
    "डाक्यूमेंट",
    "डॉकमेंट",
    "रकम",
    "लोन",
    "फीस",
    "सैलरी",
    "अप्रूवल",
    "قرض",
    "لون",
    "ریٹ",
    "ڈاکومنٹ",
    "ڈاکومنٹس",
    "امونٹ",
    "فیس",
    "سیلری",
)
_AUTO_ADVANCE_NODES = {"next_step"}
_CONSENT_REVOCATION_TERMS = (
    "do not record",
    "don't record",
    "no recording",
    "not record",
    "cannot record",
    "can't record",
    "nahi record",
    "record nahi",
    "record mat",
    "nahi kar sakte record",
    "number mat",
    "delete my number",
    "privacy",
)

# PII patterns that must never appear in agent speech
import re as _re
_AGENT_PII_PATTERNS = [
    _re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),   # card number
    _re.compile(r'\b\d{12}\b'),                                          # Aadhaar
    _re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b'),                             # PAN
    _re.compile(r'\b(otp|cvv|pin)\s*(?:is|hai|:)?\s*\d{3,8}\b', _re.I),  # OTP/CVV/PIN reveal
]
_SAFE_FALLBACK = "Ek moment, main aapko sahi jaankari dunga."


async def _check_agent_output(text: str) -> str:
    """Scan agent speech for PII before it reaches TTS. Replace with safe fallback if found."""
    for pattern in _AGENT_PII_PATTERNS:
        if pattern.search(text):
            logger.warning("Agent output compliance: PII pattern detected, replacing with fallback.")
            return _SAFE_FALLBACK
    return text


def _extract_agent_text(state: dict[str, Any]) -> str:
    """Return the last agent utterance from the state history."""
    history = state.get("history", [])
    for turn in reversed(list(history)):
        # Supports both Pydantic model instances and plain dicts
        if hasattr(turn, "speaker"):
            if turn.speaker == "agent":
                return str(turn.text)
        elif isinstance(turn, dict) and turn.get("speaker") == "agent":
            return str(turn.get("text", ""))
    return ""


def _looks_like_product_question(text: str) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in _QUESTION_TERMS) and any(
        term in normalized for term in _PRODUCT_TERMS
    )


def _looks_like_consent_revocation(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text.lower())
    return any(term in normalized for term in _CONSENT_REVOCATION_TERMS)


def _extract_labeled_value(context: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        match = re.search(
            rf"{re.escape(label)}\s*:\s*(.+?)(?=\s+-\s+[A-Z][A-Za-z ]+\s*:|\s+##|\Z)",
            context,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip(" -")
    return ""


def _extract_documents(context: str) -> str:
    match = re.search(
        r"Required Documents\s*(.+?)(?=\s+##|\Z)",
        context,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    docs = [
        item.strip(" -")
        for item in re.split(r"\s+-\s+", match.group(1))
        if item.strip(" -")
    ]
    return ", ".join(docs[:5])


def _extract_sentence(context: str, *needles: str) -> str:
    normalized = re.sub(r"\s+", " ", context)
    sentences = re.split(r"(?<=[.!?])\s+|\s+-\s+", normalized)
    for sentence in sentences:
        lower = sentence.lower()
        if all(needle in lower for needle in needles):
            return sentence.strip(" -")
    return ""


def _answer_from_rag_context(query: str, context: str) -> str:
    query_lower = query.lower()
    facts: list[str] = []

    if any(term in query_lower for term in ("document", "doc", "डॉक", "डाक", "ڈاک")):
        docs = _extract_documents(context)
        if docs:
            facts.append(f"documents: {docs}")

    if any(term in query_lower for term in ("interest", "rate", "ब्याज", "इंट्रेस्ट", "ریٹ")):
        value = _extract_labeled_value(context, ("Interest Rate",))
        if value:
            facts.append(f"interest rate: {value}")

    if any(term in query_lower for term in ("processing", "fee", "फीस", "فیس")):
        value = _extract_labeled_value(context, ("Processing Fee",))
        if value:
            facts.append(f"processing fee: {value}")

    if any(term in query_lower for term in ("amount", "loan amount", "रकम", "امونٹ")):
        value = _extract_labeled_value(context, ("Loan Amount",))
        if value:
            facts.append(f"loan amount: {value}")

    if any(term in query_lower for term in ("tenure", "duration", "time period")):
        value = _extract_labeled_value(context, ("Tenure",))
        if value:
            facts.append(f"tenure: {value}")

    if any(term in query_lower for term in ("salary", "income", "सैलरी", "آمدنی", "سیلری")):
        value = _extract_labeled_value(context, ("Minimum Monthly Income",))
        if value:
            facts.append(f"minimum monthly income: {value}")

    if any(term in query_lower for term in ("approval", "approve", "अप्रूवल")):
        value = _extract_sentence(context, "approval")
        if value:
            facts.append(value)

    if any(term in query_lower for term in ("prepayment", "pre-payment")):
        value = _extract_sentence(context, "prepayment")
        if value:
            facts.append(value)

    if not facts:
        fallback = re.sub(r"\s+", " ", context).strip()
        if fallback:
            facts.append(fallback[:280])

    if not facts:
        return "Rahul ji, is sawaal ka brochure context abhi available nahi mila."

    return f"Rahul ji, brochure ke hisaab se {'. '.join(facts[:2])}."


async def _late_turn_answer(
    query: str,
    product: str,
    rag_fn: RAGCallable | None,
) -> tuple[str | None, str]:
    if _looks_like_consent_revocation(query):
        return (
            "Theek hai, main aapki permission ke bina personal details record ya use nahi karunga. "
            "Aap eligibility ya product details pooch sakte hain.",
            "consent_recovery",
        )

    if _looks_like_product_question(query):
        if rag_fn is None:
            from rag.retriever import retrieve_context

            rag_fn = retrieve_context
        try:
            context = await rag_fn(query, product, 2)
            return _answer_from_rag_context(query, context), "rag_after_close"
        except Exception as exc:
            logger.debug(f"Late-turn RAG answer failed: {exc}")
            return (
                "Rahul ji, is product ki exact eligibility detail abhi retrieve nahi ho paayi. "
                "Aap income, amount, documents, ya interest rate ke baare mein pooch sakte hain.",
                "rag_after_close",
            )

    return None, "late_turn"


class LangGraphProcessor(FrameProcessor):
    """Manages one call's dialog graph.  Expects the graph to already have
    been started (opener invoked) before the first TranscriptionFrame arrives.

    Args:
        app:    Compiled LangGraph StateGraph (from build_graph()).
        config: {"configurable": {"thread_id": call_id}} for MemorySaver.
    """

    def __init__(
        self,
        app: Any,
        config: dict[str, Any],
        closed_rag_fn: RAGCallable | None = None,
    ) -> None:
        super().__init__()
        self._app = app
        self._config = config
        self._closed_rag_fn = closed_rag_fn

    async def _auto_advance(self) -> list[tuple[dict[str, Any], float]]:
        generated: list[tuple[dict[str, Any], float]] = []

        for _ in range(3):
            snapshot = await self._app.aget_state(self._config)
            pending = tuple(getattr(snapshot, "next", ()) or ())
            if not pending or pending[0] not in _AUTO_ADVANCE_NODES:
                break

            t0 = time.perf_counter_ns()
            result: dict[str, Any] = await self._app.ainvoke(None, self._config)
            llm_ms = (time.perf_counter_ns() - t0) / 1_000_000
            generated.append((result, llm_ms))

        return generated

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if not isinstance(frame, TranscriptionFrame):
            await self.push_frame(frame, direction)
            return

        # Check current state to avoid processing after conversation ends
        current_state = await self._app.aget_state(self._config)
        current_node = current_state.values.get("current_node", "")

        pending = tuple(getattr(current_state, "next", ()) or ())
        is_terminal_or_pending_close = current_node in ("close", "__end__") or (
            pending and pending[0] == "close"
        )

        # Keep late customer turns recoverable. This catches questions or consent
        # revocations after next_step/close without advancing the graph to END.
        if is_terminal_or_pending_close:
            t0 = time.perf_counter_ns()
            product = current_state.values.get("product", "personal_loan")
            answer, node_name = await _late_turn_answer(
                frame.text,
                product,
                self._closed_rag_fn,
            )
            if answer:
                text_frame = TextFrame(text=answer)
                text_frame.metadata["node_name"] = node_name
                text_frame.metadata["turn_index"] = current_state.values.get("turn_index", 0)
                llm_ms = (time.perf_counter_ns() - t0) / 1_000_000
                await self.push_frame(frame, direction)
                await self.push_frame(text_frame, direction)
                await self.push_frame(LatencyFrame(hop="llm", duration_ms=llm_ms), direction)
                return

            await self.push_frame(frame, direction)
            return

        asr_text = frame.text
        
        # Phase 2: Run compliance check (PII detection)
        try:
            from guardrail.compliance import check_compliance
            from guardrail.redact import redact_str
            
            compliance_result = await check_compliance(
                asr_text,
                product=current_state.values.get("product", "personal_loan")
            )
            
            if not compliance_result.get("compliant", True):
                logger.warning(f"Compliance violation detected: {compliance_result.get('violations')}")
                # Redact sensitive data from asr_text before processing
                asr_text = redact_str(asr_text)
        except Exception as e:
            logger.debug(f"Compliance check failed (continuing): {e}")

        t0 = time.perf_counter_ns()

        # Inject customer utterance and advance the dialog graph
        self._app.update_state(self._config, {"asr_text": asr_text})
        result: dict[str, Any] = await self._app.ainvoke(None, self._config)
        llm_ms = (time.perf_counter_ns() - t0) / 1_000_000
        generated_turns = [(result, llm_ms), *await self._auto_advance()]

        # Forward original transcription so downstream processors aren't stuck.
        await self.push_frame(frame, direction)

        for generated_state, generated_llm_ms in generated_turns:
            agent_text = _extract_agent_text(generated_state)
            if not agent_text:
                continue

            # Pre-TTS compliance: scan agent output for PII before synthesis
            agent_text = await _check_agent_output(agent_text)

            text_frame = TextFrame(text=agent_text)
            text_frame.metadata["node_name"] = generated_state.get("current_node", "unknown")
            text_frame.metadata["turn_index"] = generated_state.get("turn_index", 0)
            await self.push_frame(text_frame, direction)
            await self.push_frame(
                LatencyFrame(hop="llm", duration_ms=generated_llm_ms),
                direction,
            )
