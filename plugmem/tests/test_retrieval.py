from pathlib import Path

from plugmem.app import PlugMem
from plugmem.core.llm.fake import FakeLLM
from plugmem.core.retrieval.retriever import RetrievalInput


def test_retrieval_returns_matching_memory(tmp_path: Path) -> None:
    db_path = tmp_path / "retrieval.db"
    plugmem = PlugMem.build_default(str(db_path), llm=FakeLLM())

    raw_trace = [
        {"obs": "The shopping site search page is open.", "action": "open_search_page"},
        {"obs": "The agent enters 'wireless mouse' in the search box.", "action": "search_wireless_mouse"},
        {"obs": "The agent sorts results by price ascending to find the cheapest option.", "action": "sort_by_price"},
        {"obs": "The agent confirms the top result is a relevant wireless mouse.", "action": "inspect_result"},
    ]

    plugmem.ingest(
        raw_trace=raw_trace,
        task_type="web_agent",
        instruction="Find the cheapest relevant wireless mouse on the website.",
    )

    retrieved = plugmem.retriever.retrieve(
        RetrievalInput(query="How do I find the cheapest wireless mouse?")
    )

    assert len(retrieved.proposition_ids) >= 1
    assert len(retrieved.prescription_ids) >= 1
    assert len(retrieved.evidence_step_ids) >= 1
    assert any(score > 0 for score in retrieved.scores.values())
