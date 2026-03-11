from pathlib import Path

from plugmem.app import PlugMem
from plugmem.core.llm.fake import FakeLLM


def test_reasoning_builds_memory_block(tmp_path: Path) -> None:
    db_path = tmp_path / "reasoning.db"
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

    memory_context = plugmem.retrieve(query="How do I find the cheapest wireless mouse?")

    assert "Relevant Facts:" in memory_context.final_prompt_block
    assert "Useful Procedures:" in memory_context.final_prompt_block
    assert "Grounding Evidence:" in memory_context.final_prompt_block
    assert "wireless mouse" in memory_context.final_prompt_block.lower()
    assert memory_context.semantic_summary
    assert memory_context.procedural_summary
