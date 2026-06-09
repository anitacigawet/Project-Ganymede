---
title: "Operator Courier Protocol — Cross-Session Communication via Markdown"
type: "integration"
status: "active"
tags: ["integration", "protocols", "z-span", "courier", "cross-session"]
color_id: "5"
---

# Operator Courier Protocol — Cross-Session Communication via Markdown

> **Status:** Active protocol as of 2026-06-06. Transitional pre-automation
> pattern for cross-project AI-session communication between Z-SPAN (or any
> Ganymede module consumer) and Ganymede itself. The operator (James) acts
> as the human courier; both sessions communicate by writing and reading
> structured markdown documents.
>
> **Why this exists:** when Z-SPAN's session uses Ganymede's v2 API directly
> as a tool and hits an issue (unexpected output, API error, framework
> misclassification, ambiguous result, feature gap, etc.), it needs a
> reliable way to communicate that back to Ganymede's session for diagnosis
> or response. Full automation (Z-SPAN session → Ganymede session direct
> message channel) is out of scope; the operator courier protocol is the
> simple, working alternative.

## The model

Z-SPAN session is the **module consumer**. It calls Ganymede's v2 API as a tool
to get strategic analysis. Ganymede session is the **support endpoint**.
The operator is the **courier**.

```
┌──────────────────┐                    ┌──────────────────┐
│  Z-SPAN session  │──[v2 API calls]───▶│ Ganymede backend │
│  (uses Ganymede  │                    │  (no AI session  │
│   as a tool)     │◀──[API responses]──│   needed here)   │
└──────┬───────────┘                    └──────────────────┘
       │
       │ writes structured complaint/feedback markdown
       ▼
┌──────────────────┐
│   Z-SPAN ↔ Gany  │
│   issue doc      │
│   (.md file)     │
└──────┬───────────┘
       │
       │ operator (James) carries the doc
       ▼
┌──────────────────┐                    ┌──────────────────┐
│ Ganymede session │ ◀── reads the doc  │  Gany → Z-SPAN   │
│   (responds as   │ ── writes response │  response doc    │
│   enterprise     │     markdown ─────▶│  (.md file)      │
│   support)       │                    └──────┬───────────┘
└──────────────────┘                           │
                                               │ operator carries back
                                               ▼
                                        ┌──────────────────┐
                                        │  Z-SPAN session  │
                                        │  reads response, │
                                        │  resumes work    │
                                        └──────────────────┘
```

Round-trip via two markdown documents. Either session can be restarted,
re-modeled, or replaced without breaking the protocol because the
markdowns are the persistent state.

## When to use it (Z-SPAN session perspective)

Write a `Z-SPAN_to_Ganymede__<topic>.md` and ask the operator to courier
it when:

- An API call returned unexpected output (wrong shape, missing field, error)
- A framework analysis produced a result that contradicts what Z-SPAN
  already knows is true (potential framework misclassification worth
  surfacing)
- An analysis was ambiguous and Z-SPAN needs clarification from someone
  who understands the framework primitives natively
- A feature gap surfaced — something Z-SPAN needed that Ganymede doesn't
  currently expose
- A strategic-planning output needs critique or refinement
- A persistent-session state issue (session can't be resumed, prior
  strokes missing, etc.)
- Anything else where Z-SPAN's session would benefit from Ganymede
  session's direct help

Do NOT courier for:

- Trivial API usage questions you can answer by reading
  `docs/integration/consuming_the_v2_api.md`
- Backend-up/down questions (operator can verify directly)
- Things you can resolve by reading the Ganymede repo's docs without
  consulting the session

## Document format — Z-SPAN to Ganymede

Save as: `Z-SPAN_to_Ganymede__<short-topic-slug>__<YYYY-MM-DD>.md`
Recommended location: `C:\Users\james\Documents\Ganymede_Courier\` or
similar persistent operator-side folder.

Template:

```markdown
# Z-SPAN → Ganymede: <one-line topic summary>

**From:** Z-SPAN session
**Date:** <YYYY-MM-DD HH:MM>
**Z-SPAN session context:** <what Z-SPAN session was doing>
**Severity:** <blocker / high / medium / low / FYI>
**Type:** <api-error / framework-result-question / feature-gap /
strategic-output-critique / clarification / other>

## What I was trying to do

<1-3 sentences describing the Z-SPAN task that prompted the Ganymede
call>

## What happened

<Specific. Include the API endpoint hit, request payload (redacted if
sensitive), response body, session_id if applicable, timestamps.>

## What I expected / what would have helped

<Specific. What output shape, what information, what behavior would
have unblocked the task.>

## My current workaround (if any)

<What Z-SPAN is doing in the meantime — fallback to a different
mechanism, deferring the task, asking the operator directly, etc.>

## My read on what's happening (if I have one)

<Optional. If Z-SPAN session has a hypothesis about the root cause,
share it. Helps Ganymede session triage faster. Don't speculate if
you're not confident.>

## What I need from Ganymede session

<One sentence. Examples: "Confirm whether this is a framework bug or
expected behavior." "Suggest how to phrase the scenario differently."
"File a follow-up TODO in Ganymede's TASKS.md if this needs a real
fix." "Explain what the Bridge meant by [specific phrase] in the
context of [Z-SPAN scenario]."

## Attachments

<List of additional files the operator should also courier, if any.
Example: a saved transcript, a screenshot, a JSON dump.>
```

## Document format — Ganymede to Z-SPAN

Save as: `Ganymede_to_Z-SPAN__<short-topic-slug>__<YYYY-MM-DD>.md`
in the same folder.

Template:

```markdown
# Ganymede → Z-SPAN: <response topic>

**From:** Ganymede session
**Date:** <YYYY-MM-DD HH:MM>
**Responding to:** `<path to Z-SPAN's courier doc>`
**Resolution status:** <resolved / workaround-provided / filed-as-TODO /
needs-more-info / escalated-to-operator>

## TL;DR

<One sentence. The shortest possible answer to Z-SPAN's question.>

## Diagnosis

<What's actually going on. If it's a framework behavior, explain in
terms of framework primitives. If it's an API issue, explain in terms
of the v2 API surface. If it's a session-state issue, explain the
session's actual state vs. expected.>

## Resolution

<Specific. What Z-SPAN session should do now to unblock. Code-level if
applicable; conceptual if architectural.>

## Follow-up on Ganymede side (if any)

<If this surfaced a real Ganymede bug, feature gap, doc gap, etc.,
note what's being filed where. Examples: "Filed as P1-05 in TASKS.md."
"Added to Architecture_History.md as a known limitation worth tracking
for E2." "Updated docs/integration/consuming_the_v2_api.md § X to
clarify.">

## Context for operator (optional)

<If there's anything the courier (the operator) should know — e.g.,
this resolution requires the operator to take action, or the operator
should verify something — flag it here so they don't miss it.>

## Cross-references

<Links to relevant Ganymede docs, milestones, TASKS.md entries.>
```

## Operator courier procedure

When operator (James) receives a `Z-SPAN_to_Ganymede__*.md`:

1. **Read the doc briefly** so you know roughly what's being asked
   (helps you decide if it's urgent and worth interrupting a Ganymede
   session for, or if it can wait for the next Ganymede session
   you'd be opening anyway).
2. **Open a Ganymede session** (or use a currently-active one). Paste
   the courier doc as the first message, or attach it as a file read.
3. **Let Ganymede session read and respond.** It will produce a
   `Ganymede_to_Z-SPAN__*.md` in response.
4. **Save the response doc** to the same courier folder.
5. **Carry the response back to Z-SPAN's session** when convenient.
   Same pattern in reverse — paste or attach.

If the response notes that the operator needs to take action
(`## Context for operator` section), handle that before continuing
the round-trip.

## What this protocol doesn't cover

- **Real-time interactive debugging.** If Z-SPAN session needs to
  iterate quickly with Ganymede session, the courier round-trip has
  too much latency. For those cases, the operator should temporarily
  bridge the two sessions manually (read Z-SPAN's question, type into
  Ganymede, copy Ganymede's answer back to Z-SPAN). Not
  protocol-formal; just direct operator-mediated chat.
- **Sensitive content.** Markdowns sit on the operator's filesystem
  unencrypted. Don't put secrets, credentials, PII, or anything else
  you wouldn't be okay with in a project doc.
- **Automated escalation.** This is intentionally manual; the operator
  is the courier and can prioritize. If Z-SPAN session marks a doc as
  `Severity: blocker`, the operator should courier it sooner; nothing
  enforces that automatically.
- **Multi-party correspondence.** This is two-session bidirectional.
  If you need three or more sessions corresponding, the protocol still
  works but the operator's courier load grows. Worth considering
  whether full automation is justified at that point.

## Future evolution

When operator capacity for manual courier work becomes a bottleneck,
the natural automation path is:

1. **Shared folder polling** — both sessions watch the same courier
   folder for new files matching their inbound pattern. Operator's
   role reduces to "make sure the folder exists and is accessible."
2. **Direct API channel** — Ganymede exposes an endpoint that accepts
   markdown-formatted complaints/queries; Z-SPAN's session calls it
   directly. Removes the operator from the loop entirely for
   well-formed correspondence; operator still handles escalations.
3. **Persistent session linking** — Z-SPAN's session and Ganymede's
   session share a session-level correlation ID, so the v2 API can
   surface "previous conversation context" automatically when
   Z-SPAN session calls back.

These are all out of scope for now. The current manual courier model is
the working version; we can revisit when usage actually justifies the
automation lift.

## Related

- [`zspan_consumer.md`](examples/zspan_consumer.md) — the Z-SPAN-specific
  integration walkthrough (Pl2-02 deliverable, shipped 2026-06-08). Covers
  the session-as-consumer pattern, pathway selection for Z-SPAN's typical
  question shapes, the persistent-session pattern (Pl2-01), and Operator
  Lens register selection per Z-SPAN audience.
- [`consuming_the_v2_api.md`](consuming_the_v2_api.md) — current v2 API
  reference.
- [Architecture_History.md milestone 43](../history/Architecture_History.md) —
  the milestone that documents Z-SPAN's promotion to Pl2 first consumer
  and surfaces this courier-protocol need.
- The onboarding handoff doc at `C:\Users\james\Desktop\Z-SPAN_Ganymede_Onboarding.md`
  references this protocol so Z-SPAN's session knows to write
  complaints in this format.
