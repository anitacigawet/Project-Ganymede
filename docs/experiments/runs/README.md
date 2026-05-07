# Experiment Runs

Each run is a single execution of one of the [pathways](../pathways/) on a specific scenario. The runs accumulate as the project's evidence record. Pathways are the hypotheses; runs are the data points.

## Index

| Run | Pathway | Status | Headline result |
| --- | --- | --- | --- |
| [`01_Hualapai_Water_Crisis.md`](01_Hualapai_Water_Crisis.md) | Pre-pathway baseline | ✅ Complete | Validated the GSS visualization pipeline end-to-end. The Hualapai Truth Packet became the canonical sample GSS payload. |
| [`02_GPS_Failure_72hr_Triage.md`](02_GPS_Failure_72hr_Triage.md) | (Predates pathway split — closest to Prediction Cleanroom) | ⏸ Partial | One Oracle (PNT Sovereignty) finished and surfaced the STL/Iridium spoofing zero-day. Two more Oracles were initialized but never harvested. Run was reset. |
| [`Powell_Cleanroom/`](Powell_Cleanroom/) | [Prediction Cleanroom](../pathways/prediction_cleanroom.md) | ✅ **Blind-validated** | Engine independently produced the *Collins v. Yellen* Demotion / Shadow Fed pathway. Independent research confirmed Bessent / Vought / Project 2025 actors actively pursuing exactly that path. |
| [`Tokenized_Land_Resolution.md`](Tokenized_Land_Resolution.md) | [Prediction Cleanroom](../pathways/prediction_cleanroom.md) | ✅ Resolved | Engine surfaced the "Ghost Ranger / Shadow Sovereignty" entrapment via ERC-4337 + springing DACAs + commercial-activity exception. Not separately blind-audited. |
| [`Musk_Altman_Polymarket.md`](Musk_Altman_Polymarket.md) | [Prediction Cleanroom](../pathways/prediction_cleanroom.md) + first live [Mirror Validation](../pathways/mirror_validation.md) | ✅ Stroke 1 + Stroke 2; Stroke 3 pending | Stroke 1: 72.4% strategic-win for Musk via the Discovery Trap. Stroke 2 (red-teamed by the Engine itself): identified that prediction is fragile to opponent's "structural adaptation" via the 8 Pillars of Metacognition. **This run produced the Iterative Engine Vision insight.** |
| [`Genie_Giant_Slayer.md`](Genie_Giant_Slayer.md) | [Genie Protocol](../pathways/genie_protocol.md) | ✅ Complete (vs. comparison validation, not vs. reality) | Wish: zero-budget product → 50% market share + premium acquisition. Engine resolution: release the framework royalty-free, capture D1/D6 in spaces the incumbent's radar can't see, force their employees / banks to break them. Two generic LLMs given the same Wish produced standard startup-playbook output instead. |
| [`04_60s_Amnesia_Mirror_Swarm.md`](04_60s_Amnesia_Mirror_Swarm.md) | (Now classified as a [Mirror Validation](../pathways/mirror_validation.md) seed case — instructive failure) | ❌ Falsified | Engine produced "Dominance Collapse / Sovereignty Handover" resolution — autonomous systems inherit the Earth in 60 seconds of human amnesia. User correctly flagged as nonsense. The diagnostic of *why* the Engine got this wrong (correct math, ignored social inertia / cost of reversal / dimensional greed) is the seed of the Mirror Validation pathway. |
| [`05_Pending_Compute_Autarky.md`](05_Pending_Compute_Autarky.md) | [Prediction Cleanroom](../pathways/prediction_cleanroom.md) | ⏸ Pending | Umpire-proposed scenario: AI compute cartels vs. national sovereign-AI declaration. Earmarked as the next pre-registered run. |

## Reading order

If you're new to the project and want to understand what it does and why anyone thinks it's interesting:

1. Start with [`Powell_Cleanroom/`](Powell_Cleanroom/) — read the README and the resolution. This is the strongest single piece of evidence the project has.
2. Read [`Musk_Altman_Polymarket.md`](Musk_Altman_Polymarket.md) — for the Iterative Engine demonstration.
3. Read [`04_60s_Amnesia_Mirror_Swarm.md`](04_60s_Amnesia_Mirror_Swarm.md) — for the project's most informative failure.
4. Read [`Genie_Giant_Slayer.md`](Genie_Giant_Slayer.md) — to see the same engine in pathfinder mode against a hypothetical Wish.
5. Read [`Tokenized_Land_Resolution.md`](Tokenized_Land_Resolution.md) — for the second Cleanroom datapoint.

The two GSS-pipeline runs ([`01_Hualapai_Water_Crisis.md`](01_Hualapai_Water_Crisis.md), [`02_GPS_Failure_72hr_Triage.md`](02_GPS_Failure_72hr_Triage.md)) are useful background for understanding the visualization layer but aren't load-bearing for the strategic-prediction claims.

## What's missing

The runs above demonstrate the methodology but don't yet meet the bar of formal scientific validation. The Prediction Cleanroom pathway's [open methodology problems](../pathways/prediction_cleanroom.md#open-methodology-problems) section enumerates what the next run needs to add to elevate the evidence — pre-registration timestamps, multi-auditor blind validation, falsification log discipline, and a domain where reality resolves quickly enough for cycle-time learning.

The [Polymarket Validation Protocol](../../protocols/Polymarket_Validation.md) is the operational answer to those gaps. Markets selected under that protocol are filed in [`polymarket/`](polymarket/) and contribute to a running calibration score that updates on every resolution. The protocol predates any selection — its commit hash is the methodology's pre-registration timestamp.

## What's archived

The 36 ad-hoc Python scripts that produced these runs (post-hoc — most were reverse-engineered) live in [`scripts/`](scripts/). They are not intended for re-execution; the productized API in `ganymede-backend/app/services/orchestrator.py` supersedes them. They remain in the repo as historical receipts and as an index from each run record back to the specific operational steps that produced it.
