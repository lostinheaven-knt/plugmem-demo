from __future__ import annotations

import argparse
import json

from plugmem.app.plugmem import PlugMem


def main() -> None:
    p = argparse.ArgumentParser(description="Query PlugMem and print a structured answer")
    p.add_argument("--db", required=True, help="Path to sqlite db")
    p.add_argument("--query", required=True, help="Query text")
    p.add_argument("--instruction", default="", help="Optional instruction")
    p.add_argument("--state", default="", help="Optional state")
    p.add_argument("--json", action="store_true", help="Print full JSON")
    args = p.parse_args()

    pm = PlugMem.build_default(args.db)
    ans = pm.retrieve_structured(query=args.query, instruction=args.instruction, state=args.state)

    if args.json:
        print(json.dumps(ans.model_dump(), ensure_ascii=False, indent=2))
        return

    print(ans.answer)

    if ans.cited_items:
        print("\nCitations:")
        for ci in ans.cited_items:
            print(f"- {ci.type}:{ci.id}")

    if ans.suggested_actions:
        print("\nSuggested actions:")
        for a in ans.suggested_actions:
            # Keep it resilient to schema changes.
            d = a.model_dump() if hasattr(a, "model_dump") else dict(a)
            label = d.get("label") or d.get("type") or "action"
            desc = d.get("description") or d.get("detail") or ""
            print(f"- {label}: {desc}")


if __name__ == "__main__":
    main()
