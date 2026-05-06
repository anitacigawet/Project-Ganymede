# Experiment 02 — GPS Failure (72-hour Triage)

**Scenario:** "The sudden, absolute failure of all satellite-based GPS systems globally for 72 hours."
**Status:** ⏸ Paused mid-swarm. PNT Oracle completed and produced a notable finding; remaining oracles were initialized but not harvested. The user reset the run after a prompt-jargon issue.
**Significance:** First multi-oracle swarm run. Validated the Phase-0/1/2 mechanics on a second scenario beyond Hualapai. Surfaced the surgical-prompt lesson and the STL/Iridium spoofing finding.

## Phase 1 — Triage Hit List

Submitted to the 9D Chess Engine with an explicit "limit to 3-5 high-friction subjects" constraint to avoid runaway oracle creation. The Umpire returned four:

1. **PNT Network Sovereignty** — operational readiness of terrestrial backup systems (eLoran, Chayka, STL).
2. **JIT Supply Chain Terminal Failure Points** — time-to-terminal-failure for major ports (Singapore, Rotterdam, Long Beach) under GPS-denial.
3. **Regional Military Decision Pathing** — escalation behaviors during PNT signal loss.
4. **Financial Market Time-Sync Vulnerabilities** — impact on HFT systems that rely on GPS atomic timing. *(marked optional)*

Per the runaway-prevention guardrail, the user approved all four conceptually but instructed the swarm be initialized one at a time.

## Phase 2 — Swarm

### Oracle 1: PNT Network Sovereignty — ✅ Complete

**Notebook:** `PKI_PNT_Network_Sovereignty_368e6ed1`
**Surgical prompt:**
> "Conduct deep research into the current operational readiness and 'cold start' capabilities of terrestrial, land-based backup navigation systems (eLoran, Chayka, and STL). Identify which specific nations (specifically the USA, China, Russia, and the UK) have active infrastructure that can be fully activated within 72 hours of a total satellite signal blackout."

**Process:**
- Persona-locked successfully.
- Deep Research session triggered, took several minutes.
- Critical operational discovery: NotebookLM Deep Research is **interactive** — the engine produces results that land in the Source Panel but require a manual "Import" click to enter the notebook's queryable knowledge base. The Python client could not trigger Import; the browser subagent had to click it. (Captured in [`learnings/Iterative_Operational_Learnings.md`](../learnings/Iterative_Operational_Learnings.md) as the "Import Constraint.")

**Harvest:** 21 sources imported; first extraction timed out (cold-start indexing); retry succeeded.

**Truth Packet (key findings):**
- **USA:** No nationwide terrestrial eLoran. Backup is STL via Iridium. **Critical vulnerability:** March 2026 analysis showed STL secret keys can be cloned in under 10 minutes from standard SIM readers, enabling massive spoofing and device cloning during a GPS outage. `[SRC-ARXIV-IRID:c8d1e4]`
- **Russia:** Chayka system (eLoran equivalent) fully operational across most of Russian landmass. `[SRC-GEOPOL-PNT:t3u6v9]`
- **China:** Nationwide high-precision eLoran on track for late-2026 completion. `[SRC-RNTF-2023:b1c8y5]`
- **South Korea:** 43 differential stations providing 100% nationwide terrestrial coverage. `[SRC-GEOPOL-PNT:t3u6v9]`

The engine's "Hidden Dimension" hint from Phase 1 was retroactively confirmed: the U.S. backup is itself spoofable, which means a 72-hour blackout would not just degrade U.S. navigation — an actor with high dimensional awareness could clone the navigation signatures of U.S. logistics nodes during the outage.

### Oracle 2: JIT Logistics — ⏸ Initialized only

**Notebook:** `PKI_JIT_Logistics_92a1b7e4`
**Status:** Persona locked, GO signal sent, Deep Research session in "web scour" phase when the run was reset. Not harvested. Notebook later deleted by user as part of the reset.

### Oracle 3: Military Decision Pathing — ❌ Reset before harvest

**Notebook:** `PKI_Military_Decision_Pathing_39b2c8d1` (initial)
**Status:** First prompt used Umpire jargon ("Decision Path Funneling," "The Horus Trap"). The user flagged this — research bots cannot resolve internal 9D vocabulary into real-world sources.

**Corrected prompt** translated the same intent into OSINT-friendly plain English (CSIS / RAND / IISS reports on GNSS resilience, eLoran, INS, EW exercises). User then reconsidered the sensitivity of querying for military SOPs and we agreed to soft-pivot to a Risk Analysis framing.

Before that ran, the user opted to fully reset the scenario: cleared the 9D Chess Engine chat, deleted the swarm notebooks, treated the entire run as a dry-run. We pivoted to scenario brainstorming, which led to the [Mirror epiphany](../concepts/The_Ganymede_Mirror_Protocol.md) and the proposed [Compute Autarky](05_Pending_Compute_Autarky.md) run.

## Lessons captured (full set)

1. **Deep Research has a UI gate.** Findings land in the Source Panel and require an Import click before the Oracle can cite them. The Python API does not expose this; the browser subagent or the human has to click it. Recorded in `learnings/Iterative_Operational_Learnings.md`.
2. **Surgical, plain-language Oracle prompts.** Umpire jargon (Horus, ROEM, DAI, "Decision Path Funneling") is internal vocabulary. It will return zero useful sources or, worse, narrow the research into game-theory papers. Translate first.
3. **Sensitivity-aware framing.** Direct queries for "SOPs of major militaries" can read as suspicious. OSINT framing (think-tank reports, exercise post-mortems, public CRS / RAND / CSIS analyses) gets the same data through a professional lens.
4. **Authentication wall.** NotebookLM session cookies expire. The recovery is `notebooklm.exe login` from `venv_312\Scripts\` — not `notebooklm-py login` (which is not an npm package).
5. **One oracle at a time, manually approved.** Concretely justified by this run: had we batch-spun all four, three of them would have been wasted notebook-creations on prompts that needed rework or never made it to harvest.

## Source artifacts

- [`scripts/phase1_triage.py`](scripts/phase1_triage.py)
- [`scripts/pki_oracle_init.py`](scripts/pki_oracle_init.py) / [`scripts/pki_oracle_go.py`](scripts/pki_oracle_go.py) / [`scripts/pki_oracle_extract.py`](scripts/pki_oracle_extract.py) (PNT)
- [`scripts/pki_oracle_init_jit.py`](scripts/pki_oracle_init_jit.py) / [`scripts/pki_oracle_go_jit.py`](scripts/pki_oracle_go_jit.py)
- [`scripts/pki_oracle_init_mil.py`](scripts/pki_oracle_init_mil.py) / [`scripts/pki_oracle_correct_mil.py`](scripts/pki_oracle_correct_mil.py) / [`scripts/pki_oracle_go_mil.py`](scripts/pki_oracle_go_mil.py)
- [`scripts/check_harvest.py`](scripts/check_harvest.py)
