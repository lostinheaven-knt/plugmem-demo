from __future__ import annotations

from pathlib import Path

from plugmem.core.schema.semantic import Proposition
from plugmem.core.storage.sqlite_store import SQLiteStore
from plugmem.core.structuring.deduplicator import LLMDeduplicator
from plugmem.tests.fake_merge_llm import MergeFakeLLM


def test_semantic_merge_decision_marks_inactive_and_audits(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    store = SQLiteStore(db_path)
    store.initialize()

    llm = MergeFakeLLM(relationship="UPDATE_SAME_FACT")
    dedup = LLMDeduplicator(llm=llm, store=store)

    earlier = Proposition(content="User likes wireless mouse", concepts=["mouse"], source_step_ids=["s1"], metadata={"active": True})
    later = Proposition(content="User prefers wireless mice", concepts=["mouse"], source_step_ids=["s2"], metadata={"active": True})

    out = dedup.deduplicate_propositions(new_items=[later], existing_items=[earlier])

    assert len(out) == 1
    merged = out[0]
    assert "Merged fact" in merged.content

    # earlier/later should be marked inactive and point to merged id
    assert earlier.metadata.get("active") is False
    assert earlier.metadata.get("superseded_by") == merged.proposition_id

    assert later.metadata.get("active") is False
    assert later.metadata.get("superseded_by") == merged.proposition_id

    # audit should have at least one proposition_merge entry
    rows = store.conn.execute(
        "SELECT item_type, judge_result, confidence FROM dedup_audit WHERE item_type = 'proposition_merge'"
    ).fetchall()
    assert len(rows) >= 1

    store.close()
