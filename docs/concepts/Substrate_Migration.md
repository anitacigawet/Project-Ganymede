---
title: "Substrate Migration — NotebookLM → Sonnet + Qdrant (Hybrid)"
type: "concept"
status: "active"
tags: ["architecture", "substrate", "migration", "qdrant", "sonnet", "fable-audit"]
color_id: "6"
---

# Substrate Migration — NotebookLM → Sonnet + Qdrant (Hybrid)

> **Status:** Plan drafted 2026-07-02 (Fable 5 session, post-audit-#1). Pending
> audit #2 (adversarial plan review) before execution. Operator authorization:
> James 2026-07-02 — hybrid substrate, Sonnet generator, "take the wheel."
>
> **One-sentence shape:** the analytical strokes (Engine / Mirror Auditor /
> Connection Bridge / Operator Lens) move from NotebookLM notebooks to
> Sonnet via headless `claude -p` with the full 9D foundations corpus carried
> in-context; NotebookLM survives **only** as the PKI Oracle Deep Research
> harvester; a Qdrant node on the operator's Surface Pro (same architecture as
> Z-SPAN's `surfacepro_rag_node`, separate service + collections) becomes the
> accumulating Truth-Packet library and session-history search layer.

## 1. Decision provenance

| Decision | By | When |
|---|---|---|
| Remove NotebookLM from analytical strokes; keep for Oracle harvest only (hybrid) | James | 2026-07-02 |
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
                        │     └─ NotebookLM service (harvest-scoped):       │
                        │          PKI Oracle create → Deep Research →      │
                        │          import → hash-cited Truth Packet         │
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
  the orchestrator already does — `_count_bridges_in_audit` (regex on
  `Bridge N (STRUCTURAL|IMPLIED)`), `_parse_audit_findings` (numbered fault
  categories), `_extract_final_resolution_section` (FINAL RESOLUTION header),
  `_strip_trailing_cta`. SM-1 ships regex-conformance tests that fire real
  strokes and assert the parsers extract non-empty structure.

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
Create `ganymede-backend/venv_mac` on python3.11; derive + check in
`requirements.txt` (fastapi, uvicorn, pydantic, httpx, notebooklm(-py),
google-genai — verified against imports); backend boots headless with
NotebookLM init degraded (main.py already degrades per milestone 46);
`GET /api/health` green; TestClient smoke for sessions endpoints.
**Done:** health + sessions endpoints respond on :8000 without NotebookLM auth.

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
`run_bicameral_loop`, `synthesize`, `triage` (triage stays Engine-persona —
same substrate seam). Sonnet path skips: bridge-notebook provisioning
(stateless Bridge), injection budgets + truncation (full-fidelity injection),
cooldown gate. NotebookLM path untouched. PDF→md extraction lands.
**Done:** `GANYMEDE_SUBSTRATE=sonnet` runs the full iterative loop end-to-end
on a toy scenario with zero NotebookLM calls; `=notebooklm` still compiles the
old path (execution untested until SM-3's auth).

**SM-3 · Side-by-side validation window (F3) — the one-time experiment**
⛔ *Operator gate: `notebooklm login` on this Mac (first time on this
machine); NotebookLM quota spend (~8-12 Engine/Auditor/Bridge calls total,
explicitly authorized by this plan).*
Replay with **recorded packets** (no new harvests): Powell (P1-02 record) and
LMArena Run 7 (session `de892dc9…` / run record) — identical packets → both
substrates → structured diff: FINAL RESOLUTION agreement, dimensional
coverage, sphere behavior (notice presence, out-of-sphere claims), jargon
register, output-shape parser compatibility, length, wall time, cost.
Product: `docs/experiments/runs/Substrate_SideBySide.md` + a
methodology_questions Q2 (locus-of-intelligence) update — first
same-corpus-different-base-model data the project has ever had.
**Done:** diff report exists; go/no-go call on cutover recorded in it.

**SM-4 · Cutover + constitution rewrite**
Default `GANYMEDE_SUBSTRATE=sonnet`. NotebookLM analytical path stays
code-present (pause-not-delete; rollback = flip the env). Docs:
OVERVIEW hard-guardrails rewrite (#1-#3 harvest-scoped; new: corpus-in-git
integrity, persona constants as canon, explicit model pinning, node-token
handling), `docs/concepts/Closed_RAG_Sphere.md` written (F9 — physics→policy
+ the dangling Run-7 link fixed), CLAUDE.md/ROADMAP/TASKS sweep, UI
provenance labels, Architecture_History **milestone 52**.
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

Sequencing: SM-0 → SM-1 → SM-2 → SM-3 → SM-4 → SM-5 → SM-6, with SM-5
parallel-eligible after SM-1 (its Mac-side client doesn't depend on cutover).

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
Deep-Research replacement (F12's `claude -p`+WebSearch idea stays parked); no
multi-tenant/auth work on the node beyond bearer token.

## 10. Audit #2 log

*(Filled after the adversarial plan review; execution does not start until
this section records the verdict.)*
