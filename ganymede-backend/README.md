# Ganymede Backend

FastAPI service implementing the Universal Logic Loop over the 9D Chess Engine and the PKI Authentication Oracle swarm.

## Architecture

```
app/
├── main.py                          # FastAPI app + endpoints
└── services/
    ├── notebooklm_service.py        # low-level NotebookLM client wrapper
    ├── gemini_service.py            # Gemini compiler (legacy; kept for future)
    └── orchestrator.py              # Universal Logic Loop primitives
```

The **orchestrator** composes `NotebookLMService` into the four-phase
Universal Logic Loop. Each method is one explicit step. There is no
auto-run "do everything" call — the runaway-prevention guardrail is
enforced in code (`create_oracle` makes exactly one notebook per call).

## Endpoints

| Method | Path | Phase | Maps to |
| --- | --- | --- | --- |
| `GET`  | `/api/health` | — | health check |
| `POST` | `/api/triage` | 1 | `orchestrator.triage` |
| `POST` | `/api/oracle` | 2.1 | `orchestrator.create_oracle` (one notebook) |
| `POST` | `/api/oracle/{id}/go` | 2.2 | `orchestrator.send_go` |
| `POST` | `/api/oracle/{id}/harvest` | 2.3 | `orchestrator.harvest` |
| `POST` | `/api/swarm/harvest` | 2.3 | `orchestrator.harvest_swarm` (parallel) |
| `POST` | `/api/synthesize` | 3 | `orchestrator.synthesize` |
| `POST` | `/api/resolution-check` | 4 | `orchestrator.resolution_check` |
| `POST` | `/api/orchestrate` | (legacy) | composite single-shot for the frontend Cortex Clipboard |

## Running

```powershell
cd ganymede-backend
.\venv_312\Scripts\activate
$env:PYTHONPATH = "."
uvicorn app.main:app --reload --port 8000
```

OpenAPI docs: <http://localhost:8000/docs>

## Using the UI from another device on the LAN

`run_dev.bat` binds the backend to `0.0.0.0` and prints the LAN URLs on
startup. Open `http://<host-lan-ip>:3000` from a phone or laptop on the same
network — the frontend derives the backend host from the page's own origin
(`ganymede-ui/src/lib/backend.ts`), so nothing needs configuring, and it keeps
working when the host's DHCP address changes. Override with
`NEXT_PUBLIC_GANYMEDE_BASE_URL` only when the backend lives on a *different*
host than the UI.

Two caveats:

- **Windows Firewall** must allow inbound TCP 3000 + 8000 on the private
  profile. Windows usually prompts the first time; if a second device can't
  connect while `curl` works locally, this is why.
- **The API has no authentication.** Binding to `0.0.0.0` means anyone on the
  network can drive runs (consuming NotebookLM quota) and read past sessions.
  Fine on a trusted home LAN; do not do it on public/shared wifi. To revert to
  localhost-only, change `--host 0.0.0.0` back to `--host 127.0.0.1` in
  `run_dev.bat` and set `GANYMEDE_CORS_ORIGIN_REGEX=` (empty) to drop the
  private-range CORS allowance.

## Required environment

- **`GOOGLE_API_KEY`** — for `GeminiService` (currently invoked only via `test_compiler.py`; `main.py` doesn't call Gemini directly).
- **NotebookLM session** — **dormant by decision** (Substrate Migration,
  TASKS § SM, 2026-07-02: no re-auth, no further NotebookLM runtime; the
  NotebookLM code path is retained as the rollback artifact). Everything
  below is rollback-artifact procedure, not routine operation.
  Ganymede uses a **dedicated** NotebookLM home at
  `%USERPROFILE%\.notebooklm-ganymede` (set via `NOTEBOOKLM_HOME` in `.env` and
  `run_dev.bat`; added 2026-07-22 after a shared-profile relogin captured
  Z-SPAN's worker account and Ganymede lost access to its own notebooks —
  LIST_NOTEBOOKS empty + PERMISSION_DENIED on the Engine). Never point this
  at Z-SPAN's `~/.notebooklm`. If the session is expired or the profile is
  fresh, sign in with the Google account that owns the Engine notebook:
  ```powershell
  $env:NOTEBOOKLM_HOME = "$env:USERPROFILE\.notebooklm-ganymede"
  .\venv_312\Scripts\python.exe -m notebooklm login
  ```

## Hard guardrails (enforced in code)

1. **The 9D Chess Engine and Mirror Auditor are read-only.** Canonical Engine `0a7d2672-009e-4995-9477-68c9b2fd9e54` and Mirror Auditor `756e3683-f651-4381-b560-b13711b84ce6` are hardcoded as `CHESS_ENGINE_ID` and `MIRROR_AUDITOR_ID` in `notebooklm_service.py`. Only `query_chess_engine` / `query_mirror_auditor` (read-only) and `configure_chess_engine` / `configure_mirror_auditor` (idempotent persona application from `docs/protocols/`) are allowed against them. Earlier validated runs used Engine ID `5967ce5d-f9eb-4f4e-b3e1-620f643d8390`, preserved as `LEGACY_ENGINE_ID` for traceability.
2. **All NotebookLM API calls cooldown-gated.** Hard floor 8s between calls (Z-SPAN-recommended default), soft caps 20/hour and 100/day. See [`../docs/protocols/Account_Safety.md`](../docs/protocols/Account_Safety.md). Don't bypass with direct `self.client.X` calls — route through `NotebookLMService`.
3. **No auto-batching of oracle creation.** `POST /api/oracle` creates exactly one notebook. To create N oracles, the caller calls the endpoint N times.

See `docs/OVERVIEW.md` for the full guardrail list and `docs/protocols/` for the protocols.

## Tests / smoke runs

`test_compiler.py` and `test_swarm_logic.py` at the backend root are smoke scripts, not formal tests. They invoke the services against the live NotebookLM workspace.

## Historical scripts

The 36 ad-hoc scripts that previously lived in `ganymede-backend/scratch/` have been archived to `docs/experiments/scripts/`. See its README for a script-by-script index. The patterns they encoded are now exposed as endpoints via `app/services/orchestrator.py`.
