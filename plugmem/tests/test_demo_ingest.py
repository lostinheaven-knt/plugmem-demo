from pathlib import Path

from plugmem.app import PlugMem
from plugmem.core.llm.fake import FakeLLM


def test_demo_ingest_populates_store(tmp_path: Path) -> None:
    db_path = tmp_path / "demo.db"
    plugmem = PlugMem.build_default(str(db_path), llm=FakeLLM())

    raw_trace = [
        {"obs": "The search page is open.", "action": "open_search_page"},
        {"obs": "The agent searches for wireless mouse.", "action": "search_wireless_mouse"},
        {"obs": "The agent sorts results by price ascending.", "action": "sort_by_price"},
    ]

    plugmem.ingest(
        raw_trace=raw_trace,
        task_type="web_agent",
        instruction="Find the cheapest relevant wireless mouse.",
    )

    proposition_count = plugmem.sqlite_store.conn.execute(
        "SELECT COUNT(*) FROM propositions"
    ).fetchone()[0]
    prescription_count = plugmem.sqlite_store.conn.execute(
        "SELECT COUNT(*) FROM prescriptions"
    ).fetchone()[0]
    edge_count = plugmem.sqlite_store.conn.execute(
        "SELECT COUNT(*) FROM edges"
    ).fetchone()[0]

    assert proposition_count >= 1
    assert prescription_count >= 1
    assert edge_count >= 1
