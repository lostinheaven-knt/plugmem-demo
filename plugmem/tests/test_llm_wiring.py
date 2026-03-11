from __future__ import annotations

from pathlib import Path

from plugmem.app import PlugMem
from plugmem.core.llm.fake import FakeLLM


def test_build_default_uses_env_loader_when_no_llm(tmp_path: Path) -> None:
    db_path = tmp_path / "env_loader.db"
    plugmem = PlugMem.build_default(str(db_path), llm=FakeLLM())
    assert plugmem.standardizer.llm is not None
    assert plugmem.semantic_extractor.llm is not None
    assert plugmem.procedural_extractor.llm is not None
