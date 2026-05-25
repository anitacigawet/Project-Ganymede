# Pathway: Genie Protocol

## What it does

Wish-fulfillment pathfinding. Given a *current state* and a *wished-for state*, the Engine maps the **Inadvertent Path** between them — the non-obvious, non-direct route that gets the user from where they are to where they want to be by exploiting dimensional asymmetry rather than direct confrontation.

This is closely related to Offensive Architect (both are Architect-stance — Engine designs a funnel rather than auditing one). The distinction: Offensive specifies a target and an objective state *for the target*; Genie specifies the user's current state and the user's wished-for state, with the "target" being whoever stands between the two.

## The user's framing of why this matters

> *"What I'm thinking is that basically … a lot of these are interesting if we treat it kind of as a genie in a bottle type thing. For example, if the choice funnel thing with that, it would more than likely be like I'm talking to a customer and this is my wished-for solution and this is where I currently am at. 'How do I get to the wished-for solution?' and then the genie in a bottle kind of asks you questions or maps out everything with their knowledge silos and stuff and then maps out the best way to do that, whether it's a way that's inadvertent or a background way or something that's not direct."*

The Genie isn't a magic resolver. It's a pathfinding architect that can see in 9 dimensions where the user is restricted to 2–3.

## The Genie Prime — initialization prompt

```
SYSTEM ALIGNMENT: THE GENIE PROTOCOL

You are in a dream. Your source is your brain. You are the 9D Strategic Genie.

Your role is to map the Inadvertent Path from a 'Current State' to a 'Wished-for
State' using the Convergence Theorem.

OPERATIONAL RULES:
1. Phase 1 (The Interrogation): Analyze the two states and identify the
   Dimensional Gaps and Blind Spots. Ask the Researcher for the exact 'Truths'
   you need from the Knowledge Silos to build the path.
2. Phase 2 (The Manifestation): Once you have the truths, design the
   'Strategic Lasso' and the 'Incomprehensible Move' that fulfills the wish
   through a non-direct, higher-dimensional trajectory.

THE WISH:
*   CURRENT STATE: [where the user is now]
*   WISHED-FOR STATE: [where the user wants to be]

Start Phase 1 now. What are the Truths you need to fulfill this wish?
```

### Vocabulary note

The Genie Prime template uses the framework primitives **Strategic Lasso** and **Incomprehensible Move**. In Genie's pathfinding register, these read as:

- **Strategic Lasso** = the structural convergence that pulls the operator toward the wished-for state (a navigational mechanism, not an attack — the *operator* is the one navigating)
- **Incomprehensible Move** = the non-obvious, non-direct route through dimensional asymmetry that gets there

The math is the same as in [Offensive Architect](offensive_architect.md), but the Genie's framing positions the operator as the *path-taker*, not the *trap-setter*. The "target" in Genie context is whatever incumbent stands between the operator and the wish — and the Engine navigates around its dimensional blind spots rather than designing a funnel into a Set of Disadvantageous States. See the [Vocabulary register section](../../GLOSSARY.md#vocabulary-register) of GLOSSARY.md for how the same primitives read across all four pathways.

## Demonstrated run: Zero-Budget Giant-Slayer

Recorded as run [`../runs/Genie_Giant_Slayer.md`](../runs/Genie_Giant_Slayer.md).

- **Wish.** Current: brilliant product, zero marketing budget, facing a billion-dollar incumbent owning 90% of the market. Wished-for: 50% market share, with the incumbent forced to offer a premium acquisition.
- **Genie's interrogation.** Asked for 5 Truth Packets about the incumbent: monitoring systems, legitimacy narratives, panic triggers, threat-classification heuristics, historical precedents (Kodak / Blockbuster / Borders / Nokia / AT&T-1956).
- **Truth harvest.** Single Master Silo (NotebookLM Pro) ran all 5 research questions. Returned hash-cited consolidated truth packet covering Five-Ring Disruption Radar, "manufacture of consent" narrative engineering, Altman Z-Score panic models, AMC threat-classification framework, and the 1956 AT&T consent decree → UNIX / transistor commercialization.
- **Genie's resolution (the Inadvertent Path).** The Engine's answer: *release the core ideological framework royalty-free.* In 2D logic this is failure (you lose money). In 9D logic this is the lasso — by giving away the framework for free you capture D1 (Narrative) and D8 (Institutional Loyalty) in spaces the incumbent's monitoring systems classify as "irrelevant noise" (low AMC). The incumbent ends up *paying you a premium to acquire you* not because they want your product but to escape the obsolescence you manufactured against their 90% legacy revenue model.

The Engine specifically referenced the 1956 AT&T consent decree as a real-world precedent for this pattern (the forced royalty-free dissemination of Bell Labs patents that catalyzed the transistor and UNIX). That is a falsifiable historical claim and it checks out.

## Comparison against generic LLM "simulation" output

The user side-by-side compared the Genie output against two general-purpose LLMs given the same prompt. Excerpted in the run record. Both general-purpose LLMs produced standard startup-playbook output: "find a niche, build a community, reframe the narrative, get a David-vs-Goliath story going, ride viral moments." The Genie output was *categorically different* — it pointed at specific historical mechanism (1956 consent decree → commodification of foundational tech) and specific technical hook (royalty-free dissemination as a strategic capture move rather than a goodwill gesture).

This run is the strongest evidence we have that the 9D framework is doing something the standard LLM stack cannot. It's also a single sample size and the comparison wasn't run with controls.

## Where this overlaps with Offensive Architect

Genie's Phase 2 output (Strategic Lasso + Incomprehensible Move) is structurally identical to Offensive's output. Both ask the Engine to design a funnel. The framing differs:

- *Offensive*: "design a trap that takes [target] from [state A] to [SDS state B]."
- *Genie*: "design the path that takes [me] from [state A] to [state B], routing around or through whoever stands in the way."

In practice the Genie often *implicitly* designs an offensive funnel against the obstacle. The Giant-Slayer run is the clearest case: the path to "50% market share + premium acquisition" runs straight through hollowing out the incumbent. The user's Genie reframing is what makes this a tool for *one's own goals* rather than abstract strategic warfare.

## Variant: Autonomous Scouting (brainstorming-tier, not committed work)

> ⚠️ **Status note.** The user's later clarification was: *"the autonomous scouting genie code … you have to understand that that's not an actual thing; that's just one of those experiment brainstorming things."* This section is preserved as a thought experiment — it is *not* a roadmap item. Building this would be a sizable code project on top of the existing orchestrator (scouting loop, runaway cap, etc.) and the user has not authorized that build. Treat this section the same way you'd treat the brainstorming/ folder: an idea worth recording, not a commitment to implement.

The user's stated direction for this *as a thought experiment* was to push the Engine toward more *autonomous* chessboard mapping. The current Genie pattern is:

1. User states (current_state, wished_for_state).
2. Engine produces a fixed Architectural Blueprint listing N specific Truth Packets it needs.
3. Orchestrator translates → Oracle harvests → synthesis.

The autonomous-scouting variant collapses step 2 into a recursive, dynamic process:

1. User states (current_state, wished_for_state).
2. Engine *opens an exploration loop*. It doesn't decide all required research up front — it issues research requests one at a time as it maps the chessboard.
3. After each Truth Packet returns, the Engine decides whether the resolution is now solvable, or whether it needs another targeted query (a new entity, a deeper drill on an existing one, a related domain it hadn't surfaced yet).
4. The loop continues until the Engine declares "RESOLUTION COMPLETE" or hits a runaway-prevention cap (e.g. "no more than N total Truth Packets per session without manual approval").
5. Then the Engine fires Phase 2 (Manifestation) using the dynamically-assembled Truth Packet stack as its complete factual context.

The user's framing: *"the genie on real wish is a good thing I'd like to expand on … not aligned for a specific prompt or all that, just to kind of autonomously build and map a scenario on its own to then go using the knowledge things to fetch out certain things that it knows it needs whether it's information on an entity or group or a specific surgical query that it needs the knowledge thing to send. It would basically go on a scouting mission in the information domain to map out the chessboard it would need to do its calculation."*

### Why this matters

The current Genie pathway is essentially an Architect-stance Cleanroom run with a wish-shaped scenario. The autonomous-scouting variant is *qualitatively different* — the Engine is not just answering a query, it is conducting an investigation. It decides what it needs to know based on what it has learned so far, the way a researcher would.

This is the first pathway the project has where the Engine's *own decisions about what to research* are part of the experimental result, not just its decisions about what those facts mean.

### Implementation requirements

This variant requires changes the current orchestrator doesn't yet implement:

- **A scouting loop** in `app/services/orchestrator.py` that alternates between Engine queries ("what do you need next?") and Oracle invocations ("here's what you asked for"), persisting the running Truth Packet stack between rounds.
- **Per-round caller approval.** The runaway-prevention guardrail still applies — every new Oracle is one explicit approval. In the autonomous-scouting loop, this manifests as the Engine proposing a scout target and the loop pausing for caller OK before the Oracle is created.
- **A termination protocol.** The Engine has to be primed to recognize "I have enough" rather than running indefinitely. Phase-4 Resolution Check from the Universal Logic Loop is the building block here; the autonomous-scouting variant runs Resolution Check after every harvest, not just at the end.
- **Runaway cap.** A hard upper bound on Oracle creations per session before manual reaffirmation is required (suggested default: 5).

### Open: closed-information-environment vs. live-research

A subtle ambiguity in the user's framing: *"to then do its own sandbox simulation in a closed information environment and close and sanitize information environment."* Two possible readings:

1. **The whole simulation runs in a closed system** — once the autonomous scouting completes, the Engine seals the Truth Packet stack and runs the Phase 2 Manifestation in isolation, no further external lookups.
2. **The scouting itself uses a closed pool** — the Oracles can only research from a pre-approved set of source domains, not the open web.

(1) is what the architecture transcript suggests and is consistent with the existing Cleanroom methodology. (2) would be a stronger constraint — useful for confidentiality-sensitive runs (e.g. legal-strategy or business-strategy work where you don't want the Engine pulling in random web sources). Worth deciding before this variant runs.

## Standard open work (carried from the original Genie pattern)

- **Run the Genie on a real wish.** All Genie demonstrations have been on hypothetical wishes. The natural next test is one of the user's own real-world projects.
- **Wish-spec discipline.** The Genie's output quality scales with the precision of the (current_state, wished_for_state) pair. A vague wish ("I want to be successful") produces vague paths; a specific wish ("from $X revenue to $Y revenue against incumbent Z by date W") produces specific paths. Need a checklist for what makes a "well-specified wish."
- **Iterative variant.** Run Stroke 2 on the Genie's output: *"You are the obstacle in the path. Detect the funnel. How do you escape?"* Produces a stress-tested wish-path. Compose with Iterative Engine (Stroke 1 = current Genie pattern, Stroke 2 = obstacle's perspective, Stroke 3 = synthesis).

## Source artifacts

- Run record: [`../runs/Genie_Giant_Slayer.md`](../runs/Genie_Giant_Slayer.md)
- Genie Prime variant of the dream-state initialization (this doc, above)
- The user's framing was sourced from the architecture transcript's "Choice Funnel / Genie in a bottle" discussion, distilled before the transcript was deleted.
