---
title: "Polymarket Validation Protocol"
type: "protocol"
status: "active"
tags: ["protocols", "operational"]
color_id: "6"
---

# Polymarket Validation Protocol

## Why this exists

The project's run library has demonstrated the methodology on real scenarios — Powell, Tokenized Land, Musk-Altman, Giant-Slayer — but every prior run was either retrospectively validated or partially completed. The runs index calls out exactly what's missing:

> *pre-registration timestamps, multi-auditor blind validation, falsification log discipline, and a domain where reality resolves quickly enough for cycle-time learning.*

This protocol defines how the project uses **Polymarket** as that domain. Markets resolve YES/NO with a clean ground truth, every market URL is a stable timestamp, and resolution typically lands in days-to-weeks rather than months. Scored across a series of runs, the project moves from "we got Powell" anecdote to "we calibrate at Brier *X* over an *N*-market window" — a different category of evidence.

The framework itself is unchanged. This protocol is operational discipline around how runs are selected, locked, executed, and scored, not a new pathway. Most Polymarket runs use the [Prediction Cleanroom](../experiments/pathways/prediction_cleanroom.md) pathway with its existing Genie-Prime / Iterative Engine machinery.

## Run lifecycle

```
1. SELECT  → pick a market that satisfies the parameter set
2. LOCK    → commit run file with URL, resolution criteria, market price at t=0
3. RUN     → harvest information on the underlying question, Engine + Mirror Audit, freeze prediction
4. WAIT    → market resolves on its own schedule
5. SCORE   → append resolution + Brier component to the run file
```

Each stage produces a git commit. The commit hashes are the timestamps — there is no separate "publication" step. The repo's commit history *is* the pre-registration record.

## Selection parameters

A market is eligible for the validation track if all of the following hold:

| Parameter | Requirement | Rationale |
| --- | --- | --- |
| Resolution window | 2–8 weeks from selection | Long enough for the strategic-physics framing to matter; short enough to close runs within a quarter and iterate on cycle-time learning. |
| Resolution criteria | Unambiguous on a single read-through | Avoids losing runs to "Engine analyzed the real question, market resolved on a technicality." |
| Underlying dynamics | Observable structural pressures (legal proceedings, regulatory deadlines, corporate strategic moves, political appointments, court rulings) | Where 9D-physics-style funnel logic actually applies. Coin-flip exogenous shocks are out of scope. |
| Information asymmetry | Solving requires combining multiple structural signals | If the answer reduces to one news headline, the framework adds no value over a search. |
| Domain | Anything except sports, entertainment, weather, single-event surprise resolutions, and crypto-price markets | These don't fit the strategic-physics substrate. |
| Market liquidity | Sufficient that the resolution criteria are likely to be enforced cleanly (skip dust-volume markets where edge cases get messy) | Practical reliability of resolution. |

Markets that don't satisfy these criteria can still be useful for the *exploration* track (see below); the validation-track selection is stricter on purpose.

## Lock format

Each run gets a file at `docs/experiments/runs/polymarket/<slug>.md` with the following sections committed at lock time:

```markdown
# <Market title>

**Polymarket URL:** <full URL>
**Resolution deadline:** <date>
**Resolution criteria:** <verbatim quote of the market's resolution rules>
**Market price at t=0:** YES <price>%, NO <price>%, volume $<amount> (timestamp: <ISO>)
**Pathway:** prediction_cleanroom (or other)
**Iterative:** yes / no
**Locked at commit:** <will fill in after commit lands>

## Selection rationale

<2-3 sentences on which selection parameters this market satisfies and why it was picked over alternatives>

## Prediction (FROZEN — do not edit after this commit)

<Engine output: probability, Strategic Lasso, Incomprehensible Move, Final Resolution. For iterative runs, include all three strokes.>

## Resolution (filled in when market closes)

*pending*
```

The run file is committed twice: once at lock-time with the prediction frozen, then once at resolution-time with the score appended. Edits to the prediction section after the lock commit are protocol violations and would be visible in `git log -p`.

## Scoring

For each closed run:

- **Brier component** = (predicted_probability − actual_outcome)² where actual_outcome is 1 if the market resolved YES, 0 if NO.
- **Log-loss component** = −log(predicted_probability_of_actual_outcome).

The aggregate score is the mean Brier across all closed validation-track runs, plus the calibration curve (binned predicted-vs-realized rates). Both numbers update with every resolution; both live in `docs/experiments/runs/polymarket/_score.md` regenerated by a script.

Reference points for what a Brier score means:

| Brier | Interpretation |
| --- | --- |
| 0.25 | Random guessing / always 50% |
| ~0.18–0.22 | Casual prediction-makers |
| ~0.10–0.15 | Calibrated forecasters |
| < the market's own Brier on the same set | Genuine edge over crowd reasoning |

The honest comparison is "Engine vs. the market price at t=0" — the market price is itself a prediction, and beating it (or matching it while producing different reasoning) is the meaningful claim.

## Exploration vs. validation track

There are two tracks. They share the framework but have different rules.

**Validation track** (the calibration-score canon):
- Frozen protocol. Selection criteria, prompt structures, Oracle harvest shape, audit categories — none of these change mid-track.
- Every market that meets the selection criteria and gets locked is in the score, regardless of how the run goes.
- No retroactive removal. A run that got the answer wildly wrong stays in the score; that's the point.
- Refinement insights from exploration roll into validation only at versioned cut-points (`v1`, `v2`, …), and the cut-point is a separate commit that closes one validation epoch and opens the next. The score is reported per epoch.

**Exploration track**:
- Anything goes. Try different prompt structures, different Oracle configurations, different framings, different scenarios that would have been ineligible for validation.
- Lives in `docs/experiments/runs/polymarket/exploration/` so it's filed separately from validation runs.
- Never feeds the score directly. Insights from exploration that prove out can be proposed as a validation-track epoch boundary.

The wall between the two tracks is what protects the project from the optimization trap — once a calibration score exists, the pull to tweak the framework "to do better" on it is enormous, and the framework stops being a thing under test the moment that happens.

## Account & operational discipline

- **Polymarket account is the operator's, not the framework's.** The framework consumes market metadata (URL, resolution criteria, price-at-t=0) by reading the public market page. It never logs in, never places orders, never holds funds. The operator may keep a small (≤$10) account for the convenience of seeing markets in their normal Polymarket UI; that account is not part of the validation infrastructure.
- **No trading from the framework.** Even with a funded account, the framework doesn't take positions. Trading would introduce skin-in-the-game incentives that contaminate the methodology (most obviously, a temptation to selectively report).
- **Cooldown discipline still applies.** Each run is one or more NotebookLM API calls; the [Account Safety](Account_Safety.md) gate governs them like any other run. A burst of Polymarket runs in close succession should respect the same per-call and inter-session cooldowns.
- **No engine queries about market price during the harvest.** The Oracles harvest information about the underlying real-world question. They don't need to be told the market exists or what the price is. This isn't a strict firewall — incidental exposure during selection is fine — it's just that the harvest prompt doesn't volunteer market data.

## What this protocol intentionally does *not* do

- **It doesn't try to make the framework price-blind.** Selecting a market necessarily exposes the operator (or selecting agent) to the market price. We accept that and don't pretend otherwise. The integrity check is whether the *Engine's reasoning* is structurally derived rather than market-anchored — and that's visible in the stroke text, not enforceable through information firewalls.
- **It doesn't define a target Brier score.** A target makes the score the goal and invites optimization-trap drift. The honest reporting is whatever Brier comes out across the closed set, with the calibration curve and a comparison against the market's own Brier on the same set.
- **It doesn't lock the project to Polymarket forever.** Polymarket is a convenient first venue because of liquidity and the public commit history. If the project's framework demonstrably calibrates well, future epochs may extend to Kalshi, Manifold, or domain-specific resolution sources. Adding a venue is a versioned-cut-point change, not a free addition.

## How this addresses the runs README's "what's missing"

The runs index lists four gaps in the project's evidence record. This protocol addresses each:

| Gap (from runs/README.md) | How this protocol addresses it |
| --- | --- |
| Pre-registration timestamps | Each run's git commit hash IS the timestamp. Public, unforgeable, predates the resolution by definition. |
| Multi-auditor blind validation | The Mirror Auditor (Stroke 2) provides one in-framework audit. External auditors (other operators running the same framework on the same markets) can be layered on per-epoch. |
| Falsification log discipline | Validation-track runs cannot be removed retroactively. The score reports all closed runs including misses. |
| Domain with fast resolution | Polymarket markets typically resolve in days-to-weeks. Cycle-time learning becomes practical in a way it isn't on, e.g., 6-month macroeconomic predictions. |

## Historical compliance note

This protocol was added before any Polymarket validation runs landed. The first locked market — and the first commit hash that anchors a validation-track run — comes after this file is committed. That ordering is a methodology requirement: the rules must predate any selection.
