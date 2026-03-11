from pathlib import Path

from plugmem.core.storage.sqlite_store import SQLiteStore


def test_sqlite_store_initializes_all_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "plugmem.db"
    store = SQLiteStore(db_path)
    store.initialize()

    rows = store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {row[0] for row in rows}

    assert "episode_steps" in table_names
    assert "propositions" in table_names
    assert "concepts" in table_names
    assert "prescriptions" in table_names
    assert "intents" in table_names
    assert "edges" in table_names
    assert "source_links" in table_names
    assert "dedup_audit" in table_names
