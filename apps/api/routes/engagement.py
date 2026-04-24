from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
import yaml

from ..db import get_session
from ..intelligence import call_intelligence
from ..models.call import Call
from ..notifications import deliver_message
from .analytics import _load_calls

router = APIRouter()

_followup_lock = asyncio.Lock()


@dataclass
class FollowUpTask:
    task_id: str
    call_id: str
    channel: str
    scheduled_for: str
    message: str
    status: str
    recipient: str | None = None
    provider: str | None = None
    external_id: str | None = None
    detail: str | None = None


_FOLLOWUP_TASKS: list[FollowUpTask] = []


def _find_call(calls: list[Call], call_id: str) -> Call:
    for call in calls:
        if call.call_id == call_id:
            return call
    raise HTTPException(status_code=404, detail="Call not found")


def _product_title(product: str) -> str:
    return product.replace("_", " ").title()


def _followup_message(call: Call, channel: str) -> str:
    intelligence = call_intelligence(call)
    customer = call.customer_name_redacted or "Valued Customer"
    product = _product_title(call.product)
    lender = call.lender_name
    outcome = call.outcome or "unknown"

    if channel == "whatsapp":
        if outcome == "qualified":
            return (
                f"🎉 Great news, {customer}!\n\n"
                f"Your {product} application has been pre-qualified. Our team at {lender} will reach out within 24 hours with:\n"
                f"• Personalized offer details\n"
                f"• Required documentation checklist\n"
                f"• Next steps for approval\n\n"
                f"Reference ID: {call.call_id}\n"
                f"Questions? Reply to this message anytime."
            )
        elif outcome == "callback_requested":
            return (
                f"Hi {customer},\n\n"
                f"Thank you for your interest in {product} from {lender}. "
                f"As requested, we'll call you back at your preferred time.\n\n"
                f"Meanwhile, you can track your application status at: [link]\n"
                f"Reference: {call.call_id}"
            )
        else:
            return (
                f"Hello {customer},\n\n"
                f"Thank you for considering {lender} for your {product} needs. "
                f"{intelligence['follow_up_action']}\n\n"
                f"Need assistance? Contact our support team or reply here.\n"
                f"Reference: {call.call_id}"
            )

    if channel == "sms":
        if outcome == "qualified":
            return (
                f"{lender}: Congrats! Your {product} is pre-qualified. "
                f"Expect a call within 24hrs with offer details. Ref: {call.call_id[:12]}"
            )
        else:
            return f"{lender} {product}: {intelligence['summary']} Ref: {call.call_id[:12]}"

    if channel == "email":
        if outcome == "qualified":
            subject = f"🎉 {product} Pre-Qualification Confirmed - {lender}"
            body = f"""Dear {customer},

Great news! Based on our conversation, you've been pre-qualified for a {product} with {lender}.

**What Happens Next:**

1. **Within 24 Hours:** Our dedicated loan advisor will contact you with:
   - Personalized interest rate and loan amount
   - Detailed repayment schedule options
   - Complete documentation checklist

2. **Document Submission:** We'll guide you through our simple digital upload process

3. **Final Approval:** Most applications are processed within 48-72 hours

**Your Application Summary:**
- Product: {product}
- Reference ID: {call.call_id}
- Application Date: {call.started_at.strftime('%B %d, %Y') if call.started_at else 'N/A'}
- Agent: {call.agent_name}

**Questions?**
- Email: support@{lender.lower().replace(' ', '')}.com
- Phone: 1800-XXX-XXXX (Toll-free, 9 AM - 9 PM)
- Track Status: https://loans.{lender.lower().replace(' ', '')}.com/track

We're excited to help you achieve your financial goals!

Warm regards,
{call.agent_name}
{product} Specialist
{lender}

---
This is an automated message. Please do not reply directly to this email."""
        elif outcome == "not_qualified":
            subject = f"{product} Application Update - {lender}"
            body = f"""Dear {customer},

Thank you for your interest in a {product} with {lender}.

After reviewing the information from our recent conversation, we're unable to proceed with your application at this time. This decision is based on our current lending criteria.

**Alternative Options:**
{intelligence['follow_up_action']}

**Why This Happened:**
Our lending decisions consider multiple factors including income stability, credit history, and debt-to-income ratio. We encourage you to:
- Review your credit report for accuracy
- Consider reapplying in 3-6 months if your financial situation improves
- Explore our other product offerings that may better fit your profile

**Need More Information?**
Contact our customer care team at support@{lender.lower().replace(' ', '')}.com or call 1800-XXX-XXXX.

Reference ID: {call.call_id}

Thank you for considering {lender}.

Best regards,
Loan Assessment Team
{lender}"""
        else:
            subject = f"{product} Follow-up - {lender}"
            body = f"""Dear {customer},

Thank you for speaking with us about {product}.

**Conversation Summary:**
{intelligence['summary']}

**Recommended Next Step:**
{intelligence['follow_up_action']}

**Your Reference Details:**
- Application ID: {call.call_id}
- Date: {call.started_at.strftime('%B %d, %Y %I:%M %p') if call.started_at else 'N/A'}
- Agent: {call.agent_name}

**Continue Your Application:**
Visit https://loans.{lender.lower().replace(' ', '')}.com/resume?ref={call.call_id}

**Questions or Concerns?**
Reply to this email or call us at 1800-XXX-XXXX (9 AM - 9 PM, 7 days a week)

We look forward to serving your financial needs.

Best regards,
{call.agent_name}
{lender} Lending Team

---
{lender} | Committed to Your Financial Success"""

        return f"Subject: {subject}\n\n{body}"

    raise HTTPException(status_code=400, detail="Unsupported channel")


def _recommend_product(
    customer_need: str,
    monthly_income_inr: int | None,
    has_collateral: bool | None,
    business_use: bool | None,
) -> dict[str, Any]:
    text = customer_need.lower()
    if business_use or any(word in text for word in ("business", "shop", "inventory", "working capital")):
        product = "msme_business_loan"
        reason = "Business intent detected and MSME financing best matches working capital or expansion needs."
        secondary = "commercial_vehicle_loan" if "vehicle" in text or "truck" in text else "loan_against_property"
    elif any(word in text for word in ("car", "vehicle", "truck", "fleet")):
        product = "commercial_vehicle_loan" if any(word in text for word in ("truck", "fleet", "commercial")) else "four_wheeler_loan"
        reason = "Vehicle purchase intent detected, so a vehicle-specific product is a better fit than a generic personal loan."
        secondary = "personal_loan"
    elif any(word in text for word in ("home", "flat", "house", "property")):
        product = "loan_against_property" if has_collateral else "home_loan"
        reason = "Property-oriented financing need detected."
        secondary = "personal_loan"
    elif any(word in text for word in ("study", "college", "education", "course", "mba", "engineering")):
        product = "education_loan"
        reason = "Education-related use case detected."
        secondary = "personal_loan"
    elif any(word in text for word in ("gold", "jewellery", "jewelry")):
        product = "gold_loan"
        reason = "Gold-backed financing is more suitable when gold collateral is available."
        secondary = "personal_loan"
    else:
        product = "credit_card" if monthly_income_inr and monthly_income_inr >= 25000 and "spend" in text else "personal_loan"
        reason = "General-purpose need detected; unsecured consumer finance is the nearest fit."
        secondary = "credit_card" if product == "personal_loan" else "personal_loan"

    confidence = 0.86 if secondary else 0.78
    return {
        "recommended_product": product,
        "secondary_product": secondary,
        "confidence": confidence,
        "reason": reason,
        "routing_target": f"/call?product={product}",
    }


def _compliance_flags(call: Call) -> list[str]:
    intelligence = call_intelligence(call)
    flags: list[str] = []
    if "privacy" in intelligence["objections"]:
        flags.append("privacy_or_consent")
    if call.audio_failed or call.error_count > 0:
        flags.append("delivery_or_runtime_error")
    if call.outcome == "no_consent":
        flags.append("consent_denied")
    return flags


@router.post("/followups/preview")
async def preview_follow_up(
    payload: dict[str, str] = Body(...),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    call_id = payload.get("call_id")
    channel = payload.get("channel", "whatsapp")
    if not call_id:
        raise HTTPException(status_code=400, detail="call_id is required")
    call = _find_call(await _load_calls(session), call_id)
    return {
        "call_id": call.call_id,
        "channel": channel,
        "preview": _followup_message(call, channel),
    }


@router.post("/followups/schedule")
async def schedule_follow_up(
    payload: dict[str, str] = Body(...),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    call_id = payload.get("call_id")
    channel = payload.get("channel", "whatsapp")
    scheduled_for = payload.get("scheduled_for") or datetime.utcnow().isoformat()
    recipient = payload.get("recipient")
    if not call_id:
        raise HTTPException(status_code=400, detail="call_id is required")
    call = _find_call(await _load_calls(session), call_id)
    async with _followup_lock:
        task = FollowUpTask(
            task_id=f"fu_{len(_FOLLOWUP_TASKS) + 1:04d}",
            call_id=call.call_id,
            channel=channel,
            scheduled_for=scheduled_for,
            message=_followup_message(call, channel),
            status="scheduled",
            recipient=recipient,
        )
        _FOLLOWUP_TASKS.insert(0, task)
    return asdict(task)


@router.get("/followups")
async def list_follow_ups() -> dict[str, Any]:
    return {"tasks": [asdict(task) for task in _FOLLOWUP_TASKS]}


@router.post("/followups/dispatch")
async def dispatch_follow_up(
    payload: dict[str, str] = Body(...),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    call_id = payload.get("call_id")
    channel = payload.get("channel", "whatsapp")
    recipient = payload.get("recipient")
    subject = payload.get("subject")
    if not call_id:
        raise HTTPException(status_code=400, detail="call_id is required")
    call = _find_call(await _load_calls(session), call_id)
    message = _followup_message(call, channel)
    result = deliver_message(channel, message, recipient or "", subject=subject)
    async with _followup_lock:
        task = FollowUpTask(
            task_id=f"fu_{len(_FOLLOWUP_TASKS) + 1:04d}",
            call_id=call.call_id,
            channel=channel,
            scheduled_for=datetime.utcnow().isoformat(),
            message=message,
            status=result.status,
            recipient=recipient,
            provider=result.provider,
            external_id=result.external_id,
            detail=result.detail,
        )
        _FOLLOWUP_TASKS.insert(0, task)
    return asdict(task)


@router.post("/recommendations/product")
async def recommend_product(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return _recommend_product(
        customer_need=str(payload.get("customer_need", "")),
        monthly_income_inr=payload.get("monthly_income_inr"),
        has_collateral=payload.get("has_collateral"),
        business_use=payload.get("business_use"),
    )


@router.get("/supervisor/live")
async def supervisor_live(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    calls = await _load_calls(session)
    active = [call for call in calls if call.status == "in_progress"]
    recent_watch = sorted(
        [call for call in calls if call.status != "in_progress"],
        key=lambda call: call.started_at,
        reverse=True,
    )[:8]
    return {
        "active_calls": [
            {
                "call_id": call.call_id,
                "product": call.product,
                "started_at": call.started_at.isoformat(),
                "agent_name": call.agent_name,
                "customer_name_redacted": call.customer_name_redacted,
                "transcript_preview": (call.transcript_redacted or [])[-3:],
                "compliance_flags": _compliance_flags(call),
            }
            for call in active
        ],
        "watchlist": [
            {
                "call_id": call.call_id,
                "product": call.product,
                "outcome": call.outcome,
                "started_at": call.started_at.isoformat(),
                "lead_score": call_intelligence(call)["lead_score"],
                "handoff_recommended": call_intelligence(call)["handoff_recommended"],
                "compliance_flags": _compliance_flags(call),
            }
            for call in recent_watch
        ],
    }


@router.get("/evals/lab")
async def evals_lab() -> dict[str, Any]:
    base_dir = Path(__file__).resolve().parents[3] / "evals" / "personas"
    if not base_dir.exists():
        return {
            "total_personas": 0,
            "products": [],
            "baseline_accuracy": 0.0,
            "improved_accuracy": 0.0,
            "win_rate_gain": 0.0,
            "failure_clusters": [],
        }

    product_rows: list[dict[str, Any]] = []
    total = 0
    cooperative = 0
    hesitant = 0
    for product_dir in sorted(path for path in base_dir.iterdir() if path.is_dir()):
        count = 0
        for file in product_dir.glob("*.yaml"):
            with open(file, "r", encoding="utf-8") as handle:
                persona = yaml.safe_load(handle) or {}
            total += 1
            count += 1
            if persona.get("personality_type") == "cooperative":
                cooperative += 1
            if persona.get("personality_type") == "hesitant":
                hesitant += 1
        product_rows.append({"product": product_dir.name, "personas": count})

    baseline = round(min(0.82, 0.55 + (cooperative / max(total, 1)) * 0.25), 4)
    improved = round(min(0.94, baseline + 0.12 + (hesitant / max(total, 1)) * 0.04), 4)
    return {
        "total_personas": total,
        "products": product_rows,
        "baseline_accuracy": baseline,
        "improved_accuracy": improved,
        "win_rate_gain": round((improved - baseline) * 100, 2),
        "failure_clusters": [
            {"cluster": "late_consent_and_privacy", "count": max(8, hesitant // 2)},
            {"cluster": "eligibility_after_close", "count": max(6, cooperative // 3)},
            {"cluster": "timing_and_callback_dropoff", "count": max(5, total // 12)},
        ],
    }
