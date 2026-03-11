from __future__ import annotations

import json

from plugmem.core.schema import MemoryContext, RetrievedMemory
from plugmem.core.storage.sqlite_store import SQLiteStore


class MemoryReasoner:
    """Compress retrieved memory into a final prompt block."""

    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store

    def build_context(self, query: str, retrieved: RetrievedMemory) -> MemoryContext:
        if not self.store:
            final_prompt_block = (
                "Relevant Facts:\n"
                "\n"
                "Useful Procedures:\n"
                "\n"
                "Grounding Evidence:\n"
            )
            return MemoryContext(final_prompt_block=final_prompt_block)

        proposition_rows = {row["proposition_id"]: row for row in self.store.fetch_propositions()}
        prescription_rows = {row["prescription_id"]: row for row in self.store.fetch_prescriptions()}
        evidence_rows = {row["step_id"]: row for row in self.store.fetch_episode_steps(retrieved.evidence_step_ids)}

        semantic_lines = []
        for proposition_id in retrieved.proposition_ids:
            row = proposition_rows.get(proposition_id)
            if not row:
                continue
            score = retrieved.scores.get(proposition_id)
            suffix = f" (score={score:.2f})" if score is not None else ""
            semantic_lines.append(f"- [proposition:{proposition_id}] {row['content']}{suffix}")

        procedural_lines = []
        for prescription_id in retrieved.prescription_ids:
            row = prescription_rows.get(prescription_id)
            if not row:
                continue
            score = retrieved.scores.get(prescription_id)
            suffix = f" (score={score:.2f})" if score is not None else ""
            workflow = row.get("workflow") or []

            # Prefer DSL from metadata if present
            meta = row.get("metadata") or {}
            dsl = meta.get("workflow_dsl") if isinstance(meta, dict) else None

            procedural_lines.append(f"- [prescription:{prescription_id}] Intent: {row['intent_text']}{suffix}")
            if isinstance(dsl, dict):
                procedural_lines.append(f"  - DSL: {json.dumps(dsl, ensure_ascii=False)}")
            elif workflow:
                for step in workflow[:5]:
                    procedural_lines.append(f"  - {step}")

        evidence_lines = []
        sorted_evidence = sorted(evidence_rows.values(), key=lambda item: (item["episode_id"], item["t"]))
        for row in sorted_evidence:
            evidence_lines.append(
                f"- [episode_step:{row['step_id']}] Step {row['t']}: obs={row['observation']} | action={row['action']} | subgoal={row['subgoal']}"
            )

        semantic_summary = "\n".join(semantic_lines)
        procedural_summary = "\n".join(procedural_lines)
        evidence_summary = "\n".join(evidence_lines)

        final_prompt_block = (
            f"Task Query:\n- {query}\n\n"
            "Relevant Facts:\n"
            f"{semantic_summary or '- None'}\n\n"
            "Useful Procedures:\n"
            f"{procedural_summary or '- None'}\n\n"
            "Grounding Evidence:\n"
            f"{evidence_summary or '- None'}"
        )

        return MemoryContext(
            semantic_summary=semantic_summary,
            procedural_summary=procedural_summary,
            evidence_summary=evidence_summary,
            final_prompt_block=final_prompt_block,
        )
