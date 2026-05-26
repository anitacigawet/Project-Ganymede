'use client';

/**
 * AuthPill — NotebookLM session-cookie health indicator.
 *
 * Floats in the top-right of the layout. Polls /api/v2/auth/status every 30s
 * (well inside the backend's 300s cache TTL) and shows a colored dot:
 *
 *   green   — cookies are valid
 *   amber   — status unknown / probe error
 *   red     — cookies expired or missing (NotebookLM calls will fail)
 *
 * Clicking the pill opens a dropdown with the relogin flow:
 *   1. Click "Sign in" — backend spawns `python -m notebooklm login`, which
 *      opens a Google OAuth tab in the user's default browser.
 *   2. User completes the sign-in in that tab.
 *   3. Back in the pill, user clicks "I'm finished" — backend feeds ENTER
 *      to the subprocess so it saves cookies, then exits.
 *   4. Status auto-refreshes.
 *
 * The pill is purely informational + manual-action. It never auto-refreshes
 * cookies, never opens browser tabs on its own, never blocks user navigation.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ShieldCheck, ShieldAlert, ShieldQuestion, Loader2, X } from 'lucide-react';

type AuthStatus = {
  status: 'valid' | 'expired' | 'missing' | 'unknown';
  details?: string | null;
  checked_at?: string | null;
  cached?: boolean;
  cache_age_seconds?: number | null;
  /** Whether the backend's notebooklm_svc.client is alive. Drift from
   *  ``status`` (cookies valid but service dead) triggers auto-reinit. */
  client_initialized?: boolean;
};

type ReinitializeResult = {
  reinitialized: boolean;
  client_initialized: boolean;
  details?: string | null;
  error?: string | null;
};

type ReloginSpawn = {
  spawned: boolean;
  cmd?: string | null;
  pid?: number | null;
  note?: string | null;
  error?: string | null;
};

type ReloginConfirm = {
  confirmed: boolean;
  exit_code?: number | null;
  output?: string | null;
  note?: string | null;
  error?: string | null;
};

const BACKEND_URL =
  process.env.NEXT_PUBLIC_GANYMEDE_BASE_URL ?? 'http://127.0.0.1:8000';

const POLL_INTERVAL_MS = 30_000;

async function fetchStatus(force = false): Promise<AuthStatus> {
  const url = `${BACKEND_URL}/api/v2/auth/status${force ? '?force=true' : ''}`;
  const r = await fetch(url, { cache: 'no-store' });
  if (!r.ok) {
    return { status: 'unknown', details: `HTTP ${r.status}` };
  }
  return r.json();
}

async function postRelogin(): Promise<ReloginSpawn> {
  const r = await fetch(`${BACKEND_URL}/api/v2/auth/relogin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  return r.json();
}

async function postConfirmRelogin(timeoutSeconds = 30): Promise<ReloginConfirm> {
  const r = await fetch(`${BACKEND_URL}/api/v2/auth/relogin/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ timeout_seconds: timeoutSeconds }),
  });
  return r.json();
}

async function postReinitialize(): Promise<ReinitializeResult> {
  const r = await fetch(`${BACKEND_URL}/api/v2/auth/reinitialize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  return r.json();
}

function StatusIcon({ status, busy }: { status: AuthStatus['status']; busy?: boolean }) {
  if (busy) {
    return <Loader2 className="w-4 h-4 animate-spin text-slate-300" />;
  }
  if (status === 'valid') {
    return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
  }
  if (status === 'expired' || status === 'missing') {
    return <ShieldAlert className="w-4 h-4 text-rose-400" />;
  }
  return <ShieldQuestion className="w-4 h-4 text-amber-400" />;
}

function statusLabel(s: AuthStatus['status']): string {
  switch (s) {
    case 'valid':
      return 'Auth OK';
    case 'expired':
      return 'Sign in';
    case 'missing':
      return 'Sign in';
    default:
      return 'Checking';
  }
}

function dotColor(s: AuthStatus['status']): string {
  switch (s) {
    case 'valid':
      return 'bg-emerald-400';
    case 'expired':
    case 'missing':
      return 'bg-rose-400';
    default:
      return 'bg-amber-400';
  }
}

export function AuthPill() {
  const [status, setStatus] = useState<AuthStatus>({ status: 'unknown' });
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  // Relogin flow state — null when no flow in progress; 'awaiting' when subprocess
  // has been spawned and we're waiting for the user to confirm; 'confirming' while
  // the confirm POST is in flight; null again on success/failure.
  const [reloginPhase, setReloginPhase] = useState<
    null | 'awaiting' | 'confirming'
  >(null);
  const [flowMessage, setFlowMessage] = useState<string | null>(null);
  // Persistent banner shown whenever a fetch to the backend throws.  Distinct
  // from flowMessage so a reachability problem can outlive an info message.
  // Cleared by the next successful status refresh.
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Background poll
  const timerRef = useRef<number | null>(null);
  // Tracks whether we've already fired auto-reinit for the current valid-but-
  // dead-svc state, so polling doesn't fire it on every tick.
  const autoReinitFiredRef = useRef<boolean>(false);

  const refresh = useCallback(async (force = false) => {
    setBusy(true);
    try {
      const s = await fetchStatus(force);
      setStatus(s);
      setFetchError(null); // backend reachable — clear any prior banner
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'unknown error';
      setStatus({ status: 'unknown', details: `fetch failed: ${msg}` });
      setFetchError(
        `Cannot reach backend at ${BACKEND_URL}. Is uvicorn running? (${msg})`,
      );
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    refresh(false);
    const id = window.setInterval(() => {
      void refresh(false);
    }, POLL_INTERVAL_MS);
    timerRef.current = id;
    return () => {
      if (timerRef.current !== null) {
        window.clearInterval(timerRef.current);
      }
    };
  }, [refresh]);

  // Reinitialize the backend's notebooklm_svc. Fired manually from the
  // dropdown button, or automatically when the pill detects status=valid
  // alongside client_initialized=false (cookies on disk are fresh but the
  // in-process service object is still the failed-startup one).
  const handleReinit = useCallback(async (silent = false) => {
    if (!silent) {
      setBusy(true);
      setFlowMessage('Reinitialising backend…');
    }
    try {
      const result = await postReinitialize();
      if (result.reinitialized) {
        autoReinitFiredRef.current = true;
        if (!silent) {
          setFlowMessage('Backend reinitialised. Refreshing status…');
        }
        await refresh(true);
        if (!silent) {
          window.setTimeout(() => setFlowMessage(null), 1500);
        }
      } else {
        const msg = result.error || 'reinit failed';
        setFlowMessage(`Reinit failed: ${msg}`);
        autoReinitFiredRef.current = false; // let the next valid-status tick retry
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'unknown error';
      setFlowMessage(`Reinit request failed: ${msg}`);
      autoReinitFiredRef.current = false;
    } finally {
      if (!silent) setBusy(false);
    }
  }, [refresh]);

  // Auto-fire reinit when the backend says cookies are valid but its
  // notebooklm_svc.client is None. Common after a terminal-side
  // `python -m notebooklm login` with the backend still running. The ref
  // guard prevents the poll loop from firing it on every 30s tick.
  useEffect(() => {
    if (
      status.status === 'valid' &&
      status.client_initialized === false &&
      !autoReinitFiredRef.current &&
      !busy
    ) {
      void handleReinit(true);
    }
    if (status.client_initialized === true) {
      autoReinitFiredRef.current = false;
    }
  }, [status.status, status.client_initialized, busy, handleReinit]);

  const handleStartSignIn = async () => {
    setBusy(true);
    setFlowMessage(null);
    try {
      const spawn = await postRelogin();
      if (!spawn.spawned) {
        setFlowMessage(`Failed to start sign-in: ${spawn.error ?? 'unknown error'}`);
        return;
      }
      setFetchError(null); // request landed — clear stale unreachable banner
      setReloginPhase('awaiting');
      setFlowMessage(
        spawn.note ??
          'Browser opening. Complete Google sign-in, then click "I’m finished".',
      );
    } catch (e: unknown) {
      // Previously this fell through silently as an unhandledRejection so the
      // user saw the click do nothing.  Surface the failure inline instead.
      const msg = e instanceof Error ? e.message : 'unknown error';
      setFetchError(
        `Sign-in request failed: ${msg}. Backend not reachable at ${BACKEND_URL}?`,
      );
    } finally {
      setBusy(false);
    }
  };

  const handleConfirmSignIn = async () => {
    setReloginPhase('confirming');
    setBusy(true);
    setFlowMessage('Saving cookies…');
    try {
      const confirm = await postConfirmRelogin(60);
      if (confirm.confirmed) {
        setFlowMessage('Cookies saved. Refreshing status…');
        // Force-refresh so the new cookies are probed immediately.
        await refresh(true);
        setReloginPhase(null);
        setFlowMessage(null);
      } else {
        setFlowMessage(
          confirm.error ??
            `Sign-in confirm failed (exit_code=${confirm.exit_code ?? 'n/a'}). Try again.`,
        );
        setReloginPhase('awaiting');
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'unknown error';
      setFlowMessage(`Confirm request failed: ${msg}`);
      setReloginPhase('awaiting');
    } finally {
      setBusy(false);
    }
  };

  const lastChecked = status.checked_at
    ? new Date(status.checked_at).toLocaleTimeString()
    : '—';

  return (
    // Pinned bottom-left so it sits next to the Next.js dev-mode "N" badge.
    // The dropdown opens UPWARD (absolute bottom-full) because the pill is
    // near the bottom edge — a default downward-opening dropdown would clip.
    <div className="fixed bottom-4 left-14 z-50 select-none font-mono text-xs">
      {/* Pill */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={[
          'flex items-center gap-2 px-3 py-1.5 rounded-full',
          'bg-slate-900/80 hover:bg-slate-800 backdrop-blur-xl',
          'border border-slate-700/60 shadow-lg',
          'text-slate-200 transition-colors',
        ].join(' ')}
        title={`NotebookLM auth: ${status.status}`}
      >
        <StatusIcon status={status.status} busy={busy && !open} />
        <span>{statusLabel(status.status)}</span>
        <span
          className={[
            'inline-block w-1.5 h-1.5 rounded-full',
            dotColor(status.status),
          ].join(' ')}
        />
      </button>

      {/* Dropdown panel — anchored to the pill's top so it floats above. */}
      {open && (
        <div
          className={[
            'absolute bottom-full left-0 mb-2 w-80 p-4 rounded-xl',
            'bg-slate-900/95 backdrop-blur-xl',
            'border border-slate-700/60 shadow-2xl',
            'text-slate-300',
          ].join(' ')}
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <div className="text-sm font-semibold text-slate-100">
                NotebookLM session
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                Last checked: {lastChecked}
                {status.cached
                  ? ` (cached ${Math.round(status.cache_age_seconds ?? 0)}s)`
                  : ' (fresh)'}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-slate-500 hover:text-slate-300"
              aria-label="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Reachability banner — fetchError is set whenever any backend
              call from this component throws (status poll, relogin, confirm,
              reinit).  Persistent across re-renders until the next successful
              status refresh clears it. */}
          {fetchError && (
            <div className="mb-3 p-2 rounded-md bg-rose-950/50 border border-rose-500/50 text-rose-200 text-[10px] leading-relaxed">
              <div className="font-semibold uppercase tracking-widest text-rose-300 mb-1">
                Backend unreachable
              </div>
              <div>{fetchError}</div>
            </div>
          )}

          <div className="space-y-1.5 mb-3 text-[11px]">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Cookies</span>
              <span className="font-medium text-slate-100">{status.status}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Backend client</span>
              <span
                className={[
                  'font-medium',
                  status.client_initialized === false
                    ? 'text-amber-300'
                    : 'text-slate-100',
                ].join(' ')}
              >
                {status.client_initialized === false ? 'not initialised' : 'ready'}
              </span>
            </div>
            {status.details && (
              <div className="text-slate-400 text-[10px] leading-relaxed">
                {status.details}
              </div>
            )}
            {status.status === 'valid' && status.client_initialized === false && (
              <div className="text-amber-300 text-[10px] leading-relaxed border-t border-amber-500/20 pt-1.5">
                Cookies are valid but the backend service is still on its
                pre-login state. Auto-reinit firing — or click below.
              </div>
            )}
          </div>

          {/* Re-auth flow */}
          {reloginPhase === null && (
            <div className="space-y-1.5">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => void refresh(true)}
                  disabled={busy}
                  className="flex-1 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-[11px]"
                >
                  Re-check now
                </button>
                <button
                  type="button"
                  onClick={handleStartSignIn}
                  disabled={busy}
                  className="flex-1 px-3 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-[11px]"
                >
                  Sign in
                </button>
              </div>
              <button
                type="button"
                onClick={() => void handleReinit(false)}
                disabled={busy}
                className="w-full px-3 py-1.5 rounded-md bg-slate-800/60 hover:bg-amber-600/20 hover:text-amber-200 border border-slate-700 disabled:opacity-50 text-slate-300 text-[11px]"
                title="Close + re-initialise the backend's NotebookLMService. Use after a terminal-side `python -m notebooklm login`."
              >
                Reinit backend
              </button>
            </div>
          )}

          {reloginPhase === 'awaiting' && (
            <div className="space-y-2">
              <p className="text-[11px] text-slate-300 leading-relaxed">
                A browser tab should open for Google sign-in.
                Complete the sign-in there, then click below to save cookies.
              </p>
              <button
                type="button"
                onClick={handleConfirmSignIn}
                disabled={busy}
                className="w-full px-3 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-[11px] font-medium"
              >
                I’m finished — save cookies
              </button>
            </div>
          )}

          {reloginPhase === 'confirming' && (
            <div className="text-[11px] text-slate-400 flex items-center gap-2">
              <Loader2 className="w-3 h-3 animate-spin" /> Saving cookies…
            </div>
          )}

          {flowMessage && (
            <div className="mt-3 text-[10px] text-slate-400 leading-relaxed border-t border-slate-800 pt-2">
              {flowMessage}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
