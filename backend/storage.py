from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    """Small SQLite repository suitable for the single-instance demo deployment."""

    def __init__(self, path: Optional[Path] = None):
        default = Path(__file__).resolve().parent / "data" / "app.db"
        self.path = path or Path(os.getenv("DATABASE_PATH", str(default)))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, filename TEXT NOT NULL, sha256 TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
                    page_count INTEGER, chunk_count INTEGER NOT NULL DEFAULT 0,
                    error TEXT, warnings TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    document_id TEXT NOT NULL, chunk_index INTEGER NOT NULL, page INTEGER NOT NULL,
                    section TEXT NOT NULL, text TEXT NOT NULL, vector TEXT NOT NULL,
                    PRIMARY KEY (document_id, chunk_index)
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    document_id TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL, PRIMARY KEY (document_id, kind)
                );
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, operation TEXT NOT NULL,
                    model TEXT NOT NULL, latency_ms REAL NOT NULL, prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL, success INTEGER NOT NULL,
                    estimated_cost_usd REAL NOT NULL DEFAULT 0,
                    metadata TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
                );
                """
            )
            columns = {row[1] for row in db.execute("PRAGMA table_info(metrics)").fetchall()}
            if "estimated_cost_usd" not in columns:
                db.execute("ALTER TABLE metrics ADD COLUMN estimated_cost_usd REAL NOT NULL DEFAULT 0")

    def find_by_hash(self, sha256: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM documents WHERE sha256 = ?", (sha256,)).fetchone()
        return dict(row) if row else None

    def create_document(self, document_id: str, filename: str, sha256: str) -> Dict[str, Any]:
        created_at = utc_now()
        with self._connect() as db:
            db.execute(
                "INSERT INTO documents (id, filename, sha256, status, progress, created_at) VALUES (?, ?, ?, 'QUEUED', 0, ?)",
                (document_id, filename, sha256, created_at),
            )
        return self.get_document(document_id) or {}

    def update_document(self, document_id: str, **fields: Any) -> None:
        allowed = {"status", "progress", "page_count", "chunk_count", "error", "warnings"}
        values = {key: value for key, value in fields.items() if key in allowed}
        if "warnings" in values:
            values["warnings"] = json.dumps(values["warnings"])
        if not values:
            return
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as db:
            db.execute(
                f"UPDATE documents SET {assignments} WHERE id = ?",  # keys are allow-listed
                (*values.values(), document_id),
            )

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        return dict(row) if row else None

    def list_documents(self) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM documents ORDER BY created_at DESC LIMIT 50").fetchall()
        return [dict(row) for row in rows]

    def replace_chunks(self, document_id: str, chunks: List[Dict[str, Any]]) -> None:
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            db.executemany(
                "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        document_id, chunk["chunk_index"], chunk["page"], chunk["section"],
                        chunk["text"], json.dumps(chunk["vector"]),
                    )
                    for chunk in chunks
                ],
            )

    def get_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index", (document_id,)
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["vector"] = json.loads(item["vector"])
            result.append(item)
        return result

    def save_artifact(self, document_id: str, kind: str, payload: Dict[str, Any]) -> None:
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO artifacts VALUES (?, ?, ?, ?) ON CONFLICT(document_id, kind) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                (document_id, kind, json.dumps(payload), utc_now()),
            )

    def get_artifact(self, document_id: str, kind: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute(
                "SELECT payload FROM artifacts WHERE document_id = ? AND kind = ?", (document_id, kind)
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def record_metric(self, operation: str, model: str, latency_ms: float, prompt_tokens: int = 0,
                      completion_tokens: int = 0, success: bool = True,
                      estimated_cost_usd: float = 0,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO metrics (operation, model, latency_ms, prompt_tokens, completion_tokens, success, estimated_cost_usd, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (operation, model, latency_ms, prompt_tokens, completion_tokens, int(success), estimated_cost_usd, json.dumps(metadata or {}), utc_now()),
            )

    def metrics_summary(self) -> Dict[str, Any]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT operation, COUNT(*) calls, ROUND(AVG(latency_ms), 2) avg_latency_ms, SUM(prompt_tokens + completion_tokens) total_tokens, ROUND(SUM(estimated_cost_usd), 6) estimated_cost_usd, SUM(success) successes FROM metrics GROUP BY operation"
            ).fetchall()
            totals = db.execute("SELECT COUNT(*) documents, SUM(chunk_count) chunks FROM documents").fetchone()
        return {"documents": totals["documents"] or 0, "chunks": totals["chunks"] or 0,
                "operations": [dict(row) for row in rows]}
