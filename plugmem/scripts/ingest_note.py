from __future__ import annotations

import argparse
from datetime import datetime

from plugmem.app.plugmem import PlugMem


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest a free-form note into PlugMem")
    p.add_argument("--db", required=True, help="Path to sqlite db")
    p.add_argument("--task_type", default="note", help="Episode task_type")
    p.add_argument("--instruction", default="Ingest note", help="Episode instruction")
    p.add_argument("--text", required=True, help="Note text")
    p.add_argument("--source", default="manual", help="Source label")
    args = p.parse_args()

    pm = PlugMem.build_default(args.db)
    trace = [{"observation": args.text, "action": "note", "source": args.source}]
    metadata = {"source": args.source, "imported_at": datetime.utcnow().isoformat() + "Z"}
    pm.ingest(raw_trace=trace, task_type=args.task_type, instruction=args.instruction, metadata=metadata)

    print("OK: ingested 1 note")


if __name__ == "__main__":
    main()
