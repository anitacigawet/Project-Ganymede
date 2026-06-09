'use client';

/**
 * BridgeNotebookManager — operator-facing UI for the P1-04 bridge-notebook
 * lifecycle decision (Option C, operator-managed with categorized
 * delete-suggestions).
 *
 * Fetches `GET /api/v2/bridge/notebooks` and renders each registered Bridge
 * notebook as a row with:
 *   - Title + truncated notebook ID
 *   - Created-at + age
 *   - Originating session ID + status (if known)
 *   - Suggested-category badge (color-coded: rose=likely_safe_to_delete,
 *     amber=review, emerald=recently_used)
 *   - One-line reason for the suggestion
 *   - Delete button (two-click confirm to avoid accidental deletes)
 *
 * Delete fires `DELETE /api/v2/notebooks/{id}` against the existing
 * notebook-management endpoint; on success, the row drops from the
 * refetched survey. The HTTP handler also deregisters from the
 * bridge_registry so the next survey reflects the change.
 *
 * Self-contained: no required props, fetches its own data, manages its
 * own state. Drop in wherever the operator wants the management UI.
 */

import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, RefreshCw, Trash2, X } from 'lucide-react';

const DEFAULT_BACKEND =
  process.env.NEXT_PUBLIC_GANYMEDE_BASE_URL ?? 'http://127.0.0.1:8000';

interface BridgeNotebookRow {
  notebook_id: string;
  title: string;
  created_at: string;
  age_hours: number;
  session_id: string | null;
  session_status: string | null;
  provision_path: string;
  foundations_uploaded: number;
  truth_packets_uploaded: number;
  suggested_action: 'delete' | 'review' | 'keep';
  suggested_category: 'likely_safe_to_delete' | 'review' | 'recently_used';
  reason: string;
}

interface SurveyResponse {
  notebooks: BridgeNotebookRow[];
  total: number;
  safe_to_delete: number;
  needs_review: number;
  keep: number;
}

function formatAge(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}

function categoryTint(category: BridgeNotebookRow['suggested_category']): {
  badge: string;
  text: string;
  label: string;
} {
  switch (category) {
    case 'likely_safe_to_delete':
      return {
        badge: 'border-rose-700/40 bg-rose-950/40',
        text: 'text-rose-200',
        label: 'Likely safe to delete',
      };
    case 'review':
      return {
        badge: 'border-amber-700/40 bg-amber-950/40',
        text: 'text-amber-200',
        label: 'Review before deciding',
      };
    case 'recently_used':
      return {
        badge: 'border-emerald-700/40 bg-emerald-950/40',
        text: 'text-emerald-200',
        label: 'Recently used — keep',
      };
  }
}

function provisionPathLabel(path: string): string {
  switch (path) {
    case 'iterate_level_1':
      return 'Level 1 /iterate';
    case 'bicameral_loop_level_2':
      return 'Level 2 bicameral loop';
    case 'standalone_provision':
      return 'Standalone /bridge/provision';
    default:
      return path;
  }
}

export function BridgeNotebookManager() {
  const [survey, setSurvey] = useState<SurveyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [primedForDelete, setPrimedForDelete] = useState<string | null>(null);
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${DEFAULT_BACKEND}/api/v2/bridge/notebooks`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      }
      const data = (await res.json()) as SurveyResponse;
      setSurvey(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleDeleteClick = useCallback(
    async (notebookId: string) => {
      // Two-click confirm — first click primes the button; second within
      // 4s fires the delete. Avoids accidental deletions of notebooks
      // the operator may want to keep.
      if (primedForDelete !== notebookId) {
        setPrimedForDelete(notebookId);
        window.setTimeout(() => {
          setPrimedForDelete((cur) => (cur === notebookId ? null : cur));
        }, 4000);
        return;
      }

      setPrimedForDelete(null);
      setDeletingIds((prev) => new Set(prev).add(notebookId));
      try {
        const res = await fetch(
          `${DEFAULT_BACKEND}/api/v2/notebooks/${notebookId}`,
          { method: 'DELETE' },
        );
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${await res.text()}`);
        }
        // Refetch to reflect the deregistration on the survey.
        await refresh();
      } catch (err) {
        setError(
          `Delete failed for ${notebookId}: ${err instanceof Error ? err.message : String(err)}`,
        );
      } finally {
        setDeletingIds((prev) => {
          const next = new Set(prev);
          next.delete(notebookId);
          return next;
        });
      }
    },
    [primedForDelete, refresh],
  );

  if (loading && survey === null) {
    return (
      <div className="space-y-4 p-6">
        <div className="text-sm text-slate-400">Loading bridge notebooks…</div>
      </div>
    );
  }

  if (error && survey === null) {
    return (
      <div className="space-y-4 p-6">
        <div className="flex items-start gap-3 rounded-md border border-rose-700/40 bg-rose-950/40 p-3 text-sm">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-300" />
          <div className="flex-1">
            <div className="font-medium text-rose-200">
              Failed to load bridge notebooks
            </div>
            <div className="mt-0.5 text-xs text-rose-300/80">{error}</div>
          </div>
          <button
            type="button"
            onClick={refresh}
            className="rounded border border-rose-700/40 bg-rose-900/40 px-2.5 py-1.5 text-xs text-rose-200 hover:bg-rose-900/50"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const notebooks = survey?.notebooks ?? [];

  return (
    <div className="space-y-4 p-6">
      {/* Header + summary counts + refresh */}
      <div className="flex items-baseline justify-between gap-3">
        <div>
          <h1 className="text-lg font-medium text-slate-100">
            Bridge Notebooks
          </h1>
          <p className="mt-0.5 text-xs text-slate-400">
            Auto-provisioned Bridge notebooks from the orchestrator. Suggestions
            are advisory — you make the final call on each row.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded border border-slate-700/50 bg-slate-900/60 px-2.5 py-1.5 text-xs text-slate-200 hover:bg-slate-800/70 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {survey && (
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="rounded border border-slate-700/50 bg-slate-900/60 px-2 py-0.5 text-slate-300">
            Total: {survey.total}
          </span>
          {survey.safe_to_delete > 0 && (
            <span className="rounded border border-rose-700/40 bg-rose-950/40 px-2 py-0.5 text-rose-200">
              {survey.safe_to_delete} likely safe to delete
            </span>
          )}
          {survey.needs_review > 0 && (
            <span className="rounded border border-amber-700/40 bg-amber-950/40 px-2 py-0.5 text-amber-200">
              {survey.needs_review} need review
            </span>
          )}
          {survey.keep > 0 && (
            <span className="rounded border border-emerald-700/40 bg-emerald-950/40 px-2 py-0.5 text-emerald-200">
              {survey.keep} recently used
            </span>
          )}
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-md border border-rose-700/40 bg-rose-950/40 p-3 text-sm">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-300" />
          <div className="flex-1 text-rose-200">{error}</div>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-rose-300 hover:text-rose-100"
            aria-label="Dismiss error"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {notebooks.length === 0 ? (
        <div className="flex items-start gap-3 rounded-md border border-slate-700/50 bg-slate-900/60 p-4 text-sm">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-300" />
          <div>
            <div className="font-medium text-slate-200">No Bridge notebooks tracked</div>
            <div className="mt-0.5 text-xs text-slate-400">
              The registry is empty — no auto-provisioned Bridge notebooks
              this backend session. Operator-curated notebooks (created
              outside the orchestrator) aren&apos;t tracked here and need to be
              managed via raw API calls.
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {notebooks.map((nb) => {
            const tint = categoryTint(nb.suggested_category);
            const isPrimed = primedForDelete === nb.notebook_id;
            const isDeleting = deletingIds.has(nb.notebook_id);
            return (
              <div
                key={nb.notebook_id}
                className="rounded-md border border-slate-700/50 bg-slate-900/60 p-3 text-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <span className="font-medium text-slate-100">
                        {nb.title}
                      </span>
                      <span
                        className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${tint.badge} ${tint.text}`}
                      >
                        {tint.label}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-slate-400 font-mono break-all">
                      {nb.notebook_id}
                    </div>
                    <div className="mt-1.5 text-xs text-slate-300">{nb.reason}</div>
                    <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-500">
                      <span>Age: {formatAge(nb.age_hours)}</span>
                      <span>·</span>
                      <span>Path: {provisionPathLabel(nb.provision_path)}</span>
                      {nb.session_id && (
                        <>
                          <span>·</span>
                          <span>
                            Session: <span className="font-mono">{nb.session_id.slice(0, 8)}</span>
                            {nb.session_status && (
                              <span className="ml-1 text-slate-400">
                                ({nb.session_status})
                              </span>
                            )}
                          </span>
                        </>
                      )}
                      <span>·</span>
                      <span>
                        {nb.foundations_uploaded} foundations + {nb.truth_packets_uploaded} truth packets
                      </span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteClick(nb.notebook_id)}
                    disabled={isDeleting}
                    className={`shrink-0 inline-flex items-center gap-1.5 rounded px-2.5 py-1.5 text-xs font-medium transition ${
                      isPrimed
                        ? 'border border-rose-500/60 bg-rose-800/70 text-rose-50 hover:bg-rose-800/90'
                        : 'border border-rose-700/40 bg-rose-950/40 text-rose-200 hover:bg-rose-900/50'
                    } disabled:opacity-50`}
                    aria-label={`Delete notebook ${nb.notebook_id}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    {isDeleting ? 'Deleting…' : isPrimed ? 'Click to confirm' : 'Delete'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="rounded-md border border-slate-700/50 bg-slate-900/40 p-3 text-xs text-slate-400">
        <div className="font-medium text-slate-300 mb-1">How suggestions work</div>
        <ul className="list-disc list-inside space-y-0.5">
          <li><span className="text-rose-300">Likely safe to delete</span>: session terminal &gt;2h ago, or orphaned + &gt;48h old</li>
          <li><span className="text-amber-300">Review</span>: session recently finished, or orphaned with unclear status</li>
          <li><span className="text-emerald-300">Recently used</span>: originating session still running</li>
        </ul>
        <div className="mt-2 text-slate-500">
          The registry is in-memory and clears on backend restart. The
          actual notebooks persist in NotebookLM either way; this UI shows
          what was provisioned during the current backend session.
        </div>
      </div>
    </div>
  );
}
