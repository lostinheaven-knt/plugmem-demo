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

## Notes

- Secrets are read from `.secrets.env` (never commit it).
- The included database under `plugmem/data/` is just a local demo artifact.
