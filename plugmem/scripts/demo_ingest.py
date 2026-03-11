from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugmem.app import PlugMem
from plugmem.core.llm.fake import FakeLLM


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    db_path = base_dir / "data" / "plugmem_demo.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Default to real DeepSeek (loaded from .secrets.env / env vars via PlugMem.build_default).
    # If secrets are not configured, fall back to FakeLLM for an offline demo.
    try:
        plugmem = PlugMem.build_default(str(db_path))
        llm_name = type(plugmem.standardizer.llm).__name__ if plugmem.standardizer.llm else "None"
        print(f"LLM: {llm_name}")
    except Exception as e:
        print(f"[warn] Failed to initialize real LLM from env (.secrets.env). Falling back to FakeLLM. Error: {e}")
        plugmem = PlugMem.build_default(str(db_path), llm=FakeLLM())

    raw_trace = [
        {
            "obs": "The shopping site search page is open.",
            "action": "open_search_page",
        },
        {
            "obs": "The agent enters 'wireless mouse' in the search box.",
            "action": "search_wireless_mouse",
        },
        {
            "obs": "The agent sorts results by price ascending to find the cheapest option.",
            "action": "sort_by_price",
        },
        {
            "obs": "The agent inspects the top result and confirms it is a relevant wireless mouse.",
            "action": "inspect_result",
        },
    ]

    plugmem.ingest(
        raw_trace=raw_trace,
        task_type="web_agent",
        instruction="Find the cheapest relevant wireless mouse on the website.",
        metadata={"demo": True},
    )

    conn = sqlite3.connect(db_path)
    tables = [
        "episode_steps",
        "propositions",
        "concepts",
        "prescriptions",
        "intents",
        "edges",
        "source_links",
        "dedup_audit",
    ]

    print(f"Demo database: {db_path}")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")

    print("\nSample propositions:")
    for row in conn.execute("SELECT proposition_id, content FROM propositions LIMIT 5"):
        print(f"- {row[0]} :: {row[1]}")

    print("\nSample prescriptions:")
    for row in conn.execute("SELECT prescription_id, intent_text, workflow_json FROM prescriptions LIMIT 5"):
        print(f"- {row[0]} :: {row[1]} :: {row[2]}")

    print("\nSample edges:")
    for row in conn.execute("SELECT src_id, edge_type, dst_id FROM edges LIMIT 10"):
        print(f"- {row[0]} -[{row[1]}]-> {row[2]}")

    conn.close()
    plugmem.sqlite_store.close()


if __name__ == "__main__":
    main()
