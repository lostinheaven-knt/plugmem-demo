from __future__ import annotations

import networkx as nx

from plugmem.core.schema import Episode, Prescription, Proposition


class MemoryGraphStore:
    """In-memory graph mirror for PlugMem knowledge structures."""

    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()

    def add_episode(self, episode: Episode) -> None:
        previous_step_id: str | None = None
        for step in episode.steps:
            self.graph.add_node(step.step_id, node_type="episode_step", data=step.model_dump())
            if previous_step_id is not None:
                self.graph.add_edge(previous_step_id, step.step_id, edge_type="next")
            previous_step_id = step.step_id

    def add_propositions(self, propositions: list[Proposition]) -> None:
        for prop in propositions:
            self.graph.add_node(prop.proposition_id, node_type="proposition", data=prop.model_dump())
            for concept in prop.concepts:
                concept_id = f"concept::{concept.lower()}"
                self.graph.add_node(concept_id, node_type="concept", name=concept)
                self.graph.add_edge(prop.proposition_id, concept_id, edge_type="mentions")
            for source_step_id in prop.source_step_ids:
                self.graph.add_edge(prop.proposition_id, source_step_id, edge_type="proves_from")

    def add_prescriptions(self, prescriptions: list[Prescription]) -> None:
        for prescription in prescriptions:
            self.graph.add_node(
                prescription.prescription_id,
                node_type="prescription",
                data=prescription.model_dump(),
            )
            intent_id = f"intent::{prescription.intent.lower()}"
            self.graph.add_node(intent_id, node_type="intent", name=prescription.intent)
            self.graph.add_edge(prescription.prescription_id, intent_id, edge_type="solves")
            for source_step_id in prescription.source_step_ids:
                self.graph.add_edge(prescription.prescription_id, source_step_id, edge_type="proves_from")
