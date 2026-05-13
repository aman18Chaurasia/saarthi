"""Nudge API endpoints for transcription-driven suggestions."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..db import get_session
from ..models.nudge import Nudge, NudgeHistory, NudgeTemplate

router = APIRouter()


# Request/Response models
class NudgeTemplateCreate(BaseModel):
    product: str
    trigger_type: str
    trigger_keywords: list[str]
    title: str
    suggestion: str
    priority: str = "medium"
    confidence_threshold: float = 0.7
    meta_info: dict[str, str] = {}


class NudgeTemplateUpdate(BaseModel):
    title: str | None = None
    suggestion: str | None = None
    priority: str | None = None
    enabled: bool | None = None
    confidence_threshold: float | None = None
    trigger_keywords: list[str] | None = None
    meta_info: dict[str, str] | None = None


class NudgeCreate(BaseModel):
    call_id: str
    template_id: uuid.UUID | None = None
    product: str
    route: str
    title: str
    suggestion: str
    priority: str
    priority_score: float
    confidence: float
    transcript_chunk: str
    speaker: str = "customer"
    audio_id: str | None = None
    emitted: bool = True
    suppression_reason: str | None = None
    policy_checks: dict[str, bool] = {}


class NudgeHistoryUpdate(BaseModel):
    viewed: bool | None = None
    dismissed: bool | None = None
    used: bool | None = None
    helped: bool | None = None
    feedback_text: str | None = None


# Templates endpoints
@router.get("/templates")
async def list_templates(
    product: str | None = Query(None),
    trigger_type: str | None = Query(None),
    enabled: bool | None = Query(True),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List all nudge templates with optional filters."""
    query = select(NudgeTemplate)
    if product:
        query = query.where(NudgeTemplate.product == product)
    if trigger_type:
        query = query.where(NudgeTemplate.trigger_type == trigger_type)
    if enabled is not None:
        query = query.where(NudgeTemplate.enabled == enabled)

    result = await session.exec(query)
    templates = result.all()

    return [
        {
            "id": str(t.id),
            "product": t.product,
            "trigger_type": t.trigger_type,
            "trigger_keywords": t.trigger_keywords,
            "title": t.title,
            "suggestion": t.suggestion,
            "priority": t.priority,
            "enabled": t.enabled,
            "confidence_threshold": t.confidence_threshold,
            "meta_info": t.meta_info,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in templates
    ]


@router.post("/templates")
async def create_template(
    data: NudgeTemplateCreate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a new nudge template."""
    template = NudgeTemplate(
        product=data.product,
        trigger_type=data.trigger_type,
        trigger_keywords=data.trigger_keywords,
        title=data.title,
        suggestion=data.suggestion,
        priority=data.priority,
        confidence_threshold=data.confidence_threshold,
        meta_info=data.meta_info,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)

    return {
        "id": str(template.id),
        "product": template.product,
        "trigger_type": template.trigger_type,
        "title": template.title,
        "created_at": template.created_at.isoformat(),
    }


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: str,
    data: NudgeTemplateUpdate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Update an existing nudge template."""
    result = await session.exec(
        select(NudgeTemplate).where(NudgeTemplate.id == uuid.UUID(template_id))
    )
    template = result.first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if data.title is not None:
        template.title = data.title
    if data.suggestion is not None:
        template.suggestion = data.suggestion
    if data.priority is not None:
        template.priority = data.priority
    if data.enabled is not None:
        template.enabled = data.enabled
    if data.confidence_threshold is not None:
        template.confidence_threshold = data.confidence_threshold
    if data.trigger_keywords is not None:
        template.trigger_keywords = data.trigger_keywords
    if data.meta_info is not None:
        template.meta_info = data.meta_info

    template.updated_at = datetime.utcnow()
    session.add(template)
    await session.commit()
    await session.refresh(template)

    return {"status": "updated", "id": str(template.id)}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Delete a nudge template."""
    result = await session.exec(
        select(NudgeTemplate).where(NudgeTemplate.id == uuid.UUID(template_id))
    )
    template = result.first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await session.delete(template)
    await session.commit()
    return {"status": "deleted", "id": template_id}


# Nudges endpoints
@router.get("/nudges")
async def list_nudges(
    call_id: str | None = Query(None),
    product: str | None = Query(None),
    route: str | None = Query(None),
    emitted: bool | None = Query(None),
    limit: int = Query(100, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List nudges with optional filters."""
    query = select(Nudge)
    if call_id:
        query = query.where(Nudge.call_id == call_id)
    if product:
        query = query.where(Nudge.product == product)
    if route:
        query = query.where(Nudge.route == route)
    if emitted is not None:
        query = query.where(Nudge.emitted == emitted)

    query = query.order_by(Nudge.created_at.desc()).limit(limit)
    result = await session.exec(query)
    nudges = result.all()

    return [
        {
            "id": str(n.id),
            "call_id": n.call_id,
            "template_id": str(n.template_id) if n.template_id else None,
            "product": n.product,
            "route": n.route,
            "title": n.title,
            "suggestion": n.suggestion,
            "priority": n.priority,
            "priority_score": n.priority_score,
            "confidence": n.confidence,
            "transcript_chunk": n.transcript_chunk,
            "speaker": n.speaker,
            "audio_id": n.audio_id,
            "emitted": n.emitted,
            "suppression_reason": n.suppression_reason,
            "policy_checks": n.policy_checks,
            "created_at": n.created_at.isoformat(),
        }
        for n in nudges
    ]


@router.post("/nudges")
async def create_nudge(
    data: NudgeCreate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a new nudge (called during transcription flow)."""
    nudge = Nudge(
        call_id=data.call_id,
        template_id=data.template_id,
        product=data.product,
        route=data.route,
        title=data.title,
        suggestion=data.suggestion,
        priority=data.priority,
        priority_score=data.priority_score,
        confidence=data.confidence,
        transcript_chunk=data.transcript_chunk,
        speaker=data.speaker,
        audio_id=data.audio_id,
        emitted=data.emitted,
        suppression_reason=data.suppression_reason,
        policy_checks=data.policy_checks,
    )
    session.add(nudge)
    await session.commit()
    await session.refresh(nudge)

    # Create history entry
    history = NudgeHistory(nudge_id=nudge.id, call_id=data.call_id)
    session.add(history)
    await session.commit()

    return {
        "id": str(nudge.id),
        "call_id": nudge.call_id,
        "title": nudge.title,
        "emitted": nudge.emitted,
        "created_at": nudge.created_at.isoformat(),
    }


@router.get("/nudges/{nudge_id}")
async def get_nudge(
    nudge_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get a specific nudge by ID."""
    result = await session.exec(select(Nudge).where(Nudge.id == uuid.UUID(nudge_id)))
    nudge = result.first()
    if not nudge:
        raise HTTPException(status_code=404, detail="Nudge not found")

    return {
        "id": str(nudge.id),
        "call_id": nudge.call_id,
        "template_id": str(nudge.template_id) if nudge.template_id else None,
        "product": nudge.product,
        "route": nudge.route,
        "title": nudge.title,
        "suggestion": nudge.suggestion,
        "priority": nudge.priority,
        "priority_score": nudge.priority_score,
        "confidence": nudge.confidence,
        "transcript_chunk": nudge.transcript_chunk,
        "speaker": nudge.speaker,
        "audio_id": nudge.audio_id,
        "emitted": nudge.emitted,
        "suppression_reason": nudge.suppression_reason,
        "policy_checks": nudge.policy_checks,
        "created_at": nudge.created_at.isoformat(),
    }


# History endpoints
@router.patch("/nudges/{nudge_id}/history")
async def update_nudge_history(
    nudge_id: str,
    data: NudgeHistoryUpdate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Update nudge interaction history (viewed, dismissed, used, feedback)."""
    result = await session.exec(
        select(NudgeHistory).where(NudgeHistory.nudge_id == uuid.UUID(nudge_id))
    )
    history = result.first()
    if not history:
        raise HTTPException(status_code=404, detail="Nudge history not found")

    now = datetime.utcnow()
    if data.viewed is not None and data.viewed:
        history.viewed = True
        history.viewed_at = now
    if data.dismissed is not None and data.dismissed:
        history.dismissed = True
        history.dismissed_at = now
    if data.used is not None and data.used:
        history.used = True
        history.used_at = now
    if data.helped is not None:
        history.helped = data.helped
    if data.feedback_text is not None:
        history.feedback_text = data.feedback_text

    session.add(history)
    await session.commit()
    return {"status": "updated", "nudge_id": nudge_id}


@router.get("/analytics/nudges")
async def nudge_analytics(
    product: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get nudge analytics (emit rate, usage, effectiveness)."""
    query = select(Nudge)
    if product:
        query = query.where(Nudge.product == product)

    result = await session.exec(query)
    nudges = result.all()

    total = len(nudges)
    emitted = sum(1 for n in nudges if n.emitted)
    suppressed = total - emitted

    # Get history data
    history_query = select(NudgeHistory)
    if product:
        nudge_ids = [n.id for n in nudges]
        history_query = history_query.where(NudgeHistory.nudge_id.in_(nudge_ids))  # type: ignore

    history_result = await session.exec(history_query)
    histories = history_result.all()

    viewed = sum(1 for h in histories if h.viewed)
    dismissed = sum(1 for h in histories if h.dismissed)
    used = sum(1 for h in histories if h.used)
    helped = sum(1 for h in histories if h.helped is True)

    return {
        "total_nudges": total,
        "emitted": emitted,
        "suppressed": suppressed,
        "emit_rate": round(emitted / total * 100, 1) if total > 0 else 0,
        "viewed": viewed,
        "viewed_rate": round(viewed / emitted * 100, 1) if emitted > 0 else 0,
        "dismissed": dismissed,
        "used": used,
        "usage_rate": round(used / viewed * 100, 1) if viewed > 0 else 0,
        "helped_count": helped,
        "helpfulness_rate": round(helped / used * 100, 1) if used > 0 else 0,
    }
