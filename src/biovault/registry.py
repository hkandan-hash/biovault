"""SQLite-backed dataset registry.

Every ingested dataset gets one row here: who it is, where its bytes live, its
size, its SHA-256 fingerprint, and arbitrary JSON metadata. The registry is the
single source of truth the rest of the platform (CLI today, API/UI later) reads
from.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    id                TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    original_filename TEXT,
    stored_path       TEXT NOT NULL,
    kind              TEXT,
    content_type      TEXT,
    size_bytes        INTEGER,
    sha256            TEXT,
    created_at        TEXT,
    metadata_json     TEXT
);
CREATE INDEX IF NOT EXISTS idx_datasets_sha256 ON datasets(sha256);
CREATE INDEX IF NOT EXISTS idx_datasets_kind   ON datasets(kind);
"""


@dataclass
class Dataset:
    id: str
    name: str
    original_filename: str
    stored_path: str
    kind: str
    content_type: str
    size_bytes: int
    sha256: str
    created_at: str
    metadata: dict = field(default_factory=dict)


class Registry:
    """Thin, typed wrapper over a SQLite datasets table."""

    def __init__(self, db_path: "str | Path") -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    # -- lifecycle -------------------------------------------------------
    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Registry":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- writes ----------------------------------------------------------
    def add(self, ds: Dataset) -> Dataset:
        self._conn.execute(
            "INSERT INTO datasets (id, name, original_filename, stored_path, kind, "
            "content_type, size_bytes, sha256, created_at, metadata_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ds.id,
                ds.name,
                ds.original_filename,
                ds.stored_path,
                ds.kind,
                ds.content_type,
                ds.size_bytes,
                ds.sha256,
                ds.created_at,
                json.dumps(ds.metadata),
            ),
        )
        self._conn.commit()
        return ds

    def delete(self, dataset_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        self._conn.commit()
        return cur.rowcount > 0

    # -- reads -----------------------------------------------------------
    def get(self, dataset_id: str) -> Optional[Dataset]:
        row = self._conn.execute(
            "SELECT * FROM datasets WHERE id = ?", (dataset_id,)
        ).fetchone()
        return self._row_to_dataset(row) if row else None

    def find_by_sha256(self, digest: str) -> Optional[Dataset]:
        row = self._conn.execute(
            "SELECT * FROM datasets WHERE sha256 = ? LIMIT 1", (digest,)
        ).fetchone()
        return self._row_to_dataset(row) if row else None

    def list(self, kind: Optional[str] = None) -> "list[Dataset]":
        if kind:
            rows = self._conn.execute(
                "SELECT * FROM datasets WHERE kind = ? ORDER BY created_at DESC, id",
                (kind,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM datasets ORDER BY created_at DESC, id"
            ).fetchall()
        return [self._row_to_dataset(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _row_to_dataset(row: sqlite3.Row) -> Dataset:
        return Dataset(
            id=row["id"],
            name=row["name"],
            original_filename=row["original_filename"],
            stored_path=row["stored_path"],
            kind=row["kind"],
            content_type=row["content_type"],
            size_bytes=row["size_bytes"],
            sha256=row["sha256"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata_json"] or "{}"),
        )
