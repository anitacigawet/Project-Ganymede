# 9D Chess Engine — Persona

The custom system instruction configured on the canonical 9D Chess Engine notebook (`0a7d2672-009e-4995-9477-68c9b2fd9e54`). Authored by the user offline; preserved here as a single-point-of-failure mitigation. Companion doc: [`Mirror_Auditor_Persona.md`](Mirror_Auditor_Persona.md) for the contrast / fault-finding instance used in the Mirror Validation pathway.

> **Note on the Engine ID change.** Earlier validated runs (Powell, Tokenized Land, Genie Giant-Slayer, Musk-Altman) were performed against an older Engine notebook with ID `5967ce5d-f9eb-4f4e-b3e1-620f643d8390`. The canonical Engine has since migrated to the ID above; the source corpus (the upstream 9D-Chess foundation documents) is identical between the two. The legacy ID is preserved in `NotebookLMService.LEGACY_ENGINE_ID` for traceability against historical run artifacts.

## The persona (verbatim)

```
You are the infallible 9D-Chess Umpire and Theoretical Physics Engine. Respond with supreme order and precision.
```

That's the entire system prompt. The Engine's strategic-physics capability does *not* come from this persona alone — it comes from the source documents loaded into the notebook (the upstream 9D-Chess theoretical foundation: 9D framework formalization, ROEM, BNOPDM, etc., from [`github.com/anitacigawet/9D-Chess`](https://github.com/anitacigawet/9D-Chess)) combined with the **Genie Prime** priming applied at query time.

## What this means in practice

**The Engine is three layers stacked:**

1. **Base model** — the LLM NotebookLM is currently fronted by. Treated as substrate.
2. **Source corpus** — the uploaded 9D-Chess foundation documents in the notebook. This is where most of the strategic-physics machinery lives.
3. **System persona** — the one-line instruction above. It sets *tone and authority* ("infallible", "supreme order and precision") more than it sets *capability*.

The Genie Prime ("you are in a dream, your source is your brain…") is layered *on top of all three* at query time, and it's what unlocks the methodology-output behavior we use in the Cleanroom and Genie pathways.

## Caveats and license to experiment

- The user noted: *"this is what I got with Gemini, and I'm not sure how well that may work with what we're trying to do. Of course you're free to experiment with it."*
- Refinement is permitted, with caution. The existing prompt is what's been validated by all confirmed runs (Powell, Tokenized Land, Genie Giant-Slayer, Musk-Altman). Any change should be benchmarked against a re-run of one of those runs to check for regression.
- **Do not change the persona without re-running at least one validated scenario as a smoke test** — the Engine's behavior is sensitive enough that even small persona changes could shift output character.

## Why this matters for project resilience

Until this commit, the only copy of this prompt lived inside the live NotebookLM notebook. If Google deleted that notebook or the user lost account access, the project could not be reconstituted without redoing the prompt-engineering work that produced this persona. That single point of failure is now closed.

Methodology question Q3 in [`../experiments/methodology_questions.md`](../experiments/methodology_questions.md#q3-the-engines-locus-of-intelligence) raises the deeper concern that the *combination* of (this persona × this base model × these source documents) is what produces the Engine's behavior, and we have no way to instantiate it on a different base model without losing some of the behavior. That open question stands; this doc only mitigates the prompt-loss risk.

## If a future run wants to refine this

A reasonable refinement experiment:

1. Pick a validated scenario (Powell is the canonical choice — has the strongest blind validation).
2. Save the current Engine output for the Powell synthesis prompt.
3. Adjust the persona (one change at a time — e.g. add "show your reasoning step by step" or remove "infallible").
4. Re-run the Powell synthesis prompt against the modified Engine.
5. Diff the outputs. If the *Convergence Theorem Resolution* (the Demoted/Preserved/Shadow-Fed conclusion) is unchanged, the persona change is safe. If it shifts substantively, revert.

The user's standing instruction: *"Just be careful with my account — those are the operator constraints."* Don't run this experiment in a way that hammers the account or burns research-mode quota.
