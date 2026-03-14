from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from plugmem.app.plugmem import PlugMem


@dataclass
class SourceDoc:
    path: Path
    kind: str  # memory_md | daily


def _iter_markdown_files(include_memory_md: bool, include_daily: bool, days: int) -> list[SourceDoc]:
    root = Path(__file__).resolve().parents[2]  # workspace root
    docs: list[SourceDoc] = []

    if include_memory_md:
        p = root / "MEMORY.md"
        if p.exists():
            docs.append(SourceDoc(path=p, kind="memory_md"))

    if include_daily:
        memdir = root / "memory"
        if memdir.exists():
            cutoff = date.today() - timedelta(days=days)
            for p in sorted(memdir.glob("*.md")):
                # Expect YYYY-MM-DD.md
                m = re.match(r"(\d{4}-\d{2}-\d{2})\.md$", p.name)
                if not m:
                    continue
                try:
                    d = date.fromisoformat(m.group(1))
                except ValueError:
                    continue
                if d >= cutoff:
                    docs.append(SourceDoc(path=p, kind="daily"))

    return docs


def _split_markdown_to_items(text: str) -> list[dict]:
    lines = text.splitlines()
    items: list[dict] = []
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        chunk = "\n".join(buf).strip()
        buf = []
        if not chunk:
            return
        items.append({"observation": chunk, "action": "observe"})

    for ln in lines:
        # Treat fenced blocks as boundaries.
        if ln.strip().startswith("```"):
            flush()
            continue

        if not ln.strip():
            flush()
            continue

        # Keep headings as separate items.
        if re.match(r"^#{1,6}\s+", ln):
            flush()
            buf.append(ln.strip())
            flush()
            continue

        buf.append(ln.rstrip())

    flush()
    return items


def main() -> None:
    p = argparse.ArgumentParser(description="Import legacy OpenClaw markdown memory into PlugMem")
    p.add_argument("--db", required=True, help="Path to sqlite db")
    p.add_argument("--include-memory-md", action="store_true", help="Import workspace root MEMORY.md")
    p.add_argument("--include-daily", action="store_true", help="Import workspace memory/YYYY-MM-DD.md")
    p.add_argument("--days", type=int, default=30, help="How many recent daily notes to import")
    p.add_argument("--dry-run", action="store_true", help="Parse only; do not write")
    args = p.parse_args()

    docs = _iter_markdown_files(args.include_memory_md, args.include_daily, args.days)
    if not docs:
        print("No input docs found. Nothing to import.")
        return

    pm = None if args.dry_run else PlugMem.build_default(args.db)

    total_eps = 0
    total_items = 0
    for doc in docs:
        text = doc.path.read_text(encoding="utf-8")
        items = _split_markdown_to_items(text)
        if not items:
            continue

        meta = {
            "source_path": str(doc.path),
            "source_kind": doc.kind,
            "imported_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

        # One episode per file (simple + stable)
        task_type = "legacy_memory_import"
        instruction = f"Import legacy markdown from {doc.path.name}"

        if pm is not None:
            pm.ingest(raw_trace=items, task_type=task_type, instruction=instruction, metadata=meta)

        total_eps += 1
        total_items += len(items)
        print(f"Imported {doc.path} :: items={len(items)}")

    print(f"DONE :: episodes={total_eps} items={total_items} dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
