---
title: "Substrate Migration — NotebookLM → Sonnet + Qdrant (Hybrid)"
type: "concept"
status: "active"
tags: ["architecture", "substrate", "migration", "qdrant", "sonnet", "fable-audit"]
color_id: "6"
---

# Substrate Migration — NotebookLM → Sonnet + Qdrant (Hybrid)

> **Status:** Plan drafted 2026-07-02 (Fable 5 session, post-audit-#1);
> **scope-revised 2026-07-02-b** (operator: *"i dont want to run anymore
> notebookLM stuff honestly, just want to migrate"* — NotebookLM goes fully
> dormant, no re-auth ever; SM-3 redesigned loginless; SM-7 harvest
> replacement added). Pending audit #2 (adversarial plan review) before
> execution. Operator authorization: James 2026-07-02 — "take the wheel."
>
> **One-sentence shape:** the analytical strokes (Engine / Mirror Auditor /
> Connection Bridge / Operator Lens) move from NotebookLM notebooks to
> Sonnet via headless `claude -p` with the full 9D foundations corpus carried
> in-context; the PKI Oracle harvest moves to a WebSearch-grounded `claude -p`
> oracle (SM-7) with the NotebookLM path retained dormant-not-deleted; a
> Qdrant node on the operator's Surface Pro (same architecture as Z-SPAN's
> `surfacepro_rag_node`, separate service + collections) becomes the
> accumulating Truth-Packet library and session-history search layer.

## 1. Decision provenance

| Decision | By | When |
|---|---|---|
| Remove NotebookLM from analytical strokes; keep for Oracle harvest only (hybrid) | James | 2026-07-02 |
| **Scope revision (-b): no further NotebookLM runtime at all** — no re-auth on this machine, no live side-by-side calls; hybrid → full dormancy; harvest replacement (SM-7) promoted from parked F12 idea to a real phase; old-machine `sessions.db` backup offered for exact-packet replay | James (*"i dont want to run anymore notebookLM stuff honestly, just want to migrate"*) | 2026-07-02 |
| Sonnet as the replacement generator ("included in my subscription" — corrected to "included non-interactive compute cap," see § 4) | James, verified against Z-SPAN D-119/D-121 | 2026-07-02 |
| Two Fable 5 audits: #1 pre-migration architecture (done), #2 this plan (pending) | James | 2026-07-02 |
| Surface Pro Qdrant node, same architecture as Z-SPAN's, NOT shared infrastructure | James | 2026-07-02 |

Audit #1 findings F1–F12 (chat record, 2026-07-02) are the requirements this
plan must close. The act-now set: **F1** (corpus-in-context; Qdrant re-scoped),
**F2** (closed sphere physics→policy), **F3** (cross-base-model window),
**F4** (guardrail rewrite), **F6** (input-cap machinery retires), **F7**
(personas port), **F9** (write `Closed_RAG_Sphere.md`).

This migration is also the **Silo 3 / M3 "framework decision" firing**: ROADMAP
M3 anticipated "pursue a home-brewed runtime (NotebookLM is the wrong
substrate)." The 2026-07-02 resolution is subtler — the substrate isn't
*wrong* (milestone 51 validated output produced on it); it's being traded up
for cost, control, observability, and epistemic explicitness, with its one
irreplaceable capability (Deep Research) retained.

## 2. Target architecture

```
                        ┌─ Mac (this machine) ──────────────────────────────┐
 operator / consumer →  │ FastAPI backend (:8000)                           │
                        │   Dispatcher (DeepSeek/Gemini — unchanged)        │
                        │   GanymedeOrchestrator                            │
                        │     ├─ EngineSubstrate = SonnetSubstrate          │
                        │     │    claude -p --model <pinned> per stroke:   │
                        │     │    persona + FULL foundations corpus        │
                        │     │    + scenario + Truth Packets + priors      │
                        │     │    (Engine / Auditor / Bridge / Lens)       │
                        │     ├─ WebSearch PKI Oracle (SM-7):               │
                        │     │    claude -p + WebSearch, PKI persona,      │
                        │     │    hash-cites URLs → Truth Packet           │
                        │     └─ NotebookLM service: DORMANT               │
                        │          (code retained, never invoked; no auth   │
                        │          on this machine — rollback artifact)     │
                        │   SessionStore (SQLite — unchanged)               │
                        └────────────┬──────────────────────────────────────┘
                                     │ LAN HTTP, bearer token
                        ┌────────────▼──────────────────────────────────────┐
                        │ Surface Pro — ganymede-rag-node (FastAPI :8767)   │
                        │   BGE-small-en-v1.5 (shared model instance OK)    │
                        │   Qdrant (shared Podman container, own            │
                        │   collections): ganymede_truth_packets,           │
                        │   ganymede_strokes                                │
                        └───────────────────────────────────────────────────┘
```

**What does NOT change:** dispatcher + its providers, SessionStore/persistence,
WS event stream, session/stroke contracts (one additive field, § 4), UI panels
(provenance labels only), hard guardrails #5–#7 (jargon-strip, zero-degradation
packets, holistic synthesis — the epistemic constitution).

## 3. Substrate adapter design

New module `ganymede-backend/app/services/substrate.py`:

```python
class EngineSubstrate(Protocol):
    async def query_engine(self, prompt: str, *, grounding: GroundingBundle) -> SubstrateResult
    async def query_auditor(self, prompt: str, *, grounding: GroundingBundle) -> SubstrateResult
    async def query_bridge(self, prompt: str, *, grounding: GroundingBundle) -> SubstrateResult
    async def translate(self, prompt: str) -> SubstrateResult   # no grounding needed
```

- `GroundingBundle` = ordered (corpus_files, truth_packets, prior_strokes).
  The Sonnet implementation renders it as a stable prompt prefix (corpus
  first — cache-friendly); the NotebookLM implementation ignores corpus
  (notebook-resident) and injects only what today's templates inject.
- `SubstrateResult` = text + `cost_usd: Optional[float]` + `substrate: str` +
  `model_id: Optional[str]`.
- `NotebookLMSubstrate` wraps the existing `query_chess_engine` /
  `query_mirror_auditor` / bridge-notebook path **unchanged** — it exists so
  the orchestrator has exactly one seam and the SM-3 side-by-side window can
  run both substrates from the same call sites.
- `SonnetSubstrate` invokes `claude -p` per stroke, mirroring Z-SPAN's
  `synthesize_via_claude_p` (binary resolution chain: `shutil.which` →
  `GANYMEDE_CLAUDE_BIN` → known nvm path; `--output-format stream-json` to
  capture `total_cost_usd`; explicit `--model` per invocation per the
  explicit-at-invocation discipline). Model default `GANYMEDE_ENGINE_MODEL`
  (Sonnet current-gen; exact ID live-verified in SM-1 before pinning).
  Timeout 300s default. Retry ×2 on empty/nonzero-exit.
- Selection: `GANYMEDE_SUBSTRATE` env (`sonnet` | `notebooklm`), plus
  per-request override field for the SM-3 comparison harness.
- Personas: reuse the constants in `notebooklm/client.py:85-166` verbatim,
  plus a **sphere-discipline block** (§ 5) appended for the Sonnet side only.
- Output-format conformance: Sonnet strokes MUST keep satisfying the parsing
  the orchestrator already does — **five load-bearing parsers**:
  `_count_bridges_in_audit` (regex on `Bridge N (STRUCTURAL|IMPLIED)`),
  `_parse_audit_findings` (numbered fault categories),
  `_extract_final_resolution_section` (FINAL RESOLUTION header),
  `_strip_trailing_cta`, and `parse_triage_hit_list` (orchestrator.py:2042 —
  the `<HIT_LIST_JSON>` marker contract at :145-149; a triage that misses the
  marker shape silently degrades `run_universal_loop` to blueprint-only
  synthesis at :1898-1914, so this one is REQUIRED in conformance tests).
  Soft dependents (benign failure = extra paid bicameral iterations, noted
  not tested): `_is_audit_substantive`, `_resolution_stable`. SM-1 ships
  conformance tests that fire real strokes and assert all five parsers
  extract non-empty structure.
- `SubstrateResult` fields persisted per stroke: `cost_usd`, `substrate`,
  and `model_id` (three additive `StrokeResult` fields — model_id makes R3
  silent-routing observable per stroke, not just per config).

## 4. Cost model (evidence: Z-SPAN D-119 + D-121, live-metered 2026-06-17)

- Headless `claude -p` is **decoupled from interactive Max usage**; it bills
  against an **included monthly non-interactive compute cap** (~$100/mo MAX
  5x, ~$200/mo MAX 20x, resets monthly). Not cash; use-it-or-lose-it.
- Live-measured base overhead ~18¢/invocation (Sonnet, trivial prompt, CLI
  2.1.158) — the Claude Code harness prompt rides every call. Estimate
  ~30-35¢/stroke with the ~45k-token corpus + packets; **≈ $1.30 of cap per
  full 4-stroke run**; ~35¢ for a Universal-Loop synthesis; +~25¢/translation.
- Ganymede volume is operator-triggered (single-digit runs/week) → single-digit
  dollars of cap per month. **Watch-item:** the cap is shared with Z-SPAN's
  Sonnet serving layer; contention is a future calibration conversation, not a
  present problem.
- **Observability requirement:** per-stroke `cost_usd` captured from the
  stream-json result event → new optional field on `StrokeResult` → persisted
  by the existing SessionStore save path → surfaced in session state. A
  WARNING log above `GANYMEDE_RUN_COST_WARN` (default $5) per session. No
  hard gate in v1 (no unattended loops exist; bicameral cap is 10 iterations).
- **Escape hatch (flag, not build):** direct Anthropic API via key
  (`GANYMEDE_ANTHROPIC_API_KEY` + `substrate=sonnet_api`) — same prompts, no
  harness overhead, prompt-caching-friendly (~$0.30/run cash). Implement only
  if cap contention materializes; the adapter seam makes it additive.
- SM-1 empirically answers whether identical corpus prefixes get server-side
  cache hits across `claude -p` invocations (two identical strokes 60s apart,
  compare `total_cost_usd`).

## 5. Closed-sphere enforcement (F2 — the migration's deepest risk)

NotebookLM enforced grounding **architecturally** (model mostly can't see
beyond notebook sources). Sonnet knows the world; the sphere becomes
**policy**. Three enforcement layers, none optional:

1. **Sphere-discipline block** appended to every Sonnet-side persona:
   knowledge sphere = (a) foundations corpus below, (b) Truth Packets below,
   (c) prior strokes below — exclusively. External-world facts appearing in
   packets ⇒ open with the epistemic notice (Run 7's `Notice: …` shape,
   now REQUIRED, not emergent). A needed-but-absent fact ⇒ state
   `DATA NOT AVAILABLE IN SPHERE`, never supply from memory.
2. **Code-level notice check** in `SonnetSubstrate`: packets present but no
   `Notice:` prefix ⇒ WARNING log + `sphere_notice_missing` flag on the
   stroke (visible in session state; cheap, syntactic, catches drift).
3. **Bridge persona extension (both substrates):** new numbered duty — flag
   `OUT-OF-SPHERE` any synthesis claim resting on facts absent from packets
   + foundations. The Bridge already polices itself this way
   (client.py:152); this extends the discipline to what it audits. Semantic
   enforcement rides the existing audit stroke — no new machinery.

SM-3's diff report grades both substrates on sphere behavior explicitly.

## 6. Corpus packaging (F1)

- `docs/foundations/*.md` (12 files, ~120k chars ≈ 30k tokens) — assembled
  in sorted order with per-file headers into the prompt prefix by a
  `CorpusAssembler` (env override `GANYMEDE_CORPUS_FILES` for subset runs —
  this is what makes M2's kernel-vs-scaffolding test a flag, per F10/audit).
- The one PDF (`Neuro-Linguistic Programming & VR…`, 22 pp) gets a **one-time
  text extraction** to a checked-in `.md` sibling (SM-2 chunk; extraction
  faithfulness spot-verified against the PDF before the file joins the
  corpus). Until then the Sonnet corpus is the 12 markdown files; NotebookLM
  keeps the PDF natively either way. Default corpus = **all files**
  (faithful-port-first, per the validated-path discipline); leaner subsets
  are experiments, not defaults.

## 7. Phases

**SM-0 · Mac environment bring-up** *(no NotebookLM needed)*
Backend has never run on this machine (venv_312 is a committed Windows venv).
Create `ganymede-backend/venv_mac` on **python3.12** (parity with the
known-good venv_312; 3.11 fallback with a justification note if the brew
install fights back); author + check in `requirements.txt` pinned from
venv_312's dist-info — fastapi 0.136.1, uvicorn 0.46.0, pydantic 2.13.3,
httpx 0.28.1, google-genai 1.74.0, `notebooklm-py==0.3.4` **base extra only**
(playwright is `[browser]`-extra, login-flow-only — a dormant backend never
installs it), **plus the two invisible-to-import-grep runtime deps the
reviewer caught: `websockets` (uvicorn WS protocol for the v2 event stream)
and `python-dotenv` (main.py silently skips `.env` without it)**. Ship a
checked-in `.env.example` documenting dormant mode: `GANYMEDE_AUTO_RELOGIN=0`
(reviewer finding: default-ON auto-relogin spawns a `notebooklm login`
attempt on every boot — auth_check.py:555-563 — which is not-dormant),
substrate default, cost-warn threshold. Backend boots with NotebookLM init
degraded-and-quiet; `GET /api/health` green; sessions endpoints + WS route
import clean.
**Done:** health + sessions endpoints respond on :8000 with zero NotebookLM
auth AND zero login-spawn attempts in the boot log.

**SM-1 · SonnetSubstrate service** *(no NotebookLM needed)*
`substrate.py` (protocol + both implementations + claude-p wrapper +
cost capture + notice check + conformance retries); persona constants
re-exported with sphere block; live verification: fire Engine persona +
corpus + a toy scenario through `claude -p`; regex-conformance tests
(Bridge/Auditor output shapes vs the four parsers); cache-hit experiment;
pin the verified model ID. `StrokeResult.cost_usd` + `substrate` fields
(additive, backward-compatible with persisted sessions).
**Done:** a real Sonnet stroke round-trips with cost recorded and parsers
extracting structure; conformance tests green.

**SM-2 · Orchestrator seam + corpus assembler + PDF extraction**
Thread `EngineSubstrate` through `run_synthesis_stroke`, `run_audit_stroke`,
`audit_with_bridge`, `run_translation`, `run_iterative_engine`,
`run_bicameral_loop`, `synthesize`, `triage`, **and `run_universal_loop`'s
Phase-1 triage, which calls `svc.query_chess_engine` INLINE at
orchestrator.py:1886 rather than via `triage()` (reviewer catch — missing it
would leave a live NotebookLM call inside the "migrated" loop)**. Gate
`main.py` startup NotebookLM init on substrate (dormant ⇒ skip init +
auto-relogin entirely rather than try-and-degrade). Mark the legacy
`/api/orchestrate` surface (main.py:425 direct `query_notebook`) and
`resolution_check` as notebooklm-only dormant endpoints. Sonnet path skips:
bridge-notebook provisioning (stateless Bridge), injection budgets +
truncation (full-fidelity injection), cooldown gate. NotebookLM path
otherwise untouched. PDF→md extraction lands.
**Done:** `GANYMEDE_SUBSTRATE=sonnet` runs the full iterative loop end-to-end
on a toy scenario with zero NotebookLM calls; `=notebooklm` still compiles the
old path (execution untested until SM-3's auth).

**SM-3 · Recorded-baseline validation (F3, loginless — scope-revision -b)**
*No NotebookLM runtime anywhere in this phase.* The comparison runs Sonnet
against the **recorded** NotebookLM outputs already in the repo:
- **Powell replay:** the canonical run record carries full Truth Packet text
  (the P1-02 null-test driver parses packets from the markdown — same
  extraction reused). Identical packets → Sonnet → structured diff against
  the recorded Powell Engine Resolution.
- **Run 7 replay (upgrade, gated on the old-machine backup):** operator
  offered the pre-handoff `ganymede-backend/data/sessions.db` from the old
  computer. When copied over (one file, non-blocking), session `de892dc9…`'s
  exact truncated packets replay into Sonnet against Run 7's recorded
  synthesis. Until then, Powell alone is the go/no-go basis.
- **Canonical-notebook corpus parity** (self-pass finding): unverifiable
  without auth, and auth is now never happening — the residual is accepted
  and documented: parity evidence = provision_bridge_notebook's docstring
  intent (orchestrator.py:954) + foundations README's 13-doc claim. Noted
  in the diff report as a caveat, not a blocker.
Diff dimensions: FINAL RESOLUTION agreement, dimensional coverage, sphere
behavior (notice presence, out-of-sphere claims), jargon register,
output-shape parser compatibility, length, cost. Caveat logged in the
report: recorded-vs-fresh is temporally asymmetric (base models + prompts
drifted since the recordings) — weaker than same-day side-by-side, which
the operator declined deliberately to avoid NotebookLM runtime.
Product: `docs/experiments/runs/Substrate_SideBySide.md` + a
methodology_questions Q2 (locus-of-intelligence) update — first
same-corpus-different-base-model data the project has ever had.
**Done:** diff report exists; go/no-go call on cutover recorded in it.

**SM-4 · Cutover + constitution rewrite**
Default `GANYMEDE_SUBSTRATE=sonnet`. The entire NotebookLM path (analytical
AND harvest) stays code-present but dormant (pause-not-delete; rollback =
flip the env + re-auth, operator-owned). Docs: OVERVIEW hard-guardrails
rewrite (#1-#3 marked dormant-with-the-substrate, reactivation conditions
documented; new: corpus-in-git integrity, persona constants as canon,
explicit model pinning, node-token handling), `docs/concepts/Closed_RAG_Sphere.md`
written (F9 — physics→policy + the dangling Run-7 link fixed),
CLAUDE.md/ROADMAP/TASKS sweep, UI provenance labels **including the AuthPill
(reviewer: it polls `/auth/status` cleanly under dormancy but would show red
forever — becomes a "Substrate: Sonnet" state or hides when dormant)**,
Architecture_History **milestone 52**. Known gap until SM-7: the Dispatcher
UI's auto-harvest path (real-world Cleanroom via Universal Logic Loop) has no
live harvester — consumer-supplied packets (`/managed-run`, Z-SPAN shape) are
unaffected.
**Done:** fresh clone + SM-0 steps + `sonnet` default = working analytical
engine with no Google auth at all.

**SM-5 · Surface Pro ganymede-rag-node**
⛔ *Operator gate: install on Surface Pro (courier the handoff doc to the
Surface Pro Claude session, Z-SPAN V1-RAG-1 pattern).*
Port Z-SPAN's `server.py` shape → `ganymede-rag-node/` (own service, port
8767, own bearer token, shared Podman Qdrant + BGE venv documented as
reuse-OK): collections `ganymede_truth_packets` (payload: subject, packet
text, session_id, scenario hash, harvest date, source label) +
`ganymede_strokes` (final syntheses, register translations). Mac-side
`rag_node_client.py` + wire-ins: persist packet on ORACLE_HARVESTED; persist
final stroke on SESSION_COMPLETE; `GET /api/v2/knowledge/search` passthrough
endpoint ("have we researched X?"). Install handoff doc
`docs/integration/ganymede_rag_node_handoff.md` (V1_RAG1-style).
Non-blocking enrichment; analytical engine works without the node (guarded by
`GANYMEDE_RAG_NODE_TOKEN` presence, Z-SPAN worker pattern).
**Done:** harvested packets from the next real run appear in Qdrant and are
searchable from the Mac.

**SM-6 · Retirement + hygiene sweep**
Mark input-cap machinery NotebookLM-path-only (comments, not deletion);
`.gitignore` + purge the committed Windows venv (repo −~5,000 files — flagged
here so the big diff is expected); memory updates
(`project_closed_rag_sphere_principle` redefinition, substrate memory,
`feedback_zspan_reference_first` path fix → `~/Desktop/zspan`); TASKS/ROADMAP
closeout; milestone 52 addendum if anything surprised.
**Done:** contract docs + memory agree with the code again.

**SM-7 · WebSearch PKI Oracle — the harvest replacement (scope-revision -b)**
Replaces NotebookLM Deep Research as the Universal Logic Loop's Phase-2
harvester. `WebSearchOracle` in the substrate module: `claude -p` with
WebSearch enabled (`--allowedTools` per headless docs — exact flag verified
live), `PKI_ORACLE_PERSONA` ported with the hash-citation format re-anchored
to URLs (`[SRC-{domain-slug}:{hash}]`), one invocation per subject taking the
surgical prompt verbatim (Hard Guardrail #5's jargon-strip already upstream
in triage). Quality bar before it becomes the default harvester, validated
on one real subject: ≥15 distinct sources cited OR an explicit shortfall
marker in the packet (honesty-over-fabulation, per the PKI persona's
DATA NOT FOUND discipline); packet shape must satisfy the existing
zero-degradation synthesis path unchanged. Cost note: headless WebSearch
pricing against the included cap is UNVERIFIED — SM-7's metering answers it
before any default flips; if per-search pricing lands cash-side, surface to
operator before adopting (per the no-unexpected-recurring-cost rule).
`run_universal_loop` Phase 2 branches on substrate; ORACLE_* session events
keep firing (payload gains `oracle_kind: websearch|notebooklm`) so the
visualizer needs no rework.
**Done:** one real-world Cleanroom question drives triage → WebSearch
oracles → grounded synthesis end-to-end with zero NotebookLM calls, and the
packet quality bar is met + recorded in a short run note.

Sequencing: SM-0 → SM-1 → SM-2 → SM-3 → SM-4 → SM-7 → SM-5 → SM-6, with
SM-5 parallel-eligible after SM-1 (its Mac-side client doesn't depend on
cutover) and SM-7 buildable any time after SM-1 (it reuses the claude-p
wrapper + metering).

## 8. Risk register

| # | Risk | Mitigation |
|---|---|---|
| R1 | Sphere leakage (Sonnet world knowledge contaminates grounded synthesis) | § 5 three layers; SM-3 grades it; Bridge OUT-OF-SPHERE audit ongoing |
| R2 | Output-shape drift breaks the four parsers | SM-1 conformance tests; personas already specify output shape (the portable kind) |
| R3 | Model availability / silent routing | Explicit `--model` per invocation; ID live-verified at SM-1; **Fable-as-Engine declined** — pinning the Engine to the exact model class the project's own milestone 51 documented being federally pulled is substrate fragility the project just escaped; Fable stays a per-run experiment value |
| R4 | `claude -p` env fragility (PATH under service contexts, harness updates) | Z-SPAN's resolution chain + pinned fallback path; stream-json parse guarded |
| R5 | Framework behavior shifts under 10× grounding (dimensional greed amplified) | Faithful-port-first; SM-3 diff is the detector; budgets remain env-tunable knobs |
| R6 | Node unreachable / network asymmetry (Z-SPAN hit this — courier 2026-06-24) | Node optional-by-token; enrichment path degrades silently with WARNING |
| R7 | Headless cap contention with Z-SPAN | Per-stroke cost in SessionStore; warn threshold; API-key escape hatch flag |
| R8 | PDF extraction infidelity | One-time, spot-verified, checked-in; NotebookLM side unaffected |

**Rollback:** every phase lands behind the substrate flag until SM-4; SM-4
itself is one env-default commit — revert = flip `GANYMEDE_SUBSTRATE` back.
Nothing NotebookLM-side is deleted anywhere in this plan.

## 9. Non-goals

No UI redesign; no M2 unpause (the flag exists, the experiment stays parked);
no E1-06 unpause; no Bicameral redesign; no public-release moves; no
multi-tenant/auth work on the node beyond bearer token; no deletion of any
NotebookLM code anywhere (dormancy, not removal — rollback stays real).

## 10. Audit #2 log

**Self-refutation pass (Fable session, 2026-07-02) — five findings, all
integrated into the plan above:**

1. ❌→fixed **SM-3's Run 7 replay was impossible as drafted** — `data/` is
   gitignored; session `de892dc9…`'s SQLite row did not survive the clone.
   Redesign: Powell recorded-packet replay (packets verbatim in the repo
   record) + Run 7 exact-packet replay gated on the operator's old-machine
   `sessions.db` backup. (Superseded the interim fresh-harvest idea, which
   died with scope-revision -b's no-NotebookLM-runtime rule.)
2. ⚠️→fixed **`resolution_check` is chat-stateful** (relies on Engine-notebook
   conversational memory; sends no scenario/synthesis content). Not called by
   any session-aware loop — marked notebooklm-only legacy in SM-2. The
   iterative + bicameral loops are stateless-safe by inheritance: the
   input-cap era forced explicit re-injection of all prior content, which
   accidentally made every loop prompt self-contained.
3. ⚠️→SM-1 item **the ~18¢ base invocation cost likely includes loading the
   operator's full interactive config (MCP servers etc.)** — SM-1 verifies an
   isolated/slim configuration for subprocess calls and re-measures.
4. ⚠️→SM-3 caveat **canonical-notebook corpus parity is unverifiable without
   auth** (and auth is never happening per -b). Accepted residual, evidence
   documented (orchestrator.py:954 docstring intent + foundations README).
5. ⚠️→SM-0 item **pin `notebooklm-py`'s exact working version from the
   committed Windows venv's dist-info BEFORE SM-6 purges it** — the venv is
   currently the only record of the known-good dependency set.

**Fresh-context adversarial reviewer (2026-07-02, second launch — first was
killed by a session interrupt):** verdict **EXECUTE-WITH-REVISIONS**, no
BLOCK-level finding. Rollback story, cost arithmetic (33¢/stroke, $1.32/run
re-derived ✓), Powell replay basis (`Powell_Cleanroom/03_Truth_Packets.md`,
4 verbatim fenced packets, 13,176 chars + the null-test parser at
`scripts/powell_bridge_null_test.py:40-70`), and SM-7 viability all HELD
under attack. Revisions required and applied in this revision (-c):

1. REFUTED (narrow): `parse_triage_hit_list` is a **fifth** load-bearing
   parser (silent blueprint-only degradation on marker miss) → § 3 + SM-1
   conformance tests.
2. Startup is not dormant as drafted — `main.py:181-225` initialize() +
   default-ON `auto_relogin` (auth_check.py:555-563) spawns a login attempt
   per boot → SM-0 `.env.example` (`GANYMEDE_AUTO_RELOGIN=0`) + SM-2
   substrate-gated startup.
3. SM-2 seam list missed the inline `query_chess_engine` at
   orchestrator.py:1886 (run_universal_loop Phase 1) → added; legacy
   `/api/orchestrate` (main.py:425) marked dormant.
4. SM-0 requirements were missing `websockets` (WS event stream dies
   silently under plain uvicorn) + `python-dotenv` (.env silently skipped)
   → added; python3.12 for venv_312 parity (3.11 fallback documented).
5. Minor: `StrokeResult` gains three fields not one (cost_usd, substrate,
   model_id — R3 observability); AuthPill dormant-state label (SM-4);
   reference-file nit (Z-SPAN's text-mode synthesizer vs stream-json
   metering wrapper are two files — plan knowingly merges both patterns).

Reviewer also **resolved the corpus-parity residual affirmatively**:
`docs/foundations/README.md:43,51` documents the canonical Engine notebook
as grounded-in-this-corpus and reconstructable-from-these-files. The
residual shrinks to post-import operator drift only.

**Verdict recorded: EXECUTE. SM-0 begins.**
