"""One-off: apply the updated CHESS_ENGINE_PERSONA to the canonical Engine notebook.

Changing the CHESS_ENGINE_PERSONA constant in client.py does NOT propagate to
the canonical Engine notebook on NotebookLM's side — the persona is applied
at the notebook level, not at query time. This script triggers
``configure_chess_engine()``, which is the sanctioned path for updating the
canonical Engine's persona (the HTTP endpoint at
``/api/v2/notebooks/{id}/configure-persona`` refuses writes to canonical IDs
by design — see milestone 31).

Idempotent. Safe to re-run.

Run from project root:
    cd ganymede-backend
    venv_312\\Scripts\\python.exe reconfigure_chess_engine.py
"""

import asyncio
import sys

from app.services.notebooklm import NotebookLMService
from app.services.notebooklm.client import CHESS_ENGINE_PERSONA


async def main() -> int:
    print("Loading NotebookLM client from storage...")
    svc = NotebookLMService()
    try:
        await svc.initialize()
    except Exception as exc:
        print(f"ERROR: failed to initialize NotebookLM client: {exc}")
        print("Hint: re-run `notebooklm login` if cookies are expired.")
        return 1

    try:
        print(
            f"Applying CHESS_ENGINE_PERSONA ({len(CHESS_ENGINE_PERSONA)} chars) "
            f"to canonical Engine {svc.CHESS_ENGINE_ID}"
        )
        print("Persona text:")
        print("---")
        print(CHESS_ENGINE_PERSONA)
        print("---")
        await svc.configure_chess_engine()
        print("OK: persona applied to canonical Engine notebook.")
        return 0
    except Exception as exc:
        print(f"ERROR during configure_chess_engine: {exc}")
        return 1
    finally:
        await svc.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
