from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from plugmem.core.schema import Episode, Prescription, Proposition


class SQLiteStore:
    """SQLite persistence for PlugMem entities."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._in_transaction = False

    def initialize(self) -> None:
        schema_sql = """
        CREATE TABLE IF NOT EXISTS episode_steps (
            step_id TEXT PRIMARY KEY,
            episode_id TEXT NOT NULL,
            t INTEGER NOT NULL,
            observation TEXT NOT NULL,
            state TEXT,
            action TEXT NOT NULL,
            reward REAL,
            subgoal TEXT,
            metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS propositions (
            proposition_id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            confidence REAL,
            metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS concepts (
            concept_id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            aliases_json TEXT,
            metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS prescriptions (
            prescription_id TEXT PRIMARY KEY,
            intent_text TEXT NOT NULL,
            workflow_json TEXT NOT NULL,
            success_score REAL,
            metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS intents (
            intent_id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS edges (
            edge_id TEXT PRIMARY KEY,
            src_type TEXT NOT NULL,
            src_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            dst_type TEXT NOT NULL,
            dst_id TEXT NOT NULL,
            metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS source_links (
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            source_step_id TEXT NOT NULL,
            PRIMARY KEY (item_type, item_id, source_step_id)
        );

        CREATE TABLE IF NOT EXISTS dedup_audit (
            audit_id TEXT PRIMARY KEY,
            item_type TEXT NOT NULL,
            candidate_id TEXT NOT NULL,
            existing_id TEXT NOT NULL,
            judge_result TEXT NOT NULL,
            confidence REAL,
            reason TEXT,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_episode_steps_episode_t ON episode_steps(episode_id, t);
        CREATE INDEX IF NOT EXISTS idx_propositions_content ON propositions(content);
        CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name);
        CREATE INDEX IF NOT EXISTS idx_prescriptions_intent_text ON prescriptions(intent_text);
        CREATE INDEX IF NOT EXISTS idx_intents_name ON intents(name);
        CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_id, edge_type);
        CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_id, edge_type);
        CREATE INDEX IF NOT EXISTS idx_source_links_source_step ON source_links(source_step_id);
        CREATE INDEX IF NOT EXISTS idx_dedup_audit_item ON dedup_audit(item_type, candidate_id, existing_id);
        """
        self.conn.executescript(schema_sql)
        self.conn.commit()

    def configure_pragmas(self) -> None:
        """Best-effort SQLite pragmas for better performance and correctness."""
        try:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
            self.conn.execute("PRAGMA foreign_keys=ON;")
        except sqlite3.Error:
            # Best-effort only.
            pass

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Wrap multiple writes into a single transaction.

        Avoids excessive commits and speeds up batch ingestion.
        """
        if self._in_transaction:
            yield
            return

        self._in_transaction = True
        try:
            self.conn.execute("BEGIN")
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            self._in_transaction = False

    def _commit_if_needed(self) -> None:
        if not self._in_transaction:
            self.conn.commit()

    def write_episode(self, episode: Episode) -> None:
        for step in episode.steps:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO episode_steps (
                    step_id, episode_id, t, observation, state, action, reward, subgoal, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step.step_id,
                    step.episode_id,
                    step.t,
                    step.observation,
                    step.state,
                    step.action,
                    step.reward,
                    step.subgoal,
                    json.dumps(step.metadata, ensure_ascii=False),
                ),
            )
        self._commit_if_needed()

    def write_propositions(self, propositions: list[Proposition]) -> None:
        for item in propositions:
            self.conn.execute(
                "INSERT OR REPLACE INTO propositions (proposition_id, content, confidence, metadata_json) VALUES (?, ?, ?, ?)",
                (item.proposition_id, item.content, item.confidence, json.dumps(item.metadata, ensure_ascii=False)),
            )
            self._replace_source_links("proposition", item.proposition_id, item.source_step_ids)
            self._upsert_concepts(item.concepts)
            self._replace_edges_for_item(
                src_type="proposition",
                src_id=item.proposition_id,
                mentions=[(self._concept_id(name), name) for name in item.concepts],
                solves=[],
                source_step_ids=item.source_step_ids,
            )
        self._commit_if_needed()

    def write_prescriptions(self, prescriptions: list[Prescription]) -> None:
        for item in prescriptions:
            self.conn.execute(
                "INSERT OR REPLACE INTO prescriptions (prescription_id, intent_text, workflow_json, success_score, metadata_json) VALUES (?, ?, ?, ?, ?)",
                (
                    item.prescription_id,
                    item.intent,
                    json.dumps(item.workflow, ensure_ascii=False),
                    item.success_score,
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )
            self._replace_source_links("prescription", item.prescription_id, item.source_step_ids)
            self._upsert_intent(item.intent)
            self._replace_edges_for_item(
                src_type="prescription",
                src_id=item.prescription_id,
                mentions=[],
                solves=[(self._intent_id(item.intent), item.intent)],
                source_step_ids=item.source_step_ids,
            )
        self._commit_if_needed()

    def write_dedup_audit(
        self,
        item_type: str,
        candidate_id: str,
        existing_id: str,
        judge_result: str,
        confidence: float | None = None,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO dedup_audit (
                audit_id, item_type, candidate_id, existing_id, judge_result, confidence, reason, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"audit_{uuid4().hex}",
                item_type,
                candidate_id,
                existing_id,
                judge_result,
                confidence,
                reason,
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self._commit_if_needed()

    def fetch_propositions(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT proposition_id, content, confidence, metadata_json FROM propositions").fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            concept_rows = self.conn.execute(
                """
                SELECT c.name
                FROM edges e
                JOIN concepts c ON c.concept_id = e.dst_id
                WHERE e.src_id = ? AND e.edge_type = 'mentions'
                """,
                (row["proposition_id"],),
            ).fetchall()
            items.append(
                {
                    "proposition_id": row["proposition_id"],
                    "content": row["content"],
                    "confidence": row["confidence"],
                    "metadata": json.loads(row["metadata_json"] or "{}"),
                    "concept_names": [concept_row["name"] for concept_row in concept_rows],
                }
            )
        return items

    def fetch_prescriptions(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT prescription_id, intent_text, workflow_json, success_score, metadata_json FROM prescriptions"
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            items.append(
                {
                    "prescription_id": row["prescription_id"],
                    "intent_text": row["intent_text"],
                    "workflow": json.loads(row["workflow_json"] or "[]"),
                    "success_score": row["success_score"],
                    "metadata": json.loads(row["metadata_json"] or "{}"),
                }
            )
        return items

    def fetch_source_links(self, item_id: str | None = None, item_type: str | None = None) -> list[sqlite3.Row]:
        query = "SELECT * FROM source_links WHERE 1=1"
        params: list[Any] = []
        if item_id is not None:
            query += " AND item_id = ?"
            params.append(item_id)
        if item_type is not None:
            query += " AND item_type = ?"
            params.append(item_type)
        return list(self.conn.execute(query, params))

    def fetch_episode_steps(self, step_ids: list[str] | None = None) -> list[dict[str, Any]]:
        if not step_ids:
            rows = self.conn.execute(
                "SELECT step_id, episode_id, t, observation, state, action, reward, subgoal, metadata_json FROM episode_steps"
            ).fetchall()
        else:
            placeholders = ",".join("?" for _ in step_ids)
            rows = self.conn.execute(
                f"SELECT step_id, episode_id, t, observation, state, action, reward, subgoal, metadata_json FROM episode_steps WHERE step_id IN ({placeholders})",
                step_ids,
            ).fetchall()
        return [
            {
                "step_id": row["step_id"],
                "episode_id": row["episode_id"],
                "t": row["t"],
                "observation": row["observation"],
                "state": row["state"],
                "action": row["action"],
                "reward": row["reward"],
                "subgoal": row["subgoal"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            }
            for row in rows
        ]

    def fetch_edges(self, src_id: str | None = None, dst_id: str | None = None, edge_type: str | None = None) -> list[sqlite3.Row]:
        query = "SELECT * FROM edges WHERE 1=1"
        params: list[Any] = []
        if src_id is not None:
            query += " AND src_id = ?"
            params.append(src_id)
        if dst_id is not None:
            query += " AND dst_id = ?"
            params.append(dst_id)
        if edge_type is not None:
            query += " AND edge_type = ?"
            params.append(edge_type)
        return list(self.conn.execute(query, params))

    def _replace_source_links(self, item_type: str, item_id: str, source_step_ids: list[str]) -> None:
        self.conn.execute("DELETE FROM source_links WHERE item_type = ? AND item_id = ?", (item_type, item_id))
        for source_step_id in source_step_ids:
            self.conn.execute(
                "INSERT OR REPLACE INTO source_links (item_type, item_id, source_step_id) VALUES (?, ?, ?)",
                (item_type, item_id, source_step_id),
            )

    def _replace_edges_for_item(
        self,
        src_type: str,
        src_id: str,
        mentions: list[tuple[str, str]],
        solves: list[tuple[str, str]],
        source_step_ids: list[str],
    ) -> None:
        self.conn.execute("DELETE FROM edges WHERE src_type = ? AND src_id = ?", (src_type, src_id))

        for concept_id, _ in mentions:
            self._insert_edge(src_type, src_id, "mentions", "concept", concept_id)
        for intent_id, _ in solves:
            self._insert_edge(src_type, src_id, "solves", "intent", intent_id)
        for source_step_id in source_step_ids:
            self._insert_edge(src_type, src_id, "proves_from", "episode_step", source_step_id)

    def _insert_edge(
        self,
        src_type: str,
        src_id: str,
        edge_type: str,
        dst_type: str,
        dst_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO edges (edge_id, src_type, src_id, edge_type, dst_type, dst_id, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"edge_{uuid4().hex}",
                src_type,
                src_id,
                edge_type,
                dst_type,
                dst_id,
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )

    def _upsert_concepts(self, concept_names: list[str]) -> None:
        for name in concept_names:
            self.conn.execute(
                "INSERT OR IGNORE INTO concepts (concept_id, name, aliases_json, metadata_json) VALUES (?, ?, ?, ?)",
                (self._concept_id(name), name, json.dumps([], ensure_ascii=False), json.dumps({}, ensure_ascii=False)),
            )

    def _upsert_intent(self, intent_name: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO intents (intent_id, name, metadata_json) VALUES (?, ?, ?)",
            (self._intent_id(intent_name), intent_name, json.dumps({}, ensure_ascii=False)),
        )

    @staticmethod
    def _concept_id(name: str) -> str:
        return f"concept::{name.strip().lower()}"

    @staticmethod
    def _intent_id(name: str) -> str:
        return f"intent::{name.strip().lower()}"

    def close(self) -> None:
        self.conn.close()
