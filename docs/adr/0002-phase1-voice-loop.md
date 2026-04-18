# ADR 0002 — Phase 1 Voice Loop: Personal Loan Vertical Slice

**Date:** 2026-04-18
**Status:** Proposed
**Deciders:** Aman Chaurasia
**Supersedes:** —
**Related:** ADR 0001 (Cloud-First Inference)

---

## Context

Phase 1 delivers a single end-to-end voice loop for the Personal Loan product. A browser client streams microphone audio over WebSocket to a FastAPI server, which runs a Pipecat-ai pipeline. The pipeline transcribes audio with Groq Whisper, drives a LangGraph dialog state machine to produce agent responses using Groq LLM, synthesises speech via ElevenLabs TTS, and streams audio frames back to the browser. Every call is persisted in Postgres with PII redacted by Microsoft Presidio.

This ADR locks the component interfaces, wire protocol, state model, error strategy, latency budget, persistence schema, and test plan so that implementation can proceed without ambiguity.

> **Model name correction:** ADR 0001 and CLAUDE.md currently reference `llama-3.1-70b-versatile`. Phase 1 uses `llama-3.3-70b-versatile`, which Groq made GA in late 2024 and which supersedes the 3.1 series. CLAUDE.md §4 and ADR 0001 must be updated before the first code commit.

---

## Decision

### 1. Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    Browser (Next.js 14)                          │
│                                                                  │
│  Microphone → MediaRecorder (PCM 16kHz mono)                    │
│  WebSocket client  ←→  ws://api/ws/call/{call_id}               │
│  Audio playback ← AudioWorklet (streamed TTS chunks)            │
│  Transcript panel ← tts_text / asr_partial events               │
└──────────────────────────┬───────────────────────────────────────┘
                           │  WebSocket (binary + JSON frames)
┌──────────────────────────▼───────────────────────────────────────┐
│                  FastAPI  apps/api                               │
│                                                                  │
│  /ws/call/{call_id}  WebSocket endpoint                         │
│  /metrics            Prometheus-compatible counters             │
│  /health             liveness probe                             │
└──────────────────────────┬───────────────────────────────────────┘
                           │  async coroutine handoff
┌──────────────────────────▼───────────────────────────────────────┐
│              Pipecat-ai Pipeline  (per-call instance)           │
│                                                                  │
│  ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  VAD frame   │    │  ASR frame      │    │  LangGraph      │ │
│  │  processor   │───▶│  processor      │───▶│  frame          │ │
│  │  (webrtcvad) │    │  (Groq Whisper) │    │  processor      │ │
│  └──────────────┘    └─────────────────┘    └────────┬────────┘ │
│                                                       │          │
│                            ┌──────────────────────────▼────────┐ │
│                            │  TTS frame processor              │ │
│                            │  (ElevenLabs streaming)           │ │
│                            └──────────────────────────┬────────┘ │
└───────────────────────────────────────────────────────┼──────────┘
                                                        │
          ┌─────────────────────────────────────────────┘
          │  audio bytes + text events → WebSocket back to browser
          │
  ┌───────▼───────────────────────────────────────────────────────┐
  │  External Cloud APIs                                          │
  │  • Groq  /openai/v1/audio/transcriptions  (Whisper large-v3) │
  │  • Groq  /openai/v1/chat/completions      (llama-3.3-70b)    │
  │  • ElevenLabs  /v1/text-to-speech/{voice_id}/stream          │
  └───────────────────────────────────────────────────────────────┘
          │
  ┌───────▼───────────────────────────────────────────────────────┐
  │  Persistence Layer                                            │
  │  • PostgreSQL 16 — calls table (SQLModel + Alembic)          │
  │  • Presidio redaction runs before every DB write             │
  │  • Redis 7 — in-flight call state cache (TTL 30 min)         │
  └───────────────────────────────────────────────────────────────┘
```

---

### 2. Data Flow Per Turn (with Timing Annotations)

Each agent turn starts when webrtcvad detects end-of-speech and ends when the last TTS audio chunk arrives at the browser. Target total: **≤ 300 ms** on Groq-hosted path.

```
t=0 ms      webrtcvad fires EndOfSpeech (~2 ms detection); Pipecat emits
            EndFrame to ASR processor. Accumulated PCM buffer (typically
            0.5–3 s) is flushed to Groq Whisper via HTTPS POST
            /audio/transcriptions.

t=0–80 ms   [ASR budget: 80 ms]
            Groq Whisper returns JSON { text, language, segments }.
            Pipecat emits TranscriptionFrame(text, is_final=True).
            WS event `asr_final` sent to browser (for live transcript panel).

t=80 ms     LangGraph frame processor receives TranscriptionFrame.
            - Updates DialogState.history with customer utterance (raw).
            - Assembles node-specific system prompt (from personal_loan.yaml)
              + few-shot examples; calls Groq LLM **once** via
              packages/llm_client/ in JSON mode (response_format=json_object).

t=80–230 ms [LangGraph + LLM budget: 150 ms]
            Groq returns a single JSON object:
              {
                "classified_intent": "affirm"|"deny"|"provide_value"|"unclear",
                "slots_extracted": { <slot_name>: <value>, ... },
                "agent_turn_text": "<≤30-word agent response>"
              }
            LangGraph validates the JSON, updates DialogState.slots from
            slots_extracted, evaluates transition conditions using
            classified_intent (see §6), then builds AgentTurn(text,
            node_name, slots_updated). WS event `agent_text` sent to browser.

t=230 ms    TTS frame processor receives TextFrame(agent_turn.text).
            Calls ElevenLabs /v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream
            with model=eleven_turbo_v2_5, output_format=pcm_16000.

t=230–290 ms [TTS first-byte budget: 60 ms]
            ElevenLabs streams first PCM chunk (~200 ms of audio).
            Pipecat forwards bytes immediately; WS sends binary `tts_audio`
            frame. Browser AudioWorklet begins playback.

t=290–300 ms [Network jitter budget: 10 ms]
            Remaining TTS chunks stream; browser plays through.
            WS event `turn_end` sent when final chunk is forwarded.

Total e2e (mic-to-speaker): ~290 ms nominal, ≤ 300 ms budget.
```

**Latency measurement:** Each processor records `start_ns` / `end_ns` using `time.perf_counter_ns()`. On `turn_end`, the pipeline emits a `LatencyFrame` with `{asr_ms, llm_ms, tts_first_byte_ms, e2e_ms}`. The FastAPI `/metrics` handler aggregates these into p50/p95 histograms.

---

### 3. WebSocket Message Protocol

**Transport:** `ws://host/ws/call/{call_id}` — one socket per call. Binary frames carry raw PCM; JSON text frames carry control events.

#### 3.1 Client → Server

| Event / Frame | Format | Payload fields | Notes |
|---|---|---|---|
| `start_call` | JSON | `{type, call_id, customer_id, product, agent_name, lender_name, customer_name}` | First message after connection opens |
| audio chunk | Binary | raw PCM int16, 16 kHz, mono, 20 ms chunks | Sent continuously while mic is open |
| `end_call` | JSON | `{type, call_id, reason}` reason: `"user_hangup"` \| `"timeout"` | Client-initiated hangup |
| `ping` | JSON | `{type}` | Keepalive every 15 s; server replies `pong` |

#### 3.2 Server → Client

| Event | Format | Payload fields | Notes |
|---|---|---|---|
| `call_accepted` | JSON | `{type, call_id, session_token}` | Ack after `start_call` processed |
| `asr_partial` | JSON | `{type, call_id, text, sequence}` | Interim ASR result; may be empty string |
| `asr_final` | JSON | `{type, call_id, text, language, duration_ms, sequence}` | Committed transcript turn |
| `agent_text` | JSON | `{type, call_id, text, node_name, turn_index}` | Agent utterance text (display before audio) |
| `tts_audio` | Binary | PCM int16, 16 kHz, mono, variable chunk size | Prefix byte `0x01` distinguishes from future video; strip before feeding AudioWorklet |
| `turn_end` | JSON | `{type, call_id, turn_index, latency:{asr_ms, llm_ms, tts_first_byte_ms, e2e_ms}}` | Signals playback complete; browser may re-enable mic |
| `call_ended` | JSON | `{type, call_id, outcome, duration_s, turn_count}` | Terminal event; triggers dashboard card |
| `pong` | JSON | `{type}` | Reply to client ping |
| `error` | JSON | `{type, call_id, code, message, retryable}` | See §3.3 |

#### 3.3 Error Frame Codes

| Code | `retryable` | Meaning |
|---|---|---|
| `ASR_TIMEOUT` | true | Groq Whisper did not respond within 3 s |
| `ASR_ERROR` | true | Groq returned 4xx/5xx |
| `LLM_TIMEOUT` | true | LLM call exceeded 5 s |
| `LLM_ERROR` | true | Groq returned 4xx/5xx |
| `TTS_TIMEOUT` | true | ElevenLabs first byte not received within 3 s |
| `TTS_ERROR` | true | ElevenLabs returned 4xx/5xx |
| `SESSION_EXPIRED` | false | call_id not found or TTL elapsed |
| `PROTOCOL_ERROR` | false | Malformed frame received |
| `INTERNAL_ERROR` | false | Unhandled exception; call will be closed |

When `retryable=true` the pipeline retries up to 2 times with 150 ms backoff before emitting the error frame and closing the call.

---

### 4. LangGraph State Shape

```python
# packages/dialog/personal_loan/state.py
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


class SlotSet(BaseModel):
    name_confirmed: bool = False
    has_time: Optional[bool] = None          # customer said they have 2 min
    monthly_income_inr: Optional[int] = None
    loan_purpose: Optional[str] = None       # "home_reno"|"travel"|"other"|…
    consent_given: Optional[bool] = None
    # populated on outcome
    outcome: Optional[Literal["qualified", "not_qualified", "no_consent",
                               "callback_requested", "dropped"]] = None


class TurnRecord(BaseModel):
    speaker: Literal["agent", "customer"]
    text: str                                # raw (not redacted); redaction happens pre-DB
    node_name: str
    turn_index: int


DialogNode = Literal[
    "opener",
    "identity_confirm",
    "qualify",
    "qualify_followup",
    "consent",
    "next_step",
    "close",
    "__end__",
]


class DialogState(BaseModel):
    call_id: str
    customer_id: str
    product: str = "personal_loan"
    agent_name: str
    lender_name: str
    customer_name: str
    current_node: DialogNode = "opener"
    history: list[TurnRecord] = Field(default_factory=list)
    slots: SlotSet = Field(default_factory=SlotSet)
    retry_count: int = 0          # per-node retries due to unclear user input
    error_count: int = 0          # API-level errors this call
    turn_index: int = 0
    # set by pipeline, not LangGraph
    asr_text: str = ""            # latest customer utterance (raw)
```

The state is serialised to Redis (JSON) keyed by `call_id` after each node, with TTL = 30 minutes. On reconnect after a mid-call disconnect the pipeline rehydrates state from Redis.

---

### 5. Node Definitions

Each node is a LangGraph `StateGraph` node (async function). It receives `DialogState`, appends to `history`, then makes a **single** Groq LLM call in JSON mode with a node-specific system prompt derived from `personal_loan.yaml`. The LLM returns one JSON object containing `classified_intent`, `slots_extracted`, and `agent_turn_text` (see §6). The node validates the response, updates `DialogState.slots`, and returns the mutated state. The Pipecat LangGraph frame processor bridges `asr_text → node → agent_turn_text`.

| Node | Trigger | Responsibility | Script reference |
|---|---|---|---|
| `Opener` | Call start (no user input yet) | Greet customer, confirm identity question | `nodes.opener` |
| `IdentityConfirm` | Customer responds to opener | Confirm the customer is the target person; check if they have 2 min | `nodes.identity_confirm` |
| `Qualify` | Identity confirmed + has_time=True | Ask for monthly income | `nodes.qualify` |
| `QualifyFollowup` | Income captured | Ask loan purpose | `nodes.qualify.follow_up` |
| `Consent` | Slots income + purpose filled | Explain data recording; request consent | `nodes.consent` |
| `NextStep` | Consent granted | Confirm SMS/email follow-up | `nodes.next_step` |
| `Close` | NextStep delivered OR consent refused OR customer has no time | Farewell; emit `call_ended` event | `nodes.close` |

Each node generates exactly **one** agent turn (≤ 30 words, per script constraint). The LLM is instructed to strictly follow the script template; it may only vary slot-filling phrases. It must not introduce new product terms, fees, or legal commitments.

---

### 6. Transition Conditions

Transitions are evaluated by the LangGraph conditional edge after each node returns. The condition function receives `DialogState` and returns the target `DialogNode`.

```
Opener
  → IdentityConfirm      always (no user input required before first agent turn)

IdentityConfirm  (customer_input = asr_text)
  → Qualify              if slots.name_confirmed AND slots.has_time == True
  → Close                if slots.has_time == False  ("customer busy")
  → IdentityConfirm      if retry_count < 2 AND intent unclear
  → Close                if retry_count >= 2          ("max retries")

Qualify  (income captured)
  → QualifyFollowup      if slots.monthly_income_inr is not None
  → Qualify              if retry_count < 2 AND income not understood
  → Close                if retry_count >= 2

QualifyFollowup  (purpose captured)
  → Consent              if slots.loan_purpose is not None
  → QualifyFollowup      if retry_count < 2
  → Close                if retry_count >= 2

Consent  (consent signal)
  → NextStep             if slots.consent_given == True
  → Close                if slots.consent_given == False  ("no consent")
  → Consent              if retry_count < 2 AND intent unclear
  → Close                if retry_count >= 2

NextStep
  → Close                always (no further branching in Phase 1)

Close
  → __end__              always
```

**Structured LLM output (Groq JSON mode):** The dialog LLM call uses `response_format={"type": "json_object"}`. The system prompt instructs the model to always return exactly three keys: `classified_intent` (one of `affirm | deny | provide_value | unclear`), `slots_extracted` (a dict of slot names to extracted values, empty dict if none), and `agent_turn_text` (the next agent utterance, ≤ 30 words). This eliminates the separate intent-classifier call, keeping the total LLM budget at 140 ms. If the response fails JSON validation (schema mismatch or parse error), the node treats it as `classified_intent=unclear` and increments `retry_count`.

---

### 7. Error Handling Strategy

#### 7.1 ASR Failure (Groq Whisper)

- **Timeout (> 3 s):** Pipecat emits `ErrorFrame(code=ASR_TIMEOUT)`; retry up to 2× with 150 ms backoff.
- **API error (4xx/5xx):** Same retry logic.
- **After 2 retries:** Send `error` WS frame to browser; increment `DialogState.error_count`; if `error_count >= 3` close call with `outcome=dropped`.
- **Empty transcript:** Treat as unclear intent; increment `retry_count` on current node (max 2 per node, same as normal unclear-intent path).

#### 7.2 LLM Timeout / Error (Groq)

- **Timeout (> 5 s):** Retry 2×. If still failing, deliver a scripted fallback utterance ("Ek minute, main check karta hoon…") using a hard-coded string from the YAML `error_fallback` key (to be added in Phase 1 YAML update).
- **After fallback:** Advance node to `Close` with `outcome=dropped`; log error with `call_id`.

#### 7.3 TTS Failure (ElevenLabs)

- **First-byte timeout (> 3 s) or API error:** Retry 2×.
- **After 2 retries:** Send `agent_text` WS event only (no audio); mark turn with `audio_failed=True` in the DB transcript JSON so the replay player shows a text-only badge.
- **Do not close the call** for TTS failure alone; the call continues in text mode.

#### 7.4 WebSocket Disconnect Mid-Turn

- **Server side:** On socket close, Pipecat pipeline receives a `EndFrame`; current in-flight API calls are cancelled via `asyncio.CancelledError`. `DialogState` is flushed to Redis with `status=interrupted`.
- **Reconnect within TTL (30 min):** Client re-sends `start_call` with same `call_id`; server rehydrates state from Redis and resumes from `current_node`.
- **No reconnect:** Background cleanup task (runs every 5 min) detects stale Redis keys (TTL elapsed), writes partial call to DB with `outcome=dropped`, then deletes the key.
- **Browser side:** On `onclose`, attempt one reconnect after 2 s with exponential backoff (max 3 attempts). Show "Reconnecting…" toast. If all retries fail, show "Call disconnected" and end-call card.

---

### 8. Latency Budget Allocation

Target: **≤ 300 ms mic-to-speaker** on Groq-hosted path (hosted environment; per ADR 0001 and CLAUDE.md §3).

| Hop | Budget | Owner | How measured |
|---|---|---|---|
| VAD end-of-speech detection | ~2 ms | webrtcvad (pure C, no torch) | `time.perf_counter_ns()` in VAD frame processor |
| PCM → Groq Whisper API (ASR) | **80 ms** | Groq (`whisper-large-v3`) | `asr_start` to `asr_end` |
| LangGraph state update + intent classify | ~10 ms | Local Python | included in LLM budget |
| Groq LLM call (`llama-3.3-70b-versatile`) | **140 ms** | Groq | `llm_start` to first complete sentence |
| ElevenLabs TTS first byte | **60 ms** | ElevenLabs (`eleven_turbo_v2_5`) | `tts_start` to first PCM chunk received |
| Network jitter (API round-trip variance) | **10 ms** | Network | difference of e2e vs sum |
| **Total** | **300 ms** | | `e2e_ms` in `turn_end` event |

**Degraded-mode targets (local laptop, no GPU):**  
Same pipeline but Groq APIs are still used; latency is identical (cloud bottleneck, not local). Local budget is also ≤ 300 ms because no local inference is used (ADR 0001).

**Breach handling:** If `e2e_ms > 300` on three consecutive turns, a Prometheus counter `latency_breach_total` is incremented and a structured log warning is emitted. No automatic circuit breaker in Phase 1.

#### 8.1 Perceived Latency

The pipeline budget above measures time from VAD EndOfSpeech to first TTS audio byte. However, the user perceives latency differently: the turn feels "slow" from the moment they stop speaking, which includes the VAD silence-padding window.

```
User stops speaking
        │
        ├── VAD silence padding (default 300 ms, tunable)
        │   webrtcvad accumulates `VAD_SILENCE_PADDING_MS` of silence
        │   before firing EndOfSpeech. This window is not included in the
        │   pipeline budget above — it is additive.
        │
        ▼ EndOfSpeech fires → pipeline starts
        │
        ├── Pipeline: ~290 ms (§8 above)
        │
        ▼ First TTS audio byte arrives at browser

Total perceived latency = VAD_SILENCE_PADDING_MS + e2e_ms
                        = 300 ms + ~290 ms = ~590 ms  (default)
                        = 200 ms + ~290 ms = ~490 ms  (tuned)
```

**Configuration:** `VAD_SILENCE_PADDING_MS` is read from the environment (`.env`). Default: `300`. Minimum enforced by code: `150` (below this webrtcvad produces excessive false end-of-speech on Hinglish code-switching).

**Trade-off:**

| Padding | Perceived latency | Risk |
|---|---|---|
| 300 ms (Phase 1 default) | ~590 ms | Safe for Hinglish; mid-sentence pauses in code-switching not mistaken for EoS |
| 200 ms | ~490 ms | May clip Hinglish sentences where the speaker pauses briefly at the code-switch boundary |
| 150 ms | ~440 ms | High false-EoS rate on Hinglish; not recommended until Phase 3 IndicConformer integration |

Phase 1 ships `VAD_SILENCE_PADDING_MS=300`. Reducing to `200` is a one-line `.env` change and can be tested manually against Phase 1 recordings before Phase 3.

---

### 9. Persistence Schema (SQLModel)

```python
# apps/api/models/call.py
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class Call(SQLModel, table=True):
    __tablename__ = "calls"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    call_id: str = Field(index=True, unique=True)   # ws session id
    customer_id: str = Field(index=True)
    product: str                                     # "personal_loan"
    agent_name: str
    lender_name: str
    customer_name_redacted: str                      # Presidio-redacted display name

    status: str                                      # "in_progress"|"completed"|"dropped"
    outcome: Optional[str] = None                    # "qualified"|"not_qualified"|"no_consent"|…

    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_s: Optional[float] = None

    turn_count: int = 0
    error_count: int = 0
    audio_failed: bool = False

    # Presidio-redacted full transcript: [{speaker, text, node, turn_index}]
    transcript_redacted: list[dict[str, Any]] = Field(
        default=[], sa_column=Column(JSONB)
    )

    # Latency stats: {asr_p50, asr_p95, llm_p50, llm_p95, tts_p50, tts_p95, e2e_p50, e2e_p95}
    latency_stats: dict[str, float] = Field(
        default={}, sa_column=Column(JSONB)
    )

    # Raw LangGraph slots at call close (non-PII values only post-redaction)
    slots_redacted: dict[str, Any] = Field(
        default={}, sa_column=Column(JSONB)
    )
```

**Alembic:** One migration per schema change. Initial migration creates `calls` table. Migration files live in `apps/api/alembic/versions/`.

**Indexes:** `call_id` (unique), `customer_id`, `(product, status, started_at)` composite.

**Retention:** In dev, a background task purges rows with `started_at < now() - 7 days` (matches audio purge policy from CLAUDE.md §5).

---

### 10. Presidio Redaction Integration Point

Presidio runs **after** the call closes, **before** any DB write or log write. It does **not** run before the LLM — the LLM sees raw transcript text to maintain dialog coherence.

```
Call closes (Close node fires __end__)
    │
    ▼
DialogState.history (list of TurnRecord, raw text)
    │
    ▼
packages/guardrail/redact.py  ←── Presidio AnalyzerEngine + AnonymizerEngine
    │   Custom recognizers:
    │     • AadhaarRecognizer  (12-digit, Verhoeff checksum)
    │     • PANRecognizer      (AAAAA0000A pattern)
    │     • LuhnCardRecognizer (13–19 digit, Luhn checksum)
    │     • PhoneINRecognizer  (10-digit Indian mobile)
    │   Standard recognizers: PERSON, EMAIL_ADDRESS, PHONE_NUMBER
    │
    ▼
redacted_history (list[dict])  ← PII replaced with <AADHAAR_REDACTED>, <PAN_REDACTED>, etc.
    │
    ▼
DB write: Call.transcript_redacted = redacted_history
          Call.slots_redacted       = redact_dict(slots)
          Call.customer_name_redacted = redact_str(customer_name)
```

**What is never stored:** Raw Aadhaar numbers, PANs, card numbers, full mobile numbers. These exist only in memory during the call's lifetime and are overwritten when the process ends.

**Log policy:** Python `logging` at WARNING+ level; any log line that would contain PII must pass through `redact_str()` before formatting. Enforced by a custom `RedactingFormatter` in `apps/api/logging_config.py`.

---

### 11. Test Plan

#### 11.1 pytest (automated, must pass in CI)

| Test | File | What it verifies |
|---|---|---|
| LangGraph happy path | `tests/dialog/test_personal_loan_graph.py` | Full Opener→Close traversal with mocked LLM responses; assert final `outcome=qualified`, all slots filled, correct node sequence |
| LangGraph retry path | same file | Customer gives unclear input twice on `Qualify`; assert `retry_count` increments; third try succeeds |
| LangGraph no-consent path | same file | Consent node receives `deny`; assert `outcome=no_consent`, transitions to Close |
| Presidio — Aadhaar | `tests/guardrail/test_redaction.py` | Inject Verhoeff-valid Aadhaar from `fixtures/fake_identifiers.py`; assert redacted string contains `<AADHAAR_REDACTED>` |
| Presidio — PAN | same file | Same for PAN pattern |
| Presidio — Luhn card | same file | Same for Luhn-valid card |
| Presidio false-negative — invalid checksum Aadhaar | same file | Inject a 12-digit number with **invalid** Verhoeff checksum (generated by `fixtures/fake_identifiers.py` with `valid=False`); assert the string is **not** redacted (recognizer must reject it) |
| Presidio false-negative — random 12-digit number | same file | Inject a random 12-digit integer that is not a valid Aadhaar (e.g. `000000000000`); assert no `<AADHAAR_REDACTED>` placeholder appears in output |
| YAML loader | `tests/scripts/test_yaml_loader.py` | `personal_loan.yaml` loads without error; all six node keys present; `<pause:wait_user/>` markers parseable |
| Intent schema | `tests/scripts/test_intent_schema.py` | `personal_loan.intents.json` validates against JSON Schema; every intent has `examples` array ≥ 3 items |
| Latency metrics | `tests/api/test_metrics.py` | `/metrics` returns 200; response contains `asr_duration_ms`, `llm_duration_ms`, `tts_duration_ms`, `e2e_duration_ms` histogram families |
| Call persistence | `tests/api/test_call_persistence.py` | After mock call completes, `calls` table row exists; `transcript_redacted` contains no raw PAN/Aadhaar strings |

All tests use `pytest-asyncio` with `asyncio_mode = "auto"`. LLM and TTS calls are mocked with `pytest-httpx`. No real API keys required in CI.

#### 11.2 Manual QA (reviewer checklist before Phase 1 sign-off)

| Check | Pass criterion |
|---|---|
| Browser mic grant | Chrome prompts for mic; granting it starts audio streaming without page reload |
| Opener fires immediately | Within 1 s of "Start call" click, agent plays greeting in browser |
| Live transcript | Customer speech appears in transcript panel as `asr_partial` events while speaking; finalises on silence |
| Happy path end-to-end | Completing all 6 nodes results in "Call ended — Qualified" card with replay button |
| Replay button | Clicking replay plays the stored TTS audio without re-calling any API |
| Dashboard persistence | After page refresh, completed call still appears in calls list |
| Latency display | `turn_end` events show `e2e_ms` in browser console; p95 ≤ 300 ms on Groq path |
| Redaction spot-check | Inspect DB `transcript_redacted` column; confirm no raw Aadhaar/PAN visible |
| Disconnect-reconnect | Close browser tab mid-call, reopen within 1 min; assert call resumes from last node |
| ElevenLabs voice | Audio sounds like the configured `ELEVENLABS_VOICE_ID`; no robotic artefacts |

---

## Consequences

### Positive

- End-to-end scope is narrow enough for a 3-week sprint (Phase 1, Weeks 2–4).
- WebSocket protocol is versioned by the `session_token`; browser client can detect API upgrades.
- LangGraph state is a pure Pydantic model — easy to snapshot, replay, and unit-test without running the full pipeline.
- Presidio integration point (post-call, pre-DB) is the lowest-risk placement: LLM retains full dialog context; stored data is always clean.
- ElevenLabs `eleven_turbo_v2_5` provides < 60 ms TTFB at ≤ 10,000 chars/month on the free tier — sufficient for Phase 1 demo volume.

### Negative / Risks

| Risk | Mitigation |
|---|---|
| ElevenLabs free tier cap (10k chars/month) | Each turn ≤ 30 words ≈ 150 chars; 10k chars ≈ 66 turns ≈ ~11 calls. Sufficient for demo; upgrade to Starter ($5/mo) if exceeded. Do not exceed without user approval (per Phase 1 constraints). |
| Groq Whisper 80 ms budget is tight | Groq p50 is ~50–70 ms for utterances < 5 s; budget includes 10 ms network. If breached, first mitigation is to reduce VAD silence padding from 300 ms to 200 ms before ASR flush. |
| LangGraph in-memory state | Redis TTL provides durability but is not transactional. On server crash, in-flight call state may be lost. Acceptable for Phase 1 demo; Phase 3 will add Postgres-backed checkpointer. |
| Presidio misses novel PII patterns | Custom recognizers cover Aadhaar/PAN/Luhn. Any other PII class (IFSC, UPI IDs) is not redacted in Phase 1. Logged as a known gap; Phase 3 adds LLM-judge second pass. |

---

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| REST polling instead of WebSocket | Cannot stream audio frames; adds ≥ 200 ms latency per turn |
| gRPC streaming | Requires gRPC client in browser (grpc-web proxy); adds infra complexity out of scope for Phase 1 |
| Presidio before LLM | Redacted text breaks coreference resolution ("your <PHONE_REDACTED>" confuses LLM); confirmed in pilot test |
| SQLite for Phase 1 | No JSONB; complex migration path to Postgres in Phase 2; Docker Compose already has Postgres running |
| XTTS-v2 HF Space as TTS | HF Space cold-start (20–40 s) violates 300 ms budget; ElevenLabs turbo model is faster for Phase 1. XTTS remains default `TTS_PROVIDER=hf_space` for Phase 2+ once keep-alive ping is implemented. |
