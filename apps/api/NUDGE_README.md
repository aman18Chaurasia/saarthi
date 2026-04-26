# Nudge System Implementation

Product-wise nudge/suggestion system for real-time agent assistance during transcription flows.

## Architecture

3-table schema:
- **nudge_templates**: Product-specific suggestion templates
- **nudges**: Real-time nudges generated during calls
- **nudge_history**: Tracking viewed/used/feedback

## Setup

### 1. Run Migration

```bash
cd saarthi/apps/api
alembic upgrade head
```

### 2. Seed Templates

```bash
python seed_nudges.py
```

Seeds 30+ templates across all 10 products.

## API Endpoints

### Templates
- `GET /api/templates?product={product}&trigger_type={type}` - List templates
- `POST /api/templates` - Create template
- `PATCH /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

### Nudges
- `GET /api/nudges?call_id={call_id}&product={product}` - List nudges
- `POST /api/nudges` - Create nudge (called by transcription service)
- `GET /api/nudges/{id}` - Get specific nudge

### History & Feedback
- `PATCH /api/nudges/{id}/history` - Update interaction (viewed/dismissed/used/feedback)
- `GET /api/analytics/nudges?product={product}` - Analytics dashboard

## Frontend Integration

`NudgePanel` component auto-polls for new nudges every 2s during active calls.

Display in call UI → agent can mark as used → submit feedback (helped/not helpful).

## Transcription Flow Integration

To wire nudges into transcription flow:

1. Import nudge models and routes in your transcription handler
2. When processing transcript chunk:
   ```python
   # Example pseudocode
   if trigger_detected(chunk):
       nudge = Nudge(
           call_id=call_id,
           product=product,
           route="PRODUCT_FACT",  # or OBJECTION, ELIGIBILITY
           title="Interest Rate Details",
           suggestion="Our rates start from 10.5% p.a.",
           transcript_chunk=chunk,
           confidence=0.85,
           ...
       )
       session.add(nudge)
       await session.commit()
   ```
3. Frontend polls `/api/nudges?call_id={call_id}` and displays new nudges

## Template Fields

```json
{
  "product": "personal_loan",
  "trigger_type": "product_fact",  // or objection, eligibility
  "trigger_keywords": ["interest", "rate"],
  "title": "Interest Rate Details",
  "suggestion": "Our rates start from 10.5% p.a.",
  "priority": "medium",  // low, medium, high
  "confidence_threshold": 0.7,
  "enabled": true
}
```

## Analytics

Track effectiveness:
- Emit rate (emitted vs suppressed)
- View rate
- Usage rate (used / viewed)
- Helpfulness (helped / used)

`GET /api/analytics/nudges` returns aggregate stats.

## TODO

- [ ] Hook into existing transcription pipeline (apps/api/pipeline.py or websocket handler)
- [ ] Implement keyword matching logic for template selection
- [ ] Add Redis pub/sub for real-time nudge push (instead of polling)
- [ ] Add suppression logic (cooldown, dedupe) in nudge creation
- [ ] Connect to LLM for objection-type nudges (RAG-based)
