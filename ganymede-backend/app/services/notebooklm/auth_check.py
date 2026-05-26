"""NotebookLM auth health check + relogin spawn.

Stateless module-level functions — no service instance required. Pattern
adapted from Z-SPAN's ``notebooklm_bridge/auth_check.py``. The wrapper's
``NotebookLMClient.from_storage()`` is the cheapest auth probe (it loads
cookies from the local store and verifies them); we cache the result so
the UI can poll without bothering NotebookLM repeatedly.

The relogin flow spawns ``python -m notebooklm login`` as a child
subprocess and feeds it ENTER on stdin after the user has completed the
Google sign-in in the launched browser. This is the operational sibling to
the ``v2`` API's auth-pill UI — Ganymede doesn't ship that UI today, but
this module exposes the primitives any consumer (or a future Ganymede UI)
needs to build one.

Public API:
    check_auth_status(force=False) -> dict
        Sync entry point. Returns:
          { "status":     "valid" | "expired" | "missing" | "unknown",
            "checked_at": ISO timestamp string,
            "details":    short human-readable note,
            "cached":     bool,
            "cache_age_seconds": float (only when cached) }

    check_auth_status_async(force=False) -> dict
        Async sibling — call from inside an event loop.

    spawn_relogin() -> dict
        Spawns ``python -m notebooklm login`` as a child subprocess.

    confirm_relogin(timeout_seconds=30.0) -> dict
        Feeds ENTER to the in-flight login subprocess and waits for exit.

    relogin_status() -> dict
        Lightweight probe of the in-flight login subprocess.

    invalidate_cache() -> None
        Force the next status check to re-probe.

Cache TTL is 300s by default — override via GANYMEDE_NOTEBOOKLM_AUTH_CHECK_TTL.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = float(os.environ.get("GANYMEDE_NOTEBOOKLM_AUTH_CHECK_TTL", "300"))

# Module-level cache. Single-process — a separate worker will have its own
# cache instance. That's fine; staleness is bounded by TTL.
_cached_status: dict | None = None
_cached_at: float = 0.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _probe() -> dict:
    """Probe NotebookLM auth by attempting ``from_storage()``.

    The wrapper's own auth verification raises ``ValueError("Authentication
    expired or invalid...")`` when the cookie session is dead.
    """
    try:
        from notebooklm import NotebookLMClient
    except ImportError as e:
        return {
            "status": "missing",
            "details": f"notebooklm-py is not installed: {e}",
        }

    try:
        await NotebookLMClient.from_storage()
        # Don't actually open the client — just verifying credentials load.
        # The from_storage() call itself raises on expired auth.
        return {
            "status": "valid",
            "details": "Cookies loaded and verified.",
        }
    except FileNotFoundError as e:
        return {
            "status": "missing",
            "details": f"No saved cookies — has `notebooklm login` been run? ({e})",
        }
    except ValueError as e:
        msg = str(e)
        if "expired" in msg.lower() or "invalid" in msg.lower():
            return {
                "status": "expired",
                "details": "Session cookies expired. Re-run `notebooklm login`.",
            }
        return {"status": "unknown", "details": msg}
    except Exception as e:
        logger.exception("auth probe failed unexpectedly")
        return {"status": "unknown", "details": f"{type(e).__name__}: {e}"}


def _cache_lookup(force: bool) -> dict | None:
    """Return cached result if still fresh, else None."""
    if force or _cached_status is None:
        return None
    age = time.monotonic() - _cached_at
    if age >= _CACHE_TTL_SECONDS:
        return None
    return {**_cached_status, "cached": True, "cache_age_seconds": round(age, 1)}


def _cache_store(result: dict) -> None:
    global _cached_status, _cached_at
    _cached_status = result
    _cached_at = time.monotonic()


async def check_auth_status_async(force: bool = False) -> dict:
    """Async-context auth health check. Use this from inside an event loop.

    Awaits ``_probe`` directly so we don't trip the "asyncio.run() cannot be
    called from a running event loop" guard.
    """
    cached = _cache_lookup(force)
    if cached is not None:
        return cached

    result = await _probe()
    result["checked_at"] = _now_iso()
    result["cached"] = False
    _cache_store(result)
    return result


def check_auth_status(force: bool = False) -> dict:
    """Check NotebookLM auth, with caching. Synchronous wrapper.

    For callers NOT inside an event loop (Flask request handlers, CLI scripts).
    If you're inside an async context, call :func:`check_auth_status_async`
    instead — calling this from a running loop returns a ``status=unknown``
    stub rather than crashing.

    Pass ``force=True`` to bypass the cache (used after a successful re-login).
    """
    cached = _cache_lookup(force)
    if cached is not None:
        return cached

    try:
        result = asyncio.run(_probe())
    except RuntimeError as e:
        if "asyncio.run() cannot be called" in str(e):
            return {
                "status": "unknown",
                "checked_at": _now_iso(),
                "details": "auth probe must run from sync context — use check_auth_status_async()",
                "cached": False,
            }
        raise

    result["checked_at"] = _now_iso()
    result["cached"] = False
    _cache_store(result)
    return result


def invalidate_cache() -> None:
    """Force the next ``check_auth_status`` call to actually probe."""
    global _cached_status, _cached_at
    _cached_status = None
    _cached_at = 0.0


# Module-level handle to the in-flight ``notebooklm login`` subprocess.
# Single-user dev workflow — only one re-auth in flight at a time.
_relogin_proc: subprocess.Popen | None = None


def _relogin_alive() -> bool:
    """True if there's a re-auth subprocess that's still running."""
    return _relogin_proc is not None and _relogin_proc.poll() is None


def spawn_relogin() -> dict:
    """Spawn ``notebooklm login`` as a child subprocess.

    The subprocess will:
      1. Open a browser to Google's OAuth page (immediately).
      2. Block waiting for ENTER on stdin (the CLI's confirmation prompt).
      3. Save cookies and exit ONLY after we feed ``\\n`` via :func:`confirm_relogin`.

    Returns immediately so the UI can prompt the user to complete sign-in.

    This is intentionally NOT a detached process — keeping the parent-child
    relationship lets us write to stdin from the same Python process. The
    trade-off is that the process dies if the host is killed mid-flow,
    which is acceptable for a dev re-auth.
    """
    global _relogin_proc

    # If a previous attempt is still alive, kill it before starting a new one.
    if _relogin_alive():
        try:
            _relogin_proc.kill()
            _relogin_proc.wait(timeout=2)
        except Exception:
            pass
        _relogin_proc = None

    py = sys.executable or "python"
    cmd = [py, "-m", "notebooklm", "login"]

    try:
        kwargs: dict = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "close_fds": True,
        }
        # On Windows, give the child its own process group so the browser
        # subprocess that ``notebooklm login`` opens isn't tied to our console.
        if os.name == "nt":
            NEW_GROUP = 0x00000200  # subprocess.CREATE_NEW_PROCESS_GROUP
            kwargs["creationflags"] = NEW_GROUP

        _relogin_proc = subprocess.Popen(cmd, **kwargs)
        invalidate_cache()
        return {
            "spawned": True,
            "cmd": " ".join(cmd),
            "pid": _relogin_proc.pid,
            "note": (
                "Browser should open shortly. Complete the Google sign-in, "
                "THEN return here and confirm — only then will cookies be saved."
            ),
        }
    except Exception as e:
        logger.exception("failed to spawn notebooklm login")
        return {"spawned": False, "cmd": " ".join(cmd), "error": str(e)}


def confirm_relogin(timeout_seconds: float = 30.0) -> dict:
    """Feed ENTER to the in-flight ``notebooklm login`` subprocess.

    Then wait for it to exit, signalling cookie save is complete.

    Returns ``{ confirmed: bool, exit_code: int | None, output: str, error?: str }``.

    Call this ONLY after the user has actually completed the Google sign-in
    in the launched browser.
    """
    global _relogin_proc

    if _relogin_proc is None:
        return {
            "confirmed": False,
            "error": "No re-auth in progress. Click 'Re-authenticate' first.",
        }
    if _relogin_proc.poll() is not None:
        # Already exited
        out = _read_remaining(_relogin_proc)
        code = _relogin_proc.returncode
        _relogin_proc = None
        invalidate_cache()
        return {
            "confirmed": True,
            "exit_code": code,
            "output": out,
            "note": (
                "Subprocess had already exited before confirm. "
                "Cookies state may or may not be saved — check status."
            ),
        }

    try:
        try:
            _relogin_proc.stdin.write(b"\n")
            _relogin_proc.stdin.flush()
            _relogin_proc.stdin.close()
        except (BrokenPipeError, OSError) as e:
            logger.warning("stdin write failed (process may have already exited): %s", e)

        try:
            _relogin_proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            _relogin_proc.kill()
            _relogin_proc.wait(timeout=2)
            out = _read_remaining(_relogin_proc)
            _relogin_proc = None
            invalidate_cache()
            return {
                "confirmed": False,
                "exit_code": None,
                "output": out,
                "error": (
                    f"Login subprocess didn't finish within {timeout_seconds:.0f}s "
                    "after ENTER. Killed it."
                ),
            }

        out = _read_remaining(_relogin_proc)
        code = _relogin_proc.returncode
        _relogin_proc = None
        invalidate_cache()
        return {
            "confirmed": code == 0,
            "exit_code": code,
            "output": out,
        }
    except Exception as e:
        logger.exception("confirm_relogin failed")
        return {"confirmed": False, "error": str(e)}


def _read_remaining(proc: subprocess.Popen) -> str:
    """Drain whatever's in the subprocess's stdout pipe — best-effort, non-blocking."""
    try:
        if proc.stdout is None:
            return ""
        data = proc.stdout.read()
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")
        return data or ""
    except Exception:
        return ""


def relogin_status() -> dict:
    """Lightweight probe: is a re-auth in flight, exited, or absent?"""
    global _relogin_proc
    if _relogin_proc is None:
        return {"in_flight": False, "exited": False}
    code = _relogin_proc.poll()
    if code is None:
        return {"in_flight": True, "exited": False, "pid": _relogin_proc.pid}
    return {"in_flight": False, "exited": True, "exit_code": code}
