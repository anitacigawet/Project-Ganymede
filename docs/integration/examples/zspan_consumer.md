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

This doc is the reference write-up of how Z-SPAN's Claude session consumes the Ganymede v2 API. If you're building a similar long-running strategic-planning consumer, this is the concrete picture; for the abstract API surface read [`../consuming_the_v2_api.md`](../consuming_the_v2_api.md). For why Z-SPAN is the named Pl2 consumer at all (the 2026-06-06 Cube-of-Space pattern-recognition validation event), read [milestone 43](../../history/Architecture_History.md).

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
3. **Calls Ganymede's v2 API directly via HTTP** (curl, Python requests, or `WebFetch`-style tool calls — whatever the session has available).
4. **Reads the result** and translates it for whatever Z-SPAN audience the operator is targeting (open-source contributors, civic-tech advocates, sympathetic municipal staff, funders).
5. **Persists artifacts** into Z-SPAN's repo (positioning docs, decision-log entries, case studies).
6. **Resumes later** — strategic decisions span weeks. Pl2-01 [persistent session state](../../history/Architecture_History.md) (milestone 46) is the surface that makes this work.

There's no embedded "Ganymede panel" in Z-SPAN's frontend. There's no tRPC adapter. Z-SPAN's session reads this doc, hits the API, writes the artifacts. The operator courier-protocol covers cross-session communication when something needs Ganymede-session attention.

## The hook point

There is no single code file — the hook is conceptual: **whenever Z-SPAN's session is reasoning about strategic positioning, competitive response, or terminology lock-in, it should consider whether the question is Ganymede-shaped and call the API instead of reasoning standalone.**

Ganymede-shaped means:

- The question has a **strategic-asymmetry structure** — somebody can see something somebody else can't (DAI asymmetry).
- There's a **named opponent or structural counterforce** the question is about (Granicus, CivicPlus, the legacy GovTech bundling pattern, an entrenched procurement workflow, etc.).
- The outcome is **falsifiable** at some horizon ("by Q3 we'll have N municipal adoptions" — cleanroom) OR there's a **specific wished-for state** ("Z-SPAN becomes the reference implementation for transparent municipal-data publishing" — genie).
- The question would benefit from **Bridge audit** — i.e., the standard "what's the obvious answer?" gives a mythology-laden symmetric narrative and Z-SPAN's session can sense there's a higher-dimensional move it's missing.

Examples that ARE Ganymede-shaped:

- *"Should Z-SPAN double down on 'Public Truth Ledger' terminology or pivot to 'Citizen-First Infrastructure'?"* → cleanroom pathway, with the Bridge as a check against framework's tendency toward symmetric Set/Horus framing.
- *"How should Z-SPAN respond to Granicus's likely defensive bundling move when civic-tech procurement RFPs start asking for open-data export?"* → genie pathway with `current_state` = current Z-SPAN posture + `wished_for_state` = positioning that forces Granicus into a closed-source counter-product.
- *"What's the non-obvious move a giant-slayer plays against an entrenched GovTech monopoly?"* → genie pathway (Giant-Slayer scenario shape).

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

In Ganymede vocabulary, that's typically:

- **Genie pathway** when Z-SPAN has a current state and wants a path to a wished-for state (positioning, terminology lock-in).
- **Cleanroom pathway** when the question is "will X happen by Y" (a specific falsifiable strategic-positioning question).
- **Iterative engine with Bridge enabled** (Bicameral Convergence Level 1, the default) for first-look; **Bicameral Convergence Level 2** (`/bicameral-loop`) when the first audit reveals friction worth resolving.
- **Operator Lens translation** post-synthesis, typically `plain_english` for civic-tech advocates or `executive_brief` for funder-facing summaries; `cube_of_space` register for aesthetic-leaning audiences (the milestone 43 transcript was already in that register).

## Mapping to the Ganymede API

### Pathway selection

| Z-SPAN question shape | Pathway | Scenario fields |
| --- | --- | --- |
| "Should Z-SPAN do X or Y?" — falsifiable | `cleanroom` | `question` |
| "How does Z-SPAN get from A (current) to B (wished)?" | `genie` | `current_state`, `wished_for_state` |
| "How does Z-SPAN design against Granicus to force them into X?" | `offensive` | `target` = Granicus posture; `objective_state` = the forced-move state |
| "Audit this Z-SPAN positioning argument for hidden weaknesses" | `mirror_audit` | `prior_resolution` = the argument text |

Most Z-SPAN questions are `genie` or `cleanroom`. `offensive` is the Architect-stance for designing strategic funnels against opponents; useful when Z-SPAN's session is reasoning about *forcing* an opponent into a structurally disadvantageous move. `mirror_audit` is useful for stress-testing a positioning doc the operator drafted before publishing.

### Truth Packets — Z-SPAN's typical set

Z-SPAN's session typically ships 3-5 packets per question:

1. **Competitive landscape packet** — Granicus / CivicPlus / OpenGov posture, pricing, lock-in mechanisms.
2. **Z-SPAN current state packet** — terminology, audience, features shipped, recent strategic decisions from the repo's decision log.
3. **Friction-point packet** — what's making the question pressing (the RFP cycle, the announcement, the funder pitch).
4. **Audience packet** (optional) — who is going to read or be persuaded by the output. Determines the Operator Lens register downstream.
5. **Constraint packet** (optional) — what Z-SPAN is unwilling to do (e.g., "Z-SPAN will not pursue municipal contracts with mandatory closed-source data residency clauses"). Keeps the Engine from suggesting moves the operator already vetoed.

### Iterative vs Bicameral Level 2 selection

The default Z-SPAN call is `POST /api/v2/sessions/{id}/iterate` with `iterative: true, max_strokes: 3, include_bridge: true`. That's three strokes (synthesis → Mirror Auditor → re-synthesis with both Auditor and Bridge friction) + one Bridge audit. Walltime: ~10-15 minutes; ~14-18 NotebookLM calls.

When that first run's Bridge audit surfaces friction worth iterating on (e.g., "this is a symmetric Set/Horus framing — there's an Incomprehensible Move available you're not surfacing"), escalate to `POST /api/v2/sessions/{id}/bicameral-loop` for a closed-loop Engine↔Bridge mirror-bounce until convergence. Walltime: ~10-30 minutes depending on iteration count; ~20-30 NotebookLM calls. Per [`docs/concepts/Bicameral_Convergence.md`](../../concepts/Bicameral_Convergence.md), this is the substrate that produces specific-instance predictions, not mechanism-category gestures.

Rule of thumb:

- **Single-pass `/synthesize`** — never. Z-SPAN questions are decision-grade; the Stroke 1 plausible-sounding output is operationally fragile.
- **`/iterate` Level 1** — default first call. Cheap and produces the audited resolution.
- **`/bicameral-loop` Level 2** — when Level 1's Bridge surfaces unresolved structural friction OR when the question is high-enough-stakes that closing the architectural gap (per [milestone 42](../../history/Architecture_History.md)) is worth the extra wall time.

### Operator Lens register selection

After any of the above, call `POST /api/v2/sessions/{id}/translate` per stroke for the register the audience needs.

| Z-SPAN audience | Register | Why |
| --- | --- | --- |
| Civic-tech advocates, sympathetic municipal staff | `plain_english` | Default. Strips DAI / SDS / ROEM jargon for non-framework readers. |
| Funders, board, decision-makers | `executive_brief` | 3-5 paragraph summary: bottom-line → mechanism → falsification risk → what-to-watch. |
| Aesthetic / mission-framing surfaces (manifestos, recruitment, conf talks) | `cube_of_space` | Geometric / spatial vocabulary. The register the milestone 43 transcript pioneered. |
| Internal repo decision-log entries | (none — keep technical) | Future-Claude needs the framework vocabulary for traceability. |

The `cleaned_response` field on each StrokeResult already strips trailing chatbot-CTAs (P1-03b) so the translated output stays clean.

## Concrete integration shape — a worked walkthrough

A real Z-SPAN-session interaction with Ganymede, end-to-end. Assume backend on `http://127.0.0.1:8000` with a healthy NotebookLM session.

### Step 1 — Health-check

```bash
curl -s http://127.0.0.1:8000/api/v2/health
```

```json
{
  "status": "healthy",
  "cooldown": { "calls_last_hour": 0, "calls_last_24h": 5, ... },
  "active_sessions": 0
}
```

If `cooldown.calls_last_hour` is approaching `hourly_cap` (20), defer the run; an iterate call fires ~14 calls.

### Step 2 — Create the session

```bash
curl -s -X POST http://127.0.0.1:8000/api/v2/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": {
      "current_state": "Z-SPAN is a pre-launch open-source municipal-meeting platform. Terminology in use: \"Public Truth Ledger.\" Audience targeted: civic-tech contributors + early-adopter municipalities. Feature surface: meeting ingestion, transcript search, decision-log export. Funding stage: pre-seed, operator-funded.",
      "wished_for_state": "Z-SPAN is the canonical reference implementation for transparent municipal-meeting data, positioned such that legacy closed-source vendors (Granicus etc.) must either match its openness or visibly abandon municipal accountability as a category.",
      "dream_state": true
    },
    "pathway": "genie",
    "iterative": true,
    "max_strokes": 3
  }'
```

Returns `{ session_id, state }`. Capture `session_id` — Pl2-01 persistence means you can come back to this session days later.

### Step 3 — Run the iterative loop with Bridge

```bash
SESSION_ID="<the uuid from step 2>"
curl -s -X POST http://127.0.0.1:8000/api/v2/sessions/${SESSION_ID}/iterate \
  -H "Content-Type: application/json" \
  -d '{
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
        "content": "Two upcoming RFP cycles in the operator's target municipalities mention \"open data export\" as a procurement requirement for the first time. Granicus is expected to respond either with a closed-source bulk-export gateway (delayed, $$$) or a deflection move (e.g., claim existing API is sufficient). Z-SPAN has the opportunity to set the procurement-standard language before Granicus's response lands.",
        "source_label": "Operator municipal-procurement watch list 2026-06"
      }
    ],
    "include_bridge": true
  }'
```

Returns when the loop terminates (~10-15 min). Body: `{ strokes: [StrokeResult, StrokeResult, StrokeResult], state }` — Stroke 1 (synthesis), Stroke 2 (Mirror Auditor), Stroke 2b (Connection Bridge), Stroke 3 (re-synthesis with both audits as friction).

The natural reading order is `state.has_final_resolution` → `strokes[3].cleaned_response ?? strokes[3].raw_response` for the audited final, then back-skim the Mirror Auditor (`strokes[1].audit_findings`) and Bridge (`strokes[2].raw_response`) to see what frictions Stroke 3 had to address.

### Step 4 — Translate for the audience

```bash
curl -s -X POST http://127.0.0.1:8000/api/v2/sessions/${SESSION_ID}/translate \
  -H "Content-Type: application/json" \
  -d '{ "stroke_number": 3, "register": "executive_brief" }'
```

```json
{
  "stroke_number": 3,
  "register": "executive_brief",
  "translated_text": "...3-5 paragraph executive-brief version of the audited final...",
  "source_length": 4821,
  "translated_length": 1247
}
```

Wall time ~30-50s (one cooldown-gated Engine call, per milestone 45 — the translation routes through the canonical NotebookLM Engine, not Gemini Flash, to preserve the closed-RAG-sphere principle).

If the Stroke 3 will land in multiple audiences, fire `/translate` once per register; the translations are cached on the session and surfaced together via `GET /sessions/{id}/strokes`.

### Step 5 — Complete the session

```bash
curl -s -X POST http://127.0.0.1:8000/api/v2/sessions/${SESSION_ID}/complete
```

`/complete` is idempotent. Returns the `FinalResolution` with all strokes and the canonical `final_text`. The session is now terminal (`status: complete`) and persisted in the SessionStore — it survives backend restart.

### Step 6 — File the artifact in Z-SPAN's repo

Z-SPAN's session writes a decision-log entry referencing the `session_id` so future runs can call back to this conversation's reasoning. Recommended naming: `decisions/D-NNN-<short-slug>.md` with the Ganymede `session_id` recorded in a frontmatter field for the courier-protocol use case.

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
    },
    ...
  ],
  "total": 12,
  "limit": 20,
  "offset": 0
}
```

Filters: `status`, `pathway`, `q` (substring over scenario JSON + final_text), `limit` (1-200), `offset`. Returns the full `Scenario` per row + 200-char `final_text_preview` so the session can pick relevant prior runs without per-row detail fetches.

### Resuming a prior session's context

`GET /api/v2/sessions/{id}` returns the lightweight state; `GET /api/v2/sessions/{id}/strokes` returns the full strokes + Operator Lens translations:

```bash
curl -s "http://127.0.0.1:8000/api/v2/sessions/5263e33a-.../strokes"
```

```json
{
  "session_id": "5263e33a-...",
  "strokes": [
    { "stroke_number": 1, "raw_response": "...", ... },
    { "stroke_number": 2, "audit_findings": [...], ... },
    { "stroke_number": 3, "final_resolution": "...", "cleaned_response": "...", ... }
  ],
  "translations": {
    "3:executive_brief": "...",
    "3:plain_english": "..."
  }
}
```

Z-SPAN's session reads the prior strokes back, decides whether to extend (typically by creating a *new* session whose scenario references the prior session_id in a Truth Packet), and proceeds.

### The "build on prior strokes" pattern

Pl2-01 makes prior sessions browseable. For the actual "extend a prior session's reasoning forward" semantic, the current pattern is:

1. Read the prior session's Stroke 3 final resolution via `GET /sessions/{id}/strokes`.
2. Create a NEW session for the follow-up question.
3. Include a Truth Packet whose `content` quotes or summarizes the prior session's resolution + `source_label` references the prior session_id.

This is intentionally manual — folding prior-session context into a new session via Truth Packets keeps the substrate explicit and auditable. A future Pl2-02-or-later chunk may add an orchestrator-level `parent_session_id` mechanism that does the inheritance automatically; out of scope for Pl2-01.

## Courier-protocol usage

When something happens during a Z-SPAN call that needs Ganymede-session attention — unexpected API output, framework misclassification, ambiguous result, feature gap, persistent-session-state confusion — Z-SPAN's session writes a courier doc.

Save as: `Z-SPAN_to_Ganymede__<short-topic-slug>__<YYYY-MM-DD>.md` in the operator's `C:\Users\james\Documents\Ganymede_Courier\` folder (or equivalent).

Use it for:

- API call returned unexpected output (wrong shape, missing field, error envelope).
- Framework analysis contradicts what Z-SPAN already knows is true (potential framework misclassification worth surfacing to Ganymede's session).
- Strategic-output critique — the Stroke 3 read flat or symmetric-narrative-y; what's the underlying issue?
- Feature gap — Z-SPAN needed something Ganymede doesn't expose.
- Persistent-session state issue — session can't be resumed, prior strokes missing, list endpoint returns unexpected results.
- Clarification on framework primitives in the context of Z-SPAN's scenario.

Don't use it for:

- Trivial usage questions answerable by re-reading this doc or [`../consuming_the_v2_api.md`](../consuming_the_v2_api.md).
- Backend-up/down probes (the operator verifies).

Full templates + the courier procedure are at [`../operator_courier_protocol.md`](../operator_courier_protocol.md).

## What this case taught the general API design

Z-SPAN as Pl2 first consumer surfaced (or pressure-tested) several principles that should generalize to future consumers:

- **Some consumers are sessions, not apps.** PrisonBreak embeds Ganymede in a running web app; Z-SPAN's session calls it as a CLI/HTTP tool. The v2 API has to be ergonomic from both shapes. Pl2-01's persistent-session-state surface is the difference between "Z-SPAN comes back to a prior conversation" and "the prior conversation has to be reconstructed from screenshots / scrapings."
- **Operator-curated Truth Packets are first-class.** PrisonBreak's RAG-derived packets are one valid shape; Z-SPAN's inline-drafted packets are another. Ganymede doesn't enforce a particular grounding mechanism — what it enforces is the Zero-Degradation rule (the orchestrator never modifies packet content) so the consumer's grounding intent gets to the Engine intact.
- **The Operator Lens (Pl3) is load-bearing for non-framework-native audiences.** Z-SPAN's audiences are mostly civic-tech advocates, municipal IT, funders — none of whom natively speak DAI / SDS / ROEM / Strategic Lasso. The translation surface (per milestone 45) is what makes the framework's output actually useful for advocacy work. Future consumers with non-framework-native audiences should plan on calling `/translate` per stroke that lands in those audiences.
- **Bicameral Convergence Level 2 (`/bicameral-loop`) is the right escalation when Level 1's Bridge surfaces friction.** Don't burn a long `/iterate` run + then escalate "manually" by re-running with `include_bridge=true` (default already does that). Escalate by hitting `/bicameral-loop` when the first run's Bridge audit names structural friction Level 1's re-synthesis didn't fully resolve.
- **Persistent session state should be the default, not the exception.** Long-running strategic-planning consumers can't tolerate a registry that loses everything on backend restart. Pl2-01 (milestone 46) made persistence opt-out via `GANYMEDE_DISABLE_SESSION_PERSISTENCE=1`. The default is "sessions persist."
- **Closed-RAG-sphere discipline is non-negotiable.** Z-SPAN's session must NOT bypass the Engine / Auditor / Bridge personas and call Gemini directly for analytical work — Pl3's mid-flight correction (commit `2e0a699`) is the canonical instance of why. Gemini Flash is scoped to dispatcher intent classification ONLY. Analytical content flows through the closed RAG sphere; everything else is a contamination risk.

## Relationship to Z-SPAN's own decision-log

Z-SPAN's repo maintains its own decisions log (`decisions/D-NNN-*.md` style — see Z-SPAN repo for the canonical format). When a Ganymede call produces a load-bearing strategic decision, the natural flow is:

1. Ganymede session runs to completion + the operator approves the output.
2. Z-SPAN's session drafts a decision-log entry that quotes the load-bearing claims, names the Strategic Lasso + Incomprehensible Move, and records the Ganymede `session_id` in frontmatter for traceability.
3. The decision-log entry lives in Z-SPAN's repo; the underlying Ganymede session lives in Ganymede's SessionStore. The two reference each other but neither is the source of truth for the other — the decision-log is the canonical Z-SPAN record; the Ganymede session is the canonical reasoning record.

Future-Z-SPAN-Claude reading a decision-log entry can pull the `session_id` and hit `GET /sessions/{id}/strokes` to get the full reasoning back. That's the cross-session memory pattern Pl2-01 enables.

## Cross-references

- [Architecture_History milestone 43](../../history/Architecture_History.md) — Z-SPAN pattern-recognition validation + Operator Lens primitive + Pl2 consumer pivot rationale.
- [Architecture_History milestone 46](../../history/Architecture_History.md) — Pl2-01 persistent session state design + verification.
- [`../consuming_the_v2_api.md`](../consuming_the_v2_api.md) — canonical v2 API surface reference. Read this for endpoint-by-endpoint detail.
- [`../operator_courier_protocol.md`](../operator_courier_protocol.md) — cross-session communication protocol when Z-SPAN's session needs Ganymede-session attention.
- [`./prisonbreak_consumer.md`](prisonbreak_consumer.md) — sibling example: the embedded-app consumer shape (contrast with Z-SPAN's session-as-consumer shape).
- [`../../concepts/Bicameral_Convergence.md`](../../concepts/Bicameral_Convergence.md) — Level 1 vs Level 2 selection rationale.
- Onboarding handoff for Z-SPAN's first session: `C:\Users\james\Desktop\Z-SPAN_Ganymede_Onboarding.md` (operator filesystem; not in repo).
