---
name: project-pl2-zspan-first-consumer
description: "Z-SPAN is Ganymede's named Pl2 first module consumer (replacing PrisonBreak, who's now planned second). Courier protocol live at docs/integration/operator_courier_protocol.md. NEW handoff doc at C:\\Users\\james\\Desktop\\Z-SPAN_Handoff_v2.md (2026-06-10 rewrite — replaces the earlier Onboarding doc that was too complex per James's actual handoff attempt). Pl2-01 persistence (46) + Pl2-02 consumer-spec doc (47) + Pl2-extension `/managed-run` endpoint (48) all shipped; only Pl2-03 first live session remains."
metadata: 
  node_type: memory
  type: project
  originSessionId: b1fabc43-1fa7-4ec9-b300-429b7b733143
---

Z-SPAN is the named Pl2 first module consumer per milestone 43 (2026-06-06). PrisonBreak is preserved as planned second consumer.

**Why Z-SPAN won the pivot:** the 2026-06-06 NotebookLM transcript exchange (the Cube-of-Space conversation) demonstrated that the framework's strategic-reasoning maps cleanly to Z-SPAN's competitive situation — open-source civic-data platform vs. legacy closed-source GovTech (Granicus etc.). Z-SPAN instantiates the Strategic Funnel + Asymmetric Perception Game pattern the framework formalizes. The framework correctly identified Z-SPAN's structural-pattern category from a generic prompt (Pl1 / fourth Ganymede validation event). Combined with Z-SPAN being James's most active project with live strategic decisions, Z-SPAN is a much better Pl2 fit than PrisonBreak's "digital public defender" hypothetical.

**Critical artifacts already in place:**

1. **NEW handoff doc at `C:\Users\james\Desktop\Z-SPAN_Handoff_v2.md`** (2026-06-10 rewrite) — single-paste-in onboarding for Z-SPAN's first message. Replaces the earlier `Z-SPAN_Ganymede_Onboarding.md` which proved too complex when James actually tried to use it. The v2 handoff uses the Theory-of-Mind framing for what Ganymede is (per the 2026-06-10 Gemini brainstorm; see [[project-public-release-deferred]]), names ONE HTTP call (`POST /api/v2/managed-run`) as the consumer surface, briefly covers persistence + courier protocol. ~200 lines. Tested-ready.

2. **Courier protocol at `docs/integration/operator_courier_protocol.md`** — the cross-session communication pattern. Z-SPAN's session writes `Z-SPAN_to_Ganymede__*.md` documents to flag issues / questions / feedback; James couriers them to Ganymede's session; Ganymede responds with `Ganymede_to_Z-SPAN__*.md`. Round-trip via two markdown documents. Includes full templates for both directions + operator courier procedure. Future-Claude on the Ganymede side: when an operator pastes a courier doc, respond as enterprise support — diagnose, propose resolution, file any follow-ups in TASKS.md or Architecture_History.md.

3. **Operator Lens (Pl3) shipped 2026-06-06** — Z-SPAN session will see translated outputs alongside technical. Three registers: `plain_english`, `cube_of_space`, `executive_brief`. Backed by the canonical Engine (NOT Gemini; see [[project-closed-rag-sphere-principle]]).

**Ganymede-side Pl2 prep work — all claude-autonomous chunks done:**

1. ~~**Persistent session state.**~~ ✅ **SHIPPED 2026-06-08 (milestone 46).** SQLite-backed `SessionStore` at `ganymede-backend/app/services/session_store.py`; `Session` and `SessionRegistry` wired for save-on-mutation + rehydrate-on-startup. New endpoints: `GET /api/v2/sessions` (paginated list with status/pathway/q filters) + `GET /api/v2/sessions/{id}/strokes`. Round-trip verified end-to-end via TestClient lifecycle.

2. ~~**`docs/integration/examples/zspan_consumer.md` integration spec.**~~ ✅ **SHIPPED 2026-06-08 (milestone 47); REWRITTEN 2026-06-10 (milestone 48).** First version taught Z-SPAN the granular API (pathway selection table, Truth Packet shape, iterate-vs-bicameral, register selection) and was too complex per James's actual handoff attempt. Rewritten version leads with `/managed-run` as primary; granular API preserved as fall-back for embedded-app consumers.

3. ~~**`POST /api/v2/managed-run` endpoint.**~~ ✅ **SHIPPED 2026-06-10 (milestone 48).** Single-call composition of dispatch → create → iterate-or-bicameral_loop → translate → complete. The recommended entry point for session-as-consumer projects. Consumer sends `scenario_text` (NL) + `truth_packets` + optional `register` / `depth`; gets back `session_id` + `pathway_chosen` + `final_text` + `translated_text` + `strokes`. Composition only — no new orchestrator logic; all primitives existed already.

4. **First live Z-SPAN strategic-planning session.** Operator-driven; requires Z-SPAN's session to produce a real positioning question + call `/managed-run` end-to-end. James pastes the `Z-SPAN_Handoff_v2.md` as Z-SPAN's first message. Run record at `docs/experiments/runs/Z-SPAN_First_Strategic_Session.md` + Architecture_History milestone (open). **PAUSED 2026-06-13** while Z-SPAN's own development cycle is busy. The Ganymede side has nothing left to build — pickup is gated on Z-SPAN's availability, not on Ganymede-side work. Higher leverage post-milestone-51 ([[project-structural-attractor-validation]]) because the framework's structural-attractor capability is exactly the consumer shape Z-SPAN's strategic-positioning questions need.

**Pl2 deliverables not blocking immediate Z-SPAN start:**

Z-SPAN's session can BEGIN reading + producing feedback without persistent sessions. The first wave of Z-SPAN-side work is reading the Project Ganymede repo, milestones 42-45, the framework primitives, and producing strategic-planning questions. Those don't require persistent sessions.

**The locked sequence at last operator direction (2026-06-06):**

P1-03b (CTA-suppression post-processor) → P1-04 (Bridge notebook lifecycle Option C) → Pl3 (Operator Lens) → Pl2 (Z-SPAN as first consumer) AT THE VERY END.

All of P1-03b / P1-04 / Pl3 shipped 2026-06-06 (commits `30f1121` / `b851986` / `1929586` + `2e0a699` correction). Pl2 is what remains. The sequence is operator-locked — don't reorder.

**Cross-references:**

- Architecture_History milestone 43 — Z-SPAN pattern recognition + Operator Lens primitive surfaced + Pl2 consumer pivot rationale
- Architecture_History milestone 44 — P1-04 Bridge notebook lifecycle
- Architecture_History milestone 45 — Pl3 Operator Lens (with mid-flight correction recorded)
- Handoff doc (current — 2026-06-10): `C:\Users\james\Desktop\Z-SPAN_Handoff_v2.md`. The earlier `Z-SPAN_Ganymede_Onboarding.md` was retired when James caught the cognitive-overload symptom during the actual handoff attempt; do NOT reference it as the canonical onboarding.
- Courier protocol spec: `docs/integration/operator_courier_protocol.md`
- ROADMAP.md § "Silo 4 — Pluggable" Pl2 deliverables
- Operator Lens canonical-Engine-backed implementation: `app/services/orchestrator.py:run_translation` + `TRANSLATION_PROMPT_TEMPLATES`
- Closed-sphere principle: [[project-closed-rag-sphere-principle]]
