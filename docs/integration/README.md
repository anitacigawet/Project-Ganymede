# Integration

The project's north star (per [`../OVERVIEW.md`](../OVERVIEW.md#north-star-module-not-service)) is to plug Ganymede into the user's other projects as a private analysis module. This folder is where the API design for that integration lives.

| File | What it contains |
| --- | --- |
| [`module_design.md`](module_design.md) | The general-purpose Ganymede module API — the surface any consuming project would talk to. Designed to be consumer-agnostic. |
| [`prisonbreak_consumer.md`](prisonbreak_consumer.md) | PrisonBreak as the first concrete validation case. Identifies the existing hook point (`SimulatePanel.tsx`), what data PrisonBreak would pass in, what it would expect back, and how the integration plugs into PrisonBreak's existing tRPC + WebSocket architecture without touching its NotebookLM-only AI stance. |

These docs are **design proposals, not committed work.** They are at the "we have explored what the shape would be and identified the open decisions" stage. Nothing is being built against them until the user reviews and signs off.

## Why PrisonBreak first

The user explicitly chose PrisonBreak as the first integration target because it already has a `SimulatePanel.tsx` placeholder explicitly waiting for a "9D Chess plug-in interface." That placeholder is the cleanest possible integration test:

- The boundary between PrisonBreak's job (NotebookLM-grounded retrieval and summarization of case documents) and Ganymede's job (strategic analysis — "what would a defense attorney do next") is *already articulated in the placeholder's own UI copy*.
- PrisonBreak already has the orchestration patterns Ganymede integration needs (Python subprocess for NotebookLM bridge, tRPC + WebSocket for stream-style updates, SQLite for storing analysis output).
- The deliverable PrisonBreak wants from Ganymede is well-shaped: strategic options for an attorney to evaluate, grounded in the case's already-surfaced findings.

Once the integration shape is validated against PrisonBreak, the same module API generalizes to any future consumer.
