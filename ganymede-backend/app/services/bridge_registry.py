"""Server-side registry of auto-provisioned Bridge notebooks (P1-04).

NotebookLM's SDK does not expose a "list notebooks" API surface, so to
support the operator-facing Bridge-notebook management UX (per the P1-04
decision: Option C — operator-managed with categorized delete-suggestions)
we track auto-provisioned Bridge notebooks server-side as they're created.

The registry exists to answer: *what Bridge notebooks did we create, when,
for which sessions, and which ones are likely safe to delete now?* It
does NOT track operator-curated notebooks (named manually outside the
orchestrator's auto-provision path) — those aren't in the registry and
remain operator-managed via the bare ``DELETE /api/v2/notebooks/{id}``
endpoint.

Persistence: in-memory for v1. Survives within a backend process but
clears on restart. Follow-up: file-backed persistence so the registry
survives across backend restarts (the actual notebooks still exist in
NotebookLM either way; the registry just loses the metadata).

Lifecycle:
- Orchestrator auto-provisions a Bridge notebook → calls ``register``.
- Operator hits ``GET /api/v2/bridge/notebooks`` to see the survey →
  ``list_with_suggestions`` returns the table.
- Operator hits ``DELETE /api/v2/notebooks/{id}`` to remove a notebook
  → ``deregister`` removes the registry entry. The HTTP delete endpoint
  is responsible for invoking this hook.

Decision per operator (2026-06-06): all notebook-delete actions go through
the operator (no auto-cleanup). The registry's job is to SUGGEST which
ones look safe to delete; the operator makes the call.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class BridgeNotebookEntry:
    """Metadata about one auto-provisioned Bridge notebook.

    Stored in the registry from the moment the orchestrator finishes
    provisioning until ``deregister`` is called (typically by the
    HTTP ``DELETE /api/v2/notebooks/{id}`` handler).
    """
    notebook_id: str
    title: str
    """The title used at provision time. Auto-provision titles follow
    canonical patterns: ``"Bridge — {session_id[:8]} iterate"`` for Level 1,
    ``"Bicameral Loop — {session_id[:8]}"`` for Level 2. The standalone
    ``POST /api/v2/bridge/provision`` endpoint uses caller-supplied titles."""
    created_at: datetime
    session_id: Optional[str]
    """The session this notebook was created FOR. None for the standalone
    ``/bridge/provision`` path (which produces a notebook ID for the caller
    to use later — no specific session is associated)."""
    provision_path: str
    """Which code path provisioned this notebook:
        ``"iterate_level_1"`` — auto-provisioned inside ``run_iterative_engine``.
        ``"bicameral_loop_level_2"`` — auto-provisioned inside ``run_bicameral_loop``.
        ``"standalone_provision"`` — created via ``POST /api/v2/bridge/provision``.
    """
    foundations_uploaded: int = 0
    truth_packets_uploaded: int = 0


@dataclass
class BridgeNotebookSurveyRow:
    """One row in the operator-facing survey. Includes the entry's
    metadata plus a categorization suggestion the UI can render with
    color-coded badges + reasoning the operator can read before deciding
    to click delete."""
    notebook_id: str
    title: str
    created_at: datetime
    age_hours: float
    """Hours since creation, for display + categorization heuristic."""
    session_id: Optional[str]
    session_status: Optional[str]
    """Current status of the originating session if it's still in the
    SessionRegistry (``running`` / ``complete`` / ``error`` / ``cancelled``).
    None when the session is gone or wasn't tracked (standalone path).
    The suggestion logic uses this — a terminal session status strengthens
    the case for delete."""
    provision_path: str
    foundations_uploaded: int
    truth_packets_uploaded: int
    suggested_action: str
    """One of ``"delete"`` / ``"review"`` / ``"keep"``. The operator
    makes the final call; this is advisory only."""
    suggested_category: str
    """One of ``"likely_safe_to_delete"`` / ``"review"`` / ``"recently_used"``.
    UI renders with a color-coded badge."""
    reason: str
    """Human-readable one-line explanation of why this row got its
    suggested_action. Surfaces directly in the UI so the operator sees
    the reasoning rather than just the label."""


class BridgeNotebookRegistry:
    """Thread-safe in-memory registry of auto-provisioned Bridge notebooks.

    Single instance per backend process (module-global below). Tests that
    need an isolated registry should instantiate this directly.
    """

    def __init__(self):
        self._entries: dict[str, BridgeNotebookEntry] = {}
        self._lock = threading.Lock()

    def register(
        self,
        notebook_id: str,
        title: str,
        session_id: Optional[str],
        provision_path: str,
        foundations_uploaded: int = 0,
        truth_packets_uploaded: int = 0,
    ) -> None:
        """Record a newly-provisioned Bridge notebook in the registry."""
        with self._lock:
            self._entries[notebook_id] = BridgeNotebookEntry(
                notebook_id=notebook_id,
                title=title,
                created_at=datetime.now(timezone.utc),
                session_id=session_id,
                provision_path=provision_path,
                foundations_uploaded=foundations_uploaded,
                truth_packets_uploaded=truth_packets_uploaded,
            )
            logger.info(
                "BridgeNotebookRegistry: registered %s (%s, session=%s, path=%s)",
                notebook_id, title, session_id, provision_path,
            )

    def deregister(self, notebook_id: str) -> bool:
        """Remove a Bridge notebook from the registry (e.g. after the
        operator deleted it via the HTTP DELETE endpoint). Returns True
        if the entry was present; False if it was already absent.
        Idempotent — safe to call from the DELETE handler unconditionally.
        """
        with self._lock:
            entry = self._entries.pop(notebook_id, None)
            if entry is not None:
                logger.info(
                    "BridgeNotebookRegistry: deregistered %s (%s)",
                    notebook_id, entry.title,
                )
            return entry is not None

    def list_all(self) -> list[BridgeNotebookEntry]:
        """Snapshot of all registered Bridge notebooks (chronological by
        creation time, oldest first)."""
        with self._lock:
            entries = list(self._entries.values())
        return sorted(entries, key=lambda e: e.created_at)

    def list_with_suggestions(
        self,
        session_status_lookup: dict[str, str],
    ) -> list[BridgeNotebookSurveyRow]:
        """Survey list with per-row categorization suggestion.

        ``session_status_lookup`` maps session_id → current status (the
        v2_routes endpoint builds this from the SessionRegistry).
        Sessions absent from the lookup are treated as "session gone"
        (process restart, manual discard) which doesn't strengthen the
        delete case on its own — the operator may still want to keep the
        notebook for substrate reuse.

        Suggestion logic (priority order — first match wins):
          1. Session terminal (complete/cancelled/error) AND notebook
             >2 hours old → likely_safe_to_delete + delete.
          2. Session terminal AND notebook ≤2 hours old → review +
             review (recently-used, operator may re-audit).
          3. Session running → recently_used + keep (active session
             may still use this notebook).
          4. Session unknown AND notebook >48 hours old →
             likely_safe_to_delete + delete (old + orphaned).
          5. Session unknown AND notebook ≤48 hours old → review +
             review.
        """
        now = datetime.now(timezone.utc)
        rows = []
        for entry in self.list_all():
            age_seconds = (now - entry.created_at).total_seconds()
            age_hours = age_seconds / 3600.0
            session_status = (
                session_status_lookup.get(entry.session_id)
                if entry.session_id
                else None
            )

            # Categorization heuristic
            terminal_statuses = {"complete", "cancelled", "error"}
            if session_status in terminal_statuses:
                if age_hours > 2.0:
                    category = "likely_safe_to_delete"
                    action = "delete"
                    reason = (
                        f"Session {session_status} {age_hours:.1f}h ago — "
                        f"notebook unlikely to be re-audited"
                    )
                else:
                    category = "review"
                    action = "review"
                    reason = (
                        f"Session {session_status} recently — operator may "
                        f"still re-audit before deleting"
                    )
            elif session_status == "running":
                category = "recently_used"
                action = "keep"
                reason = "Session still running — notebook may be in use"
            elif session_status is None:
                if age_hours > 48.0:
                    category = "likely_safe_to_delete"
                    action = "delete"
                    reason = (
                        f"Orphaned (session gone) and >48h old — "
                        f"safe to clean up"
                    )
                else:
                    category = "review"
                    action = "review"
                    reason = (
                        f"Session gone (process restart?) and {age_hours:.1f}h old — "
                        f"operator should confirm before deleting"
                    )
            else:
                # Unknown status string — be safe, suggest review
                category = "review"
                action = "review"
                reason = f"Unknown session status '{session_status}' — review"

            rows.append(BridgeNotebookSurveyRow(
                notebook_id=entry.notebook_id,
                title=entry.title,
                created_at=entry.created_at,
                age_hours=age_hours,
                session_id=entry.session_id,
                session_status=session_status,
                provision_path=entry.provision_path,
                foundations_uploaded=entry.foundations_uploaded,
                truth_packets_uploaded=entry.truth_packets_uploaded,
                suggested_action=action,
                suggested_category=category,
                reason=reason,
            ))
        return rows

    def count(self) -> int:
        """Snapshot count of registered notebooks. For ops/tests."""
        with self._lock:
            return len(self._entries)


# Module-global registry. Single instance per process — same pattern as
# the cooldown gate and the session registry. Tests that need isolation
# should instantiate ``BridgeNotebookRegistry()`` directly.
_REGISTRY = BridgeNotebookRegistry()


def registry() -> BridgeNotebookRegistry:
    """Accessor for the module-global Bridge notebook registry."""
    return _REGISTRY
