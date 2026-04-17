# ADR 0001 — Cloud-First Inference

**Date:** 2026-04-18
**Status:** Accepted
**Deciders:** Aman Chaurasia

---

## Context

The development machine is an Intel Core i5-8365U laptop with 16 GB RAM and an Intel UHD 620 integrated GPU (no CUDA). Local inference options evaluated:

| Model | Min VRAM | Verdict |
|---|---|---|
| Whisper-large-v3 int8 | ~4 GB GPU / 6 GB RAM | Too slow on CPU; ~30–60s per utterance |
| Llama-3.1-8B Q4 | ~5 GB GPU | CPU inference ~10–20 tok/s; violates 300 ms budget |
| XTTS-v2 | ~3–4 GB GPU | CPU synthesis ~4–8× real-time; unacceptable |

Running even one of these models locally would blow the latency budget and exhaust RAM. Running all three concurrently is not feasible.

---

## Decision

All ML inference is routed to free-tier cloud APIs:

| Concern | Provider | Free Tier Limit |
|---|---|---|
| ASR (English + Hindi) | Groq Whisper API (`whisper-large-v3`) | 28,800 audio-sec / day (~8 hr) |
| Dialog LLM | Groq (`llama-3.1-70b-versatile`) | 14,400 req / day; 6,000 tokens/min |
| TTS / voice clone | Coqui XTTS-v2 via Hugging Face Space endpoint | Shared GPU; ~1–3 s TTFB |
| TTS benchmark | ElevenLabs free tier | 10,000 chars / month |
| Embeddings | Jina AI embeddings (primary) or Gemini `text-embedding-004` (fallback) | Jina: 1M tokens free; Gemini: 1M tokens/min on free tier |

Ollama remains in the codebase as `LLM_PROVIDER=ollama` for contributors who have NVIDIA hardware, but it is **not** the default and is not required for CI.

---

## Consequences

### Positive
- Zero GPU cost during development; everything runs on the laptop.
- Groq latency (~100–200 ms for LLM) is actually better than local inference on this hardware.
- No driver/CUDA setup friction for the demo environment.

### Negative / Risks to monitor
- **Rate limits:** Groq free tier — 14,400 req/day. Persona Gym batch runs of 500 personas may exhaust the daily quota in a single run. Mitigation: add exponential back-off + quota guard in `packages/llm_client/`; run large batches overnight.
- **HF Space cold-start:** XTTS-v2 Space may sleep after inactivity, adding a 20–40 s warm-up penalty. Mitigation: keep-alive ping in the TTS wrapper; document in README.
- **Internet dependency:** CI and local dev require outbound HTTPS. Offline demo mode is not supported.
- **API key rotation:** All keys live in `.env` only. Add key expiry reminders in `docs/ops-runbook.md` once created.

---

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Upgrade to RTX 3060 laptop | Out of scope / cost for academic project |
| Google Colab for inference | No persistent server; latency spikes; awkward integration with FastAPI |
| Smaller local models (Whisper-tiny, Llama-3.2-1B) | Quality too low for BFSI demo; fails NLU eval thresholds |
