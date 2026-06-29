"""Human feedback store — verdict calibration loop.

Purpose:
    AVERA issues machine verdicts.  Engineers review them.  This store
    records *every human decision* (confirm / override) against an engine
    verdict so that accuracy can be tracked over time and confidence scores
    can be recalibrated empirically.

Design:
    - SQLite backend, zero external dependencies.
    - ``store_verdict()``  — called by the analysis pipeline when a verdict is issued.
    - ``record_feedback()`` — called by a human reviewer (or CI webhook) to confirm
                              or override the machine verdict.
    - ``calibration_stats()`` — returns per-project and global accuracy metrics.
    - ``drift_warning()``   — returns True if recent accuracy drops below threshold,
                              signalling that the engine may need recalibration.

Usage::

    from pathlib import Path
    from avera.feedback import FeedbackStore

    fb = FeedbackStore(Path("avera-feedback.db"))

    # Called automatically by analysis pipeline
    fb.store_verdict(run_id="r-001", project="bms-fast-charge",
                     verdict="confirmed_regression", risk="high",
                     confidence_score=0.95)

    # Called by engineer after review
    fb.record_feedback(run_id="r-001", human_verdict="confirmed_regression",
                       confirmed=True, reviewer="eng@acme.com",
                       notes="Thermal trace confirms the regression.")

    stats = fb.calibration_stats()
    print(stats.global_accuracy)   # 0.92

    if fb.drift_warning(window=20, threshold=0.80):
        print("WARNING: engine accuracy dropped below 80% in last 20 verdicts")
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


class FeedbackStoreError(RuntimeError):
    """Raised when a feedback-store operation fails (e.g. an integrity/foreign-key
    violation), so callers get a typed error instead of a raw ``sqlite3`` exception."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeedbackRecord:
    run_id: str
    project: str
    engine_verdict: str
    engine_risk: str
    confidence_score: float | None
    human_verdict: str | None
    confirmed: bool | None          # True=agreed, False=overruled, None=pending
    reviewer: str
    issued_at: str
    reviewed_at: str | None
    notes: str


@dataclass(frozen=True)
class CalibrationStats:
    project: str | None             # None = global
    total_verdicts: int
    reviewed: int
    confirmed: int
    overruled: int
    pending: int
    accuracy: float | None          # confirmed / reviewed, or None if no reviews yet
    most_common_override: str | None  # which engine verdict is most often overruled


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class FeedbackStore:
    """SQLite-backed feedback and calibration store.

    Parameters
    ----------
    path:
        Path to the SQLite database file.  Created on first use.
    """

    _DDL = """
    CREATE TABLE IF NOT EXISTS verdicts (
        run_id           TEXT PRIMARY KEY,
        project          TEXT NOT NULL,
        engine_verdict   TEXT NOT NULL,
        engine_risk      TEXT NOT NULL,
        confidence_score REAL,
        issued_at        TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS feedback (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id           TEXT NOT NULL REFERENCES verdicts(run_id),
        human_verdict    TEXT,
        confirmed        INTEGER,        -- 1=True, 0=False, NULL=pending
        reviewer         TEXT NOT NULL DEFAULT '',
        reviewed_at      TEXT NOT NULL,
        notes            TEXT NOT NULL DEFAULT ''
    );

    CREATE INDEX IF NOT EXISTS idx_verdicts_project ON verdicts(project);
    CREATE INDEX IF NOT EXISTS idx_feedback_run_id  ON feedback(run_id);
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._init_db()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store_verdict(
        self,
        *,
        run_id: str,
        project: str,
        verdict: str,
        risk: str,
        confidence_score: float | None = None,
    ) -> None:
        """Record a machine-issued verdict.  Idempotent (duplicate run_id ignored)."""
        with self._lock, self._connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO verdicts
                    (run_id, project, engine_verdict, engine_risk, confidence_score, issued_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, project, verdict, risk, confidence_score,
                 datetime.now(timezone.utc).isoformat()),
            )

    def record_feedback(
        self,
        *,
        run_id: str,
        confirmed: bool,
        human_verdict: str | None = None,
        reviewer: str = "",
        notes: str = "",
    ) -> None:
        """Record a human decision on a previously stored verdict.

        Parameters
        ----------
        run_id:
            Must match a previously stored verdict.
        confirmed:
            True if the human agrees with the engine verdict, False if overruling.
        human_verdict:
            The human's verdict (required when ``confirmed=False``).
        reviewer:
            Reviewer identifier (email, username, etc.).
        notes:
            Free-text justification for the decision.
        """
        try:
            with self._lock, self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO feedback
                        (run_id, human_verdict, confirmed, reviewer, reviewed_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (run_id, human_verdict, int(confirmed), reviewer,
                     datetime.now(timezone.utc).isoformat(), notes),
                )
        except sqlite3.IntegrityError as exc:
            # e.g. the foreign-key constraint: no stored verdict for this run_id.
            raise FeedbackStoreError(
                f"cannot record feedback for run_id {run_id!r}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_record(self, run_id: str) -> FeedbackRecord | None:
        """Return the combined verdict + latest feedback for a run_id."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT v.run_id, v.project, v.engine_verdict, v.engine_risk,
                       v.confidence_score, v.issued_at,
                       f.human_verdict, f.confirmed, f.reviewer,
                       f.reviewed_at, f.notes
                FROM verdicts v
                LEFT JOIN feedback f ON f.run_id = v.run_id
                WHERE v.run_id = ?
                ORDER BY f.id DESC LIMIT 1
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_pending(self, project: str | None = None) -> list[FeedbackRecord]:
        """Return verdicts that have no human feedback yet."""
        with self._connection() as conn:
            if project:
                rows = conn.execute(
                    """
                    SELECT v.run_id, v.project, v.engine_verdict, v.engine_risk,
                           v.confidence_score, v.issued_at,
                           NULL, NULL, '', NULL, ''
                    FROM verdicts v
                    LEFT JOIN feedback f ON f.run_id = v.run_id
                    WHERE f.id IS NULL AND v.project = ?
                    """, (project,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT v.run_id, v.project, v.engine_verdict, v.engine_risk,
                           v.confidence_score, v.issued_at,
                           NULL, NULL, '', NULL, ''
                    FROM verdicts v
                    LEFT JOIN feedback f ON f.run_id = v.run_id
                    WHERE f.id IS NULL
                    """
                ).fetchall()
        return [self._row_to_record(r) for r in rows]

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def calibration_stats(self, project: str | None = None) -> CalibrationStats:
        """Compute accuracy statistics.

        If ``project`` is given, scoped to that project; otherwise global.
        """
        with self._connection() as conn:
            where = "WHERE v.project = ?" if project else ""
            params: tuple[Any, ...] = (project,) if project else ()

            total = conn.execute(
                f"SELECT COUNT(*) FROM verdicts v {where}", params
            ).fetchone()[0]

            reviewed = conn.execute(
                f"""
                SELECT COUNT(DISTINCT v.run_id)
                FROM verdicts v JOIN feedback f ON f.run_id = v.run_id
                {where}
                """, params
            ).fetchone()[0]

            # Count each reviewed run ONCE, by its LATEST feedback row (a reviewer
            # may change their mind, appending a new row). Without this a run with
            # both a confirm and an overrule is double-counted, so confirmed +
            # overruled can exceed reviewed and accuracy can exceed 1.0.
            latest = (
                "JOIN (SELECT run_id, MAX(id) AS max_id FROM feedback GROUP BY run_id) "
                "latest ON latest.max_id = f.id"
            )

            confirmed_count = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM verdicts v JOIN feedback f ON f.run_id = v.run_id {latest}
                WHERE f.confirmed = 1 {'AND v.project = ?' if project else ''}
                """, params
            ).fetchone()[0]

            overruled_count = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM verdicts v JOIN feedback f ON f.run_id = v.run_id {latest}
                WHERE f.confirmed = 0 {'AND v.project = ?' if project else ''}
                """, params
            ).fetchone()[0]

            # Most commonly overruled engine verdict (by latest decision per run)
            row = conn.execute(
                f"""
                SELECT v.engine_verdict, COUNT(*) as cnt
                FROM verdicts v JOIN feedback f ON f.run_id = v.run_id {latest}
                WHERE f.confirmed = 0 {'AND v.project = ?' if project else ''}
                GROUP BY v.engine_verdict ORDER BY cnt DESC LIMIT 1
                """, params
            ).fetchone()
            most_overruled = row[0] if row else None

        pending = total - reviewed
        accuracy = round(confirmed_count / reviewed, 4) if reviewed else None

        return CalibrationStats(
            project=project,
            total_verdicts=total,
            reviewed=reviewed,
            confirmed=confirmed_count,
            overruled=overruled_count,
            pending=pending,
            accuracy=accuracy,
            most_common_override=most_overruled,
        )

    def drift_warning(self, window: int = 20, threshold: float = 0.80) -> bool:
        """Return True if accuracy in the last ``window`` reviews is below ``threshold``.

        Used as an early-warning signal that the engine may need recalibration.
        """
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT f.confirmed
                FROM feedback f
                ORDER BY f.id DESC
                LIMIT ?
                """, (window,)
            ).fetchall()

        if not rows:
            return False
        confirmed = sum(1 for r in rows if r[0] == 1)
        return (confirmed / len(rows)) < threshold

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.executescript(self._DDL)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Open a connection, commit on success / roll back on error, and ALWAYS
        close it. The sqlite3 connection context manager only commits — it never
        closes — so using it alone leaks a connection (and file descriptors) on
        every call.
        """
        conn = self._connect()
        try:
            with conn:  # commit on success, rollback on exception
                yield conn
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @staticmethod
    def _row_to_record(row: tuple[Any, ...]) -> FeedbackRecord:
        (run_id, project, eng_v, eng_r, conf, issued,
         hv, confirmed_int, reviewer, reviewed_at, notes) = row
        confirmed = (bool(confirmed_int) if confirmed_int is not None else None)
        return FeedbackRecord(
            run_id=str(run_id),
            project=str(project),
            engine_verdict=str(eng_v),
            engine_risk=str(eng_r),
            confidence_score=float(conf) if conf is not None else None,
            human_verdict=str(hv) if hv else None,
            confirmed=confirmed,
            reviewer=str(reviewer or ""),
            issued_at=str(issued),
            reviewed_at=str(reviewed_at) if reviewed_at else None,
            notes=str(notes or ""),
        )
