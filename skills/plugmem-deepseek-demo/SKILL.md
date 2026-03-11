---
name: plugmem-deepseek-demo
description: "Run the PlugMem DeepSeek demo ingest pipeline end-to-end (standardize -> extract semantic/procedural -> LLM dedup -> SQLite/graph storage -> optional retrieval). Use when you want to validate DeepSeek LLM wiring or generate a demo SQLite DB for other agents."
---

# PlugMem DeepSeek Demo Skill

## Install / Setup (project-local)

This is a **project-local skill** stored in this repo under `skills/plugmem-deepseek-demo/`.

### 1) Get the code

Make sure you are working in the PlugMem repo/workspace that contains:
- `plugmem/`
- `plugmem/scripts/demo_ingest.py`
- `skills/plugmem-deepseek-demo/SKILL.md`

### 2) Configure secrets (required for real DeepSeek)

Secrets are loaded from workspace `.secrets.env` (never commit):

```
DEEPSEEK_BASE_URL="https://api.deepseek.com"
DEEPSEEK_API_KEY="..."
DEEPSEEK_MODEL="deepseek-chat"   # optional
```

If secrets are missing, the demo script automatically falls back to `FakeLLM` for offline runs.

### 3) Python dependencies

This project expects Python with the following available:
- `openai` (used for DeepSeek OpenAI-compatible calls)
- `pyyaml`
- `pytest` (for tests)

(If you have a venv, activate it before running.)

## Usage

### Run ingest demo

```bash
python plugmem/scripts/demo_ingest.py
```

You should see `LLM: DeepSeekLLM` when real DeepSeek is active.

### Verify tests

```bash
pytest -q plugmem/tests
```

### Inspect DB quickly

```bash
sqlite3 plugmem/data/plugmem_demo.db 'select count(*) from propositions;'
```

## What it does

Running the demo performs:
- episodic standardization (infer state/subgoal/reward)
- semantic extraction (propositions + concepts)
- procedural extraction (intent + workflow)
- LLM-based dedup with audit logging
- writes to SQLite tables + updates an in-memory graph

## Quick acceptance checklist (5 minutes)

1. **Real DeepSeek path**: run the demo and confirm it prints `LLM: DeepSeekLLM`.
2. **Offline fallback**: temporarily unset `DEEPSEEK_API_KEY` and confirm it prints a warning and uses `FakeLLM`.
3. **Tests**: `pytest -q plugmem/tests` should pass.
4. **Audit evidence**: confirm `dedup_audit` has rows in `plugmem/data/plugmem_demo.db`.

## Architecture map (read when debugging)

If you need the full pipeline map, read:
- `references/pipeline.md`
