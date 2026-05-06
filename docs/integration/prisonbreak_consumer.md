# PrisonBreak as Module Consumer (Validation Case)

**Status:** Concrete-target analysis to inform the [general module design](module_design.md). Not a commitment to ship a PrisonBreak integration yet.

PrisonBreak is the user's other project. Repo: [github.com/anitacigawet/PrisonBreak](https://github.com/anitacigawet/PrisonBreak). It is a self-hosted, local-first "digital public defender" that runs source-grounded NotebookLM analysis over uploaded criminal-case documents to surface potentially overturn-able convictions for attorney review. Stack: Vite 7 + React 19 + TypeScript + tRPC v11 + socket.io + SQLite (sql.js WASM) + Python NotebookLM bridge.

PrisonBreak already has a placeholder for the Ganymede integration. The integration target is unambiguous, well-articulated, and *already explains the boundary in its own UI copy*.

## The hook point

`PrisonBreak/client/src/components/SimulatePanel.tsx`

This panel is rendered on the case-detail page (`CaseDetail.tsx` line 1166) under a "Deep Simulate — Strategic Analysis" tab. The button reads *"Run Strategic Simulation (9D Chess)"* and is currently disabled with the explicit note: *"Disabled — 9D Chess plug-in interface is not yet defined."*

The panel's own copy articulates the boundary:

> *"The descriptive analysis you've seen so far comes from NotebookLM, which is grounded in your case documents and refuses to speculate. Strategic legal analysis — 'what's the strongest argument,' 'what would a defense attorney do next,' simulated theory-of-the-case trees — is performed by a separate engine called 9D Chess."*

> *"Coming soon — a pluggable simulation engine for strategic legal analysis. PrisonBreak's role is to assemble the source-grounded record; 9D Chess's role will be to reason over it."*

That is the integration spec, written by the consumer in advance of the producer being ready. Our job on the Ganymede side is to provide the API the panel expects.

## What PrisonBreak naturally has to give Ganymede

PrisonBreak's case lifecycle has already produced rich, source-grounded structured data by the time the user clicks Simulate:

- **Case-level facts.** Defendant, charges, conviction status, jurisdiction, document set.
- **NotebookLM-derived findings** across the 5 error categories:
  - **EM** Eyewitness Misidentification
  - **MF** Misapplied Forensics
  - **FC** False Confessions
  - **OM** Official Misconduct
  - **ID** Inadequate Defense
- **Per-finding metadata**: severity (1–5), confidence, supporting evidence cites, legal basis.
- **NotebookLM grounding chain.** Every finding traces back to specific document chunks via NotebookLM's source-citation links.

This is exactly what Ganymede needs as `TruthPacket[]` input. PrisonBreak has already done the closed-RAG harvest. Ganymede doesn't need to spin up new Oracles — it can synthesize directly off PrisonBreak's already-grounded findings.

This is the cleanest possible integration: **PrisonBreak runs the closed-RAG retrieval (NotebookLM, what it's good at), Ganymede runs the strategic synthesis (9D Engine, what it's good at), no new Oracle creation needed**.

## What PrisonBreak naturally wants back

The SimulatePanel copy specifies the deliverable shape:

- *"Generate strategic options grounded in the findings the rest of the app has surfaced — discovery requests, motion strategies, plea-stage analysis, theory-of-the-case branching."*
- *"Outputs are designed for an attorney to evaluate, not consume directly."*

In Ganymede terms, that's:

- A **Genie-pathway** invocation, where:
  - `current_state` = the case as it stands (charges + findings + posture)
  - `wished_for_state` = "successful overturn" / "best motion to advance the case"
- The Engine produces an **Inadvertent Path** — a sequence of legal moves with a Strategic Lasso (the prosecution's structural vulnerability) and an Incomprehensible Move (the non-obvious motion or theory the prosecution isn't defending against).
- For high-stakes cases, the **Iterative Engine multi-stroke** option: Stroke 2 has the Engine red-team itself ("if the prosecution were aware of this strategy, what's their structural-adaptation counter?"), Stroke 3 produces the synthesis (the move that survives the prosecution waking up).

## Proposed integration shape (concrete)

Talking the general module design ([`module_design.md`](module_design.md)) onto PrisonBreak specifically:

### 1. PrisonBreak side — backend

New tRPC procedure `cases.runStrategicSimulation`:

```typescript
runStrategicSimulation: publicProcedure
  .input(z.object({
    caseId: z.string(),
    iterative: z.boolean().default(false),  // single-pass or 3-stroke
  }))
  .mutation(async ({ input }) => {
    // 1. Gather PrisonBreak's case data + NotebookLM findings
    const ctx = await assembleStrategicContext(input.caseId);

    // 2. POST to Ganymede module (HTTP shape, since PrisonBreak is TS)
    const session = await ganymedeClient.startSession({
      pathway: "genie",
      scenario: {
        current_state: ctx.caseSummary,
        wished_for_state: "Identify the strongest motion or theory available given the surfaced errors that the prosecution is structurally not defending against.",
      },
      iterative: input.iterative,
      // KEY: pre-harvested truth packets — no Oracle creation needed
      context_truth_packets: ctx.findings.map(f => ({
        subject: `${f.category} Finding (severity ${f.severity})`,
        content: f.evidence,
        source_label: f.documentRef,
      })),
    });

    // 3. Persist session ID to PrisonBreak's SQLite
    await db.insert(strategicSimulations).values({
      caseId: input.caseId,
      ganymedeSessionId: session.id,
      status: "running",
      startedAt: now(),
    });

    return { sessionId: session.id };
  });
```

### 2. PrisonBreak side — frontend

Replace the disabled button in `SimulatePanel.tsx` with a real flow:

- Click "Run Strategic Simulation" → calls `cases.runStrategicSimulation`.
- Subscribe to Ganymede's WebSocket via PrisonBreak's existing socket.io infrastructure (proxied through Express).
- Render strokes as they land: Stroke 1 result, then Stroke 2 ("the prosecution's counter to your strategy"), then Stroke 3 (the unbreakable move).
- Each stroke shows the Strategic Lasso, Incomprehensible Move, and full Resolution text in expandable cards.
- Final state persists to SQLite alongside the case; can be re-rendered on page reload.

### 3. Ganymede side — what needs to be built

The general module-design open work, scoped to PrisonBreak's needs:

- ✅ Existing: `GanymedeOrchestrator` with the right primitives.
- 🟡 Needed: Session abstraction — multi-call run state, persisted across HTTP requests.
- 🟡 Needed: WebSocket event stream.
- 🟡 Needed: Pre-harvested Truth Packet ingestion path (skips Oracle creation entirely; this is what PrisonBreak needs).
- 🟡 Needed: Iterative Engine multi-stroke encoded as a code-level loop.
- 🟢 Out of scope for v1: full Oracle approval gate (PrisonBreak doesn't need Oracle creation for v1).
- 🟢 Out of scope for v1: Mirror Validation pathway (no PrisonBreak need).

This is a smaller surface than the full general module — maybe 4–5 days of implementation rather than 1–2 weeks. Good v1 scope.

## What this validation tells us about the general module design

A few principles fall out of the PrisonBreak case that should generalize:

- **The pre-harvested Truth Packet path is the most common integration shape, not the most exotic.** Most consumers — especially any consumer that already has its own document-grounded RAG — will *not* want Ganymede creating fresh Oracles. They'll want Ganymede synthesizing over their existing findings. The general module API should treat "synthesize-from-pre-harvested" as a first-class path, not an edge case.
- **The Iterative Engine multi-stroke is the killer feature for consumers.** A single-pass Stroke-1 output is plausible-sounding but operationally fragile. The Stroke 2 self-stress-test is what produces decision-grade output. Any consumer integration should expose multi-stroke prominently.
- **WebSocket-style streaming is the right transport.** Multi-stroke runs take minutes per stroke. The consumer's UI should show progress as it happens — both for UX reasons and because a 10-minute "loading…" with no signal is unacceptable.
- **The pathway choice is mostly a prompt-selection issue.** Cleanroom / Genie / Offensive are the same code path with different priming. The module API can expose them as a `pathway` enum that selects the prompt template.

## Open questions before this turns into actual code

1. **Confirm v1 scope.** Cleanroom + Genie pathways, pre-harvested Truth Packet path only, no fresh Oracle creation. This is the minimum that lets PrisonBreak ship its `SimulatePanel` integration.
2. **Confirm transport choice.** PrisonBreak uses socket.io. Ganymede currently uses FastAPI. Either Ganymede adds socket.io support, or PrisonBreak proxies plain WebSocket through its Express server. Either works; the latter is simpler.
3. **Confirm the wished_for_state framing for legal cases.** The proposed default is "Identify the strongest motion or theory available given the surfaced errors that the prosecution is structurally not defending against." That's a Genie-shape prompt. The user (who owns prompt curation in PrisonBreak per its CLAUDE.md) may want to author a more specific default.
4. **Confirm citation handling.** PrisonBreak's findings are NotebookLM-cited (each fact has a document reference). When Ganymede synthesizes, those citations should be preserved through to the final resolution. Confirm the `TruthPacket` shape carries enough citation info for Ganymede to thread them through.
