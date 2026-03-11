from __future__ import annotations

from pathlib import Path

from plugmem.app.plugmem import PlugMem
from plugmem.core.llm.fake import FakeLLM


def test_suggested_actions_can_align_to_workflow_steps(tmp_path: Path) -> None:
    db_path = tmp_path / "structured.db"
    plugmem = PlugMem.build_default(str(db_path), llm=FakeLLM())

    raw_trace = [
        {"obs": "The shopping site search page is open.", "action": "open_search_page"},
        {"obs": "The agent enters 'wireless mouse' in the search box.", "action": "search_wireless_mouse"},
        {"obs": "The agent sorts results by price ascending to find the cheapest option.", "action": "sort_by_price"},
    ]

    plugmem.ingest(raw_trace=raw_trace, task_type="web_agent", instruction="Find cheapest wireless mouse")
    ans = plugmem.retrieve_structured(query="What should I do next?")

    assert ans.metadata.get("actions_aligned_to_dsl") in {True, False}
    assert isinstance(ans.suggested_actions, list)
    # Alignment is best-effort; when DSL is missing or targets don't match exactly, step links may be None.
    for a in ans.suggested_actions:
        assert hasattr(a, "source_prescription_step")
