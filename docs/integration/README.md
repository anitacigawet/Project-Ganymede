# Integration

Ganymede is designed as an **open primitive**, not an opinionated wrapper. The v2 API exposes raw access to the strategic-physics framework: any consumer composes its own scenarios, picks its pathway, ships its own pre-harvested Truth Packets, and decides its own UI (or no UI). Each consuming project knows its domain better than Ganymede possibly could; Ganymede's job is to provide a clean session-based API and stay out of the way.

This folder is the integration documentation for consumer authors.

## Read in this order

| File | What it covers |
| --- | --- |
| [`consuming_the_v2_api.md`](consuming_the_v2_api.md) | **Start here.** The hands-on consumer guide — concepts, lifecycle, full API reference, code examples in curl/Python/TS. Written for someone going in blind. |
| [`module_design.md`](module_design.md) | The *why* behind the API shape. Architectural commentary, what's built vs. deferred, design decisions explained. |
| [`examples/`](examples/) | Concrete reference consumers. Read these once a real codebase example would help. |

## What's in `examples/`

Each file describes a real consumer project that uses the v2 API:

- [`examples/prisonbreak_consumer.md`](examples/prisonbreak_consumer.md) — PrisonBreak's case-grounded strategic-simulation integration. Genie pathway, NotebookLM-derived case errors mapped to Truth Packets, socket.io progress streaming, React UI. The first concrete consumer.

When more consumers exist, they go here.

## Quick orientation if you're brand new

Ganymede is two persona-locked NotebookLMs (the 9D Chess Engine and the Mirror Auditor) wrapped in a session-based HTTP API. You hand it a *scenario* (what to reason about) plus *Truth Packets* (your already-harvested research findings, source-cited). It returns *strokes* — one or more Engine outputs — with the canonical strategic shapes (Strategic Lasso, Incomprehensible Move, Final Resolution).

Single-pass = one stroke. Iterative = three strokes (synthesis → audit → re-synthesis). The audit stroke is the Mirror Auditor stress-testing Stroke 1; Stroke 3 is a re-synthesis with the audit findings injected as friction.

That's the whole API mechanically. Everything in this folder is unpacking implications of that shape.
