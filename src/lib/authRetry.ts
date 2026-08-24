/**
 * Mid-session NotebookLM auth self-heal.
 *
 * NotebookLM session cookies live ~2-5 hours, then expire. When they die
 * mid-session, the SDK's pre-flight `get_source_ids` RPC (rpcid `rLM1Ne`)
 * returns a null body and the backend surfaces it as an HTTP 500 whose detail
 * carries the RPCError text. The backend only auto-recovers auth on startup,
 * so an expired-cookie call just 500s. This helper lets a call site fire the
 * one-shot `/auth/auto-relogin` (which auto-completes when the Playwright
 * profile is still signed in — the steady state) and retry once, so the
 * operator sees a brief "re-authenticating…" instead of a raw error.
 *
 * NOTE: this is a stopgap for the NotebookLM substrate. The Substrate
 * Migration (Lens/Engine on Sonnet) removes cookies entirely and makes this
 * whole failure class disappear.
 */

/**
 * True when an HTTP failure is the expired-cookie null-result signature —
 * NOT the input-cap empty rejection and NOT an ordinary error. Only this
 * shape is worth an auto-relogin; anything else should surface as-is.
 *
 * The backend detail for this failure is exactly:
 *   "RPC rLM1Ne returned null result data (possible server error ...)"
 * so we require BOTH the obfuscated method id AND the "null result data"
 * phrase. Matching either alone is too broad — an unrelated rLM1Ne failure,
 * or some other RPC's "null result data", would wrongly trigger a relogin.
 */
export function isNotebookAuthDropError(status: number, body: string): boolean {
  if (status !== 500) return false;
  return /rLM1Ne/i.test(body) && /null result data/i.test(body);
}

// Shared in-flight relogin so concurrent failing calls don't each spawn an
// overlapping `notebooklm login` / Playwright recovery. The first caller
// starts the relogin; everyone else awaits the same promise; the slot clears
// once it settles so a later expiry can trigger a fresh attempt.
let _inFlightRelogin: Promise<boolean> | null = null;

/**
 * POST `/auth/auto-relogin` and resolve `true` only if the session was
 * actually restored (confirmed + client re-initialised). Never throws — a
 * `false` result means the caller should surface the original error and point
 * the operator at the AuthPill manual flow. Deduplicated across concurrent
 * callers via the shared in-flight promise above.
 */
export function tryAutoRelogin(backend: string): Promise<boolean> {
  if (_inFlightRelogin) return _inFlightRelogin;
  _inFlightRelogin = (async () => {
    try {
      const r = await fetch(`${backend}/api/v2/auth/auto-relogin`, {
        method: 'POST',
      });
      if (!r.ok) return false;
      const d = (await r.json()) as {
        confirmed?: boolean;
        client_initialized?: boolean;
      };
      return Boolean(d?.confirmed && d?.client_initialized);
    } catch {
      return false;
    } finally {
      _inFlightRelogin = null;
    }
  })();
  return _inFlightRelogin;
}

/**
 * Run `doFetch`; if it fails with the expired-cookie signature, auto-relogin
 * once and retry. `onReauth(true)` fires when a re-auth attempt starts,
 * `onReauth(false)` when it settles — call sites use it to show a transient
 * "re-authenticating…" notice. Returns the `Response` (ok or not) for the
 * caller to handle; on a retry the retried response is returned.
 */
export async function fetchWithAuthRetry(
  backend: string,
  doFetch: () => Promise<Response>,
  onReauth?: (active: boolean) => void,
): Promise<Response> {
  const res = await doFetch();
  if (res.ok) return res;

  // Peek the body to classify. Clone so the caller can still read it if we
  // decide not to retry. If the peek itself fails (locked/disturbed body,
  // decode error), we can't classify — surface the original response.
  let body: string;
  try {
    body = await res.clone().text();
  } catch {
    return res;
  }
  if (!isNotebookAuthDropError(res.status, body)) return res;

  onReauth?.(true);
  try {
    const restored = await tryAutoRelogin(backend);
    if (!restored) return res; // original failing response; caller surfaces it
    return await doFetch();
  } finally {
    onReauth?.(false);
  }
}
