---
title: "Example: PrisonBreak"
type: "architecture-component"
status: "active"
tags: ["integration", "examples"]
color_id: "2"
---

# Example: PrisonBreak

**Status:** Built and shipped. Lives on PrisonBreak's `master` branch.

[PrisonBreak](https://github.com/anitacigawet/PrisonBreak) is a self-hosted, local-first "digital public defender" that runs source-grounded NotebookLM analysis over uploaded criminal-case documents to surface potentially overturn-able convictions for attorney review. The Simulate tab on each case-detail page calls Ganymede's v2 API to produce strategic legal analysis — discovery requests, motion strategies, theory-of-the-case branches — grounded in the per-case errors PrisonBreak has already surfaced.

This doc is a reference write-up of *how* PrisonBreak consumes the Ganymede API. If you're building a new consumer, read this for a concrete picture of what the integration looks like in real code; then consult [`../consuming_the_v2_api.md`](../consuming_the_v2_api.md) for the surface-level reference.

## The hook point

`PrisonBreak/client/src/components/SimulatePanel.tsx`

Rendered on the case-detail page under the "Simulate" tab. The button reads *"Run Strategic Simulation (9D Chess)"*. Toggle next to it: *"Iterative Engine (3-stroke loop)"*.

PrisonBreak frames the boundary in its own UI copy:

> *"The descriptive analysis you've seen so far comes from NotebookLM, which is grounded in your case documents and refuses to speculate. Strategic legal analysis — 'what's the strongest argument,' 'what would a defense attorney do next,' simulated theory-of-the-case trees — is performed by a separate engine called 9D Chess."*

That phrasing is the integration spec, written by the consumer in advance of the producer being ready. Ganymede's job is to provide the API the panel expects.

## What PrisonBreak naturally has to give Ganymede

PrisonBreak's case lifecycle has already produced rich, source-grounded structured data by the time the user clicks Simulate:

- **Case-level facts.** Defendant, charges, conviction status, jurisdiction, document set.
- **NotebookLM-derived findings** across the 5 wrongful-conviction error categories:
  - **EM** Eyewitness Misidentification
  - **MF** Misapplied Forensics
  - **FC** False Confessions
  - **OM** Official Misconduct
  - **ID** Inadequate Defense
- **Per-finding metadata**: severity (1–5), confidence, supporting evidence cites, legal basis.
- **NotebookLM grounding chain.** Every finding traces back to specific document chunks via NotebookLM's source-citation links.

This is exactly what Ganymede's v2 API needs as `truth_packets[]` input. PrisonBreak has already done the closed-RAG harvest; Ganymede synthesizes directly off PrisonBreak's already-grounded findings without spinning up new Oracles. **This is the cleanest possible integration shape — and it generalizes: any consumer with its own grounded RAG layer should follow the same pattern.**

## What PrisonBreak wants back

The SimulatePanel copy specifies the deliverable shape:

> *"Generate strategic options grounded in the findings the rest of the app has surfaced — discovery requests, motion strategies, plea-stage analysis, theory-of-the-case branching."*
>
> *"Outputs are designed for an attorney to evaluate, not consume directly."*

In Ganymede terms, that's:

- **Genie pathway** — `current_state` = the case as it stands (charges + findings + posture); `wished_for_state` = a fixed text about identifying the strongest motion the prosecution isn't structurally defending against.
- **Strategic Lasso** = the prosecution's structural vulnerability.
- **Incomprehensible Move** = the non-obvious motion the prosecution isn't defending.
- **Iterative Engine** for high-stakes cases — Stroke 2 has the Mirror Auditor stress-test Stroke 1 ("rigidity errors, pattern-matching, confidence-evidence gaps, dimensional greeds"); Stroke 3 produces a re-synthesized resolution that survives the audit.

## Concrete integration shape

### 1. PrisonBreak side — backend

A single tRPC procedure under the `cases` namespace:

```typescript
// server/ganymede/router.ts
runStrategicSimulation: publicProcedure
  .input(z.object({
    caseId: z.number(),
    iterative: z.boolean().default(false),
  }))
  .mutation(async ({ input }) => {
    // Health-check Ganymede first — useful error if backend is down
    await ganymede.health();

    // Map case + errors into a Genie-shape scenario + truth packets
    const { current_state, truthPackets } = await assembleStrategicContext(input.caseId);

    // Create a Ganymede session
    const session = await ganymede.createSession({
      scenario: { current_state, wished_for_state: DEFAULT_WISHED_FOR_STATE },
      pathway: "genie",
      iterative: input.iterative,
      max_strokes: input.iterative ? 3 : 1,
    });

    // Persist a local row for tracking
    const { id: simulationId } = await simDb.createSimulation({ ... });

    // Spawn background runner — returns immediately to the UI
    void runSimulation({ simulationId, caseId, ganymedeSessionId: session.session_id, ...});

    return { simulationId, ganymedeSessionId: session.session_id };
  });
```

The runner (`server/ganymede/runner.ts`) drives Ganymede's `/iterate` (or `/synthesize` for single-pass) and concurrently polls `/events` every 2 seconds, forwarding new SessionEvents to PrisonBreak's existing socket.io infrastructure under event names `ganymede-event` / `ganymede-complete` / `ganymede-error` on the `case-{caseId}` room. Polling instead of WebSocket-to-WebSocket bridging keeps the dependency surface small.

### 2. PrisonBreak side — frontend

`SimulatePanel.tsx`:

- Subscribes to socket.io `ganymede-*` events on the case room.
- Click "Run" → calls `cases.runStrategicSimulation`.
- Renders strokes as they arrive. Each stroke shows the Strategic Lasso, Incomprehensible Move, and full Resolution text in expandable cards.
- For iterative runs, the Mirror Auditor's Stroke 2 shows the four enumerated fault categories.
- Final state persists to `strategicSimulations` (SQLite) and re-renders on page reload.

### 3. PrisonBreak side — schema

One new table:

```sql
CREATE TABLE strategicSimulations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  caseId INTEGER NOT NULL,
  ganymedeSessionId TEXT NOT NULL,
  pathway TEXT NOT NULL DEFAULT 'genie',
  iterative INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',  -- pending|running|completed|error
  finalText TEXT,
  strokesJson TEXT,                         -- full StrokeResult[] verbatim
  errorMessage TEXT,
  startedAt INTEGER,
  completedAt INTEGER,
  createdAt INTEGER NOT NULL DEFAULT (unixepoch()),
  updatedAt INTEGER NOT NULL DEFAULT (unixepoch())
);
```

PrisonBreak persists Ganymede's stroke history verbatim so the panel can re-render the full breakdown on reload without a Ganymede round-trip.

### 4. Ganymede side — what was needed

PrisonBreak's needs drove the shape of the v2 API. Specifically:

- ✅ Session abstraction (multi-call run state)
- ✅ WebSocket event stream
- ✅ Pre-harvested Truth Packet ingestion path (skips Oracle creation entirely)
- ✅ Iterative Engine multi-stroke encoded as a single `/iterate` HTTP call
- 🟢 Out of scope for v1: Oracle approval gate (PrisonBreak doesn't need Oracle creation)
- 🟢 Out of scope for v1: full Mirror Validation pathway (PrisonBreak uses the audit-as-Stroke-2 shape internal to `/iterate`)

## What this case taught the general API design

A few principles fall out of the PrisonBreak case that should generalize to any future consumer:

- **Pre-harvested Truth Packets are the *common* integration shape, not the exotic one.** Any consumer that already has its own document-grounded RAG (NotebookLM, Pinecone, embedded vectors, anything) will *not* want Ganymede creating fresh notebooks for it. The general API treats "synthesize-from-pre-harvested" as a first-class path, not an edge case.
- **Iterative Engine multi-stroke is the killer feature for consumers.** A single-pass Stroke-1 output is plausible-sounding but operationally fragile. The Stroke 2 self-stress-test is what produces decision-grade output. Consumer integrations should expose iterative prominently.
- **WebSocket-style streaming is the right transport.** Multi-stroke runs take minutes per stroke. The consumer's UI should show progress as it happens — both for UX reasons and because a 10-minute "loading…" with no signal is unacceptable.
- **Pathway choice is mostly a prompt-selection issue.** Cleanroom / Genie / Offensive are the same code path with different priming. The module API exposes them as a `pathway` enum that selects the prompt template.
- **Polling can substitute for WebSocket in the consumer.** PrisonBreak's runner polls `/events` rather than opening a WebSocket-to-WebSocket bridge. At 2s intervals against minutes-long strokes, it's near-real-time and avoids a `ws` dependency on the Node side. WebSocket is the right *Ganymede-side* transport; consumers can choose.

## Relationship to PrisonBreak's preset wrapper

The `runStrategicSimulation` procedure is an opinionated wrapper PrisonBreak builds *on top of* the open Ganymede API. It hardcodes the scenario shape, the wished_for_state text, and the case-error → Truth-Packet mapping. That preset is appropriate for PrisonBreak's user — an attorney clicking "Run" doesn't need to author scenarios.

PrisonBreak also exposes (or could expose, depending on its UI direction) a more open path that lets a power user craft their own Scenario, edit the Truth Packets, and pick the pathway. Both shapes coexist: the preset is the one-click default, the open form is the escape hatch. Either way, both call into the same Ganymede v2 API — the difference is only on the consumer side.

This pattern (preset wrapper for the common case + open form for the power-user case, both calling the same primitive) generalizes. Future consumers can adopt the same shape without changing anything on Ganymede's side.
