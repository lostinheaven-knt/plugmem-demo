---
name: plugmem-internal
description: Use PlugMem in this workspace to ingest traces/notes into a SQLite memory store and query with citations + suggested actions. Includes legacy import from MEMORY.md + memory/*.md (A+B) and simple manual triggers (no automatic hooks).
---

# PlugMem (internal)

Use this skill when the user asks to:
- “把这段/这次任务记下来、入库、沉淀” (ingest)
- “查一下以前怎么做、从记忆里找、带引用回答” (query)
- “把历史 MEMORY.md / memory/*.md 导进 PlugMem” (legacy import)
- “跑一下 plugmem 的 demo/单测” (smoke test)

This skill is **manual-trigger** only (no automatic hooks).

## Workspace locations

- Repo root: `/root/.openclaw/workspace_coder`
- PlugMem package: `/root/.openclaw/workspace_coder/plugmem`
- Default DB (recommended): `/root/.openclaw/workspace_coder/plugmem/data/plugmem.db`

## LLM configuration (no OpenClaw provider coupling)

PlugMem loads env from:
- `./.secrets.env` (current working dir), or
- `/root/.openclaw/workspace_coder/.secrets.env`

Recommended `.secrets.env` entries:

```env
PLUGMEM_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=...  # required
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

To run without LLM (degrades extraction quality):

```env
PLUGMEM_LLM_PROVIDER=none
```

## Quick commands

### Smoke test

```bash
cd /root/.openclaw/workspace_coder
pytest -q
python -m plugmem.scripts.demo_ingest
```

### DB stats (sanity check)

```bash
cd /root/.openclaw/workspace_coder
python -m plugmem.scripts.db_stats --db plugmem/data/plugmem.db --latest 5
```

### Ingest: quick note (manual)

Use the bundled script:

```bash
cd /root/.openclaw/workspace_coder
python -m plugmem.scripts.ingest_note --db plugmem/data/plugmem.db --task_type note --instruction "..." --text "..."
```

### Query (manual)

```bash
cd /root/.openclaw/workspace_coder
python -m plugmem.scripts.query --db plugmem/data/plugmem.db --query "..."
```

### Legacy import (A+B)

Import long-term memory + recent daily notes:

```bash
cd /root/.openclaw/workspace_coder
python -m plugmem.scripts.import_legacy_memory --db plugmem/data/plugmem.db --include-memory-md --include-daily --days 30
```

## Notes / conventions

- **A (MEMORY.md)** is curated long-term memory.
- **B (memory/YYYY-MM-DD.md)** are raw daily logs; import only recent days initially.
- Legacy import uses a conservative conversion:
  - each markdown paragraph/bullet becomes a trace item: `{ "observation": <text>, "action": "observe" }`
  - episode metadata stores `source_path`, `source_kind`, `date` (if parsed), and `imported_at`.

If you need better structure, we can re-run extraction later or add a second-pass “refine” script.
