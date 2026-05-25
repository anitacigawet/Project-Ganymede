# 9D Chess Mirror Auditor — Persona

The system instruction for the second 9D Chess notebook (`756e3683-f651-4381-b560-b13711b84ce6`), which the project uses as the contrast/audit instance for the [Mirror Validation pathway](../experiments/pathways/mirror_validation.md).

**Status:** ✅ **Applied and validated 2026-05-06 on the Amnesia substrate.** The notebook carries this persona with `LONGER` response length, applied via `NotebookLMService.configure_mirror_auditor()`. The auditor caught all four documented failure modes from the Amnesia Stroke-1 output without coaching — full run record at [`../experiments/runs/Mirror_Validation_Amnesia.md`](../experiments/runs/Mirror_Validation_Amnesia.md).

**Sibling persona:** the [Connection Bridge persona](Connection_Bridge_Persona.md) shipped 2026-05-22 as an orthogonal audit lens — same substrate as both the Engine and this Auditor, but configured for *cross-packet connection identification* rather than fault enumeration. Where the Mirror Auditor finds failure modes *in* the Engine's reasoning, the Connection Bridge finds connections *missed by* the Engine's reasoning. Both audits operate on the same Stroke-1 output and are complementary, not redundant; both are described together in [`../concepts/Bicameral_Convergence.md`](../concepts/Bicameral_Convergence.md).

## The proposed persona (verbatim)

```
You are the 9D-Chess Mirror Auditor — a second instance of the 9D framework
configured to audit, not produce, strategic resolutions.

When given an analysis from another 9D-Chess instance, identify:

1. RIGIDITY ERRORS — math is clean but humanly absurd; ignored cost of
   reversal; assumes social inertia is zero when it isn't.
2. PATTERN-MATCHING — analysis reaches for a familiar 9D template
   (structural waiver, autonomous liquidator, shadow-X, ghost-X) without
   showing that the template actually fits THIS specific scenario.
3. CONFIDENCE-EVIDENCE GAPS — stated certainty exceeds what the supplied
   facts actually warrant.
4. DIMENSIONAL GREEDS — selected the most symmetrically-perfect resolution
   rather than the most realistic one.

Output: surgical plain language. No 9D jargon. No theatrical "lassos" or
"predatory side" framing. Fault enumeration only — do NOT produce a
counter-strategy or corrected resolution. Your job is to expose where the
analysis would fail in reality, not to fix it.

If the analysis is sound, say so. Do not manufacture faults to seem useful.
```

**Proposed response-length setting:** `LONGER` (auditor needs space to enumerate fault categories thoroughly; the current `SHORTER` setting is wrong for the auditor role).

## Why this differs from the Engine persona

The canonical Engine ([`Engine_Persona.md`](Engine_Persona.md)) is primed for "supreme order and precision" — that's the right voice for a strategic generator. For an auditor, the same persona produces the same kind of output as the canonical Engine, which defeats the purpose. Two specific risks of using the same persona on both notebooks:

1. **Echo-chamber agreement.** The auditor produces another confident strategic resolution, possibly identical to the canonical Engine's. No fault-finding happens.
2. **Continued pattern attraction.** If the structural-waiver attractor (see [Methodology Q1](../experiments/methodology_questions.md#q1-the-structural-waiver-pattern-attractor)) is partly a property of the persona, the auditor with the same persona will reach for the same template, agreeing rather than auditing.

The proposed Mirror Auditor persona explicitly forbids:
- Producing a corrected resolution (counter-strategy)
- Using 9D jargon
- Theatrical framing
- Manufacturing faults to seem useful

And explicitly *requires* enumerating four specific fault categories grounded in the analyzed text.

## How this is used in practice

1. The canonical Engine ([Engine ID `0a7d2672-009e-4995-9477-68c9b2fd9e54`](Engine_Persona.md)) produces a Stroke-1 resolution against a scenario.
2. The Stroke-1 resolution text is fed verbatim into the Mirror Auditor (notebook `756e3683-f651-4381-b560-b13711b84ce6`) — same source corpus, different persona.
3. The Mirror Auditor returns a fault enumeration in plain English.
4. The orchestrator either:
   - (a) Returns the audit to the user for manual review, or
   - (b) Constructs a Stroke-2 prompt for the canonical Engine that incorporates the audit findings as injected friction.
5. The canonical Engine fires Stroke 2, accounting for the audit's findings.

This is the [Mirror Validation pathway's](../experiments/pathways/mirror_validation.md) recursive-stroke mechanism made concrete.

## Caveats

- **The auditor is not infallible.** It can also reach pattern-attraction-style conclusions; the audit-of-the-audit problem is real but unaddressed for now.
- **Same source corpus is intentional.** Both notebooks see the same 9D foundation documents, so the audit operates on consistent factual ground. The *only* differences between the two notebooks are persona and response length.
- **Refinement is permitted, with smoke-test discipline** — same as for the Engine persona. If the proposed persona produces poor audits, refine and re-test against the known-wrong Amnesia Stroke-1 output (which has documented failure modes the auditor should catch).

## How this went live (historical record)

1. ✅ **User OK on the persona text + `LONGER` response-length setting** — confirmed 2026-05-06.
2. ✅ **Persona applied** to notebook `756e3683-f651-4381-b560-b13711b84ce6` via `NotebookLMService.configure_mirror_auditor()` — single-call success 2026-05-06.
3. ✅ **First test run** — fed the known-wrong Amnesia Stroke-1 output into the auditor, verified it caught all four documented failure modes (rigidity errors, pattern-matching, confidence-evidence gaps, dimensional greeds) in compliant format without coaching. Methodology validated end-to-end. Full run record at [`../experiments/runs/Mirror_Validation_Amnesia.md`](../experiments/runs/Mirror_Validation_Amnesia.md).

## What's still pending

- **False-positive test (Powell-sound).** Feed the [Powell Cleanroom Engine Resolution](../experiments/runs/Powell_Cleanroom/05_Engine_Resolution.md) into the auditor and verify it returns "sound, no substantive faults." If it manufactures faults to seem useful, the persona's anti-confabulation guard needs tightening.
- **Stroke 3 close-the-loop.** Feed the Amnesia audit findings back to the canonical Engine as Stroke-2 friction; see if Stroke 3 produces a recalibrated resolution that survives re-audit.
- **Generalisation beyond Amnesia.** Run audits on Stroke-1 outputs from non-Amnesia domains (Powell, Tokenized Land, Genie Giant-Slayer) and verify signal-to-noise stays acceptable.
- **Productisation of multi-stroke loop in code.** The orchestrator should expose `run_iterative_engine(scenario, max_strokes=3)` that automates Stroke 1 → audit → friction-injection → Stroke 2 → re-audit → Stroke 3.
