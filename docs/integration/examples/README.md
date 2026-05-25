---
title: "Example Consumers"
type: "cluster-head"
status: "active"
tags: ["integration", "examples", "cluster-head"]
color_id: "2"
---

# Example Consumers

Real projects that use Ganymede's [v2 API](../consuming_the_v2_api.md). Each example is a write-up of a consumer's integration shape — the scenario it constructs, how it builds its Truth Packets, what pathway it picks, and how it presents the result.

These exist to give a concrete reference when designing a new consumer. Reading one of these tells you what the integration *actually looks like in code* in a way the abstract API docs can't.

## Available examples

| File | Consumer | Domain | Pathway | Stack | UI? |
| --- | --- | --- | --- | --- | --- |
| [`prisonbreak_consumer.md`](prisonbreak_consumer.md) | PrisonBreak | Criminal-case wrongful-conviction analysis | Genie | TypeScript (Express + tRPC + React) | Yes — `SimulatePanel` in case-detail page |

When more consumers land, they get a row.

## What an example doc should contain

If you're writing up a new consumer, follow the shape below so the index stays consistent:

1. **What this consumer does** — one paragraph on the project itself.
2. **The hook point** — the file or feature where Ganymede integration lives.
3. **What the consumer naturally provides** — what its existing data shape is, before any Ganymede mapping.
4. **What the consumer wants back** — the deliverable shape, in its own domain language.
5. **Mapping to the Ganymede API** — concretely: scenario fields chosen, Truth Packet construction, pathway choice, iterative vs. single-pass, UI presentation pattern.
6. **What this case taught us about the general API design** — principles that should generalize. (PrisonBreak's write-up established that pre-harvested Truth Packets are the common shape, not the exotic one. Future consumers should similarly call out their generalizable lessons.)

## What's *not* an example

Internal Ganymede operator scripts (`scripts/`, `start_mocked.py`, etc.) are not consumers — they're operator tooling. They go in the appropriate operator-facing directory, not here.
