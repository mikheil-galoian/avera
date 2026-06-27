"""SQLite-backed persistent storage for AVERA analysis runs.

Design principles:
- Air-gapped: zero external dependencies, stdlib sqlite3 only
- Append-only: runs are never mutated once written (content-addressed by run_id)
- Deterministic: identical inputs always produce identical stored payloads
- Thread-safe: WAL mode + explicit connection-per-operation pattern
- Schema-versioned: _schema_version in the metadata table enables migrations

Usage::

    from pathlib import Path
    from avera.storage import AnalysisStore

    store = AnalysisStore(Path("avera-history.db"))
    store.store_analysis(report_dict, project="bms-fast-charge")

    for record in store.query_history(verdict="confirmed_regression"):
        print(record.run_id, record.risk)

    record = store.get_run("run-20260509-abc123")
    print(record.full_report)
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


# ---------------------------------------------------------------------------
# Public exceptions
# ---------------------------------------------------------------------------

class StoreError(RuntimeError):
    """Raised when a storage operation cannot be completed."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RunRecord:
    """Lightweight summary record returned by query_history().

    The ``full_report`` field is ``None`` when returned from
    :meth:`AnalysisStore.query_history` (projection query).  It is
    populated by :meth:`AnalysisStore.get_run`.
    """

    run_id: str
    project: str
    verdict: str
    risk: str
    confidence: str
    confidence_score: float
    schema_version: str
    stored_at: str                        # ISO-8601 UTC
    full_report: dict[str, Any] | None = field(default=None, compare=False)


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous  = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS _store_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id           TEXT PRIMARY KEY,
    project          TEXT NOT NULL DEFAULT '',
    verdict          TEXT NOT NULL DEFAULT '',
    risk             TEXT NOT NULL DEFAULT '',
    confidence       TEXT NOT NULL DEFAULT '',
    confidence_score REAL NOT NULL DEFAULT 0.0,
    schema_version   TEXT NOT NULL DEFAULT '',
    stored_at        TEXT NOT NULL,
    report_json      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_project   ON runs (project);
CREATE INDEX IF NOT EXISTS idx_runs_verdict   ON runs (verdict);
CREATE INDEX IF NOT EXISTS idx_runs_risk      ON runs (risk);
CREATE INDEX IF NOT EXISTS idx_runs_stored_at ON runs (stored_at);
"""

_SCHEMA_VERSION = "avera.store.v1"


# ---------------------------------------------------------------------------
# AnalysisStore
# ---------------------------------------------------------------------------

class AnalysisStore:
    """Thread-safe SQLite store for AVERA analysis runs.

    Parameters
    ----------
    path:
        Filesystem path for the SQLite database file.  Passing
        ``Path(":memory:")`` creates an in-process, non-persistent database
        useful for tests.
    """

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._local = threading.local()
        self._init_schema()

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> AnalysisStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close any open connection held by the calling thread."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    # ------------------------------------------------------------------
    # Core public API
    # ------------------------------------------------------------------

    def store_analysis(
        self,
        report: dict[str, Any],
        *,
        project: str = "",
        run_id: str | None = None,
    ) -> RunRecord:
        """Persist an AVERA report dict and return its :class:`RunRecord`.

        Parameters
        ----------
        report:
            The full JSON-serialisable report dictionary produced by
            ``avera.reports.assessment_to_dict`` or ``run_analyze``.
        project:
            Optional human-readable project name / fixture name.
        run_id:
            Explicit run identifier.  When omitted a stable identifier is
            derived from the stored-at timestamp (ISO-8601 UTC microseconds).
            Caller-supplied IDs enable idempotent re-ingestion: storing the
            same *run_id* twice is a no-op.

        Returns
        -------
        RunRecord
            The newly stored (or pre-existing) record.

        Raises
        ------
        StoreError
            If *report* is not JSON-serialisable or the write fails.
        """

        stored_at = _utc_now_iso()
        if run_id is None:
            run_id = _derive_run_id(stored_at, project)

        verdict          = str(report.get("verdict", ""))
        risk             = str(report.get("risk", ""))
        confidence       = str(report.get("confidence", ""))
        confidence_score = float(report.get("confidence_score", 0.0))
        schema_version   = str(report.get("schema_version", ""))

        try:
            report_json = json.dumps(report, sort_keys=True, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise StoreError(f"report is not JSON-serialisable: {exc}") from exc

        conn = self._connection()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO runs
                    (run_id, project, verdict, risk, confidence,
                     confidence_score, schema_version, stored_at, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, project, verdict, risk, confidence,
                    confidence_score, schema_version, stored_at, report_json,
                ),
            )
            conn.commit()
        except sqlite3.Error as exc:
            raise StoreError(f"failed to store run {run_id!r}: {exc}") from exc

        return RunRecord(
            run_id=run_id,
            project=project,
            verdict=verdict,
            risk=risk,
            confidence=confidence,
            confidence_score=confidence_score,
            schema_version=schema_version,
            stored_at=stored_at,
            full_report=report,
        )

    def get_run(self, run_id: str) -> RunRecord | None:
        """Return the full :class:`RunRecord` for *run_id*, or ``None``.

        The ``full_report`` field is populated with the original report dict.
        """

        conn = self._connection()
        row = conn.execute(
            """
            SELECT run_id, project, verdict, risk, confidence,
                   confidence_score, schema_version, stored_at, report_json
            FROM runs WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        if row is None:
            return None
        return _row_to_record(row, include_report=True)

    def query_history(
        self,
        *,
        project: str | None = None,
        verdict: str | None = None,
        risk: str | None = None,
        confidence: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 200,
        order: str = "desc",
    ) -> list[RunRecord]:
        """Return a list of matching :class:`RunRecord` (without full reports).

        All filters are ANDed together.  All string comparisons are
        case-sensitive to preserve the exact AVERA vocabulary.

        Parameters
        ----------
        project:
            Exact match on the project name.
        verdict:
            Exact match on ``verdict`` field (e.g. ``"confirmed_regression"``).
        risk:
            Exact match on ``risk`` field (e.g. ``"release_blocking"``).
        confidence:
            Exact match on ``confidence`` field (e.g. ``"high"``).
        since:
            ISO-8601 lower bound for ``stored_at`` (inclusive).
        until:
            ISO-8601 upper bound for ``stored_at`` (inclusive).
        limit:
            Maximum rows to return.  Hard-capped at 10 000 to prevent
            accidental full-table scans.
        order:
            ``"asc"`` or ``"desc"`` (default) for ``stored_at`` ordering.

        Returns
        -------
        list[RunRecord]
            Matching records ordered by ``stored_at``.  ``full_report`` is
            always ``None``; call :meth:`get_run` if you need the payload.
        """

        limit = min(int(limit), 10_000)
        order_dir = "ASC" if str(order).lower() == "asc" else "DESC"

        clauses: list[str] = []
        params: list[Any] = []

        if project is not None:
            clauses.append("project = ?")
            params.append(project)
        if verdict is not None:
            clauses.append("verdict = ?")
            params.append(verdict)
        if risk is not None:
            clauses.append("risk = ?")
            params.append(risk)
        if confidence is not None:
            clauses.append("confidence = ?")
            params.append(confidence)
        if since is not None:
            clauses.append("stored_at >= ?")
            params.append(since)
        if until is not None:
            clauses.append("stored_at <= ?")
            params.append(until)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT run_id, project, verdict, risk, confidence,
                   confidence_score, schema_version, stored_at
            FROM runs
            {where}
            ORDER BY stored_at {order_dir}
            LIMIT ?
        """
        params.append(limit)

        conn = self._connection()
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_record(row, include_report=False) for row in rows]

    def count(self, **filters: str) -> int:
        """Return the count of runs matching *filters* (same kwargs as :meth:`query_history`)."""
        return len(self.query_history(**filters, limit=10_000))

    def iter_runs(
        self,
        *,
        project: str | None = None,
        verdict: str | None = None,
        batch_size: int = 100,
    ) -> Iterator[RunRecord]:
        """Yield full :class:`RunRecord` objects (including report) in stored_at ASC order.

        Useful for bulk exports or migrations without loading everything into
        memory at once.
        """

        conn = self._connection()
        clauses: list[str] = []
        params: list[Any] = []
        if project is not None:
            clauses.append("project = ?")
            params.append(project)
        if verdict is not None:
            clauses.append("verdict = ?")
            params.append(verdict)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT run_id, project, verdict, risk, confidence,
                   confidence_score, schema_version, stored_at, report_json
            FROM runs {where}
            ORDER BY stored_at ASC
        """
        cursor = conn.execute(sql, params)
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            for row in rows:
                yield _row_to_record(row, include_report=True)

    # ------------------------------------------------------------------
    # Schema inspection helpers
    # ------------------------------------------------------------------

    def schema_version(self) -> str | None:
        """Return the stored schema version string, or ``None`` if not set."""
        conn = self._connection()
        row = conn.execute(
            "SELECT value FROM _store_meta WHERE key = 'schema_version'"
        ).fetchone()
        return row[0] if row else None

    def run_count(self) -> int:
        """Return total number of stored runs."""
        conn = self._connection()
        row = conn.execute("SELECT COUNT(*) FROM runs").fetchone()
        return int(row[0]) if row else 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connection(self) -> sqlite3.Connection:
        """Return a per-thread SQLite connection, creating it if necessary."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            db_path = str(self._path) if str(self._path) != ":memory:" else ":memory:"
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Concurrency hardening. The default SQLite busy-timeout is 0, so a
            # writer that meets a held lock fails immediately with
            # "database is locked" (e.g. under concurrent threads). Wait for the
            # lock instead, and use WAL so readers never block the single writer.
            # WAL is a persistent, file-level mode and a harmless no-op for
            # ``:memory:`` databases.
            conn.execute("PRAGMA busy_timeout = 5000")
            if db_path != ":memory:":
                conn.execute("PRAGMA journal_mode = WAL")
            self._local.conn = conn
        return conn

    def _init_schema(self) -> None:
        """Create tables and write schema version on first open."""
        conn = self._connection()
        try:
            conn.executescript(_DDL)
            conn.execute(
                "INSERT OR IGNORE INTO _store_meta (key, value) VALUES ('schema_version', ?)",
                (_SCHEMA_VERSION,),
            )
            conn.commit()
        except sqlite3.Error as exc:
            raise StoreError(f"schema initialisation failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 string with microsecond precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _derive_run_id(stored_at: str, project: str) -> str:
    """Derive a stable, human-readable run identifier.

    Uses microsecond-precision timestamp so that rapid consecutive calls
    within the same second still yield distinct identifiers.
    """
    # stored_at is "YYYY-MM-DDTHH:MM:SS.ffffffZ" — keep full microseconds
    ts_compact = stored_at.rstrip("Z").replace("T", "-").replace(":", "").replace(".", "-")
    slug = "".join(c if c.isalnum() or c == "-" else "-" for c in project)[:32].strip("-")
    parts = [p for p in ["run", ts_compact, slug] if p]
    return "-".join(parts)


def _row_to_record(row: sqlite3.Row | tuple, *, include_report: bool) -> RunRecord:
    """Convert a SQLite row to a :class:`RunRecord`."""
    # Row columns: run_id, project, verdict, risk, confidence,
    #              confidence_score, schema_version, stored_at[, report_json]
    run_id          = row[0]
    project         = row[1]
    verdict         = row[2]
    risk            = row[3]
    confidence      = row[4]
    confidence_score = float(row[5])
    schema_version  = row[6]
    stored_at       = row[7]

    full_report: dict[str, Any] | None = None
    if include_report and len(row) > 8:
        try:
            full_report = json.loads(row[8])
        except (json.JSONDecodeError, TypeError):
            full_report = None

    return RunRecord(
        run_id=run_id,
        project=project,
        verdict=verdict,
        risk=risk,
        confidence=confidence,
        confidence_score=confidence_score,
        schema_version=schema_version,
        stored_at=stored_at,
        full_report=full_report,
    )
