# SAARTHI — Claude Code Project Spec

**Self-Adaptive AI for Responsible Tele-conversational Human Interaction in BFSI**

> This file is auto-loaded by Claude Code in every session. Read it before doing anything else.
> Full 16-week breakdown: `docs/SAARTHI-Project-Plan.md`. Starter prompts: `docs/Claude-Code-Starter-Prompt.md`.

---

## 1. Project Summary

SAARTHI is a production-style, multi-agent, self-improving outbound voice agent for Indian lending products, built as a final-year major project targeting publishable novelty. It qualifies leads across 10 BFSI products via a streaming voice pipeline (ASR → LangGraph multi-agent dialog → TTS), with a real-time compliance guardrail, Hinglish code-switching, and an RLAIF self-improvement loop driven by a Synthetic Persona Gym.

---

## 2. Product Scope (10 products, all required by rubric)

1. Home Loan
2. Personal Loan ← Phase 1 pilot
3. Unsecured Loan
4. Loan Against Property (LAP / Secured)
5. Gold Loan
6. Commercial Vehicle Loan
7. Four-Wheeler Loan
8. Education Loan
9. MSME Business Loan
10. Credit Card Acquisition

Each product gets: a script YAML, an intent+slot schema, an eligibility ruleset in Neo4j, and at least 3 demo recordings (success / failure / edge case).

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────┐
│            Next.js 14 Dashboard             │
│  (live transcript · analytics · replay)     │
└────────────────────┬────────────────────────┘
                     │ WebSocket / SSE
┌────────────────────▼────────────────────────┐
│           FastAPI Orchestrator              │
│        (Pipecat-ai streaming pipeline)      │
└──────┬──────────┬──────────┬───────┬────────┘
       │          │          │       │
  ┌────▼───┐ ┌────▼──────┐ ┌▼────┐ ┌▼──────────────┐
  │  ASR   │ │ LangGraph │ │ TTS │ │  Compliance   │
  │faster- │ │Multi-Agent│ │XTTS │ │  Guardrail    │
  │whisper │ │Dialog Mgr │ │ v2  │ │(Presidio+LLM) │
  │+Indic  │ └─────┬─────┘ └─────┘ └───────────────┘
  │Conform │       │
  └────────┘ ┌─────┼──────────┐
             │     │          │
       ┌─────▼──┐ ┌▼────────┐ ┌▼──────────────┐
       │Qualif- │ │Object-  │ │  Eligibility  │
       │ier     │ │ion Hdlr │ │  Engine       │
       │Agent   │ │Agent    │ │  (Neo4j KG)   │
       └────────┘ └─────────┘ └───────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │      Persona Gym        │
                        │  (LLM-driven synthetic  │
                        │   customers, 500+ YAML) │
                        └────────────┬────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │    RLAIF / DPO Trainer  │
                        │  (LoRA on dialog model) │
                        └─────────────────────────┘

Storage : PostgreSQL 16 · Qdrant · Neo4j 5 · MinIO/S3
Bus     : Redis 7 pub/sub
Obs     : OpenTelemetry → Grafana
```

### Component Choices

| Concern | Choice | Notes |
|---|---|---|
| ASR (English) | `faster-whisper` large-v3 int8 | local |
| ASR (Hindi/Hinglish) | AI4Bharat `IndicConformer` | fallback to Whisper IndicSUPERB fine-tune |
| VAD / barge-in | `silero-vad` via Pipecat-ai | |
| TTS / voice clone | `Coqui XTTS-v2` (Apache 2.0) | reference sample at `packages/voice/samples/reference.wav` |
| Dialog LLM (local) | `llama3.1:8b` via Ollama | |
| Dialog LLM (hosted) | `llama-3.1-70b-versatile` via Groq | swapped via `LLM_PROVIDER=groq` |
| Embeddings | `nomic-embed-text` via Ollama | |
| Orchestration | LangGraph + LangSmith tracing | |
| Realtime pipeline | Pipecat-ai | handles VAD + ASR + LLM + TTS + barge-in |
| PII detection | Microsoft Presidio + LLM-as-judge | custom recognizers for PAN, Aadhaar, Luhn cards |
| RAG | Qdrant | indexed over masked product brochures + RBI FAQs |
| NLU (Hinglish) | MuRIL / IndicBERT fine-tuned | ~200 utterances/intent, LLM-assisted labeling |
| Eval | DeepEval / Ragas (LLM-as-judge) | |
| Telephony demo | Twilio Voice free tier | browser WebRTC is primary demo path |

### Latency Budget

| Env | Target |
|---|---|
| Local (laptop) | < 500 ms mic-to-speaker |
| Hosted (Groq) | < 300 ms |

---

## 4. LLM Configuration

```
LLM_PROVIDER=ollama          # ollama | groq
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBED_MODEL=nomic-embed-text
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_API_KEY=<secret>
```

All LLM calls must go through a thin `packages/llm_client/` wrapper that reads `LLM_PROVIDER` and routes accordingly. No hard-coded model names outside that wrapper and `CLAUDE.md`.

---

## 5. Coding Conventions

### Python (apps/api, packages/*)

- **Version:** Python 3.11, managed via `uv`.
- **Linting / types:** `ruff` + `mypy --strict`. CI fails on any error.
- **Testing:** `pytest` with `pytest-asyncio`. Every module needs a test.
- **Data models:** `Pydantic v2` for request/response; `SQLModel` for ORM; `Alembic` for migrations.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, etc.).
- **Secrets:** `.env` only — never committed. Use `python-dotenv` locally.
- **PII rule:** No real PAN / Aadhaar / card numbers anywhere in source or fixtures. Use `fixtures/fake_identifiers.py` (Verhoeff-valid Aadhaar, Luhn-valid cards).

### TypeScript (apps/web)

- **Framework:** Next.js 14 App Router, TypeScript strict.
- **UI:** shadcn/ui + Tailwind CSS.
- **Linting / format:** Biome.
- **Package manager:** pnpm workspace.
- **Data fetching:** TanStack Query; live data via WebSocket or SSE.
- **Charts:** Recharts.

### General

- All models and third-party libraries must be listed in `LICENSES.md` with their license and commercial-use status.
- All PII classes redacted via Presidio **before** any persistence (DB write, log write, audio archive).
- Audio stored encrypted at rest; auto-purged after 7 days in dev.
- Every new feature needs: pytest tests + at least one Persona Gym scenario.

---

## 6. Repo Layout

```
saarthi/
├── apps/
│   ├── api/                  # FastAPI + Pipecat-ai + LangGraph orchestrator
│   └── web/                  # Next.js 14 dashboard
├── packages/
│   ├── llm_client/           # LLM_PROVIDER router (Ollama ↔ Groq)
│   ├── scripts/              # Product YAMLs + intent/slot schemas
│   │   └── products/
│   │       ├── personal_loan.yaml
│   │       └── personal_loan.intents.json
│   ├── persona_gym/          # Synthetic persona generator + eval runner
│   ├── voice/                # ASR/TTS wrappers, SSML helpers, VAD
│   │   └── samples/reference.wav   # your cloned-voice reference sample
│   ├── guardrail/            # Presidio + LLM judge compliance agent
│   └── eligibility/          # Product KG + Neo4j rules engine
├── infra/
│   ├── docker-compose.yml    # postgres, redis, qdrant, neo4j, minio
│   └── k8s/                  # optional k8s manifests
├── evals/
│   ├── pronunciation/
│   ├── nlu/
│   ├── scenarios/            # per-product scripted test scenarios
│   ├── redteam/              # 50+ adversarial compliance cases
│   └── persona_runs/         # output of persona_gym CLI runs
├── docs/
│   ├── SAARTHI-Project-Plan.md
│   ├── Claude-Code-Starter-Prompt.md
│   └── adr/                  # Architecture Decision Records
├── recordings/               # 3 per product, masked (no real PII)
├── report/                   # LaTeX or Markdown → PDF via Pandoc
├── consent/                  # voice consent PDF + template
├── fixtures/
│   └── fake_identifiers.py   # Verhoeff Aadhaar + Luhn card generators
├── CLAUDE.md                 # ← this file
├── LICENSES.md
├── README.md
├── Makefile
├── .env.example
└── .gitignore
```

---

## 7. Non-Negotiables

1. **PII:** All PII redacted via Presidio before any DB write, log write, or audio archive. Logs keep `<PAN_REDACTED>` placeholders.
2. **Licenses:** Every model/library in `LICENSES.md` with license name and commercial-use flag before it ships in code.
3. **Latency:** Log p50/p95 for ASR, LLM, TTS, and e2e on every call. Expose `/metrics` (Prometheus-compatible).
4. **Synthetic PII only:** `fixtures/fake_identifiers.py` must be the only source of ID numbers in tests and fixtures.
5. **Tests:** CI must pass (`pytest -q` + `pnpm -r build`) before any merge.
6. **Secrets:** `.env` only. `.env.example` documents every variable with a comment.
7. **ADRs:** One ADR in `docs/adr/` for every significant architectural choice.

---

## 8. Hardware (TODO — fill in before Phase 1)

> **ACTION REQUIRED:** Run `systeminfo` and `nvidia-smi` (or GPU-Z) and update this section before starting Phase 1. Claude Code uses this to decide local-vs-hosted model recommendations.

| Field | Value |
|---|---|
| OS | Windows (version TBD) |
| RAM | TBD |
| CPU | TBD |
| GPU | TBD |
| VRAM | TBD |

Reference targets from project plan: 16 GB RAM + RTX 3060 (8 GB VRAM) fits Whisper-large-v3 int8 + Llama-3.1-8B Q4 concurrently with model-swapping.

---

## 9. Phased Plan (condensed)

> Full weekly detail: `docs/SAARTHI-Project-Plan.md`

### Phase 0 — Foundations (Week 1)
- Monorepo scaffold: `uv` Python workspace + `pnpm` workspace.
- Docker Compose with Postgres, Redis, Qdrant, Neo4j, MinIO (healthchecks + named volumes).
- CI skeleton: GitHub Actions lint + type-check + unit tests.
- Pre-commit hooks, ruff, mypy, Biome configured.

**Definition of done:** `make up` succeeds; `make lint` and `make test` pass on an empty test suite; `LICENSES.md` seeded.

---

### Phase 1 — MVP Loop, Personal Loan (Weeks 2–4)
- ASR → LangGraph → TTS streaming pipeline via Pipecat-ai, callable from browser.
- XTTS-v2 voice clone with reference sample.
- LangGraph: `Opener → IdentityConfirm → Qualify → Consent → NextStep → Close`.
- Dashboard: start call, live transcript, call-ended card, audio replay.
- Every call persisted in Postgres with Presidio-redacted transcript.
- `/metrics` endpoint (Prometheus); p50/p95 latency logged per hop.

**Definition of done:** Browser call → agent qualifies a Personal Loan lead end-to-end; transcript and audio appear in dashboard; pytest covers happy path + Presidio redaction + YAML loader; CI green.

---

### Phase 2 — Scale to All 10 Products (Weeks 5–7)
- Product YAMLs + intent/slot schemas for remaining 9 products.
- Eligibility Engine microservice backed by Neo4j KG.
- RAG over masked product brochures and RBI FAQs via Qdrant.
- Dashboard filters (product, status, outcome) and analytics tiles.

**Definition of done:** All 10 products callable; ≥ 10 scripted test scenarios per product passing; Neo4j eligibility queries returning correct results.

---

### Phase 3 — Differentiators (Weeks 8–11)
- Multi-agent split: Qualifier + Objection Handler + Supervisor subgraphs in LangGraph.
- Compliance Guardrail agent (parallel branch): Presidio + LLM judge; can preempt TTS; logs interventions.
- Hinglish code-switching: IndicConformer routing, Hinglish prompt exemplars, `<lang:hi>` transcript tags.
- Sentiment-adaptive prosody: lightweight classifier → SSML rate/pitch adjustments.

**Definition of done:** Guardrail red-team suite (50 adversarial cases) passes; 3 Hinglish scenarios per product pass; ADRs written for each differentiator.

---

### Phase 4 — Persona Gym + RLAIF (Weeks 12–14)
- Parametric persona generator → 500 YAML personas.
- Eval runner: `python -m persona_gym run --n 100 --product personal_loan` → JSON + CSV output.
- RLAIF: harvest preference pairs → DPO-finetune LoRA on dialog model → compare baseline vs adapted.
- Results table: baseline single-agent vs SAARTHI multi-agent vs SAARTHI + RLAIF.

**Definition of done:** 500 personas generated; batch eval runs end-to-end in text-only mode; before/after success rate comparison documented in `report/persona_gym.md`.

---

### Phase 5 — Polish + Submission (Weeks 15–16)
- 30 demo recordings (3 × 10 products), masked, with sibling transcript JSON.
- MOS listening study page (`apps/web/app/mos/`) + `evals/mos/results.csv`.
- Full Markdown report in `report/` building to PDF via Pandoc.
- README quickstart: `git clone → cp .env.example .env → make up → make api → make web`.
- CI fully green; `v1.0.0` tag + GitHub Release.

**Definition of done:** One-command reproduction works from a clean clone; rubric mapping table in README complete; all CI checks passing.

---

## 10. Key External Resources

| Resource | Purpose |
|---|---|
| [Pipecat-ai](https://github.com/pipecat-ai/pipecat) | Realtime voice pipeline (VAD + barge-in) |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Multi-agent state machine |
| [Coqui XTTS-v2](https://github.com/coqui-ai/TTS) | Voice cloning TTS |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | ASR |
| [AI4Bharat IndicConformer](https://github.com/AI4Bharat/NeMo) | Hindi/Hinglish ASR |
| [Microsoft Presidio](https://github.com/microsoft/presidio) | PII detection + redaction |
| [Groq](https://console.groq.com) | Hosted LLM inference (free tier) |
| [Ollama](https://ollama.com) | Local LLM serving |
| [Qdrant](https://qdrant.tech) | Vector DB for RAG |
| [Neo4j](https://neo4j.com) | Product eligibility knowledge graph |
| RBI BFSI compliance guidelines | Compliance guardrail rubric |
