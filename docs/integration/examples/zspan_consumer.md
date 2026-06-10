---
title: "Example: Z-SPAN"
type: "architecture-component"
status: "active"
tags: ["integration", "examples", "z-span", "pl2"]
color_id: "2"
---

# Example: Z-SPAN

**Status:** First Pl2 consumer per [Architecture_History milestone 43](../../history/Architecture_History.md). Z-SPAN's session reads this doc to know how to call Ganymede; the Ganymede backend exposes the surface this doc describes via the v2 API.

[Z-SPAN](https://github.com/anitacigawet/ZSPAN) is the operator's open-source civic-data primitive — a self-hostable platform that surfaces municipal-meeting transcripts, decisions, and agendas in a public-truth-ledger shape, competing structurally against legacy closed-source GovTech vendors (Granicus, CivicPlus, etc.). Z-SPAN uses Ganymede as a long-term strategic-planning module: terminology validation, competitive-positioning analysis, audience-facing narrative design, and high-stakes-decision audit.

This doc is the reference write-up of how Z-SPAN's Claude session consumes the Ganymede v2 API. **As of milestone 48 (2026-06-10), the recommended integration is one HTTP call to `/api/v2/managed-run`** — Ganymede internally handles pathway classification, multi-stroke orchestration, translation, and session completion. The earlier walkthrough that taught Z-SPAN the granular API surface is preserved at the bottom of this doc as the fine-grained-control fall-back.

If you're building a similar long-running strategic-planning consumer, this is the concrete picture. For the abstract API surface read [`../consuming_the_v2_api.md`](../consuming_the_v2_api.md). For why Z-SPAN is the named Pl2 consumer (the 2026-06-06 Cube-of-Space pattern-recognition validation event), read [milestone 43](../../history/Architecture_History.md).

## The model — consumer is a session, not an app

The PrisonBreak integration ([`prisonbreak_consumer.md`](prisonbreak_consumer.md)) is an *embedded app integration*: the consumer is a running web app that calls Ganymede via tRPC. Z-SPAN's integration is different in shape and the difference is load-bearing:

```
┌──────────────────────┐                ┌────────────────────────┐
│  Z-SPAN's Claude     │  HTTP/JSON     │  Ganymede backend      │
│  session             │ ─────────────► │  (FastAPI v2 API)      │
│  (interactive, with  │                │                        │
│   the operator)      │ ◄───────────── │  Engine + Auditor +    │
└──────┬───────────────┘                │  Bridge personas on    │
       │                                │  NotebookLM            │
       │ writes / reads                 └────────────────────────┘
       ▼
┌──────────────────────┐
│ Z-SPAN repo files    │
│ (decisions log,      │
│  positioning docs,   │
│  case studies)       │
└──────────────────────┘
```

Z-SPAN's session is the consumer. It:

1. **Drafts** a strategic-planning question with the operator (the operator pastes a competitive situation; the session articulates it as a Ganymede-shaped scenario).
2. **Constructs Truth Packets** inline — typically operator-curated findings drafted in the conversation, not pre-built from a RAG layer (Z-SPAN's repo doesn't have a closed-RAG layer like PrisonBreak's NotebookLM).
3. **Calls Ganymede's `/managed-run` endpoint via HTTP** (curl, Python requests, or `WebFetch`-style tool calls — whatever the session has available).
4. **Reads the result** — Ganymede returns a `translated_text` already audience-tuned to the chosen register.
5. **Persists artifacts** into Z-SPAN's repo (positioning docs, decision-log entries, case studies). The Ganymede `session_id` is captured in frontmatter for traceability.
6. **Resumes later** — strategic decisions span weeks. Pl2-01 [persistent session state](../../history/Architecture_History.md) (milestone 46) is the surface that makes this work.

There's no embedded "Ganymede panel" in Z-SPAN's frontend. There's no tRPC adapter. Z-SPAN's session reads this doc, makes one API call per strategic question, writes the artifacts. The operator courier-protocol covers cross-session communication when something needs Ganymede-session attention.

## The hook point

There is no single code file — the hook is conceptual: **whenever Z-SPAN's session is reasoning about strategic positioning, competitive response, or terminology lock-in, it should consider whether the question is Ganymede-shaped and call `/managed-run` instead of reasoning standalone.**

Ganymede-shaped means:

- The question has a **strategic-asymmetry structure** — somebody can see something somebody else can't (DAI asymmetry).
- There's a **named opponent or structural counterforce** the question is about (Granicus, CivicPlus, the legacy GovTech bundling pattern, an entrenched procurement workflow, etc.).
- The outcome is **falsifiable** at some horizon ("by Q3 we'll have N municipal adoptions") OR there's a **specific wished-for state** ("Z-SPAN becomes the reference implementation for transparent municipal-data publishing").
- The question would benefit from **Bridge audit** — i.e., the standard "what's the obvious answer?" gives a mythology-laden symmetric narrative and Z-SPAN's session can sense there's a higher-dimensional move it's missing.

Examples that ARE Ganymede-shaped:

- *"Should Z-SPAN double down on 'Public Truth Ledger' terminology or pivot to 'Citizen-First Infrastructure'?"*
- *"How should Z-SPAN respond to Granicus's likely defensive bundling move when civic-tech procurement RFPs start asking for open-data export?"*
- *"What's the non-obvious move a giant-slayer plays against an entrenched GovTech monopoly?"*

Examples that AREN'T:

- *"What font should Z-SPAN use on its landing page?"* — aesthetic preference, no strategic-asymmetry shape.
- *"Is this PR's test coverage adequate?"* — engineering question.
- *"What time should we ship the announcement?"* — operational timing, not structural.

## What Z-SPAN naturally provides

Unlike PrisonBreak (which has 5 wrongful-conviction error categories already harvested from NotebookLM per case), Z-SPAN's session arrives at the question with:

- **Competitive landscape context** — what Granicus / CivicPlus / OpenGov / etc. do, their pricing posture, their lock-in mechanisms. Drafted from the operator's market knowledge + Z-SPAN's repo's own positioning notes.
- **Z-SPAN's current strategic posture** — terminology in use, audience targeted, mechanical features shipped, decision-log entries from prior strategic calls.
- **The specific friction point** — what's making this question pressing now (an upcoming RFP cycle, a Granicus product announcement, a contributor coordination challenge, a funder pitch deck).

These are what Z-SPAN's session **manually drafts as Truth Packets** in the conversation with the operator. There's no automation harvesting them from a closed-RAG layer — the session writes them inline, the operator reviews, and they get sent to Ganymede as the `truth_packets[]` payload.

A typical Z-SPAN Truth Packet drafted this way:

```json
{
  "subject": "Granicus competitive posture (2026-06)",
  "content": "Granicus dominates the municipal-meeting platform space at ~3,500 customer governments; pricing is opaque (vendor-quoted, typically $15K-$80K/yr for mid-tier municipalities). Lock-in mechanisms: proprietary closed captions format, no bulk export API, custom HTML widgets that break if migrated. Recent product motion: acquired Granicus Engage 2024-Q4, adding constituent-engagement features upstream of meetings. Open-source replacement viability has not been demonstrated at scale.",
  "source_label": "Z-SPAN positioning doc 2026-05 + operator market-research notes"
}
```

The packet is **operator-curated, not RAG-harvested**. That's the typical Z-SPAN consumer shape and it's fine — Ganymede doesn't enforce a particular grounding mechanism, only that the packets carry source-cited claims the Engine can reason over.

## What Z-SPAN wants back

The deliverable shape Z-SPAN's session needs is shaped by the audience the operator is targeting:

- **Strategic positioning recommendation** — what move Z-SPAN should make (terminology choice, narrative framing, feature prioritization).
- **Strategic Lasso identification** — what structural vulnerability of the legacy GovTech monopoly the move exploits.
- **Incomprehensible Move surface** — what Z-SPAN can do that legacy vendors structurally cannot reply to (this is usually the open-source / public-data / verifiable-transparency move).
- **Translation into the audience's vocabulary** — Pl3 Operator Lens is heavily used. Z-SPAN audiences are mostly non-framework-native (civic-tech advocates, municipal IT staff, funders).
- **Decision-quality audit** — Bridge friction surfaces whether the recommendation is symmetric-narrative-bait or actually load-bearing.

## The simple path — `/managed-run`

One HTTP call. Ganymede internally classifies pathway, drives the multi-stroke audited loop, translates the audited final into the chosen register, persists the session. The consumer never has to learn pathway taxonomy, iterative-vs-Bicameral selection, register decision rules, or the `/complete` finalization step.

### Request

```bash
curl -s -X POST http://127.0.0.1:8000/api/v2/managed-run \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_text": "How should Z-SPAN position vs Granicus to force them into a closed-source counter-product that alienates the public when civic-tech RFPs start asking for open-data export?",
    "truth_packets": [
      {
        "subject": "Granicus competitive posture (2026-06)",
        "content": "Granicus dominates ~3,500 municipal customers; closed-source, vendor-quoted pricing ($15K-$80K/yr typical), proprietary captions format, no bulk export, custom HTML widgets that break on migration. Acquired Granicus Engage 2024-Q4. Open-source replacement viability not yet demonstrated at scale.",
        "source_label": "Z-SPAN positioning doc 2026-05 + operator market research"
      },
      {
        "subject": "Z-SPAN current posture (2026-06)",
        "content": "Pre-launch. Terminology: Public Truth Ledger. Audience: civic-tech contributors + early-adopter municipalities. Features: ingest, transcript search, decision-log export. Bulk-export-first design. Open-source license (TBD between AGPL and Apache-2.0).",
        "source_label": "Z-SPAN repo README + decisions log"
      },
      {
        "subject": "Friction — pending RFP cycle (2026-Q4)",
        "content": "Two upcoming RFP cycles in the operator target municipalities mention open data export as a procurement requirement for the first time. Granicus is expected to respond either with a closed-source bulk-export gateway (delayed, $$$) or a deflection move. Z-SPAN has the opportunity to set the procurement-standard language before Granicus response lands.",
        "source_label": "Operator municipal-procurement watch list 2026-06"
      }
    ],
    "register": "plain_english"
  }'
```

That's it. `register` defaults to `plain_english`; `depth` defaults to `iterate` (Bicameral Level 1).

### Response

```json
{
  "session_id": "5263e33a-...",
  "pathway_chosen": "genie",
  "dispatch_confidence": 0.92,
  "dispatch_rationale": "The text frames a current-state-to-wished-for-state path with a named opponent and a falsifiable horizon.",
  "clarifying_questions": [],
  "depth": "iterate",
  "register": "plain_english",
  "final_text": "<audited final in framework vocabulary — Strategic Lasso, Incomprehensible Move, ...>",
  "translated_text": "<the same audited final, re-expressed in plain English>",
  "strokes": [
    { "stroke_number": 1, "raw_response": "...", "final_resolution": "...", ... },
    { "stroke_number": 2, "audit_findings": ["..."], "audit_kind": "mirror_auditor", ... },
    { "stroke_number": 3, "raw_response": "...", "cleaned_response": "...", "final_resolution": "...", ... }
  ],
  "state": { "session_id": "...", "status": "complete", ... }
}
```

Read `translated_text` as the canonical "what to read to a human" artifact. `final_text` is the technical version preserving framework vocabulary — useful for audit traceability when filing decisions into Z-SPAN's repo decision-log. `strokes` carry the per-stage analytical history when you want to understand *why* the output is what it is.

`pathway_chosen` is the framework's classification of your question's strategic shape. If `dispatch_confidence` is low (< 0.5), check `clarifying_questions` and consider re-running with a refined `scenario_text`.

### Register selection

`register` is optional; default `plain_english`. Pick by audience:

| Z-SPAN audience | Register | Why |
| --- | --- | --- |
| Civic-tech advocates, sympathetic municipal staff | `plain_english` | Default. Strips DAI / SDS / ROEM jargon for non-framework readers. |
| Funders, board, decision-makers | `executive_brief` | 3-5 paragraph summary: bottom-line → mechanism → falsification risk → what-to-watch. |
| Aesthetic / mission-framing surfaces (manifestos, recruitment, conf talks) | `cube_of_space` | Visceral geometric vocabulary. The register the milestone 43 transcript pioneered. |
| Internal repo decision-log entries | (no translation) | Keep `final_text` for traceability — future-Claude needs the framework vocabulary. |

You can also re-translate any stroke later without re-running the whole loop:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v2/sessions/${SESSION_ID}/translate \
  -H "Content-Type: application/json" \
  -d '{ "stroke_number": 3, "register": "executive_brief" }'
```

### When to escalate to `depth=bicameral_loop`

Default `depth=iterate` handles the majority of Z-SPAN's questions cleanly: 4 strokes (Stroke 1 thesis → Mirror Auditor → Bridge → re-synthesis), ~10-15 min wall time, ~14-18 NotebookLM calls.

Escalate to `depth=bicameral_loop` (Bicameral Convergence Level 2) when:

- A first-pass `iterate` run's Bridge audit (Stroke 2b) surfaces structural friction that the re-synthesis didn't fully resolve — re-running with `bicameral_loop` lets the Engine ↔ Bridge mirror-bounce until convergence.
- The question is high-enough-stakes that closing the architectural gap (per [milestone 42](../../history/Architecture_History.md) — the gap that produced Anthropic-pause-call-as-mechanism-category but not the specific instance) is worth the extra wall time.

`bicameral_loop` wall time: ~10-30 min depending on iteration count. `max_iterations` defaults to 5 (configurable 1-10).

Rule of thumb: start with `iterate`. Only escalate when the Level 1 output reveals unresolved friction in the Bridge audit.

## Health-check before kicking off

```bash
curl -s http://127.0.0.1:8000/api/v2/health
```

If `cooldown.calls_last_hour` is approaching `hourly_cap` (20), defer — a `managed-run` fires ~14-18 calls.

NotebookLM auth probe:

```bash
curl -s "http://127.0.0.1:8000/api/v2/auth/status?force=true"
```

Should return `status: valid` + `client_initialized: true`. If not, hit `POST /api/v2/auth/auto-relogin` (or ask the operator to drive the AuthPill in the operator UI).

## Watching live progress (optional)

The session is created and persisted before the heavy strokes fire, so a WebSocket subscriber can attach immediately after `/managed-run` accepts the request:

```
ws://127.0.0.1:8000/api/v2/sessions/{session_id}/events/stream
```

Each message is a JSON `SessionEvent` (`type`, `stroke_number`, `payload`, `emitted_at`). The connection closes cleanly on the first terminal event (`session_complete`, `error`, `session_cancelled`). Useful when the operator wants stroke-by-stroke rendering as work happens; not required when the consumer is happy to wait for `/managed-run` to return the bundled result.

## The persistent-session pattern (Pl2-01)

Strategic decisions span weeks. Z-SPAN's session reasons about the Granicus question this week, ships the positioning piece, then comes back in three weeks when Granicus's response actually lands. The Pl2-01 persistence layer means that prior session is still browseable:

### Listing prior strategic sessions

```bash
curl -s "http://127.0.0.1:8000/api/v2/sessions?pathway=genie&limit=20"
```

```json
{
  "sessions": [
    {
      "session_id": "5263e33a-...",
      "status": "complete",
      "pathway": "genie",
      "created_at": "2026-06-08T18:42:14.123Z",
      "completed_at": "2026-06-08T18:55:38.456Z",
      "scenario": { "current_state": "...", "wished_for_state": "..." },
      "final_text_preview": "Position as open-source civic-data primitive that forces..."
    }
  ],
  "total": 12,
  "limit": 20,
  "offset": 0
}
```

Filters: `status`, `pathway`, `q` (substring over scenario JSON + final_text), `limit` (1-200), `offset`. Returns the full `Scenario` per row + 200-char `final_text_preview`.

### Resuming a prior session's context

```bash
curl -s "http://127.0.0.1:8000/api/v2/sessions/5263e33a-.../strokes"
```

Returns the full strokes + Operator Lens translations keyed by `{stroke_number}:{register}`.

### The "build on prior strokes" pattern

For "extend a prior session's reasoning forward":

1. Read the prior session's Stroke 3 final resolution via `GET /sessions/{id}/strokes`.
2. Call `/managed-run` for the follow-up question.
3. Include a Truth Packet whose `content` quotes or summarizes the prior session's resolution + `source_label` references the prior `session_id`.

This is intentionally manual — folding prior-session context into a new session via Truth Packets keeps the substrate explicit and auditable. A future chunk may add an orchestrator-level `parent_session_id` mechanism that does the inheritance automatically; out of scope for current Pl2 work.

## Courier-protocol usage

When something happens during a Z-SPAN call that needs Ganymede-session attention — unexpected API output, framework misclassification, ambiguous result, feature gap, persistent-session-state confusion — Z-SPAN's session writes a courier doc.

Save as: `Z-SPAN_to_Ganymede__<short-topic-slug>__<YYYY-MM-DD>.md` in the operator's `C:\Users\james\Documents\Ganymede_Courier\` folder (or equivalent).

Use it for:

- API call returned unexpected output (wrong shape, missing field, error envelope).
- Framework analysis contradicts what Z-SPAN already knows is true.
- Strategic-output critique — the Stroke 3 read flat or symmetric-narrative-y; what's the underlying issue?
- Feature gap — Z-SPAN needed something Ganymede doesn't expose.
- Persistent-session state issue — session can't be resumed, prior strokes missing.
- Clarification on framework primitives in the context of Z-SPAN's scenario.

Don't use it for:

- Trivial usage questions answerable by re-reading this doc or [`../consuming_the_v2_api.md`](../consuming_the_v2_api.md).
- Backend-up/down probes (the operator verifies).

Full templates + the courier procedure are at [`../operator_courier_protocol.md`](../operator_courier_protocol.md).

## If you need fine-grained control — the granular API

`/managed-run` composes five endpoints into one call. When Z-SPAN's session needs control over individual steps (rare), the granular API remains available:

| Step | Endpoint | What it does |
| --- | --- | --- |
| Classify intent | `POST /api/v2/dispatch` | Free-text → pathway + extracted scenario fields + confidence + clarifying questions. |
| Create session | `POST /api/v2/sessions` | Returns `session_id`. Pass `scenario` + `pathway` + `iterative: true` + `max_strokes: 3`. |
| Run the loop | `POST /api/v2/sessions/{id}/iterate` (Level 1) OR `POST /api/v2/sessions/{id}/bicameral-loop` (Level 2) | Multi-stroke audit + re-synthesis. Pass `truth_packets`. Blocks until loop terminates. |
| Translate | `POST /api/v2/sessions/{id}/translate` | Re-express a stroke in the chosen register. |
| Complete | `POST /api/v2/sessions/{id}/complete` | Idempotent finalize. Returns `FinalResolution`. |

When to use the granular API instead of `/managed-run`:

- You want to insert operator review between dispatch classification and the loop (e.g., display the dispatcher's pathway choice to a human for confirmation before burning ~15 min of NotebookLM calls).
- You're running a single synthesis stroke (`/synthesize` not `/iterate`) for a cheaper first-look pass — `/managed-run` is iterative-only.
- You want to use `/dispatch` for classification only, without running the loop at all.
- You're building an embedded-app integration (like PrisonBreak) that streams stroke-by-stroke progress to a UI and renders each stroke individually.

For most Z-SPAN questions, `/managed-run` is right. Reach for the granular API only when one of the above applies.

Endpoint-by-endpoint reference: [`../consuming_the_v2_api.md`](../consuming_the_v2_api.md).

## What this case taught the general API design

Z-SPAN as Pl2 first consumer surfaced (or pressure-tested) several principles that should generalize to future consumers:

- **Some consumers are sessions, not apps.** PrisonBreak embeds Ganymede in a running web app; Z-SPAN's session calls it as a CLI/HTTP tool. The v2 API has to be ergonomic from both shapes. Pl2-01's persistent-session-state surface and milestone 48's `/managed-run` endpoint together close the gap that made the session-as-consumer shape brittle in the original API design.
- **The dispatcher should be the canonical entry point for session-as-consumer projects, not just for human operators.** The original consumer-spec walkthrough (pre-milestone-48) taught Z-SPAN to learn pathway taxonomy, Truth Packet shape, iterate-vs-bicameral escalation, and register selection. That's framework-internal vocabulary leaking onto the consumer's cognitive surface. The dispatcher already abstracts pathway choice for human operators via DispatcherPanel; programmatic consumers deserve the same abstraction. `/managed-run` provides it.
- **Operator-curated Truth Packets are first-class.** PrisonBreak's RAG-derived packets are one valid shape; Z-SPAN's inline-drafted packets are another. Ganymede doesn't enforce a particular grounding mechanism — what it enforces is the Zero-Degradation rule (the orchestrator never modifies packet content) so the consumer's grounding intent gets to the Engine intact.
- **The Operator Lens (Pl3) is load-bearing for non-framework-native audiences.** Z-SPAN's audiences are mostly civic-tech advocates, municipal IT, funders — none of whom natively speak DAI / SDS / ROEM / Strategic Lasso. The translation surface (per milestone 45) is what makes the framework's output actually useful for advocacy work.
- **Bicameral Convergence Level 2 (`depth=bicameral_loop`) is the right escalation when Level 1's Bridge surfaces friction.** Don't burn a long `iterate` run + then escalate "manually." Escalate by re-running with `depth=bicameral_loop` when the first run's Bridge audit names structural friction Level 1's re-synthesis didn't fully resolve.
- **Persistent session state should be the default, not the exception.** Long-running strategic-planning consumers can't tolerate a registry that loses everything on backend restart. Pl2-01 (milestone 46) made persistence opt-out via `GANYMEDE_DISABLE_SESSION_PERSISTENCE=1`. The default is "sessions persist."
- **Closed-RAG-sphere discipline is non-negotiable.** Z-SPAN's session must NOT bypass the Engine / Auditor / Bridge personas and call Gemini directly for analytical work — Pl3's mid-flight correction (commit `2e0a699`) is the canonical instance of why. Gemini Flash is scoped to dispatcher intent classification ONLY (which is exactly what `/managed-run` uses it for internally — and only that). Analytical content flows through the closed RAG sphere; everything else is a contamination risk.

## Relationship to Z-SPAN's own decision-log

Z-SPAN's repo maintains its own decisions log (`decisions/D-NNN-*.md` style). When a Ganymede call produces a load-bearing strategic decision, the natural flow is:

1. `/managed-run` returns + operator approves the output.
2. Z-SPAN's session drafts a decision-log entry that quotes the load-bearing claims, names the Strategic Lasso + Incomprehensible Move (from `final_text`, since the decision-log audience is future-Z-SPAN-Claude which needs framework vocabulary for traceability), and records the Ganymede `session_id` in frontmatter.
3. The decision-log entry lives in Z-SPAN's repo; the underlying Ganymede session lives in Ganymede's SessionStore. The two reference each other but neither is the source of truth for the other — the decision-log is the canonical Z-SPAN record; the Ganymede session is the canonical reasoning record.

Future-Z-SPAN-Claude reading a decision-log entry can pull the `session_id` and hit `GET /sessions/{id}/strokes` to get the full reasoning back. That's the cross-session memory pattern Pl2-01 + `/managed-run` together enable.

## Cross-references

- [Architecture_History milestone 43](../../history/Architecture_History.md) — Z-SPAN pattern-recognition validation + Operator Lens primitive + Pl2 consumer pivot rationale.
- [Architecture_History milestone 46](../../history/Architecture_History.md) — Pl2-01 persistent session state design + verification.
- [Architecture_History milestone 48](../../history/Architecture_History.md) — `/managed-run` endpoint design + the dispatcher-as-canonical-entry-point architectural call.
- [`../consuming_the_v2_api.md`](../consuming_the_v2_api.md) — canonical v2 API surface reference. Read this when you need endpoint-by-endpoint detail.
- [`../operator_courier_protocol.md`](../operator_courier_protocol.md) — cross-session communication protocol when Z-SPAN's session needs Ganymede-session attention.
- [`./prisonbreak_consumer.md`](prisonbreak_consumer.md) — sibling example: the embedded-app consumer shape (contrast with Z-SPAN's session-as-consumer shape).
- [`../../concepts/Bicameral_Convergence.md`](../../concepts/Bicameral_Convergence.md) — Level 1 vs Level 2 selection rationale.
- Operator-facing handoff for Z-SPAN's first session: `C:\Users\james\Desktop\Z-SPAN_Handoff_v2.md` (operator filesystem; not in repo).
