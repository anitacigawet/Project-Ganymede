---
name: feedback-ui-copy-outside-in
description: "Write UI copy from the user's outside-in reading perspective, not the AI's inside-out restating perspective; collapse duplicate phrases across placeholder, help text, and headers in close proximity."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2a4d14c1-c969-452a-bbf6-9b34ec8f3f70
---

When writing or editing UI copy in [[ganymede-ui]], write from the user's outside-in perspective — what they need to read to understand and act — not the AI's inside-out perspective of restating what the form does. Cut duplicates: if a phrase appears in the placeholder, don't repeat it as help text below the input; if a section header already explains the pathway, the input description doesn't need to restate it. Rule of thumb: any word appearing 3+ times in close visible proximity is a sign of redundancy.

**Why:** James noticed (2026-05-21) that the Cleanroom RunnerPanel had byte-identical placeholder + help-text below, plus a third "Falsifiable" repetition in the description above — produced because each piece of copy was written in isolation by the AI restating the field's purpose. Reads as repetitive to a human scanning the form.

**How to apply:** When adding or editing form fields, panel headers, or instructional copy, pick one location for each piece of guidance. Don't restate placeholder text as help text. Don't restate section headers as form-field descriptions. Light-touch sweeps are preferred over restructuring layouts — collapse redundancy in place, don't redesign.
