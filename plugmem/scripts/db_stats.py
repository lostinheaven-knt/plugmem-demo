from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


TABLES = [
    "episode_steps",
    "propositions",
    "concepts",
    "prescriptions",
    "intents",
    "edges",
    "source_links",
    "dedup_audit",
]


def _count(con: sqlite3.Connection, table: str) -> int:
    cur = con.execute(f"SELECT COUNT(*) FROM {table}")
    return int(cur.fetchone()[0])


def _latest_steps(con: sqlite3.Connection, limit: int) -> list[dict]:
    rows = con.execute(
        """
        SELECT step_id, episode_id, t, action, substr(observation, 1, 160) AS observation, metadata_json
        FROM episode_steps
        ORDER BY rowid DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    out = []
    for r in rows:
        meta = {}
        try:
            meta = json.loads(r[5] or "{}")
        except Exception:
            meta = {"_raw": r[5]}
        out.append(
            {
                "step_id": r[0],
                "episode_id": r[1],
                "t": r[2],
                "action": r[3],
                "observation": r[4],
                "source_kind": meta.get("source_kind"),
                "source_path": meta.get("source_path"),
            }
        )
    return out


def _source_kind_breakdown(con: sqlite3.Connection) -> list[tuple[str, int]]:
    # metadata_json stores source_kind for legacy import steps; this is best-effort.
    rows = con.execute(
        """
        SELECT
          CASE
            WHEN json_extract(metadata_json, '$.source_kind') IS NULL THEN '(none)'
            ELSE json_extract(metadata_json, '$.source_kind')
          END AS sk,
          COUNT(*) AS n
        FROM episode_steps
        GROUP BY sk
        ORDER BY n DESC
        """
    ).fetchall()
    return [(str(r[0]), int(r[1])) for r in rows]


def main() -> None:
    p = argparse.ArgumentParser(description="Show PlugMem sqlite db stats")
    p.add_argument("--db", default="plugmem/data/plugmem.db", help="Path to sqlite db")
    p.add_argument("--latest", type=int, default=5, help="Show latest N episode_steps")
    p.add_argument("--json", action="store_true", help="Print as JSON")
    args = p.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")

    con = sqlite3.connect(str(db_path))

    stats = {"db": str(db_path), "tables": {}, "latest_steps": [], "source_kind": []}

    for t in TABLES:
        try:
            stats["tables"][t] = _count(con, t)
        except Exception as e:
            stats["tables"][t] = {"error": str(e)}

    try:
        stats["latest_steps"] = _latest_steps(con, args.latest)
    except Exception as e:
        stats["latest_steps"] = [{"error": str(e)}]

    try:
        stats["source_kind"] = [{"source_kind": k, "steps": n} for k, n in _source_kind_breakdown(con)]
    except Exception as e:
        stats["source_kind"] = [{"error": str(e)}]

    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return

    print(f"DB: {stats['db']}")
    print("Counts:")
    for k, v in stats["tables"].items():
        print(f"- {k}: {v}")

    if stats.get("source_kind"):
        print("\nepisode_steps by source_kind:")
        for row in stats["source_kind"]:
            if "error" in row:
                print(f"- error: {row['error']}")
            else:
                print(f"- {row['source_kind']}: {row['steps']}")

    if stats.get("latest_steps"):
        print("\nLatest episode_steps:")
        for s in stats["latest_steps"]:
            if "error" in s:
                print(f"- error: {s['error']}")
                continue
            extra = ""
            if s.get("source_kind") or s.get("source_path"):
                extra = f" ({s.get('source_kind')}:{s.get('source_path')})"
            print(f"- {s['step_id']} ep={s['episode_id']} t={s['t']} action={s['action']}{extra}\n  {s['observation']}")


if __name__ == "__main__":
    main()
