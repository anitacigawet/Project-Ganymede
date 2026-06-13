---
name: project-connection-bridge-validated
description: Bicameral Convergence Level 1 production since milestone 38; Level 2 backend + frontend + endpoint shipped 2026-06-06 (E1-01 through E1-05 + E1-06 prep, milestones uncatalogued). Orthogonality confirmed on three substrates; Powell null test passed discipline; LMArena Bridge catch validated forward 2026-06-05 by Anthropic's pause call.
metadata: 
  node_type: memory
  type: project
  originSessionId: b1fabc43-1fa7-4ec9-b300-429b7b733143
---

Bicameral Convergence Level 1 is production-ready. The Connection Bridge runs as Stroke 2b by default on every iterate call. Orthogonal-lenses claim empirically robust across three independent substrates.

## Methodology lesson (durable)

**Persona-as-output-discipline (vs persona-as-vocabulary) genuinely shifts reasoning when the discipline asks the model to do something its corpus enables but its default persona doesn't pursue.** The kami persona experiment failure was persona-vs-corpus-vocabulary fighting; the Bridge succeeded because it wields the same corpus for a different output task. When designing new audit/synthesis roles, write personas that specify OUTPUT REQUIREMENTS (shape, fields, discipline) rather than REASONING AXIOMS — the latter gets overridden by the corpus.

## Status (current as of milestone 48 / 2026-06-10)

Bridge is also reachable via the single-call `/managed-run` endpoint shipped milestone 48 — for session-as-consumer projects (Z-SPAN, future Claude sessions), one HTTP call composes dispatch → create → iterate (Stroke 1 → Auditor → Bridge → Stroke 3) → translate → complete with Bridge enabled by default. The granular `/iterate` and `/bicameral-loop` endpoints below remain first-class for embedded-app consumers (PrisonBreak shape) that need fine-grained control.

**Level 1 (single-pass Bridge audit) — production default:**
- `audit_with_bridge()` orchestrator method + `POST /api/v2/sessions/{id}/bridge-audit` endpoint + `POST /api/v2/bridge/provision` helper all shipped milestone 33-37.
- Milestone 38: Bridge wired into `/iterate` as Stroke 2b with `include_bridge: bool = True` default. Iterate loop now: S1 (Engine) → S2 (Auditor) → S2b (Bridge) → S3 (re-synthesis with BOTH audits, budget-split 900/600 Auditor/Bridge). Auto-provisions a Bridge notebook when no ID supplied. Bridge failures fall back to historic 3-stroke gracefully via `fail_session_on_error=False`. Backward-compat preserved via `include_bridge=false`.
- `StrokeResult.audit_kind` field distinguishes Mirror Auditor (`"mirror_auditor"`) vs Bridge (`"bridge"`) strokes in the UI.
- DispatcherPanel + RunnerPanel render Stroke 2b in its own card (amber Auditor / cyan Bridge).

**Level 2 — backend + frontend + endpoint shipped 2026-06-06:**
- ✅ `run_bicameral_loop()` orchestrator method (closed-loop Engine ↔ Bridge mirror-bounce with iteration cap, inter-iteration delay, cancel checks at iteration boundaries)
- ✅ Two convergence criteria: `no_new_structural` (count-based via `_count_bridges_in_audit`) + `resolution_stable` (difflib.SequenceMatcher on FINAL RESOLUTION section, threshold 0.85) + `_is_audit_substantive` fallback defending against non-canonical Bridge output that would false-converge
- ✅ Four bicameral SessionEventType entries (ITERATION_START / END / CONVERGED / HARD_CAP_REACHED) + cancel event (SESSION_CANCELLED)
- ✅ `POST /api/v2/sessions/{id}/cancel` endpoint + `Session.cancel_requested` flag + `SessionCancelledError` + cancel-checks at every NotebookLM-call boundary
- ✅ `POST /api/v2/sessions/{id}/bicameral-loop` HTTP endpoint
- ✅ Frontend `BicameralProgressIndicator.tsx` (iteration counter + animated side indicator + cancel button + terminal-state messaging) mounted in RunnerPanel
- ⏸️ E1-06 first live run is operator-driven (requires backend + auth + scenario approval). Code is end-to-end ready; the live exercise is your call. **PAUSED 2026-06-13** per operator decision post-milestone-51 ([[project-structural-attractor-validation]]): single-stroke Universal Logic Loop produced structural-attractor-grade output on Run 7, reducing the multi-stroke convergence loop's empirical motivation. Build artifacts retained; revisit only if validated path starts producing failures the current discipline doesn't catch.

**Level 3 still pending:** Bridge-triggers-Oracle-spawn decision logic, gated by operator approval. The Pl3 Operator Lens (translation stroke) shipped instead this session — different work-stream.

## Cross-scenario orthogonality confirmed on THREE substrates

| Substrate | Date | Bridge output | Overlap with Auditor |
|---|---|---|---|
| Amnesia | 2026-05-22 | 3 missed bridges (2 STRUCTURAL + 1 IMPLIED) | Zero |
| LMArena | 2026-05-26 (Run 7) | 2 missed connections (Strategic Lasso × D5, metacognitive adaptation × ROEM) | Zero |
| Powell | 2026-05-31 (null test) | 4 missed bridges (2 STRUCTURAL + 2 IMPLIED, 0 SPECULATIVE) | n/a (Auditor not run on Powell) |

## Powell null test result (milestone 40, important methodological finding)

The 2026-05-31 Powell-sound Bridge null test was designed as a discipline check: feed the Bridge the EXACT canonical Powell substrate + Powell Engine Resolution as `target_text` and see if it produces "0 missed bridges" (sound output detected), valid catches, or speculative over-production.

**Classification: valid catches, 0 speculative.** Bridge passes its discipline (no over-production) AND surfaces real catches the canonical Powell run missed.

**Most severe catch (Bridge 1, STRUCTURAL):** The Engine's "Renovation-Cause Pincer" Strategic Lasso explicitly relied on the DOJ criminal investigation as the for-cause mechanism. But Silo D8 of the same substrate explicitly states the DOJ probe was CLOSED on April 24, 2026 (the closure was what triggered Tillis to defect). The Engine treated the probe as ongoing while another packet on the same substrate documented its closure. Real temporal-state error in the canonical resolution.

**Implications:**
1. The "Powell was a clean win" framing in `OVERVIEW.md` / `GLOSSARY.md` needs a footnote. The blind-validation audit still stands at the *prediction* level, but the *resolution mechanism* had real missed connections.
2. **By inference, other "validated" runs (Tokenized Land, Genie Giant-Slayer) likely have similar errors that nobody Bridge-audited.** Rerunning Bridge on them would be cheap (~30 min each, similar substrate size) and would either confirm or falsify this inference.
3. **The milestone 38 decision to default `include_bridge=True` was correct.** If our strongest baseline had real missed connections, unaudited resolutions are unsafe by default.

Run record: `docs/experiments/runs/Powell_Bridge_Null_Test.md`. Driver script: `scripts/powell_bridge_null_test.py` (parses canonical Truth Packets + Engine Resolution from the run record markdown directly).

## Cross-references

- Architecture context: `docs/concepts/Bicameral_Convergence.md`
- Persona spec: `docs/protocols/Connection_Bridge_Persona.md`
- LMArena Bridge result: [[project-lmarena-prediction]]
- Framework Cleanup connection: Powell Bridge 1's "Engine processes dimensions statically" hypothesis reinforces `docs/concepts/Framework_Cleanup_Hypothesis.md` evidence point 10.
