"""Persistent registry for SimUniverse runs."""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from pydantic import BaseModel

def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


class SimUniverseRunRecord(BaseModel):
    """Serializable representation of a SimUniverse run."""

    run_id: str
    env: str
    git_sha: str
    config_path: str
    corpus_path: str
    created_at: datetime
    status: str
    error_message: str | None = None
    omega_total: float | None = None
    simuniverse_consistency: float | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "SimUniverseRunRecord":
        return cls(
            run_id=row["run_id"],
            env=row["env"],
            git_sha=row["git_sha"],
            config_path=row["config_path"],
            corpus_path=row["corpus_path"],
            created_at=datetime.fromisoformat(row["created_at"]),
            status=row["status"],
            error_message=row["error_message"],
            omega_total=row["omega_total"],
            simuniverse_consistency=row["simuniverse_consistency"],
        )


class SimUniverseRunCreate(BaseModel):
    run_id: str
    env: str
    git_sha: str
    config_path: str
    corpus_path: str


class SimUniverseRunUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None
    omega_total: Optional[float] = None
    simuniverse_consistency: Optional[float] = None

    def __init__(self, **data: object) -> None:
        super().__init__(**data)
        self._provided_fields = {
            field for field, value in data.items() if field in {
                "status",
                "error_message",
                "omega_total",
                "simuniverse_consistency",
            } and value is not None
        }

    def items(self) -> Iterable[tuple[str, object]]:
        for field in self._provided_fields:
            yield field, getattr(self, field)


class SimUniverseRunRegistry:
    """SQLite-backed registry for SimUniverse runs."""

    def __init__(self, db_path: str | Path = "simuniverse_runs.db") -> None:
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS simuniverse_runs (
                    run_id TEXT PRIMARY KEY,
                    env TEXT NOT NULL,
                    git_sha TEXT NOT NULL,
                    config_path TEXT NOT NULL,
                    corpus_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    omega_total REAL,
                    simuniverse_consistency REAL
                )
                """
            )
            conn.commit()

    def create_run(self, data: SimUniverseRunCreate) -> SimUniverseRunRecord:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO simuniverse_runs (
                        run_id, env, git_sha, config_path, corpus_path,
                        created_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data.run_id,
                        data.env,
                        data.git_sha,
                        data.config_path,
                        data.corpus_path,
                        _now(),
                        "running",
                    ),
                )
                conn.commit()
        record = self.get_run(data.run_id)
        if record is None:
            raise RuntimeError("Failed to read run after creation")
        return record

    def update_run(self, run_id: str, data: SimUniverseRunUpdate) -> SimUniverseRunRecord | None:
        updates = list(data.items())
        if not updates:
            return self.get_run(run_id)
        assignments = ", ".join(f"{field} = ?" for field, _ in updates)
        values = [value for _, value in updates]
        values.append(run_id)
        with self._lock:
            with self._connect() as conn:
                conn.execute(f"UPDATE simuniverse_runs SET {assignments} WHERE run_id = ?", values)
                conn.commit()
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> SimUniverseRunRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM simuniverse_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        return SimUniverseRunRecord.from_row(row)

    def list_runs(self, env: str | None = None, limit: int = 50) -> List[SimUniverseRunRecord]:
        query = "SELECT * FROM simuniverse_runs"
        params: tuple[object, ...] = ()
        if env:
            query += " WHERE env = ?"
            params = (env,)
        query += " ORDER BY created_at DESC LIMIT ?"
        params = params + (limit,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [SimUniverseRunRecord.from_row(row) for row in rows]
