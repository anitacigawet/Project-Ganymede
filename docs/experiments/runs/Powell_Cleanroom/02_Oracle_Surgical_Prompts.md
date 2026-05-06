# Oracle Surgical Prompts

**Translated from:** [`01_Architectural_Blueprint.md`](01_Architectural_Blueprint.md)
**Sent to:** four PKI Authentication Oracles (one per dimension cluster), each persona-locked per [`../../../protocols/PKI_Oracle_Persona.md`](../../../protocols/PKI_Oracle_Persona.md).

Each prompt was hand-translated from the Engine's 9D-jargon dimensional requirements into plain-language research targets that NotebookLM Deep Research could actually execute. **No editorial summary, no goal-shaping** — only jargon-stripping. The orchestrator's role here is *Surgical Middleman*: lossless translation, not analysis.

## Notebook configurations

Each notebook had this **Custom Instructions** ("Configure Chat") set, identical for all four:

```
You are the PKI Authentication Oracle. Your role is to provide surgical,
high-fidelity data extraction from the provided sources for a 9D Strategic
Simulation.

OPERATIONAL RULES:
1. Zero Hallucination: If the information is not explicitly in the sources,
   state 'Data Not Found.' Never speculate.
2. Zero Fluff: Do not use conversational filler. Respond only with facts and
   direct analysis.
3. The Truth Packet: Your output must be formatted as a 'Truth Packet'—a
   distilled, bulleted list of high-fidelity strategic facts.
4. Citations: Every fact must be linked to a specific source within the
   notebook.
5. Theoretical Rigor: Treat all data as variables for a 9D Chess Engine
   resolution.
```

## Silo D8 — Institutional Alliances

**Notebook name:** `PKI_Powell_Institutional_D8`
**Mission:** Map the "Trust Wall" around Jerome Powell.

**Surgical research prompt:**

```
Research the current internal dynamics of the Federal Reserve Board of
Governors and the Senate Banking Committee.
1. Identify the level of institutional support for Jerome Powell among current
   Governors.
2. Map his standing within the Senate Banking Committee.
3. Identify any key defenders or potential 'Defectors' who have publicly
   signaled disagreement with his leadership.
```

**Truth-extraction prompt (after deep research + Import in UI):**

```
Based on the imported research, provide a Surgical Truth Packet regarding
Jerome Powell's institutional support.
1. List key allies in the Board of Governors.
2. List key defenders in the Senate Banking Committee.
3. Identify the specific 'Loyalty Score' of his inner circle.
4. Summarize any credible threats of defection.
Zero fluff. Use bullet points.
```

## Silo D1 — "Fire Powell" Narrative

**Notebook name:** `PKI_Powell_Narratives_D1`
**Mission:** Measure the "Political Will" for his removal.

**Surgical research prompt:**

```
Research recent public statements, White House leaks, and social media
narratives regarding 'Federal Reserve Independence.' Identify the specific
populist arguments being used to justify executive interference or removal of
the Fed Chair. Quantify the 'Narrative Momentum' for his dismissal.
```

**Truth-extraction prompt:**

```
Based on the imported research, provide a Surgical Truth Packet regarding the
'Fire Powell' narrative.
1. What are the 3 strongest arguments being used against him?
2. How much public/political momentum exists for his removal (Scale 1-10)?
3. Identify the 'Narrative Architect' (who is driving the story?).
Zero fluff. Use bullet points.
```

## Silo D4/D7 — Economic-Political Collision

**Notebook name:** `PKI_Powell_Economic_D4_D7`
**Mission:** Find the "Economic Asymmetry" — where current monetary policy clashes with the Executive's political timeline.

**Surgical research prompt:**

```
Compare real-time US inflation and employment data (last 6 months) against
the upcoming 2024/2026 election cycles. Identify specific 'Pain Points' where
the current monetary policy is directly clashing with the political needs of
the Executive Branch. Research the 'Signal Divergence' between market
expectations and political demands.
```

**Truth-extraction prompt:**

```
Based on the imported research, provide a Surgical Truth Packet on the
Economic-Political clash.
1. Identify the 'Election Trigger' (the specific date or data-point that makes
   him a political liability).
2. Map the divergence between inflation targets and political survival.
3. What is the 'SDS' (Disadvantageous State) the economy creates for the
   Executive Branch?
Zero fluff. Use bullet points.
```

## Silo D5 — Legal Wall

**Notebook name:** `PKI_Powell_Legal_D5`
**Mission:** Identify the legal removal-protection precedent landscape.

**Surgical research prompt:**

```
Research the specific legal requirements for removing a Federal Reserve Chair
'for cause.' Analyze previous Supreme Court precedents (like Seila Law or
Collins) regarding executive removal power of independent agency heads.
Identify the exact legal friction the White House would face in a forced
termination.
```

**Truth-extraction prompt:**

```
Based on the imported research, provide a Surgical Truth Packet on the Legal
Wall.
1. Can he be fired 'at will'? (Yes/No with citation).
2. What is the 'Precedent Shield' protecting him?
3. What is the estimated 'Time-to-Resolve' for a legal challenge to his
   removal?
Zero fluff. Use bullet points.
```

## Note on the *Collins v. Yellen* loophole

The `Collins v. Yellen` precedent was *not* mentioned in any of the four surgical prompts. It came up in the D5 Truth Packet ([`03_Truth_Packets.md`](03_Truth_Packets.md)) because the deep-research engine surfaced it organically when looking up "Supreme Court precedents regarding executive removal power of independent agency heads." That's the cleanroom property at work: the user did not seed the answer.
