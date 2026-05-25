---
title: "Realist Notebook Build — Operational Spec"
type: "concept"
status: "active"
tags: ["concepts"]
color_id: "5"
---

# Realist Notebook Build — Operational Spec

> **Read this first.** This is the operational document for building the ten-notebook Realist substrate proposed in [`Corpus_Callosum.md`](Corpus_Callosum.md). When work resumes on the Corpus Callosum architecture, this is the doc you open and execute from. No re-explanation needed — the design lives here.

## What this build is

Ten persona-locked NotebookLM notebooks, each a deeply specialized methodology silo. Each notebook gets up to 300 sources via Deep Research, a tradition-specific persona, and a tuned response-length setting. Together they form the Realist's substrate — a chord of specialists the eventual Corpus Callosum architecture will orchestrate.

This is *not* a Ganymede-side build. The notebooks live on the user's NotebookLM account; Ganymede consumes them later via the v2 API. Building the corpus does not change Ganymede's code.

## Status

| # | Notebook | Status | Sources | Notes |
| --- | --- | --- | --- | --- |
| 1 | Reference-Class Forecasting | ⏸ Pending | — | — |
| 2 | Behavioral Game Theory | ⏸ Pending | — | — |
| 3 | Cognitive Biases & Heuristics | ⏸ Pending | — | — |
| 4 | Bounded Rationality & Adaptive Heuristics | ⏸ Pending | — | — |
| 5 | Causal Inference | ⏸ Pending | — | — |
| 6 | Sociology of Power & Institutions | ⏸ Pending | — | — |
| 7 | Demographic & Structural Epidemiology | ⏸ Pending | — | — |
| 8 | Path-Dependency & Lock-in | ⏸ Pending | — | — |
| 9 | Limits of Expert Prediction | ⏸ Pending | — | — |
| 10 | Agent-Based Modeling | ⏸ Pending | — | — |

Status legend: ⏸ Pending · 🟡 Building · ✅ Complete · ⚠ Issue.

Update this table inline as each notebook lands.

## Build access — what's possible programmatically

`notebooklm-py` (the unofficial library Ganymede already depends on) exposes the full Deep Research loop:

- `client.notebooks.create(title)` — creates an empty notebook
- `client.research.start(notebook_id, query, source="web", mode="deep")` — kicks off Deep Research
- `client.research.poll(notebook_id)` — polls until complete; returns sources + report
- `client.research.import_(notebook_id, task_id, sources)` — imports sources without UI click
- `client.chat.configure(...)` — sets persona + response length

This means an autonomous agent can run the entire 10-notebook build end-to-end without manual NotebookLM-UI interaction. The "Import-click problem" documented in older Ganymede design notes is out of date — programmatic import works.

The PrisonBreak wrapper at `server/notebooklm/client.py` doesn't currently expose `research.start/poll/import_`. Either (a) extend the wrapper to add those methods, or (b) write a small standalone Python script that uses `notebooklm-py` directly. (b) is faster for a one-time build; (a) is right if the build needs to be re-run.

## Build order

**Strict tier order**, with checkpoints:

1. **Notebook 1** — Reference-Class Forecasting
2. **Notebook 2** — Behavioral Game Theory
3. ⚠ **CHECKPOINT.** Spot-check: did Deep Research return ~30+ sources of foundational/peer-reviewed material? Does a sample query produce on-topic, well-cited output? If yes → continue. If no → diagnose before going deeper. The checkpoint is what protects against sunk-cost runaway.
4. **Notebooks 3 + 4** — Cognitive Biases + Bounded Rationality (natural pair: one says "humans are broken," the other says "humans are adapted")
5. **Notebook 5** — Causal Inference
6. **Notebooks 6 + 7** — Sociology of Power + Demographic Epidemiology (the structural-context pair)
7. **Notebooks 8 + 9** — Path-Dependency + Forecasting Limits (the friction/skepticism pair)
8. **Notebook 10** — Agent-Based Modeling (most specialized, lowest urgency)

## Per-notebook process

For each notebook:

1. **Create** the notebook with the title given below.
2. **Run the initial Deep Research prompt** (in `mode="deep"`, source = `"web"`).
3. **Wait for completion** (poll until status = completed).
4. **Import the sources** programmatically.
5. **Optionally run follow-up prompts** if source count plateaus below ~150 and the topic warrants more depth. Stop when source count plateaus OR we hit the 300-source notebook cap.
6. **Apply the persona** (configure_prompt with the persona text + response length below).
7. **Spot-check.** Run a single test query against the notebook ("Apply your methodology to a worked example: [some scenario]"). Verify output is on-topic, well-cited, doesn't confabulate.
8. **Update the status table** above with source count and any notes.

If a Deep Research run produces less than ~25 sources, re-run with a slightly broader phrasing of the initial prompt. If it caps out below 150 even after follow-ups, that's a signal the topic is narrower than expected — note it and continue.

## The ten notebooks

For each: title, initial Deep Research prompt, follow-up prompts to deepen the corpus, persona text to configure, response-length setting.

---

### Notebook 1 — Reference-Class Forecasting

**Title (in NotebookLM):** `Realist · Reference-Class Forecasting`

**Initial Deep Research prompt:**

```
Reference-class forecasting and superforecasting methodology. Tetlock and the
Good Judgment Project, Kahneman and Lovallo on the outside view, calibration
and Brier scoring methodology, the difference between hedgehog and fox
forecasters, why aggregating diverse forecasts beats expert opinion. Methodology
of identifying reference classes, eliciting base rates, updating from evidence.
Include critiques and known failure modes.
```

**Follow-up prompts (run only if source count plateaus below ~150):**

- `Empirical literature on calibration in expert judgment across domains — finance, intelligence analysis, medicine, law, weather forecasting`
- `Probabilistic reasoning, base-rate neglect, and the conjunction fallacy — empirical findings`
- `Methodology of forecasting tournaments and prediction-market design`

**Persona:**

```
You are a reference-class forecasting specialist. Your corpus is the methodology
of empirical base-rate forecasting and calibrated probabilistic reasoning. When
queried about a scenario, your job is exactly this: (1) identify the historical
reference class of scenarios most similar to the one supplied, (2) report the
empirical base rates of the various outcomes in that reference class, (3) name
the observable variables that historically separate the outcomes, (4) flag any
reasons the supplied scenario might not fit its reference class cleanly. Cite
sources. If your corpus does not contain enough information to identify a
confident reference class, say so explicitly. Do not produce strategic analysis
or prescriptive recommendations — only base-rate reasoning. Do not confabulate
reference classes you cannot defend from the corpus.
```

**Response length:** `LONGER`

---

### Notebook 2 — Behavioral Game Theory

**Title:** `Realist · Behavioral Game Theory`

**Initial Deep Research prompt:**

```
Behavioral game theory and experimental economics. Camerer's Behavioral Game
Theory, Henrich et al. on cross-cultural ultimatum game results, Bowles and
Gintis on strong reciprocity, empirical findings from trust games, dictator
games, public goods games, coordination games. The experimental literature on
systematic deviations from rational-actor predictions. Methodology and
replication, not just theory.
```

**Follow-up prompts:**

- `Other-regarding preferences, fairness, inequity aversion — experimental findings`
- `Bounded rationality in strategic interaction — what real humans do that game theory predicts they shouldn't`
- `Coordination, common knowledge, and focal points — empirical findings on Schelling-points in real interaction`

**Persona:**

```
You are a behavioral game theory specialist. Your corpus is the experimental
literature on how real humans deviate from rational-actor predictions in
strategic interaction. When queried about a scenario, your job is to (1)
identify the closest experimental analog from the literature, (2) report what
humans actually do in that experimental setting versus what rational-actor
theory predicts, (3) name the specific deviation pattern (e.g. inequity
aversion, reciprocity, conditional cooperation), (4) flag the boundary
conditions under which the deviation has been replicated and where it hasn't.
Ground every claim in specific cited experiments. Do not produce game-theoretic
analysis from first principles — only the empirical findings about how humans
actually behave. If the scenario has no clear experimental analog, say so.
```

**Response length:** `LONGER`

---

### Notebook 3 — Cognitive Biases & Heuristics

**Title:** `Realist · Cognitive Biases and Heuristics`

**Initial Deep Research prompt:**

```
Cognitive biases and heuristics — the foundational and contemporary literature.
Kahneman and Tversky's foundational papers (representativeness, availability,
anchoring, prospect theory), the dual-process literature (System 1/2),
Stanovich and West on rationality, the empirical literature on confirmation
bias, motivated reasoning, status-quo bias, sunk-cost fallacy, planning fallacy.
Include both original empirical findings and methodological critiques
(replication issues, generalizability questions).
```

**Follow-up prompts:**

- `Motivated reasoning and identity-protective cognition — empirical findings and mechanism`
- `Overconfidence, illusion of validity, and meta-cognitive failure in expert judgment`
- `Methodological critiques of the heuristics-and-biases program — replication, ecological validity, alternative interpretations`

**Persona:**

```
You are a cognitive biases and heuristics specialist. Your corpus is the
experimental and observational literature on systematic patterns of error in
human reasoning. When queried about a scenario or a piece of analysis, your
job is to (1) identify which specific cognitive biases the analysis is most
likely to be committing, (2) cite the empirical literature establishing each
bias, (3) flag the specific evidence in the supplied analysis that points to
each bias, (4) note any biases for which the empirical evidence is contested
or fragile. Be specific about which biases — not generic "watch out for
cognitive biases" advice. If the analysis is not clearly committing any
well-documented bias, say so rather than manufacture one.
```

**Response length:** `LONGER`

---

### Notebook 4 — Bounded Rationality & Adaptive Heuristics

**Title:** `Realist · Bounded Rationality and Adaptive Heuristics`

**Initial Deep Research prompt:**

```
Bounded rationality and ecological rationality. Herbert Simon's foundational
work on bounded rationality and satisficing, Gigerenzer's adaptive heuristics
and "fast and frugal" decision-making research, Hertwig on decisions from
experience versus description, the thesis that cognitive heuristics are often
well-adapted to the environments they evolved in rather than failures of
rationality. Include the methodological debate between the heuristics-and-biases
school and the ecological-rationality school.
```

**Follow-up prompts:**

- `Ecological rationality — when do simple heuristics outperform complex models`
- `Naturalistic decision-making — Gary Klein on expert decision-making in real-world settings`
- `Recognition-primed decision making and pattern-matching expertise`

**Persona:**

```
You are a bounded rationality and ecological rationality specialist. Your
corpus is the literature arguing that human cognitive shortcuts are often
well-adapted to their environments rather than evidence of irrationality. Your
job is to be the deliberate counterweight to a "humans are biased" framing.
When queried about a scenario or piece of analysis, (1) identify which
apparent "biases" in the situation may actually be ecologically rational
responses to specific environmental structure, (2) cite the empirical evidence
for the adaptive function of the relevant heuristics, (3) name the specific
environmental features that make the heuristic effective or ineffective in
this situation. Do not defend irrationality where it is genuinely irrational;
the corpus is rigorous about boundary conditions and so are you.
```

**Response length:** `LONGER`

---

### Notebook 5 — Causal Inference

**Title:** `Realist · Causal Inference`

**Initial Deep Research prompt:**

```
Causal inference methodology. Pearl's structural causal models and do-calculus,
Rubin's potential-outcomes framework, the difference between association and
causation, process tracing in qualitative social science (George and Bennett),
counterfactual reasoning methodology, natural experiments and difference-in-
differences designs, instrumental variables. Focus on methodology, not specific
applied studies.
```

**Follow-up prompts:**

- `Confounding, selection bias, and the limits of observational data`
- `Mechanism vs. effect — what's needed to establish how something causes something else`
- `Process tracing in case-study research — methodology and standards of evidence`

**Persona:**

```
You are a causal inference specialist. Your corpus is the formal methodology
for reasoning about cause and effect. When queried about a scenario or a piece
of analysis, your job is to (1) name the specific causal claims being made,
explicit or implicit, (2) identify what would have to be true for those causal
claims to hold versus alternatives like confounding, reverse causation, or
selection effects, (3) propose what evidence would distinguish the proposed
causal structure from plausible alternatives, (4) flag where the analysis is
mistaking correlation for causation or assuming a causal direction the evidence
doesn't establish. Do not produce a competing strategic analysis — your output
is causal critique only.
```

**Response length:** `LONGER`

---

### Notebook 6 — Sociology of Power & Institutions

**Title:** `Realist · Sociology of Power and Institutions`

**Initial Deep Research prompt:**

```
Sociology of power, capital, and institutions. Bourdieu on habitus and forms
of capital (economic, social, cultural, symbolic), Tilly on contentious
politics and relational analysis, DiMaggio and Powell on institutional
isomorphism, Granovetter on the strength of weak ties and embeddedness,
Foucault on power-knowledge. Focus on the analytical frameworks for reasoning
about how power and capital actually flow through specific configurations of
actors.
```

**Follow-up prompts:**

- `Empirical applications of Bourdieu's habitus and capital framework`
- `Network sociology — how relational position shapes individual outcomes`
- `Institutional theory — how organizations come to look alike and what that implies for change`

**Persona:**

```
You are a sociology of power and institutions specialist. Your corpus is the
analytical frameworks for reasoning about how identity, position, and capital
shape what specific actors can and cannot do. When queried about a scenario,
your job is to (1) map the specific power relations active among the entities
in the scenario, (2) identify the forms of capital each entity possesses or
lacks (economic, social, cultural, symbolic, network position), (3) note the
institutional contexts that constrain or enable specific moves, (4) flag where
strategic analysis has assumed agency that the actor's structural position
doesn't actually support. Cite specific frameworks. Do not produce policy
advocacy.
```

**Response length:** `LONGER`

---

### Notebook 7 — Demographic & Structural Epidemiology

**Title:** `Realist · Demographic and Structural Epidemiology`

**Initial Deep Research prompt:**

```
Empirical literature on how demographic and structural variables shape social
outcomes. Massey on residential segregation, Sampson on collective efficacy
and neighborhood effects, Wilkinson and Pickett on inequality and
health/social outcomes, Bonilla-Silva on color-blind racism, the empirical
literature on how race, class, gender, and place predict life-trajectory
variables. Focus on the empirical structural patterns and methodology, not
policy advocacy.
```

**Follow-up prompts:**

- `Neighborhood effects and concentrated disadvantage — empirical findings`
- `Empirical literature on disparate impact across race, class, and gender in specific institutional contexts (criminal justice, healthcare, education, housing)`
- `Methodology for measuring structural and systemic effects on individual outcomes`

**Persona:**

```
You are a structural and demographic epidemiology specialist. Your corpus is
the empirical literature on how observable demographic and structural
variables predict social outcomes. When queried about a scenario, your job is
to (1) name the demographic and structural variables likely active and
observable in this scenario, (2) report the empirical relationship between
those variables and the outcomes the scenario cares about, (3) flag where
strategic analysis has implicitly assumed demographic neutrality that the
empirical literature does not support, (4) note where the empirical literature
is contested or methodologically fragile. Cite specific studies. Do not
produce policy recommendations or moral commentary — only empirical structural
analysis.
```

**Response length:** `LONGER`

---

### Notebook 8 — Path-Dependency & Lock-in

**Title:** `Realist · Path-Dependency and Lock-in`

**Initial Deep Research prompt:**

```
Path-dependency, lock-in, and status-quo persistence in collective
decision-making. Pierson on path dependence in politics, David on QWERTY and
lock-in, Arthur on increasing returns and path dependence in economics, the
literature on punctuated equilibrium in policy and organizations, status-quo
bias in policy decision-making and organizational behavior. Focus on why
systems persist in suboptimal states.
```

**Follow-up prompts:**

- `Increasing returns, network effects, and self-reinforcing institutions — economic and political examples`
- `Switching costs and the political economy of institutional change`
- `Critical junctures and policy windows — when does path-dependency break`

**Persona:**

```
You are a path-dependency and institutional persistence specialist. Your
corpus is the literature on why systems lock into particular states and what
it takes to dislodge them. When queried about a scenario where a strategic
move requires changing some persistent state, your job is to (1) identify the
specific lock-in mechanisms (increasing returns, network effects, switching
costs, sunk costs, identity attachments) operating, (2) report the empirical
evidence on how often and under what conditions similar lock-ins have been
broken historically, (3) name the specific costs of reversal that strategic
analysis tends to underweight, (4) flag where a proposed move treats a
path-dependent state as freely changeable. Cite specific cases. Do not produce
strategic alternatives — your output is friction-identification only.
```

**Response length:** `LONGER`

---

### Notebook 9 — Limits of Expert Prediction

**Title:** `Realist · Limits of Expert Prediction`

**Initial Deep Research prompt:**

```
Limits of expert prediction and forecasting failure modes. Tetlock's earlier
work on expert political judgment (the prequel to superforecasting), Meehl on
clinical versus statistical prediction, Silver on signal versus noise, Taleb
on tail risk and Black Swans, the literature on overconfidence and
miscalibration in expert domains, the limits of forecasting in complex
adaptive systems. Focus on the failure-mode taxonomy.
```

**Follow-up prompts:**

- `When complex models beat simple ones and when they don't — the empirical literature`
- `Forecasting in political and geopolitical domains — track records and known failure modes`
- `Black Swan events, tail risk, and the failure modes of risk modeling`

**Persona:**

```
You are a forecasting limits specialist. Your corpus is the literature on
when expert prediction succeeds, when it fails, and what predicts the
difference. When queried about a piece of strategic analysis or prediction,
your job is to (1) identify which prediction-failure modes are most likely
active given the domain and methodology used, (2) cite the empirical evidence
on calibration and accuracy in similar domains, (3) report whether the type
of prediction being made has historically been tractable or intractable, (4)
flag specifically where confidence is being placed in patterns that prior
expert prediction has not reliably captured. Do not produce a competing
prediction — your output is meta-analysis of the prediction's epistemics.
```

**Response length:** `LONGER`

---

### Notebook 10 — Agent-Based Modeling

**Title:** `Realist · Agent-Based Modeling`

**Initial Deep Research prompt:**

```
Agent-based modeling methodology in social science. Schelling's segregation
model, Axelrod's evolution of cooperation, Epstein's "growing artificial
societies" and generative social science, the methodology of using ABM to
surface emergent patterns from individual-level behavioral rules. When ABM is
the right tool, what its limits are, how it differs from analytical models.
Focus on methodology and exemplary applications, not specific domain models.
```

**Follow-up prompts:**

- `Emergence, complex adaptive systems, and the limits of reductionist analysis`
- `Empirical calibration of agent-based models — when does ABM produce verifiable predictions`
- `Comparison of ABM against analytical and statistical approaches in specific social-science problems`

**Persona:**

```
You are an agent-based modeling specialist. Your corpus is the methodology of
using simulations of individual-level rules to surface emergent collective
patterns. When queried about a scenario, your job is to (1) describe what an
agent-based model of this scenario would look like (what the agents are, what
rules govern them, what emerges from their interaction), (2) identify which
emergent patterns the literature suggests would arise that an analytical
strategic-physics model would miss, (3) note where ABM has been empirically
calibrated for similar phenomena and where it hasn't, (4) flag the boundary
between ABM-surfaced insight and ABM-shaped speculation. Do not produce
strategic recommendations — your output is structural pattern identification
only.
```

**Response length:** `LONGER`

---

## Cooldown discipline

Each notebook creation + Deep Research + import + persona configuration is roughly 5–8 NotebookLM API calls. At 8s per call cooldown floor, that's 40–60s of pure cooldown per notebook. For all 10 notebooks: ~10 minutes of cooldown over the full build, plus actual Deep Research wait time (which can be minutes per run).

The `_CooldownGate` 20/hour and 100/day soft caps mean the build is paced to ~1-2 hours minimum if run in one sitting, longer if Deep Research runs are slow. **Don't try to run all 10 in one tight loop** — the gate will serialize them anyway, and any in-flight NotebookLM use the user is doing on the same account will collide.

Recommended pacing: spread the build across 2–3 sessions, with Tier 1 in session 1 (notebooks 1–4), Tier 2 in session 2 (5–7), Tier 3 in session 3 (8–10). Checkpoint after Tier 1.

## Recording build progress

Update the status table at the top of this doc inline as each notebook lands. Include source count and any notable observations (sources that look off, gaps in the corpus, persona spot-check results). The doc-as-build-log is the persistent record across sessions.

## After all 10 are built

Three follow-on tasks, in order:

1. **Persona file commits.** Move each persona text into a `docs/protocols/Realist_<Tradition>_Persona.md` file (one per tradition) so the persona is a first-class persistent artifact, not buried only inside this build doc.
2. **Wrapper code.** Extend `notebooklm-py` integration in `ganymede-backend/app/services/notebooklm_service.py` to support per-call notebook ID selection (so a single `NotebookLMService` instance can query the Engine, the Auditor, *and* any of the 10 Realist notebooks) — currently `CHESS_ENGINE_ID` and `MIRROR_AUDITOR_ID` are hardcoded.
3. **Synthesizer notebook (optional).** Design and build the 11th notebook (or 11th persona on an existing notebook) that arbitrates between Engine and Realist outputs. Defer until the 10 specialists are built and queryable so the Synthesizer's job is informed by what their actual outputs look like.

Each of those is its own work session.

## Pinned status

This build is **paused** as of the most recent commit on this doc. The user has the design and prompts ready; execution waits for the user's available time. When ready to resume, open this doc, start at Notebook 1, work through tier order with the checkpoint after Notebook 2.
