# SAARTHI

**Self-Adaptive AI for Responsible Tele-conversational Human Interaction in BFSI**

[![Tests](https://github.com/aman18Chaurasia/saarthi/actions/workflows/test.yml/badge.svg)](https://github.com/aman18Chaurasia/saarthi/actions/workflows/test.yml)
[![Lint](https://github.com/aman18Chaurasia/saarthi/actions/workflows/lint.yml/badge.svg)](https://github.com/aman18Chaurasia/saarthi/actions/workflows/lint.yml)
[![Deploy](https://github.com/aman18Chaurasia/saarthi/actions/workflows/deploy-preview.yml/badge.svg)](https://github.com/aman18Chaurasia/saarthi/actions/workflows/deploy-preview.yml)
[![codecov](https://codecov.io/gh/aman18Chaurasia/saarthi/branch/master/graph/badge.svg)](https://codecov.io/gh/aman18Chaurasia/saarthi)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Tests](https://img.shields.io/badge/tests-186%2F188%20passing-brightgreen)

SAARTHI is a production-style, multi-agent, self-improving outbound voice agent for Indian lending products. It qualifies leads across 10 BFSI products via a streaming voice pipeline (ASR → LangGraph multi-agent dialog → TTS), with a real-time compliance guardrail, Hinglish code-switching, and an RLAIF self-improvement loop driven by a Synthetic Persona Gym.

For the full project spec, architecture, and phased plan see [CLAUDE.md](CLAUDE.md).

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker Desktop | 4.x+ | https://docs.docker.com/get-docker/ |
| Node.js | 20+ | https://nodejs.org |
| pnpm | 9+ | `npm i -g pnpm` |
| uv | latest | https://docs.astral.sh/uv/getting-started/installation/ |
| API keys | — | see `.env.example` |

Required API keys (all free tier):
- **Groq** — LLM inference + Whisper ASR
- **ElevenLabs** — TTS (or set `TTS_PROVIDER=hf_space` for XTTS-v2 via HF Space)
- **Jina AI** — embeddings

---

## Quickstart

```bash
git clone <repo-url>
cd saarthi

# 1. Copy env template and fill in your API keys
cp .env.example .env

# 2. Install all dependencies and download the spaCy model Presidio needs
make setup

# 3. Start backing services (Postgres, Redis, Qdrant, Neo4j, MinIO)
make up

# 4. Run database migrations to create tables
make migrate

# 5. Start the API (http://localhost:8000)
make api

# 6. In a second terminal — start the dashboard (http://localhost:3000)
make web
```

> **Run `make setup` before anything else.** It downloads the `en_core_web_lg` spaCy
> model that Presidio requires; skipping it causes a runtime crash.

---

## Available make targets

| Target | What it does |
|---|---|
| `make setup` | `uv sync` + spaCy model download + `pnpm install` |
| `make up` | Start all Docker services |
| `make down` | Stop all Docker services |
| `make migrate` | Run database migrations (Alembic) |
| `make seed` | Populate database with test call data |
| `make seed-clear` | Clear all calls from database |
| `make api` | Run FastAPI dev server on `:8000` |
| `make web` | Run Next.js dev server on `:3000` |
| `make test` | `pytest -q` + `vitest` |
| `make lint` | ruff + mypy + biome |
