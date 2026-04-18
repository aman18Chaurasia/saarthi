# SAARTHI

> **Note:** This document was written pre-pivot. The authoritative stack
> is defined in CLAUDE.md and ADRs 0001/0002. Specifically, local LLM
> inference (Ollama, Llama-3.1-8B) was replaced by cloud inference (Groq
> llama-3.3-70b-versatile) per ADR 0001. Treat this document as historical
> planning context, not current guidance.

**Self-Adaptive AI for Responsible Tele-conversational Human Interaction in BFSI**

A production-style, multi-agent, self-improving outbound voice agent for Indian lending products — built as a final-year major project that aims for publishable novelty, not just a passing rubric score.

---

## 1. Why this reframing beats the base problem

The given problem statement ("voice agent for BFSI lead qualification") is a solid industry-style brief, but as stated it's a single-LLM scripted bot that hundreds of teams will deliver. SAARTHI elevates it on four axes that are both **impressive to evaluators** and **feasible in 3–4 months**:

| Axis | Basic project | SAARTHI |
|---|---|---|
| Architecture | One LLM, scripted dialog | Multi-agent (Qualifier · Objection Handler · Compliance Guardrail · Supervisor) via LangGraph |
| Evaluation | 10 scripted tests per product | **Synthetic Persona Gym**: 500+ LLM-generated customer personas, parameterized by mood, language mix, financial literacy, objection archetype |
| Compliance | Post-hoc masking of logs | **Real-time guardrail agent** that can interrupt the main agent mid-turn if a PII leak or policy violation is imminent |
| Learning | Static prompts forever | **RLAIF loop**: successful vs failed qualifications become preference pairs; DPO-finetune a small dialog policy model |

Each of these is a clear story in a demo and defends a page in your report.

---

## 2. Project title & branding

- **Working title:** *SAARTHI — A Self-Improving, Compliance-Aware Multi-Agent Voice System for BFSI Lead Qualification in Code-Mixed Hindi-English*
- **Tagline:** *"Your digital saarthi for every lending journey."*
- **Logo cue:** chariot wheel + waveform
- **Primary language of demos:** English first, Hinglish as the headline differentiator

---

## 3. Scope of products (all 10 required by rubric)

Home loan · Personal loan · Unsecured loan · LAP / secured loans · Gold loan · Commercial vehicle loan · Four-wheeler loan · Education loan · MSME business loan · Credit card acquisition.

Each product gets: a script YAML, an intent+slot schema, a product-specific eligibility micro-service, and at least 3 demo call recordings (1 success, 1 failure, 1 edge case).

---

## 4. Architecture (one page)

```
                     ┌──────────────────────────────────────────────┐
                     │                  Next.js Dashboard           │
                     │  (live transcript · analytics · call replay) │
                     └──────────────────────────────────────────────┘
                                         ▲
                                         │ WebSocket
                     ┌──────────────────────────────────────────────┐
                     │               FastAPI Orchestrator           │
                     └──────────────────────────────────────────────┘
                       │            │              │           │
          ┌────────────▼──┐  ┌──────▼───────┐  ┌───▼──────┐ ┌──▼─────────┐
          │ ASR           │  │ LangGraph    │  │ TTS      │ │ Compliance │
          │ faster-whisper│  │ Multi-Agent  │  │ XTTS-v2  │ │ Guardrail  │
          │ + IndicConf   │  │ Dialog Mgr   │  │ (your    │ │ (Presidio  │
          │               │  │              │  │  voice)  │ │  + LLM-J)  │
          └───────────────┘  └──────────────┘  └──────────┘ └────────────┘
                                    │
                        ┌───────────┼─────────────┐
                        │           │             │
                  ┌─────▼────┐ ┌────▼─────┐ ┌─────▼──────┐
                  │ Qualifier│ │Objection │ │Eligibility │
                  │  Agent   │ │ Handler  │ │  Engine    │
                  └──────────┘ └──────────┘ │ (Neo4j KG) │
                                            └────────────┘
                        │
                  ┌─────▼──────────┐
                  │ Persona Gym    │◄──── synthetic customers for test/train
                  │ (LLM-driven)   │
                  └────────────────┘
                        │
                  ┌─────▼──────────┐
                  │ RLAIF / DPO    │◄──── self-improvement loop
                  │ Trainer        │
                  └────────────────┘

   Storage: PostgreSQL (metadata) · Qdrant (RAG) · Neo4j (products) · MinIO/S3 (audio)
   Streaming bus: Redis pub/sub  ·  Observability: OpenTelemetry → Grafana
```

**End-to-end latency target:** < 500 ms mic-to-speaker on a laptop with a 7B-class local model via Ollama; stretch goal < 300 ms using Groq/Cerebras hosted inference for the dialog model.

---

## 5. Tech stack

### Voice
- **ASR:** `faster-whisper` (large-v3, int8) for English; `AI4Bharat IndicConformer` or Whisper fine-tuned on IndicSUPERB for Hindi/Hinglish.
- **VAD:** `silero-vad` for barge-in support.
- **TTS / Voice Clone:** `Coqui XTTS-v2` (Apache 2.0, cross-lingual voice cloning from a 6-second sample) OR `OpenVoice v2` (MIT). Fallback: ElevenLabs free tier for MOS comparisons.
- **SSML:** custom phoneme overrides for `PAN`, `CVV`, `PIN`, `OTP`, `Aadhaar` with per-language IPA; documented as the "BFSI pronunciation dictionary."

### Dialog & reasoning
- **LLM:** Llama-3.1-8B-Instruct or Qwen2.5-7B via Ollama for local dev; Groq `llama-3.1-70b-versatile` for hosted demo speed.
- **Orchestration:** LangGraph (explicit state machine with typed nodes) + LangSmith for tracing.
- **NLU for Hinglish:** MuRIL or IndicBERT fine-tuned on a small BFSI intent set you label yourself (~200 utterances per intent is enough with LLM-assisted labeling).
- **RAG:** Qdrant, indexed over masked product brochures, RBI FAQs, eligibility criteria.
- **Knowledge graph:** Neo4j — nodes for products, eligibility rules, document requirements. Agent uses Cypher queries via tool-use to reason about eligibility.

### Realtime, backend, frontend
- **Realtime pipeline:** Pipecat-ai or LiveKit Agents (both handle VAD + ASR + LLM + TTS streaming and barge-in out of the box).
- **Backend:** FastAPI + Celery + Redis. Postgres via SQLModel. Alembic migrations.
- **Frontend:** Next.js 14 (App Router) + shadcn/ui + Tailwind + Recharts + TanStack Query. Live transcript via Server-Sent Events or WebSocket.
- **Telephony demo:** Twilio Voice free tier for one end-to-end real PSTN call; browser WebRTC for the primary demo path.

### Safety, eval, ops
- **PII:** Microsoft Presidio with custom recognizers for PAN (`[A-Z]{5}[0-9]{4}[A-Z]`), Aadhaar (12-digit Verhoeff), card numbers (Luhn).
- **LLM-as-judge eval:** DeepEval or Ragas for automated scoring.
- **Observability:** OpenTelemetry spans on every ASR/LLM/TTS hop, visualized in Grafana. Latency budget dashboard is a demo highlight.
- **CI:** GitHub Actions — lint, unit tests, NLU regression, voice pronunciation regression (ASR hit-rate on a fixed set of jargon clips).
- **Deployment:** `docker compose up` for the whole stack on a laptop; optional k8s manifests for bonus points.

---

## 6. Deliverables mapped to the rubric

| Rubric item | SAARTHI artifact |
|---|---|
| Voice naturalness (30) | XTTS-v2 clone + SSML prosody + MOS form with 5 reviewers (Google Form + CSV export) |
| Pronunciation (25) | Phoneme override dictionary + ASR keyword-hit regression suite per language |
| Script quality (20) | 10 product YAMLs, each with opening/identity/qualify/objection/consent/next-step/close, pause markers (`<pause:wait_user/>`) |
| NLU correctness (15) | Intent+slot JSON per product + 500-persona Gym test pass rate |
| Compliance (10) | Presidio + LLM judge guardrail + written data-handling policy + consent PDF |

---

## 7. Phased roadmap (16 weeks)

### Phase 0 — Foundations (Week 1)
- Repo scaffold (`saarthi/` monorepo with `apps/api`, `apps/web`, `packages/scripts`, `packages/persona_gym`, `infra/`).
- Docker Compose with Postgres, Redis, Qdrant, Neo4j, MinIO.
- CI skeleton, pre-commit hooks, typed Python (ruff + mypy), Biome for the JS side.
- Record and commit your **voice consent form** and a 3-minute voice sample.

### Phase 1 — MVP Loop, single product (Weeks 2–4)
Pick **Personal Loan** as the pilot product.
- ASR→LLM→TTS streaming pipeline using Pipecat-ai, in-browser.
- Voice clone working with XTTS-v2 + your sample.
- One LangGraph with Opener → Qualifier → Close nodes.
- Minimal dashboard: start call, live transcript, end call, replay.
- 10 scripted test scenarios passing in CI.
- **Milestone demo:** call from browser → agent qualifies a synthetic Personal Loan lead end-to-end, transcript and audio appear in the dashboard.

### Phase 2 — Scale to all 10 products (Weeks 5–7)
- Product YAMLs for the remaining 9 products.
- Intent/slot schemas per product, normalization rules for salary/loan amount/tenure.
- Eligibility Engine microservice backed by Neo4j knowledge graph.
- RAG over masked product brochures.
- Dashboard filters (product, status, outcome) and analytics tiles.

### Phase 3 — The differentiators (Weeks 8–11)
- **Multi-agent split:** Qualifier + Objection Handler + Supervisor via LangGraph subgraphs.
- **Compliance Guardrail agent** running in parallel, with an interruption channel that can preempt TTS.
- **Hinglish code-switching** via IndicConformer + a language-routing prompt; annotate switches in transcripts.
- **Sentiment-adaptive prosody** — a lightweight sentiment classifier on the user's turn; map to SSML rate/pitch for the next TTS.

### Phase 4 — The novelty (Weeks 12–14)
- **Persona Gym:** parametric persona generator (age, language mix, income band, mood, objection archetype, financial literacy). 500+ personas stored as YAML. Each persona runs as an LLM role-playing the customer inside the same pipeline.
- Automated batch eval: run agent × persona matrix, collect pass/fail + latency + compliance events.
- **RLAIF:** harvest successful vs failed trajectories, form preference pairs, DPO-finetune a small dialog policy head (LoRA over Llama-3.1-8B). Show the before/after success rate.

### Phase 5 — Polish and report (Weeks 15–16)
- 3 demo recordings per product (30 total), masked.
- MOS listening study (5 reviewers, Google Form).
- Evaluation report (10–15 pages) + architecture document.
- README with one-command reproduction.
- Optional: Twilio-backed real PSTN demo; hosted demo on a $6 VPS or Hugging Face Spaces.

---

## 8. Evaluation plan

### Automated metrics (run every CI build)
- NLU accuracy: intent F1, slot exact-match on a held-out test set.
- Pronunciation: ASR hit-rate for each jargon term across 20 TTS samples.
- Latency: p50/p95 of ASR, LLM, TTS, end-to-end.
- Compliance: count of guardrail interventions on a red-team suite of 50 adversarial utterances.
- Task success: Persona Gym pass rate (qualification outcome correct per persona's ground-truth eligibility).

### Subjective
- MOS naturalness (1–5) from 5 reviewers, blind, 10 clips each.
- Script clarity/brevity scored by 3 BFSI industry contacts if reachable.

### What to put in the report
A single results table with three columns (baseline single-agent, SAARTHI multi-agent, SAARTHI + RLAIF) × all metrics. This is the killer page.

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Voice clone quality insufficient for MOS ≥ 4 | Keep ElevenLabs as a fallback and an XTTS vs ElevenLabs comparison in the report |
| Latency blows past 500 ms locally | Switch dialog model to Groq-hosted for the demo; document local vs hosted numbers honestly |
| Hinglish NLU data scarcity | Synthesize training data with an LLM, human-verify a 10% sample |
| RLAIF doesn't move the needle | Phase 4 is explicitly framed as a research experiment — reporting a negative result with ablations is still a strong contribution |
| Compliance guardrail interrupts too aggressively | Maintain a tunable threshold and a false-positive regression suite |

---

## 10. Compliance & ethics (not just for the rubric — make this a story)

- Written voice consent PDF, signed, in the repo.
- No real PANs/Aadhaars/cards anywhere — a `fixtures/fake_identifiers.py` module generates valid-format synthetic values (Verhoeff for Aadhaar, Luhn for cards) so regexes trigger but nothing is real.
- Logs: all PII classes are redacted with Presidio before persistence. Audio is stored at rest encrypted with a local KMS key.
- Retention policy: audio auto-purged after 7 days in dev; transcripts are kept with PII replaced by placeholders.
- Third-party inventory: a `LICENSES.md` listing every model, its license, and whether it permits commercial use.

---

## 11. What a great demo looks like (15 minutes)

1. **Intro slide:** problem, SAARTHI's four differentiators. (1 min)
2. **Voice clone live:** upload 30-second sample → agent speaks in your cloned voice. (1 min)
3. **Outbound call (Home Loan):** click "Call" → live transcript appears → agent qualifies, handles one objection, confirms branch visit. (3 min)
4. **Compliance interrupt:** trigger a scenario where the customer says "full CVV is 123" → guardrail flags, agent pivots, log shows redaction. (1.5 min)
5. **Hinglish switch:** customer speaks Hindi, agent adapts. (1 min)
6. **Dashboard tour:** call list, analytics, audio replay, export. (2 min)
7. **Persona Gym:** launch a batch of 50 personas → show live success rate bar, end with baseline vs RLAIF comparison chart. (3 min)
8. **Architecture + honest numbers:** latency budget, MOS scores, compliance interventions. (1.5 min)
9. **Roadmap and what's next.** (1 min)

---

## 12. Repo layout

```
saarthi/
├── apps/
│   ├── api/                 # FastAPI, LangGraph orchestrator
│   └── web/                 # Next.js dashboard
├── packages/
│   ├── scripts/             # Product YAMLs, intent/slot schemas
│   ├── persona_gym/         # Synthetic persona generator + eval runner
│   ├── voice/               # ASR/TTS wrappers, SSML helpers
│   ├── guardrail/           # Presidio + LLM judge
│   └── eligibility/         # Product KG + rules engine
├── infra/
│   ├── docker-compose.yml
│   └── k8s/                 # optional
├── evals/
│   ├── pronunciation/
│   ├── nlu/
│   └── persona_runs/
├── recordings/              # 3 per product, masked
├── report/                  # LaTeX or Markdown
├── consent/                 # voice consent PDF
├── CLAUDE.md                # project spec for Claude Code
├── LICENSES.md
└── README.md
```

---

## 13. Hardware and budget

- A laptop with 16 GB RAM + RTX 3060+ (or Apple Silicon M2+) runs the local stack; 8 GB VRAM fits Whisper-large-v3 int8 + Llama-3.1-8B Q4 concurrently if you swap as needed.
- Free tiers cover the hosted demo: Groq (fast LLM), Twilio (100 min free), Hugging Face Spaces (demo hosting), Neon (free Postgres).
- Estimated cash cost: **₹0–₹1500** if you use only free tiers, mostly for a Twilio India number if you want a live PSTN demo.

---

## 14. What to write up as the "research contribution"

Even a single novel piece elevates this from engineering-project to dissertation-worthy. Pick one:

1. **Synthetic Persona Gym** — method + release the dataset of 500 personas and the eval harness. Title idea: *"Persona-Gym: A Parametric Evaluation Harness for Outbound Voice Agents in Code-Mixed Indian BFSI."*
2. **Real-time compliance guardrail** — latency/accuracy trade-off study of inline PII detection in streaming voice dialog.
3. **RLAIF for dialog policy** in a low-resource code-mixed domain — even a negative or mixed result is publishable.

---

## 15. Immediate next steps

1. Record your 3-minute voice sample (quiet room, good mic, read BFSI jargon aloud).
2. Sign and scan the consent form (template in `consent/`).
3. Create the GitHub repo, push the skeleton.
4. Open the project in Claude Code and paste the starter prompt (see `Claude-Code-Starter-Prompt.md`).
5. Aim to finish Phase 1 (MVP loop on Personal Loan) by end of Week 4.

Good luck — this is a genuinely impressive project if you execute. The goal isn't to check rubric boxes; it's to end the year with a repo you'd be proud to put on a résumé.
