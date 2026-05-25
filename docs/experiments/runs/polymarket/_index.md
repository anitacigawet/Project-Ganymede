---
title: "Polymarket Validation Runs — Index"
type: "history-record"
status: "active"
tags: ["run", "experiments", "polymarket"]
color_id: "1"
---

# Polymarket Validation Runs — Index

The canonical roster of every market locked under the [Polymarket Validation Protocol](../../../protocols/Polymarket_Validation.md). Updated on every lock commit (new row appended) and every resolution commit (resolution + Brier columns filled).

The repo's commit history is the timestamping mechanism — a row's `Lock commit` column is a real git SHA that predates the row's market resolution. Anyone can verify pre-registration by running `git log` against this file.

## Score so far

*Empty — no closed runs yet.*

The aggregate Brier score, log-loss, and calibration curve land in [`_score.md`](_score.md) once the first market resolves. Until then, the score is undefined and the project's claim about Polymarket calibration is "we have not run any markets yet."

## Validation track

Markets that satisfied the [selection parameters](../../../protocols/Polymarket_Validation.md#selection-parameters) at lock time. Every entry stays in the score regardless of outcome.

| # | Slug | Selected | Resolves by | Pathway | Iter? | Predicted P(YES) | Market P(YES) at t=0 | Lock commit | Status | Resolution | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| *(empty — first lock pending)* | | | | | | | | | | | |

## Exploration track

Runs that didn't satisfy validation-track selection criteria (e.g. resolution window too long, ambiguous resolution criteria, deliberately off-domain) but were useful for refining prompts, Oracle structures, or audit categories. **These do not feed the score.**

Filed under [`exploration/`](exploration/). Insights that prove out across multiple exploration runs can be proposed as a validation-track epoch boundary.

## Versioned epochs

Each epoch is one frozen protocol configuration. The score is reported *per epoch* — combining scores across epochs would mix incompatible methodologies.

| Epoch | Opened | Closed | Description | Mean Brier |
| --- | --- | --- | --- | --- |
| `v1` | *pending first lock* | — | Initial protocol version. Genie-Prime framing, single-pass or 3-stroke iterative, Mirror Auditor 4-category fault enumeration. | *pending* |

A new epoch opens when a refinement insight from the exploration track is ready to roll into validation. The cut-point is its own commit and is documented inline above. Validation runs from a closed epoch stay in that epoch's score; they don't carry forward.

## Reading order for new readers

1. Read the [Polymarket Validation Protocol](../../../protocols/Polymarket_Validation.md) first — the rules of the track.
2. Read the [runs/README.md](../README.md) for the broader run library this fits into.
3. Browse individual run files in this directory once they exist.
