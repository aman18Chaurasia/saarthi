"""Post-call operational intelligence helpers for the dashboard.

These helpers intentionally stay heuristic and deterministic so the
dashboard remains available even when no online LLM is configured.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .models.call import Call

_OBJECTION_PATTERNS: dict[str, tuple[str, ...]] = {
    "interest_rate": ("interest", "rate", "expensive", "costly", "byaaj", "mehenga"),
    "eligibility": ("eligible", "eligibility", "qualify", "qualification"),
    "documents": ("document", "paper", "docs", "proof"),
    "timing": ("busy", "later", "baad", "callback", "call later"),
    "privacy": ("record", "privacy", "data", "number", "permission", "consent"),
    "trust": ("bank", "real", "fake", "fraud", "spam"),
}

_NEGATIVE_TERMS = ("no", "nahi", "nahin", "not interested", "stop", "busy", "later", "fake", "fraud")
_POSITIVE_TERMS = ("haan", "yes", "interested", "ok", "okay", "sure", "needed", "zarurat")


def _turn_texts(call: Call, speaker: str | None = None) -> list[str]:
    texts: list[str] = []
    for turn in call.transcript_redacted or []:
        if speaker and turn.get("speaker") != speaker:
            continue
        text = turn.get("text")
        if isinstance(text, str) and text.strip():
            texts.append(text.strip())
    return texts


def _joined_text(call: Call) -> str:
    return " ".join(_turn_texts(call)).lower()


def _extract_objections(call: Call) -> list[str]:
    haystack = _joined_text(call)
    found = [
        category
        for category, needles in _OBJECTION_PATTERNS.items()
        if any(needle in haystack for needle in needles)
    ]
    return found


def _sentiment_label(call: Call) -> str:
    customer_text = " ".join(_turn_texts(call, "customer")).lower()
    negative_hits = sum(term in customer_text for term in _NEGATIVE_TERMS)
    positive_hits = sum(term in customer_text for term in _POSITIVE_TERMS)
    if negative_hits >= positive_hits + 1:
        return "negative"
    if positive_hits >= negative_hits + 1:
        return "positive"
    return "neutral"


def _lead_score(call: Call, objections: list[str]) -> int:
    outcome_base = {
        "qualified": 82,
        "callback_requested": 68,
        "not_qualified": 34,
        "no_consent": 20,
        "dropped": 18,
        None: 15,
    }
    score = outcome_base.get(call.outcome, 15)

    if call.duration_s:
        if 45 <= call.duration_s <= 240:
            score += 8
        elif call.duration_s > 240:
            score += 4

    if 4 <= call.turn_count <= 14:
        score += 6
    elif call.turn_count > 14:
        score += 2

    if call.error_count == 0 and not call.audio_failed:
        score += 4
    else:
        score -= 10

    if "eligibility" in objections or "documents" in objections:
        score += 6
    if "timing" in objections and call.outcome in {"dropped", "callback_requested"}:
        score += 5
    if "privacy" in objections:
        score -= 8

    return max(0, min(100, score))


def _priority_band(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _callback_window(call: Call, objections: list[str]) -> str | None:
    if call.outcome == "qualified":
        return "Within 2 hours"
    if call.outcome == "callback_requested" or "timing" in objections:
        hour = call.started_at.hour if isinstance(call.started_at, datetime) else 12
        if hour < 12:
            return "Today 6pm-8pm"
        if hour < 17:
            return "Tomorrow 10am-12pm"
        return "Tomorrow 11am-1pm"
    if call.outcome == "dropped" and _priority_band(_lead_score(call, objections)) != "low":
        return "Next business day"
    return None


def _handoff_recommended(call: Call, objections: list[str], sentiment: str, score: int) -> bool:
    if call.outcome == "qualified":
        return True
    if score >= 70 and ("eligibility" in objections or "trust" in objections):
        return True
    if sentiment == "negative" and "privacy" in objections:
        return True
    return False


def _follow_up_action(call: Call, objections: list[str], score: int) -> str:
    if call.outcome == "qualified":
        return "Send offer summary and assign sales advisor follow-up."
    if call.outcome == "callback_requested":
        return "Schedule callback in the recommended window and retain captured qualification context."
    if call.outcome == "no_consent":
        return "Pause outreach until explicit recording/data permission is granted."
    if call.outcome == "not_qualified":
        return "Route to alternate product or nurture track with lower-threshold offers."
    if "timing" in objections and score >= 45:
        return "Retry later instead of discarding the lead."
    return "Monitor only; no immediate intervention required."


def _summary(call: Call, objections: list[str], sentiment: str) -> str:
    product = call.product.replace("_", " ")
    if call.outcome == "qualified":
        return f"Customer showed purchase intent for {product} and completed the qualification path."
    if call.outcome == "callback_requested":
        return f"Customer engaged on {product} but deferred the conversation to a later callback."
    if objections:
        top = objections[0].replace("_", " ")
        return f"Conversation on {product} surfaced {top} as the dominant blocker with {sentiment} sentiment."
    return f"Conversation on {product} ended with {call.outcome or 'unknown'} outcome and {sentiment} sentiment."


def call_intelligence(call: Call) -> dict[str, Any]:
    objections = _extract_objections(call)
    sentiment = _sentiment_label(call)
    score = _lead_score(call, objections)
    callback_window = _callback_window(call, objections)
    return {
        "lead_score": score,
        "priority": _priority_band(score),
        "sentiment": sentiment,
        "objections": objections,
        "needs_follow_up": (
            callback_window is not None
            or score >= 70
            or (call.outcome == "not_qualified" and score >= 45)
        ),
        "recommended_callback_window": callback_window,
        "handoff_recommended": _handoff_recommended(call, objections, sentiment, score),
        "follow_up_action": _follow_up_action(call, objections, score),
        "summary": _summary(call, objections, sentiment),
    }


def ops_summary(calls: list[Call]) -> dict[str, Any]:
    insights = [call_intelligence(call) for call in calls]
    if not insights:
        return {
            "high_priority_calls": 0,
            "follow_up_queue": 0,
            "handoff_queue": 0,
            "avg_lead_score": 0.0,
            "negative_sentiment_rate": 0.0,
            "top_objections": [],
        }

    objection_counts: dict[str, int] = {}
    for insight in insights:
        for objection in insight["objections"]:
            objection_counts[objection] = objection_counts.get(objection, 0) + 1

    negative_count = sum(1 for insight in insights if insight["sentiment"] == "negative")
    return {
        "high_priority_calls": sum(1 for insight in insights if insight["priority"] == "high"),
        "follow_up_queue": sum(1 for insight in insights if insight["needs_follow_up"]),
        "handoff_queue": sum(1 for insight in insights if insight["handoff_recommended"]),
        "avg_lead_score": round(
            sum(insight["lead_score"] for insight in insights) / len(insights), 2
        ),
        "negative_sentiment_rate": round((negative_count / len(insights)) * 100, 2),
        "top_objections": [
            {"objection": objection, "count": count}
            for objection, count in sorted(
                objection_counts.items(), key=lambda item: (-item[1], item[0])
            )[:5]
        ],
    }
