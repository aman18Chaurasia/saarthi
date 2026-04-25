from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from dialog.memory_manager import ConversationMemory
from dialog.objection_predictor import ObjectionPredictor
from voice.sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

LLMCallable = Callable[[list[dict[str, str]], str, str], Awaitable[Any]]
RAGCallable = Callable[[str, str | None, int], Awaitable[str]]

_QUESTION_TERMS = (
    "?",
    "kya",
    "what",
    "how",
    "kitna",
    "kitni",
    "kab",
    "kaise",
    # Hindi
    "\u0915\u094d\u092f\u093e",  # क्या
    "\u0915\u093f\u0924\u0928\u093e",  # कितना
    "\u0915\u093f\u0924\u0928\u0940",  # कितनी
    "\u0915\u092c",  # कब
    "\u0915\u0948\u0938\u0947",  # कैसे
    # Urdu
    "\u06a9\u06cc\u0627",  # کیا
    "\u06a9\u062a\u0646\u0627",  # کتنا
    "\u06a9\u062a\u0646\u06cc",  # کتنی
)

_PRODUCT_TERMS = (
    "interest",
    "rate",
    "document",
    "documents",
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
    "prepayment",
    "property",
    "eligibility",
    "gold",
    "credit card",
    # Hindi
    "\u092c\u094d\u092f\u093e\u091c",  # ब्याज
    "\u0907\u0902\u091f\u094d\u0930\u0947\u0938\u094d\u091f",  # इंट्रेस्ट
    "\u0930\u0947\u091f",  # रेट
    "\u0921\u0949\u0915\u094d\u092f\u0942\u092e\u0947\u0902\u091f",  # डॉक्यूमेंट
    "\u0932\u094b\u0928",  # लोन
    "\u092b\u0940\u0938",  # फीस
    "\u0938\u0948\u0932\u0930\u0940",  # सैलरी
    # Urdu
    "\u0642\u0631\u0636",  # قرض
    "\u0644\u0648\u0646",  # لون
    "\u0631\u06cc\u0679",  # ریٹ
    "\u0641\u06cc\u0633",  # فیس
)

_COMPLIANCE_SYSTEM_GUIDANCE = (
    "COMPLIANCE RULES:\n"
    "- Never ask the customer to share PAN number, Aadhaar number, OTP, CVV, card number, UPI PIN, "
    "bank password, or full bank account details on the call.\n"
    "- You may mention required documents in general terms, but do not request the sensitive values themselves.\n"
    "- If the customer volunteers sensitive details, tell them not to share them on the phone and continue safely."
)


def _looks_like_product_question(text: str) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in _QUESTION_TERMS) and any(
        term in normalized for term in _PRODUCT_TERMS
    )


def _insert_system_messages(
    messages: list[dict[str, str]],
    extra_messages: list[dict[str, str]],
) -> list[dict[str, str]]:
    if not extra_messages:
        return messages
    if not messages:
        return extra_messages
    if messages[0].get("role") == "system":
        return [messages[0], *extra_messages, *messages[1:]]
    return [*extra_messages, *messages]


class LiveConversationSupervisor:
    """Shared conversational wrapper for all product dialog LLM calls.

    This adds a lightweight live supervisor layer on top of the product graph:
    - shared compliance guidance
    - short-term/long-term memory
    - sentiment-aware response guidance
    - objection routing hints
    - product/RBI RAG context for live customer questions
    """

    def __init__(
        self,
        *,
        call_id: str,
        product: str,
        base_llm_fn: LLMCallable,
        rag_fn: RAGCallable | None = None,
    ) -> None:
        self._call_id = call_id
        self._product = product
        self._base_llm_fn = base_llm_fn
        self._rag_fn = rag_fn
        self._memory = ConversationMemory()
        self._sentiment_analyzer = SentimentAnalyzer()
        self._objection_predictor = ObjectionPredictor()
        self._turn_index = 0
        self._captured_slots: dict[str, Any] = {}

    async def __call__(
        self,
        messages: list[dict[str, str]],
        node_name: str,
        asr_text: str,
    ) -> Any:
        enriched_messages = list(messages)
        extra_system_messages = [{"role": "system", "content": _COMPLIANCE_SYSTEM_GUIDANCE}]

        if asr_text.strip():
            # For products with minimal prompt builders, add recent dialog turns explicitly.
            if len(messages) <= 2:
                recent_history = self._memory.get_recent_context(num_turns=4)
                if recent_history:
                    enriched_messages = [messages[0], *recent_history, *messages[1:]]

            try:
                sentiment = await self._sentiment_analyzer.analyze(asr_text)
                sentiment_guidance = await self._sentiment_analyzer.get_adaptive_response_guidance(sentiment)
                if sentiment_guidance:
                    extra_system_messages.append(
                        {"role": "system", "content": sentiment_guidance.strip()}
                    )
            except Exception as exc:
                logger.debug("Sentiment analysis failed for %s: %s", self._call_id, exc)

            try:
                memory_context = await self._memory.retrieve_relevant_context(asr_text, max_turns=3)
                key_facts = self._memory.get_key_facts_summary()
                memory_lines = [part for part in (memory_context, key_facts) if part]
                if memory_lines:
                    extra_system_messages.append(
                        {
                            "role": "system",
                            "content": "CONVERSATION MEMORY:\n" + "\n\n".join(memory_lines),
                        }
                    )
            except Exception as exc:
                logger.debug("Memory retrieval failed for %s: %s", self._call_id, exc)

            is_objection, objection_type, objection_response = self._objection_predictor.handle_reactive_objection(
                asr_text
            )
            if is_objection:
                extra_system_messages.append(
                    {
                        "role": "system",
                        "content": (
                            "SUPERVISOR ROUTE: objection_handler.\n"
                            f"The customer raised a likely '{objection_type}' objection.\n"
                            "Acknowledge the concern empathetically, answer it briefly with facts, and then steer back "
                            "to the current node objective.\n"
                            "If the customer did not actually provide the slot this node needs, keep "
                            "classified_intent='unclear' and leave slots_extracted empty.\n"
                            f"Suggested reassurance: {objection_response}"
                        ),
                    }
                )
            else:
                try:
                    preemptive_text = await self._objection_predictor.get_preemptive_script_addition(
                        current_stage=node_name,
                        customer_profile={"total_calls": max(1, self._turn_index // 2)},
                        current_slots=self._captured_slots,
                    )
                    if preemptive_text:
                        extra_system_messages.append(
                            {
                                "role": "system",
                                "content": (
                                    "SUPERVISOR NOTE: If it fits naturally, weave in this reassurance to reduce likely "
                                    f"drop-off or objection: {preemptive_text.strip()}"
                                ),
                            }
                        )
                except Exception as exc:
                    logger.debug("Objection preemption failed for %s: %s", self._call_id, exc)

            if self._rag_fn and _looks_like_product_question(asr_text):
                try:
                    rag_context = await self._rag_fn(asr_text, self._product, 3)
                    if rag_context:
                        extra_system_messages.append(
                            {
                                "role": "system",
                                "content": (
                                    "KNOWLEDGE BASE CONTEXT:\n"
                                    f"{rag_context}\n\n"
                                    "Answer the customer's product question accurately using this context first. "
                                    "Then guide them back to the current scripted objective in the same response. "
                                    "Do not invent facts that are not present in the context."
                                ),
                            }
                        )
                except Exception as exc:
                    logger.debug("RAG retrieval failed for %s: %s", self._call_id, exc)

        effective_messages = _insert_system_messages(enriched_messages, extra_system_messages)
        response = await self._base_llm_fn(effective_messages, node_name, asr_text)

        if asr_text.strip():
            await self._remember_turn("customer", asr_text, node_name)
        agent_text = getattr(response, "agent_turn_text", "")
        if agent_text:
            await self._remember_turn("agent", agent_text, node_name)

        slots_extracted = getattr(response, "slots_extracted", {}) or {}
        if isinstance(slots_extracted, dict):
            self._captured_slots.update(slots_extracted)

        return response

    async def _remember_turn(self, speaker: str, text: str, node_name: str) -> None:
        await self._memory.add_turn(
            speaker=speaker,
            text=text,
            node_name=node_name,
            turn_index=self._turn_index,
        )
        self._turn_index += 1


def build_supervised_llm_fn(
    *,
    call_id: str,
    product: str,
    base_llm_fn: LLMCallable,
    rag_fn: RAGCallable | None = None,
) -> LLMCallable:
    supervisor = LiveConversationSupervisor(
        call_id=call_id,
        product=product,
        base_llm_fn=base_llm_fn,
        rag_fn=rag_fn,
    )

    async def _wrapped_llm(
        messages: list[dict[str, str]],
        node_name: str,
        asr_text: str,
    ) -> Any:
        return await supervisor(messages, node_name, asr_text)

    return _wrapped_llm
