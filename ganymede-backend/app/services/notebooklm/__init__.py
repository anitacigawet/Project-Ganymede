"""NotebookLM wrapper sub-package.

Public surface:
    NotebookLMService — the read/write wrapper. Holds the canonical Engine
        and Mirror Auditor notebook IDs and exposes Studio output methods
        and Deep Research methods as mixins.
    Persona constants — PKI_ORACLE_PERSONA, CHESS_ENGINE_PERSONA,
        MIRROR_AUDITOR_PERSONA. Re-exported for callers that want to pass
        them through ``configure_persona`` directly.
    StudioSilentRejection — raised when NotebookLM repeatedly returns
        empty task IDs on Studio generation. Public so callers can catch
        explicitly.
    ResearchTimeout — raised when Deep Research doesn't complete within
        the timeout.
    _GATE — the module-global cooldown gate. Public because legacy callers
        (and ``docs/protocols/Account_Safety.md`` examples) read its stats.

The ``auth_check`` submodule is intentionally not re-exported here — it's
a stateless module with its own public functions, imported directly via
``from app.services.notebooklm import auth_check`` or
``from app.services.notebooklm.auth_check import check_auth_status``.

Module layout mirrors the Z-SPAN bridge structure: client / studio /
research / auth_check as siblings, with cooldown as the shared substrate.
"""

from .client import (
    NotebookLMService,
    PKI_ORACLE_PERSONA,
    CHESS_ENGINE_PERSONA,
    MIRROR_AUDITOR_PERSONA,
)
from .cooldown import _GATE
from .research import ResearchTimeout
from .studio import StudioSilentRejection

__all__ = [
    "NotebookLMService",
    "PKI_ORACLE_PERSONA",
    "CHESS_ENGINE_PERSONA",
    "MIRROR_AUDITOR_PERSONA",
    "StudioSilentRejection",
    "ResearchTimeout",
    "_GATE",
]
