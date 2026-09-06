/**
 * Backend base-URL resolution — single source of truth.
 *
 * Every component used to hardcode `http://127.0.0.1:8000` as its fallback.
 * That works when the browser IS the host machine, but breaks the moment the
 * UI is opened from another device on the LAN: this code runs in the REMOTE
 * browser, where `127.0.0.1` resolves to that remote device, not the machine
 * running the backend. Every fetch and the WebSocket stream would fail.
 *
 * Resolution order:
 *   1. `NEXT_PUBLIC_GANYMEDE_BASE_URL` — explicit override always wins
 *      (remote/tunnelled backends, or a backend on a different host).
 *   2. Runtime-derived from the page's own origin: whatever host you loaded
 *      the UI from, talk to the backend on that same host. Serves localhost
 *      and LAN identically with zero configuration, and survives the host's
 *      DHCP address changing.
 *   3. SSR fallback — Next pre-renders client components on the server, where
 *      `window` doesn't exist. Never used for a real request (all calls are
 *      client-side); it only has to be a valid string.
 *
 * The backend port is assumed to be 8000 (overridable via
 * `NEXT_PUBLIC_GANYMEDE_BACKEND_PORT`) because the backend is a separate
 * service from the Next dev server, not a same-origin API route.
 */

const SSR_FALLBACK = 'http://127.0.0.1:8000';

/**
 * Resolve the backend HTTP base, e.g. `http://192.168.0.151:8000`.
 *
 * Call this at request time (not at module scope) so the value is computed in
 * the browser where `window.location` is real.
 */
export function getBackendBaseUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_GANYMEDE_BASE_URL;
  if (explicit) return explicit.replace(/\/+$/, '');

  if (typeof window === 'undefined') return SSR_FALLBACK;

  const port = process.env.NEXT_PUBLIC_GANYMEDE_BACKEND_PORT ?? '8000';
  return `${window.location.protocol}//${window.location.hostname}:${port}`;
}

/**
 * Resolve the backend WebSocket base, e.g. `ws://192.168.0.151:8000`.
 * Mirrors `getBackendBaseUrl` and upgrades the scheme (http→ws, https→wss),
 * so a page served over HTTPS doesn't attempt an insecure ws:// socket that
 * the browser would block as mixed content.
 */
export function getBackendWsUrl(): string {
  return getBackendBaseUrl().replace(/^http/, 'ws');
}
