---
name: project-notebooklm-substrate-handling
description: "How Ganymede handles NotebookLM's substrate quirks: (1) input-size cap (~5,100-6,000 chars; structured error 4/132-133) avoided via persona-tightening + structural extraction in Iterative path AND truncate_packets_for_synthesis in Universal Logic Loop path since milestone 50; (2) ~5hr cookie lifetime auto-recovered via Z-SPAN-ported auto_relogin (Playwright persistent profile); (3) transient null-result RPCError on get_source_ids pre-flight handled via retry wrapper since 2026-06-10; (4) IMPORT_RESEARCH RPC timeout on multi-source Deep Research ingestion handled via httpx timeout bump + retry-on-RPCTimeoutError since milestone 50."
metadata: 
  node_type: memory
  type: project
  originSessionId: b1fabc43-1fa7-4ec9-b300-429b7b733143
---

NotebookLM has two undocumented operational quirks Ganymede works around. Both mitigations are shipped; both are stable enough that future sessions shouldn't re-derive them.

## 1. Per-query input-size cap (~5,100-6,000 chars)

NotebookLM's `chat.ask` silently rejects above ~5,100-6,000 chars with HTTP 200 + structured error envelope `[["e",4,null,null,N]]` (N typically 132 or 133). The `notebooklm-py` SDK doesn't recognize this envelope and falls through to "No answer extracted from response" + empty string. Looks like a content filter; is actually an input cap.

**Discovered 2026-05-25 diagnosing Stroke 3 empty-response bug.** Full root-cause work in `docs/experiments/runs/06_LMArena_Anthropic_Cleanroom.md` § "Third-run diagnosis."

**Mitigations all shipped (milestones 37-38, current as of 2026-05-31):**
- ✅ `CHESS_ENGINE_PERSONA` tightened for per-dimension brevity + CTA suppression (applied via `reconfigure_chess_engine.py`). Stroke 1 down from ~5,500 to ~3,900-4,500 chars.
- ✅ Skip-Stroke-3-on-empty-Stroke-2 short-circuit in `orchestrator.py:run_iterative_engine`.
- ✅ Curly-brace escape on `{stroke_1_response}` / `{audit_findings}` injection (pre-existing `.format()` KeyError that was masked by silent rejection).
- ✅ Structural extraction: `_extract_for_resynthesis` + `_truncate_audit_for_injection` in `orchestrator.py`. Env-tunable via `GANYMEDE_S1_INJECTION_BUDGET` (1800) / `GANYMEDE_S2_INJECTION_BUDGET` (1500); with Bridge in the loop the audit budget splits 900/600 via `GANYMEDE_S2_AUDITOR_BUDGET` / `GANYMEDE_S2_BRIDGE_BUDGET`.
- ✅ Always-on raw-HTTP-body logging on empty-answer paths (the only diagnostic signal we have when NotebookLM rejects).
- 🟡 Upstream PR to `notebooklm-py` for the error envelope drafted but not yet submitted. Branch `fix/chat-e-error-frame` in sibling clone at `../notebooklm-py-fork/`, submission package at `../notebooklm-py-pr/`. Pinned awaiting James's submission action.

**Net effect:** The Iterative Engine pathway is production-ready end-to-end. The cap still exists at the substrate level, but Ganymede avoids it via the persona + structural-extraction stack rather than hitting it.

**Universal Logic Loop fix shipped milestone 50 (2026-06-11):** the same cap bites `run_universal_loop`'s Phase 3 synthesis whenever multi-Oracle harvests sum past ~6,000 chars — concretely, milestone 50's first attempt fired with 15,322-char packets_block and silently rejected. Fix: new `truncate_packets_for_synthesis(packets, budget)` helper in `app/services/orchestrator.py` proportionally shrinks each Truth Packet when the combined size exceeds `GANYMEDE_SYNTHESIS_PACKETS_BUDGET` (default 4500), wired into the base `synthesize()` method so every caller (Universal Logic Loop, `/managed-run`, future consumers) inherits the fix. Each truncated packet gets an explicit `[TRUNCATED]` marker so the Engine knows upstream content was cut. Validated live on session `de892dc9-...`: 11,294-char total Truth Packets → ~4,234-char synthesis output on first attempt, no retries.

## 2. Session cookie ~5hr lifetime (auto-recovered)

Google's NotebookLM session cookies live ~5 hours, after which `from_storage()` raises "Authentication expired or invalid." Used to interrupt every long-running session with a manual re-auth prompt.

**Mitigation shipped milestone 40 (2026-05-31):** `auto_relogin()` in `app/services/notebooklm/auth_check.py`, ported from Z-SPAN's `notebooklm_bridge/auth_check.py:auto_relogin` (their D-035). Key insight from the port: `notebooklm login` CLI uses Playwright's persistent context, so when the operator is still signed in to Google in that profile (the steady state), the OAuth auto-completes in the spawned Chromium in seconds. The only blocking step is the subprocess's `input("[Press ENTER when logged in] ")` prompt. `auto_relogin` watches stdout for that prompt, sleeps a grace period for redirects to settle, then feeds ENTER programmatically.

**Wired into:**
- `app/main.py:startup_event` — on first-pass `notebooklm_svc.initialize()` failure, attempts `auto_relogin` once before declaring the client uninitialized. Backend self-recovers from cold-start with stale cookies.
- `POST /api/v2/auth/auto-relogin` endpoint — also reinitializes `notebooklm_svc` on success.

**Smoke-tested live 2026-05-31:** backend cold-started with expired cookies → recovered to `status=valid` + `client_initialized=true` in ~47s, zero manual interaction.

**Limits (documented inline):** if the Playwright profile is signed-out (cleared, 2FA challenge, Google forced re-auth), the prompt won't appear within the timeout — surfaced clearly so callers fall back to the manual `/auth/relogin` + `/auth/relogin/confirm` flow. Set `GANYMEDE_AUTO_RELOGIN=0` to disable.

**Future-session implication:** when a NotebookLM call fails with auth error, don't interrupt the operator — restart the backend (or hit `POST /api/v2/auth/auto-relogin`) and the steady-state path recovers silently. Only fall through to manual re-auth if `auto_relogin` itself returns `confirmed=false`.

## 3. Transient null-result RPCError on get_source_ids pre-flight (retry-wrapped)

NotebookLM occasionally returns HTTP 200 with a null result body on the SDK's pre-flight `get_source_ids` RPC (rpcid `rLM1Ne`, called from inside `chat.ask`). The SDK raises `notebooklm.exceptions.RPCError`. Observed mid-Cleanroom 2026-06-10 — a single bad RPC return killed a whole run with a 500.

**Mitigation shipped 2026-06-10** in `app/services/notebooklm/client.py:query_notebook`: wrapped `chat.ask` in a try/except RPCError that re-uses the existing silent-rejection retry loop (`_QUERY_MAX_ATTEMPTS` × `_QUERY_BACKOFF_BASE`). Non-final attempts log + backoff + retry; final attempt re-raises so the orchestrator surfaces persistent failures.

**Future-session implication:** when a NotebookLM call surfaces `RPCError` in the orchestrator's traceback, the wrapper already gave it 3 attempts. If all 3 fail, it's likely substrate-level (corpus issue, NotebookLM regional outage, etc.) and the right move is to investigate the notebook state, not the retry logic.

## 4. IMPORT_RESEARCH RPC timeout on multi-source Deep Research ingestion

NotebookLM's IMPORT_RESEARCH RPC (post-Deep-Research ingestion of harvested sources back into a notebook) routinely takes 90-180s on a 30-source report. The `notebooklm-py` SDK's underlying httpx client defaults to 30s read timeout — too short, so the SDK raises `notebooklm.exceptions.RPCTimeoutError: Request timed out calling IMPORT_RESEARCH` while the actual NotebookLM server work completes. Symptom is 3/3 Oracle harvest failures even when Deep Research itself succeeded.

**Discovered milestone 49 validation session** (2026-06-11): all three PKI Oracles failed at this exact step. Engine fell back to corpus-pattern-matched synthesis with no real Truth Packets — concealed by visualizer animation looking like it had worked. James caught the framing error ("you're considering it a success when the core mechanic failed").

**Mitigation shipped milestone 50 (2026-06-11):**
- ✅ `NotebookLMClient.from_storage(timeout=300)` in `app/services/notebooklm/client.py:initialize`, env-tunable via `GANYMEDE_NOTEBOOKLM_HTTP_TIMEOUT` (default bumped from SDK's 30s to **300s**).
- ✅ Retry-on-`RPCTimeoutError` in `app/services/notebooklm/research.py:import_research_sources` — 3 attempts with exponential backoff (30s → 60s → 120s). Each retry uses a fresh httpx connection, so transient network slowness recovers cleanly. Env overrides: `GANYMEDE_NOTEBOOKLM_IMPORT_RETRIES`, `GANYMEDE_NOTEBOOKLM_IMPORT_BACKOFF_BASE`.

**Validated live:** milestone 50 run (session `de892dc9-...`) — all 3 Oracles imported cleanly, no `RPCTimeoutError` retries triggered. Total wall time 30:49 with three successful harvests (5,233 + 3,690 + 2,371 chars).

**Future-session implication:** if an Oracle harvest fails with `RPCTimeoutError` after the timeout bump, the underlying issue is probably NotebookLM-side (server slower than 300s, or a corpus too large even for the bumped timeout). The retry layer already handles 3 attempts; persistent failure means investigating the notebook state or splitting the harvest into smaller chunks, not re-tuning the timeout.

## Cross-references

- Input cap diagnostic logging: `app/services/notebooklm/client.py:query_notebook` (env-gated full-prompt + always-on raw-body on empty answer).
- Cap experiment write-up: `docs/experiments/runs/06_LMArena_Anthropic_Cleanroom.md`.
- Auto-relogin: `app/services/notebooklm/auth_check.py:auto_relogin`, `app/main.py:startup_event`, `app/v2_routes.py:auth_auto_relogin`.
- Z-SPAN-first heuristic: [[feedback-zspan-reference-first]].
