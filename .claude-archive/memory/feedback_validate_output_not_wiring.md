---
name: feedback-validate-output-not-wiring
description: "Wiring success ≠ project success. When a milestone closes, distinguish 'did the plumbing fire' from 'did the system produce its actual value.' The structural fix milestone 49 routed correctly + animated the visualizer + ran cancel cleanly — but the Engine produced corpus-pattern-matched fabulation because the Truth Packet pipeline was broken upstream. James called this out explicitly 2026-06-11."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2026-06-11-milestone-50-session
---

# Validate the OUTPUT, not just the wiring

**James's framing (verbatim, 2026-06-11):** *"The entire project revolves around pki's and closed knowledge, and you're considering it a success. I'm so confused."*

He was right. I'd closed milestone 49 as a validated structural fix because:
- Dispatcher routed Cleanroom → Universal Logic Loop correctly ✓
- Visualizer animated through all stages ✓
- `/cancel` halted the loop cleanly ✓
- Session reached `status=complete` ✓

But the actual Engine output came from pattern-matching the framework's persona over an empty Truth Packet substrate (all 3 PKI Oracles had failed `IMPORT_RESEARCH` upstream). The synthesis sounded analytical because the 9D Chess Engine persona is always analytical-sounding, not because it had real harvested data to reason against.

This is the exact failure mode milestone 18 (60-second Amnesia) taught the project to recognize: *"correct math, wrong world."* The framework's confidence inherits from its persona, not from the reliability of its inputs.

## How to apply

When reporting a milestone closure, **explicitly separate two questions in the closeout text**:

1. **Did the plumbing fire?** (routing, animation, state transitions, cancel paths, completion event)
2. **Did the OUTPUT carry the project's actual value?** (in Ganymede's case: a synthesis whose claims trace back to real harvested Truth Packets — not just framework primitives applied to empty data)

If only (1) is verified, say so. Don't bundle them. The milestone is *partially* validated, not fully.

**The smell test:** if the closure narrative reads like "everything we built worked," but you can't point at a specific output artifact that demonstrates the project's value mechanism, you've validated the plumbing only. Go find the output artifact.

## Concrete example from this project

- **Milestone 49 closure (the mistake):** "Structural fix shipped, routes real-world Cleanroom to Universal Logic Loop, visualizer animates, cancel works." → presented as success.
- **Milestone 50 closure (the corrected frame):** "Three failures had to be fixed before the Universal Logic Loop produced an output grounded in real harvested data: IMPORT_RESEARCH timeout, synthesis input-cap on Phase 3, dispatcher single-provider fragility. Validated on session `de892dc9-...` — 3 successful Oracle harvests (11,294 chars), Engine prefixed an explicit epistemic-discipline notice acknowledging external Truth Packets. THIS is project success."

The Architecture_History milestone 50 cross-cutting note captures this for future sessions: *"Future milestone closeouts should explicitly distinguish did the plumbing work from did the output work and not bundle them."*

## Scope

This rule applies in any Ganymede session, especially in milestone closure reports, Architecture_History entries, and chat-level "what we shipped today" summaries. It also generalizes — any project with a load-bearing analytical pipeline should treat output quality as the success bar, not pipeline health.
