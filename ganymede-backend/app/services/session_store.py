"""SQLite-backed persistence for Sessions (Pl2-01 — Z-SPAN-as-first-consumer prerequisite).

Z-SPAN, the first Pl2 consumer (per milestone 43), uses Ganymede as a
long-term strategic-planning module. Operators need to come back to
prior strategic sessions weeks later and see the history of strokes,
not start over each time. The in-memory ``SessionRegistry`` alone
doesn't survive a backend restart; this module sits beside it and
persists session state to a single SQLite file.

Design notes:

* **Stdlib only.** ``sqlite3`` ships with Python and the project already
  uses ``loop.run_in_executor`` to bridge sync I/O into the asyncio
  event loop. Session callers use ``asyncio.to_thread`` for these operations.
  ``aiosqlite`` would be one tiny dep but stdlib is fine.
* **Sync API; async bridging at call sites.** The store's methods are
  blocking SQLite calls. Session/SessionRegistry call them via
  ``asyncio.to_thread`` so the event loop stays responsive.
* **Idempotent ``save_session``.** Treats the in-memory Session as the
  source of truth and rewrites persisted state to match. Child rows
  (strokes / events / translations) are delete-and-insert to avoid
  divergence — N is small (≤ ~10 strokes, ≤ ~50 events per session)
  so the cost is negligible.
* **Incremental saves.** ``Session`` calls ``_persist`` on every state
  mutation (stroke recorded, translation recorded, terminal transition).
  A backend crash mid-Bicameral-loop leaves the last-recorded strokes
  on disk, not a blank slate.
* **Orphan rescue on startup.** Any session left in ``running`` status
  when the backend died is flipped to ``error`` with a "backend
  restarted during run" marker, and an ``ERROR`` event is appended to
  its timeline so the events endpoint stays consistent.

Schema is created lazily on construction via ``CREATE TABLE IF NOT EXISTS``,
so dropping the DB file is a clean reset.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id            TEXT PRIMARY KEY,
    scenario_json TEXT NOT NULL,
    pathway       TEXT NOT NULL,
    iterative     INTEGER NOT NULL,
    max_strokes   INTEGER NOT NULL,
    status        TEXT NOT NULL,
    error_message TEXT,
    created_at    TEXT NOT NULL,
    completed_at  TEXT,
    final_text    TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_pathway ON sessions(pathway);

CREATE TABLE IF NOT EXISTS strokes (
    session_id    TEXT NOT NULL,
    stroke_number INTEGER NOT NULL,
    stroke_json   TEXT NOT NULL,
    PRIMARY KEY (session_id, stroke_number),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    session_id  TEXT NOT NULL,
    event_idx   INTEGER NOT NULL,
    event_json  TEXT NOT NULL,
    PRIMARY KEY (session_id, event_idx),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS translations (
    session_id      TEXT NOT NULL,
    stroke_number   INTEGER NOT NULL,
    register        TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    PRIMARY KEY (session_id, stroke_number, register),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
"""


class SessionStore:
    """SQLite-backed persistence layer for Session state.

    Open one of these per backend process (the canonical instance lives
    on the module-global ``SessionRegistry``; ``app/main.py`` constructs
    it during startup). All public methods are sync — call sites in
    async code bridge via ``asyncio.to_thread``.

    Concurrency: each public method opens its own connection (via the
    ``_connect`` context manager) and SQLite's file-level locking
    serializes writes. Reads happen on separate connections and don't
    block writers.
    """

    def __init__(self, db_path: Path | str):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
        logger.info("SessionStore opened at %s", self.db_path)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ---- save ----

    def save_session(self, session: Any) -> None:
        """Upsert one Session's full state (sync; blocking SQLite).

        Treats the in-memory ``session`` as the source of truth. The
        session row is upserted; strokes / events / translations are
        delete-and-reinsert so they exactly mirror the in-memory state
        with no orphans.
        """
        scenario_json = session.scenario.model_dump_json()
        final_text = session.final.final_text if session.final else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions
                  (id, scenario_json, pathway, iterative, max_strokes,
                   status, error_message, created_at, completed_at, final_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  scenario_json = excluded.scenario_json,
                  pathway       = excluded.pathway,
                  iterative     = excluded.iterative,
                  max_strokes   = excluded.max_strokes,
                  status        = excluded.status,
                  error_message = excluded.error_message,
                  completed_at  = excluded.completed_at,
                  final_text    = excluded.final_text
                """,
                (
                    session.id,
                    scenario_json,
                    session.pathway.value,
                    int(session.iterative),
                    session.max_strokes,
                    session.status,
                    session.error_message,
                    session.created_at.isoformat(),
                    session.completed_at.isoformat() if session.completed_at else None,
                    final_text,
                ),
            )

            conn.execute("DELETE FROM strokes WHERE session_id = ?", (session.id,))
            for stroke in session.strokes:
                conn.execute(
                    "INSERT INTO strokes (session_id, stroke_number, stroke_json) "
                    "VALUES (?, ?, ?)",
                    (session.id, stroke.stroke_number, stroke.model_dump_json()),
                )

            conn.execute("DELETE FROM events WHERE session_id = ?", (session.id,))
            for idx, event in enumerate(session.events):
                conn.execute(
                    "INSERT INTO events (session_id, event_idx, event_json) "
                    "VALUES (?, ?, ?)",
                    (session.id, idx, event.model_dump_json()),
                )

            conn.execute("DELETE FROM translations WHERE session_id = ?", (session.id,))
            for key, text in session.translations.items():
                stroke_num_str, register = key.split(":", 1)
                conn.execute(
                    "INSERT INTO translations "
                    "(session_id, stroke_number, register, translated_text) "
                    "VALUES (?, ?, ?, ?)",
                    (session.id, int(stroke_num_str), register, text),
                )

    # ---- load (startup rehydration path) ----

    def load_all(self) -> list[dict[str, Any]]:
        """Return every persisted session as a dict ready for hydration.

        Each entry has the shape Session.from_persisted_state expects:
        ``{ id, scenario_json, pathway, iterative, max_strokes, status,
            error_message, created_at, completed_at, final_text,
            strokes: [...], events: [...], translations: {...} }``.
        """
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            session_rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at ASC"
            ).fetchall()
            stroke_rows = conn.execute(
                "SELECT session_id, stroke_json FROM strokes "
                "ORDER BY session_id, stroke_number"
            ).fetchall()
            event_rows = conn.execute(
                "SELECT session_id, event_json FROM events "
                "ORDER BY session_id, event_idx"
            ).fetchall()
            translation_rows = conn.execute(
                "SELECT session_id, stroke_number, register, translated_text "
                "FROM translations"
            ).fetchall()

        strokes_by_sid: dict[str, list[dict[str, Any]]] = {}
        for r in stroke_rows:
            strokes_by_sid.setdefault(r["session_id"], []).append(
                json.loads(r["stroke_json"])
            )

        events_by_sid: dict[str, list[dict[str, Any]]] = {}
        for r in event_rows:
            events_by_sid.setdefault(r["session_id"], []).append(
                json.loads(r["event_json"])
            )

        translations_by_sid: dict[str, dict[str, str]] = {}
        for r in translation_rows:
            key = f"{r['stroke_number']}:{r['register']}"
            translations_by_sid.setdefault(r["session_id"], {})[key] = r[
                "translated_text"
            ]

        out: list[dict[str, Any]] = []
        for srow in session_rows:
            sid = srow["id"]
            out.append(
                {
                    "id": sid,
                    "scenario_json": srow["scenario_json"],
                    "pathway": srow["pathway"],
                    "iterative": bool(srow["iterative"]),
                    "max_strokes": srow["max_strokes"],
                    "status": srow["status"],
                    "error_message": srow["error_message"],
                    "created_at": srow["created_at"],
                    "completed_at": srow["completed_at"],
                    "final_text": srow["final_text"],
                    "strokes": strokes_by_sid.get(sid, []),
                    "events": events_by_sid.get(sid, []),
                    "translations": translations_by_sid.get(sid, {}),
                }
            )
        return out

    def mark_orphan_running_as_error(self, message: str) -> list[str]:
        """Flip any session left in ``running`` to ``error``. Returns
        the list of session IDs that were rescued.

        Also appends a synthetic ERROR event to each rescued session's
        timeline so the events endpoint stays consistent — the operator
        looking at the session later sees an explicit terminal event,
        not just a status flip with no corresponding event in the list.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        rescued: list[str] = []
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            orphan_rows = conn.execute(
                "SELECT id FROM sessions WHERE status = 'running'"
            ).fetchall()
            if not orphan_rows:
                return []
            for r in orphan_rows:
                sid = r["id"]
                rescued.append(sid)
                conn.execute(
                    "UPDATE sessions SET status='error', error_message=?, "
                    "completed_at=? WHERE id=?",
                    (message, now_iso, sid),
                )
                next_idx_row = conn.execute(
                    "SELECT COALESCE(MAX(event_idx), -1) + 1 AS next_idx "
                    "FROM events WHERE session_id = ?",
                    (sid,),
                ).fetchone()
                next_idx = next_idx_row["next_idx"] if next_idx_row else 0
                synthetic_event = {
                    "type": "error",
                    "stroke_number": None,
                    "payload": {
                        "message": message,
                        "exc_type": "BackendRestartedDuringRun",
                    },
                    "emitted_at": now_iso,
                }
                conn.execute(
                    "INSERT INTO events (session_id, event_idx, event_json) "
                    "VALUES (?, ?, ?)",
                    (sid, next_idx, json.dumps(synthetic_event)),
                )
        if rescued:
            logger.warning(
                "SessionStore: marked %d orphan running session(s) as error: %s",
                len(rescued),
                ", ".join(rescued),
            )
        return rescued

    # ---- query (API surface backing for list / search) ----

    def list_summaries(
        self,
        status: Optional[str] = None,
        pathway: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Lightweight session list for the ``GET /api/v2/sessions``
        endpoint. Returns small dicts with one row per session — no
        strokes / events / translations loaded.
        """
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if pathway:
            clauses.append("pathway = ?")
            params.append(pathway)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = (
            "SELECT id, pathway, iterative, max_strokes, status, error_message, "
            "created_at, completed_at, scenario_json, final_text "
            f"FROM sessions {where} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def count(
        self,
        status: Optional[str] = None,
        pathway: Optional[str] = None,
    ) -> int:
        """Total matching rows for the given filters. Lets the list
        endpoint expose pagination totals without a second query at the
        call site."""
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if pathway:
            clauses.append("pathway = ?")
            params.append(pathway)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM sessions {where}", params
            ).fetchone()
        return int(row[0]) if row else 0

    def search(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Substring search over ``scenario_json`` and ``final_text``.

        Plain ``LIKE`` rather than FTS5 to keep schema simple. N is in
        the low hundreds for the foreseeable Z-SPAN workload; a table
        scan with LIKE is fine. Promote to FTS5 if the corpus grows.
        """
        like = f"%{query}%"
        sql = (
            "SELECT id, pathway, iterative, max_strokes, status, error_message, "
            "created_at, completed_at, scenario_json, final_text "
            "FROM sessions "
            "WHERE scenario_json LIKE ? "
            "   OR (final_text IS NOT NULL AND final_text LIKE ?) "
            "ORDER BY created_at DESC LIMIT ?"
        )
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, (like, like, limit)).fetchall()
        return [dict(r) for r in rows]

    def delete(self, session_id: str) -> bool:
        """Remove a session and all its child rows. Returns True if a
        row was deleted."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE id = ?", (session_id,)
            )
            return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Default DB-path resolution
# ---------------------------------------------------------------------------

def default_db_path() -> Path:
    """Canonical path for the production SessionStore DB.

    Resolves to ``ganymede-backend/data/sessions.db`` relative to this
    module. Override at construction time via the ``GANYMEDE_SESSION_DB``
    env var, read by ``app/main.py`` on startup.
    """
    here = Path(__file__).resolve().parent  # app/services/
    backend_root = here.parent.parent  # ganymede-backend/
    return backend_root / "data" / "sessions.db"
