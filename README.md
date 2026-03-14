# PlugMem Demo

A small demo of a “memory” pipeline:

- ingest trace -> episodic standardization
- semantic extraction (propositions)
- procedural extraction (prescriptions)
- dedup audit logging
- SQLite persistence + lightweight retrieval

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

pytest -q

# (optional) run the demo ingest script
python -m plugmem.scripts.demo_ingest
```

Or using `make`:

```bash
make venv
source .venv/bin/activate
make install
make test
make demo
```

## Using PlugMem manually (recommended)

### 1) Configure secrets (never commit)

Create `/root/.openclaw/workspace_coder/.secrets.env`:

```env
PLUGMEM_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 2) Use the default DB

We recommend a single shared DB:

- `plugmem/data/plugmem.db`

### 3) Import legacy OpenClaw memory (A+B)

- A: `MEMORY.md`
- B: recent `memory/YYYY-MM-DD.md`

```bash
cd /root/.openclaw/workspace_coder
python -m plugmem.scripts.import_legacy_memory \
  --db plugmem/data/plugmem.db \
  --include-memory-md \
  --include-daily \
  --days 30
```

### 4) Sanity-check the DB

```bash
python -m plugmem.scripts.db_stats --db plugmem/data/plugmem.db --latest 5
```

### 5) Query

```bash
python -m plugmem.scripts.query --db plugmem/data/plugmem.db --query "我们之前关于 PlugMem/技能 的决策是什么？"
```

### 6) Ingest a quick note

```bash
python -m plugmem.scripts.ingest_note --db plugmem/data/plugmem.db --instruction "临时记录" --text "..."
```

## Internal OpenClaw skill

This repo includes an internal, manual-trigger OpenClaw skill:

- `skills/plugmem-internal/SKILL.md`

It documents when to ingest/query/import and the canonical command lines.

## Notes

- Secrets are read from `.secrets.env` (never commit it).
- Databases (`*.db/*.sqlite*`) are ignored by git.
- The included `plugmem/data/plugmem_demo.db` is just a demo artifact.
