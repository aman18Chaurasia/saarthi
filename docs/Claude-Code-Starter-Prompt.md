# Claude Code Starter Prompts for SAARTHI

> **Note:** This document was written pre-pivot. The authoritative stack
> is defined in CLAUDE.md and ADRs 0001/0002. Specifically, local LLM
> inference (Ollama, Llama-3.1-8B) was replaced by cloud inference (Groq
> llama-3.3-70b-versatile) per ADR 0001. Treat this document as historical
> planning context, not current guidance.

Copy–paste these into your Claude Code sessions in order. Each one is scoped so Claude doesn't overreach and you stay in control.

---

## Step 0 — Prep the workspace

In PowerShell:

```powershell
cd "D:\Major Project"
mkdir saarthi
cd saarthi
git init
claude
```

When Claude Code prompts you to trust the folder, accept.

---

## Prompt 1 — Create the project spec (CLAUDE.md)

> Paste this as your very first message to Claude Code. It produces a `CLAUDE.md` file that Claude Code auto-loads in every future session, so you don't have to re-explain the project.

```
I'm building a final-year major project called SAARTHI — a self-improving,
compliance-aware, multi-agent outbound voice agent for Indian BFSI lead
qualification. I want you to help me scaffold and build it.

Before we write any code, please create a CLAUDE.md at the repo root that
captures the project spec so every future Claude Code session in this repo
has the same context. The CLAUDE.md should include:

1. One-paragraph project summary.
2. Product scope: Home loan, Personal loan, Unsecured loan, LAP, Gold loan,
   Commercial vehicle loan, Four-wheeler loan, Education loan, MSME business
   loan, Credit card acquisition.
3. Architecture overview: FastAPI orchestrator + LangGraph multi-agent dialog
   manager + Pipecat-ai streaming pipeline + Next.js dashboard + Postgres +
   Qdrant + Neo4j + MinIO. ASR = faster-whisper + IndicConformer. TTS =
   Coqui XTTS-v2 with my cloned voice. LLM = Llama-3.1-8B via Ollama locally,
   Groq for hosted demo. PII = Microsoft Presidio + LLM-as-judge guardrail.
4. Coding conventions:
   - Python 3.11, ruff + mypy strict, pytest, SQLModel, Pydantic v2.
   - TypeScript strict, Next.js 14 App Router, shadcn/ui, Tailwind, Biome.
   - Conventional Commits.
   - All secrets via .env; never commit secrets.
   - No real customer PAN/Aadhaar/card numbers anywhere — use fixtures that
     generate Verhoeff-valid Aadhaar and Luhn-valid card numbers.
5. Repo layout:
   saarthi/
   ├── apps/{api,web}
   ├── packages/{scripts,persona_gym,voice,guardrail,eligibility}
   ├── infra/{docker-compose.yml,k8s}
   ├── evals/
   ├── recordings/
   ├── report/
   ├── consent/
   ├── CLAUDE.md, LICENSES.md, README.md
6. Non-negotiables:
   - All PII redacted via Presidio before persistence.
   - Every model/library used must be listed in LICENSES.md with its license.
   - Latency budget: <500 ms end-to-end local, <300 ms hosted.
   - Every feature must have pytest tests and a synthetic-persona eval.
7. Phased plan (mirror the SAARTHI-Project-Plan.md I'll share next).
8. Definition of done for each phase.

Write the CLAUDE.md to the repo root. Do not create any other files yet.
Ask me any clarifying questions before writing.
```

---

## Prompt 2 — Scaffold the monorepo

> Run this after Claude Code has written `CLAUDE.md`.

```
Scaffold the monorepo exactly per the repo layout in CLAUDE.md. Specifically:

1. Create a uv-managed Python workspace for apps/api and every packages/*
   that needs Python. Pin Python 3.11. Use pyproject.toml with ruff + mypy.
2. Create a pnpm workspace for apps/web (Next.js 14 App Router, TS strict,
   Tailwind, shadcn/ui initialized, Biome configured).
3. Create infra/docker-compose.yml with these services, healthchecks, and
   named volumes: postgres:16, redis:7, qdrant, neo4j:5, minio.
4. Add a Makefile (or justfile if you prefer) with targets:
     make up        # docker compose up -d
     make down
     make api       # uvicorn reload
     make web       # pnpm dev
     make test      # pytest + vitest
     make lint
5. Add .env.example with every variable the stack will eventually need
   (documented with comments). Add .gitignore covering Python, Node, IDEs,
   audio artifacts under recordings/, and .env.
6. Add a minimal GitHub Actions workflow: lint + type-check + unit tests for
   Python and web on push and PR.
7. Add consent/VOICE_CONSENT_TEMPLATE.md — a clean, signable consent form
   for voice cloning usage in this project.
8. Add LICENSES.md seeded with the libraries we already know we'll use.

Run a dry check at the end: `docker compose config`, `uv sync`, `pnpm install`,
`pytest -q`, `pnpm -r build`. Fix anything that fails. Report back with the
tree of files you created and any commands I need to run.
```

---

## Prompt 3 — Phase 1 vertical slice (Personal Loan MVP)

> This is the big one. Don't run it until Prompt 2 is clean and committed.

```
Build the Phase 1 vertical slice: an end-to-end streaming voice loop for the
Personal Loan product only, callable from the browser.

Acceptance criteria:
1. Open apps/web in the browser, click "Start call", grant mic access.
2. Speech streams to apps/api via WebSocket. faster-whisper transcribes.
3. A LangGraph dialog manager with nodes (Opener → IdentityConfirm →
   Qualify → Consent → NextStep → Close) runs and produces the agent turn.
4. Coqui XTTS-v2 synthesizes the turn in my cloned voice (use a placeholder
   reference sample at voice/samples/reference.wav for now) and streams back.
5. The dashboard shows a live transcript and a "Call ended" card with
   status, duration, transcript, and an audio replay button.
6. Every call is persisted in Postgres with a redacted transcript (pass it
   through Presidio first).
7. pytest covers: the LangGraph happy path, Presidio redaction on a fixture
   containing a Verhoeff-valid Aadhaar, and the product YAML loader.
8. Latency: log p50/p95 for ASR, LLM, TTS, e2e and expose a /metrics endpoint
   scrapable by Prometheus.

Design constraints:
- Use Pipecat-ai or LiveKit Agents — pick whichever gives us cleaner
  barge-in; justify your choice in a short ADR at docs/adr/0001-realtime.md.
- LLM should default to Ollama locally (llama3.1:8b) but be swappable to
  Groq via an env var.
- Script lives at packages/scripts/products/personal_loan.yaml with explicit
  pause markers <pause:wait_user/>.
- Intent+slot schema at packages/scripts/products/personal_loan.intents.json.

Deliver in small, reviewable commits. Stop and ask me before:
- Adding any paid API.
- Downloading model weights larger than 2 GB.
- Making architectural choices that deviate from CLAUDE.md.

Start by writing an implementation plan I can review. Do not write code until
I approve the plan.
```

---

## Prompt 4 — Scale to all 10 products

```
We shipped Phase 1 on Personal Loan. Now replicate across the 9 remaining
products: Home loan, Unsecured loan, LAP, Gold loan, Commercial vehicle loan,
Four-wheeler loan, Education loan, MSME business loan, Credit card acquisition.

For each product:
1. Create packages/scripts/products/<product>.yaml with opening, identity,
   qualifying questions, objection handling, consent capture, next step,
   close — each annotated with pause markers. Use realistic Indian BFSI
   terminology. Keep scripts concise (agent turns under 25 words on average).
2. Create packages/scripts/products/<product>.intents.json with intent
   taxonomy, slot definitions (required vs optional), sample utterances (at
   least 10 per intent), and normalization rules (e.g., "five lakhs" → 500000).
3. Add at least 10 scripted test scenarios per product under
   evals/scenarios/<product>/. Each scenario is a YAML with
   (persona_profile, expected_intents, expected_slots, expected_outcome).
4. Wire the dashboard product filter to show per-product metrics.
5. Extend the eligibility engine (packages/eligibility) with product rules.

At the end, run the full test suite and report coverage per product.
```

---

## Prompt 5 — Differentiators (Phase 3)

```
Implement the three differentiators from CLAUDE.md:

1. Multi-agent split in LangGraph:
   - Qualifier agent (primary).
   - Objection Handler agent (invoked when intent=objection).
   - Supervisor agent (routes, summarizes, decides escalation).
   Each agent is a subgraph with its own system prompt and tool set.

2. Compliance Guardrail agent:
   - Runs in a parallel branch of the LangGraph.
   - Receives every proposed agent turn before TTS.
   - Uses Presidio + an LLM judge with a tight rubric to score the turn for
     PII leakage, scope violations, and policy breaches.
   - If score > threshold, preempts the turn, logs the intervention, and
     returns a safe reformulation.
   - Red-team eval suite at evals/redteam/ with at least 50 adversarial cases.

3. Hinglish code-switching:
   - Route ASR to IndicConformer when language-ID classifier says Hindi.
   - Prompt the LLM with a Hinglish exemplar set.
   - Annotate transcripts with <lang:hi>...</lang:hi> tags.
   - Add 3 Hinglish scenarios per product to evals/scenarios/.

Ship ADRs for each in docs/adr/. Add tests. Update the dashboard to surface
guardrail interventions and language tags.
```

---

## Prompt 6 — Persona Gym and RLAIF (Phase 4, the thesis-worthy part)

```
Build the Persona Gym and RLAIF loop.

Persona Gym (packages/persona_gym):
- A parametric persona generator that samples (age, income band, education,
  language mix, mood, objection archetype, financial literacy, ground-truth
  eligibility outcome).
- Generate 500 personas as YAML fixtures.
- An eval runner that, for each persona, spins up an LLM acting as the
  customer and runs a full simulated call through our voice pipeline
  (text-only mode to keep it fast for batch).
- Metrics: qualification outcome vs ground truth, turn count, latency,
  guardrail interventions, code-switch count.
- A CLI: `python -m persona_gym run --n 100 --product personal_loan` that
  outputs evals/persona_runs/<run_id>/ with per-call JSON + aggregate CSV.

RLAIF loop:
- From persona runs, harvest preference pairs: (chosen = successful
  qualification trajectory, rejected = failed trajectory for similar persona).
- Use TRL DPOTrainer with LoRA on the dialog model.
- Produce a trained adapter. Swap it in behind a feature flag.
- Compare baseline vs adapted on a held-out 100-persona set. Output a
  results table.

Deliverable: a short report at report/persona_gym.md summarizing the
methodology and results with a baseline-vs-SAARTHI-vs-SAARTHI+RLAIF table.
```

---

## Prompt 7 — Report, demo recordings, polish (Phase 5)

```
Final polish and submission artifacts:

1. Generate 3 demo recordings per product (30 total) under recordings/.
   One success, one failure, one edge case per product. All masked (no real
   PII). Each recording has a sibling .json with the transcript and metadata.
2. Build an MOS listening study:
   - A static page at apps/web/app/mos/ that plays 10 blind clips per
     reviewer and collects 1–5 naturalness scores.
   - Export results to evals/mos/results.csv.
3. Write report/ as a Markdown report that builds to PDF via Pandoc. Include:
   executive summary, architecture, methodology, Persona Gym results,
   evaluation tables, compliance story, limitations, future work.
4. Finalize README.md with:
   - 30-second pitch.
   - Quickstart: git clone → cp .env.example .env → make up → make api →
     make web → open localhost:3000.
   - Rubric mapping table (which file/section maps to which rubric item).
5. Run a full cleanup pass: unused deps, TODOs, stale comments, passing CI.
6. Tag v1.0.0 and produce a GitHub Release with built artifacts.
```

---

## Ongoing workflow tips

- **Start every session with a TODO list.** Tell Claude Code exactly which
  phase/prompt you're in. It has `CLAUDE.md` as context but benefits from a
  fresh goal.
- **Use `/init`** inside Claude Code if you ever want it to re-scan the repo
  and refresh its view.
- **Ask for plans, not code, first.** For any non-trivial task, say:
  "Write the implementation plan. Do not touch files. I'll approve."
- **Review diffs before committing.** Claude Code shows them; don't skim.
- **Keep commits small.** Ask Claude Code to commit after every logical unit.
- **When it goes off the rails,** say: "Stop. Revert the last change. Here's
  what I actually want: …". It will.
- **Use `/clear`** between unrelated tasks to keep context focused.
- **Use headless mode for batch work:** e.g., regenerating 30 demo
  recordings — `claude -p "Regenerate the home_loan demo recordings from
  the latest scripts"`.

Good luck. Paste Prompt 1 when you're ready.
