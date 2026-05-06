# Experimental Scripts (Archive)

These 36 scripts are the literal receipts of the experiments documented in
`../`. They were one-off ad-hoc scripts written during brainstorming runs;
they are preserved here as historical artifacts, not as ongoing code.

**Do not edit or extend these.** The patterns they encode have been
productized in `ganymede-backend/app/services/orchestrator.py`. New work
should go through the FastAPI endpoints exposed in `app/main.py`.

## How they map to the orchestrator

| Old script pattern | New API |
| --- | --- |
| `phase1_triage.py`, `meta_triage*.py`, `mirror_triage.py`, `amnesia_triage.py`, `amnesia_closed_loop.py`, `amnesia_refactor.py`, `surgical_english_reset.py`, `nuance_prime_alignment.py` | `POST /api/triage` (`GanymedeOrchestrator.triage`) |
| `pki_oracle_init*.py` (6 variants) | `POST /api/oracle` (`GanymedeOrchestrator.create_oracle`) |
| `pki_oracle_go*.py` (7 variants) | `POST /api/oracle/{id}/go` (`GanymedeOrchestrator.send_go`) |
| `pki_oracle_extract.py`, `check_harvest.py` | `POST /api/oracle/{id}/harvest` (`GanymedeOrchestrator.harvest`) |
| `pki_swarm_extract.py` | `POST /api/swarm/harvest` (`GanymedeOrchestrator.harvest_swarm`) |
| `final_synthesis.py`, `powell_final_resolution.py`, `tokenized_land_resolution.py` | `POST /api/synthesize` (`GanymedeOrchestrator.synthesize`) |
| `hualapai_harvest.py` | `POST /api/orchestrate` (legacy single-shot) |
| `inspect_*.py`, `check_imports.py` | One-off API discovery — no replacement needed |
| `mirror_identity_extraction.py`, `meta_deep_dive.py`, `pki_oracle_correct_mil.py` | Run-specific; see referencing experiment doc |

## Script-by-script reference

### Triage (Phase 1)
- `phase1_triage.py` — GPS Failure 72-hour scenario (ref: [GPS run](../02_GPS_Failure_72hr_Triage.md)).
- `meta_triage.py` — Meta-query asking the Umpire to design a "max extent" test scenario.
- `meta_triage_alt.py` — Secondary meta-query for an alternative theater.
- `meta_deep_dive.py` — Clarification query about the ESP Collective's nature (ref: [Mirror Protocol](../../concepts/The_Ganymede_Mirror_Protocol.md)).
- `mirror_triage.py` — Phase 1 triage of "Ganymede Mirror vs. Status Quo" collision.
- `amnesia_triage.py` — Phase 1 triage of the 60-second amnesia event.
- `amnesia_closed_loop.py` — Closed-loop variant asking the Umpire to specify its own oracle requirements.
- `amnesia_refactor.py` — Asked the Umpire to translate jargon prompts to plain language.
- `surgical_english_reset.py` — Generated a plain-English Human Nuance Oracle prompt.
- `nuance_prime_alignment.py` — Re-aligned the Umpire's amnesia resolution under the Nuance Prime axiom.

### PKI Oracle init (Phase 2 step 1)
- `pki_oracle_init.py` — PNT Network Sovereignty (ref: [GPS run](../02_GPS_Failure_72hr_Triage.md)).
- `pki_oracle_init_jit.py` — JIT Logistics.
- `pki_oracle_init_mil.py` — Military Decision Pathing.
- `pki_oracle_init_failsafe.py` — Nuclear Command Fail-Safe (ref: [60s Amnesia run](../04_60s_Amnesia_Mirror_Swarm.md)).
- `pki_oracle_init_finance.py` — Financial Liquidity (ref: 60s Amnesia run).
- `pki_oracle_init_psych.py` — Psychological Amnesia / TGA (ref: 60s Amnesia run).

### PKI Oracle GO signal (Phase 2 step 2)
- `pki_oracle_go.py` — for PNT.
- `pki_oracle_go_jit.py` — for JIT.
- `pki_oracle_go_mil.py` — for Military.
- `pki_oracle_go_failsafe.py` / `pki_oracle_go_failsafe_final.py` — for Fail-Safe (two attempts).
- `pki_oracle_go_finance.py` — for Financial Liquidity.
- `pki_oracle_go_psych.py` — for Psychological Amnesia.
- `pki_oracle_correct_mil.py` — Re-issued Military Oracle prompt with corrected plain-language framing.

### Extraction (Phase 2 step 3)
- `pki_oracle_extract.py` — Single-Oracle Truth Packet extraction (PNT).
- `pki_swarm_extract.py` — Parallel extraction across the Fail-Safe / Financial / Psychological swarm.
- `check_harvest.py` — Status-check query to see whether Deep Research had finished.

### Synthesis (Phase 3)
- `final_synthesis.py` — 60-second amnesia 9D synthesis from the three Truth Packets (ref: [60s Amnesia run](../04_60s_Amnesia_Mirror_Swarm.md)).
- `powell_final_resolution.py` — Powell collision Convergence Theorem synthesis (ref: [Powell run](../03_Powell_Validation_Event.md)).
- `tokenized_land_resolution.py` — Tokenized Land Gambit synthesis (Argentina-style sovereign-debt-via-RWA scenario; not yet documented as a standalone experiment).

### Run-specific one-offs
- `hualapai_harvest.py` — The original first end-to-end run (ref: [Hualapai run](../01_Hualapai_Water_Crisis.md)).
- `mirror_identity_extraction.py` — Asked a "Mirror Protocol" notebook to define its own dimensional bias profile. **Note:** this script writes to a deprecated artifact path (`~/.gemini/antigravity/brain/.../artifacts/The_Mirror_Profile.md`); the output was never ingested into the repo.

### API discovery (no longer needed)
- `inspect_chat.py`, `inspect_chat_methods.py`, `inspect_client.py` — one-off `dir()` introspection used to discover the `notebooklm-py` API surface.
- `check_imports.py` — verified ChatGoal / ChatResponseLength / ChatMode imports.

## Notes on hardcoded notebook IDs

Several scripts embed concrete NotebookLM notebook IDs (e.g. PNT
`67fbf8e2-66a5-4474-b83a-7426ec9fdc50`, Failsafe `2c5d6695-...`, etc.).
Those notebooks may have been deleted from the user's NotebookLM workspace
since the run; the IDs are preserved here only as run receipts. The
productized API exposes `notebook_id` as a per-call parameter.
