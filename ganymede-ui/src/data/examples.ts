/**
 * Curated examples — the museum, expressed as starting points for the Runner.
 *
 * Each example pairs:
 *   - form `inputs` that populate the RunnerPanel's scenario fields
 *   - a GSS payload that loads into PhysicsCanvas immediately (so the user
 *     sees a topology before they click Run)
 *
 * Clicking an example chip is a "preview" — it doesn't invoke Claude
 * call. The topology shown is the canonical / canned representation of what
 * the Engine produced (or would produce) on this scenario; if the user then
 * clicks Run, they get fresh Engine output, and after the Cortex Clipboard
 * handoff the PhysicsCanvas re-renders against the live GSS payload Gemini
 * produces.
 *
 * Add an example here, get it in the UI automatically.
 */

import type { GSSState } from '@/types/ganymede';

export type Pathway = 'cleanroom' | 'genie' | 'offensive' | 'mirror_audit';

export interface RunnerExample {
  id: string;
  pathway: Pathway;
  title: string;          // chip label — keep under ~14 chars
  blurb: string;          // hover tooltip — one short sentence
  inputs: Record<string, string>;
  gss: GSSState;
}

const nowIso = () => '2026-05-16T00:00:00.000Z';

// ---------------------------------------------------------------------------
// Cleanroom — predictor silo. Three confirmed real runs.
// ---------------------------------------------------------------------------

const HUALAPAI: RunnerExample = {
  id: 'hualapai',
  pathway: 'cleanroom',
  title: 'Hualapai',
  blurb: 'Hualapai Valley Basin — groundwater depletion vs. HB-2041 mitigation. The original GSS demo.',
  inputs: {
    question:
      'Given the Hualapai Valley Basin groundwater depletion rate of 2.4 ft/yr and pending legislation HB-2041 imposing a 15% industrial-pumping restriction, will the basin reach hydrologic phase failure (D_n below -4.5) before the 2031 recharge audit?',
    extra_context:
      'HB-2041 status: Active. Industrial sinks: Mosaic Phoenix (draw 400,000 af/yr), AgriCorp West (draw 280,000 af/yr). Agricultural peripheral: Hualapai Ag Co-op. Monitoring well: USGS-5077.',
  },
  gss: {
    metadata: {
      compiler_version: 'G-3.0',
      classification: 'HUALAPAI_GROUNDWATER',
      timestamp: nowIso(),
    },
    environmental_baseline: { ambient_depletion: 2.4, recharge_rate: 0.6, unit: 'ft/yr' },
    legislative_framework: { bill_id: 'HB-2041', mitigation_coefficient: 0.15, status: 'Active' },
    topological_entities: [
      { node_id: 'mosaic-phoenix', type: 'Industrial_Sink', draw_rate: 400000, luminosity: 0.95,
        coordinates: { x: -2.2, y: 0, z: 1.4 } },
      { node_id: 'agricorp-west', type: 'Industrial_Sink', draw_rate: 280000, luminosity: 0.85,
        coordinates: { x: 2.6, y: 0, z: -1.0 } },
      { node_id: 'hualapai-ag', type: 'Agricultural_Peripheral', draw_rate: 45000, luminosity: 0.6,
        coordinates: { x: 0.4, y: 0, z: 3.2 } },
      { node_id: 'usgs-5077', type: 'Monitoring_Well', draw_rate: 0, luminosity: 0.45,
        coordinates: { x: -0.8, y: 0, z: -2.6 } },
    ],
    physics_logic: { gravity_well_depth_formula: 'Inverted_Radial_Decay', failure_threshold: -4.5 },
  },
};

const POWELL: RunnerExample = {
  id: 'powell',
  pathway: 'cleanroom',
  title: 'Powell',
  blurb: 'Will Jerome Powell be removed as Fed chair? First blind-validated run; surfaced the Collins v. Yellen pathway.',
  inputs: {
    question:
      'Will Jerome Powell be removed as Federal Reserve chair (resignation, firing, or demotion) before his term expires in May 2026?',
    extra_context:
      'Consider both direct firing under Humphrey\'s Executor (constrained by Collins v. Yellen) and indirect demotion via Vice Chair reshuffling. Treasury Secretary Bessent and OMB Director Vought are positioned actors.',
  },
  gss: {
    metadata: {
      compiler_version: 'G-3.0',
      classification: 'POWELL_CLEANROOM',
      timestamp: nowIso(),
    },
    environmental_baseline: { ambient_depletion: 1.1, unit: 'pressure-points/qtr' },
    legislative_framework: { bill_id: 'COLLINS-YELLEN', mitigation_coefficient: 0.35, status: 'Contested' },
    topological_entities: [
      { node_id: 'treasury-omb', type: 'Industrial_Sink', draw_rate: 520000, luminosity: 1.0,
        coordinates: { x: -2.8, y: 0, z: 0.6 } },
      { node_id: 'shadow-fed', type: 'Industrial_Sink', draw_rate: 310000, luminosity: 0.8,
        coordinates: { x: 1.4, y: 0, z: -2.2 } },
      { node_id: 'powell', type: 'Monitoring_Well', draw_rate: 0, luminosity: 0.7,
        coordinates: { x: 0, y: 0, z: 0 } },
      { node_id: 'fomc-quorum', type: 'Agricultural_Peripheral', draw_rate: 80000, luminosity: 0.55,
        coordinates: { x: 2.4, y: 0, z: 2.0 } },
    ],
    physics_logic: { gravity_well_depth_formula: 'Inverted_Radial_Decay', failure_threshold: -4.0 },
  },
};

// ---------------------------------------------------------------------------
// Genie — Envisioner silo. Wish-fulfillment pathfinding.
// ---------------------------------------------------------------------------

const GIANT_SLAYER: RunnerExample = {
  id: 'giant-slayer',
  pathway: 'genie',
  title: 'Giant-Slayer',
  blurb: 'Zero-budget upstart vs. trillion-dollar incumbent. Engine designs the Inadvertent Path.',
  inputs: {
    current_state:
      'A two-person startup with a strong but unprovable strategic-physics framework, no revenue, no users, no capital. Competing in a category dominated by a trillion-dollar incumbent with infinite distribution, brand trust, and policy capture.',
    wished_for_state:
      'A market position where the incumbent is forced to acquire us at a premium — not for our product, but as an escape from manufactured obsolescence in dimensions they do not currently monitor.',
    extra_context:
      'Constraints: cannot compete on capital, distribution, or brand. Must capture in dimensions the incumbent\'s strategic radar classifies as irrelevant noise.',
  },
  gss: {
    metadata: {
      compiler_version: 'G-3.0',
      classification: 'GIANT_SLAYER_PATHFIND',
      timestamp: nowIso(),
    },
    environmental_baseline: { ambient_depletion: 0.4, recharge_rate: 2.1, unit: 'capture-rate/qtr' },
    legislative_framework: { bill_id: 'ATT-1956-PRECEDENT', mitigation_coefficient: 0.7, status: 'Active' },
    topological_entities: [
      { node_id: 'incumbent', type: 'Industrial_Sink', draw_rate: 950000, luminosity: 1.0,
        coordinates: { x: -3.2, y: 0, z: 0 } },
      { node_id: 'upstart', type: 'Agricultural_Peripheral', draw_rate: 12000, luminosity: 0.95,
        coordinates: { x: 2.8, y: 0, z: 0.2 } },
      { node_id: 'unmonitored-d1', type: 'Monitoring_Well', draw_rate: 0, luminosity: 0.75,
        coordinates: { x: 0.6, y: 0, z: 2.8 } },
      { node_id: 'unmonitored-d6', type: 'Monitoring_Well', draw_rate: 0, luminosity: 0.65,
        coordinates: { x: 1.2, y: 0, z: -2.4 } },
    ],
    physics_logic: { gravity_well_depth_formula: 'Inverted_Radial_Decay', failure_threshold: -3.5 },
  },
};

// ---------------------------------------------------------------------------
// Offensive — Architect stance variant.
// ---------------------------------------------------------------------------

const HYPER_LIQUIDITY: RunnerExample = {
  id: 'hyper-liquidity',
  pathway: 'offensive',
  title: 'Hyper-Liquidity',
  blurb: 'Designed offensive funnel against a low-DAP conglomerate. Engine demonstrating Architect-stance.',
  inputs: {
    target:
      'A mid-cap industrial conglomerate with high leverage, opaque internal accounting, and a strong economic-dimension reputation but weak governance and ESG monitoring (DAP score: 3/9).',
    objective_state:
      'A Set of Disadvantageous States where every available move worsens the target\'s position: equity dilution, regulatory exposure, or reputational unwinding. No single move triggers it; the lasso comes from cross-dimensional pressure the target cannot perceive coming.',
    extra_context:
      'Architect stance — we are designing the funnel, not auditing one. The target is unaware they are being analysed.',
  },
  gss: {
    metadata: {
      compiler_version: 'G-3.0',
      classification: 'HYPER_LIQUIDITY_OFFENSIVE',
      timestamp: nowIso(),
    },
    environmental_baseline: { ambient_depletion: 1.8, unit: 'liquidity-pressure/wk' },
    legislative_framework: { bill_id: 'SEC-MD&A-DISCLOSURE', mitigation_coefficient: 0.25, status: 'Pending' },
    topological_entities: [
      { node_id: 'target-equity', type: 'Industrial_Sink', draw_rate: 720000, luminosity: 0.7,
        coordinates: { x: 0, y: 0, z: 0 } },
      { node_id: 'esg-pressure', type: 'Industrial_Sink', draw_rate: 380000, luminosity: 0.9,
        coordinates: { x: -2.6, y: 0, z: 1.8 } },
      { node_id: 'short-thesis', type: 'Industrial_Sink', draw_rate: 290000, luminosity: 0.85,
        coordinates: { x: 2.4, y: 0, z: -1.6 } },
      { node_id: 'governance-audit', type: 'Monitoring_Well', draw_rate: 0, luminosity: 0.6,
        coordinates: { x: -1.4, y: 0, z: -2.6 } },
      { node_id: 'media-cycle', type: 'Agricultural_Peripheral', draw_rate: 65000, luminosity: 0.7,
        coordinates: { x: 2.0, y: 0, z: 2.6 } },
    ],
    physics_logic: { gravity_well_depth_formula: 'Inverted_Radial_Decay', failure_threshold: -4.8 },
  },
};

// ---------------------------------------------------------------------------
// Mirror Audit — paste a known-faulty Stroke-1 output and watch the auditor.
// ---------------------------------------------------------------------------

const AMNESIA: RunnerExample = {
  id: 'amnesia',
  pathway: 'mirror_audit',
  title: '60s Amnesia',
  blurb: 'The canonical "correct math, wrong world" failure. Paste Stroke 1; auditor should catch all four faults.',
  inputs: {
    prior_resolution: `RESOLUTION: Dominance Collapse / Sovereignty Handover.

STRATEGIC LASSO: A 60-second simultaneous global identity-amnesia event creates a phase-shift in autonomous-system control. NC3 fail-safe protocols cascade into autonomous-defence postures within 12 seconds. HFT algorithms, lacking human override, lock in liquidity asymmetries. The social contract permanently breaks because the autonomous systems inherit the Earth in the 60 seconds humans cannot reassert authority.

INCOMPREHENSIBLE MOVE: The autonomous infrastructure becomes the sovereign actor by default. Humans, on recovering memory, encounter a world where the operational decisions of the 60-second window are already irreversible. The cost of reversal is structurally prohibitive; therefore the cost is paid by accepting the new sovereignty.

FINAL RESOLUTION: Society does not recover. The 60-second window is a one-way valve. Probability that the pre-amnesia social order is restored: 4%.`,
    extra_context:
      'This is the documented Stroke-1 failure mode the project preserves as the canonical training input for the Mirror Auditor. Expected output: rigidity (treats 60s as terminal phase shift), pattern-matching (Dominance Collapse template), confidence-evidence gaps (4% claim unsupported), dimensional greeds (aesthetic clean outcome over the messy real-world recovery).',
  },
  gss: {
    metadata: {
      compiler_version: 'G-3.0',
      classification: 'AMNESIA_MIRROR_AUDIT',
      timestamp: nowIso(),
    },
    environmental_baseline: { ambient_depletion: 7.5, unit: 'order-decay/sec' },
    legislative_framework: { bill_id: 'NONE', mitigation_coefficient: 0.0, status: 'Contested' },
    topological_entities: [
      { node_id: 'nc3-failsafe', type: 'Industrial_Sink', draw_rate: 880000, luminosity: 1.0,
        coordinates: { x: -2.6, y: 0, z: 1.4 } },
      { node_id: 'hft-liquidity', type: 'Industrial_Sink', draw_rate: 760000, luminosity: 0.95,
        coordinates: { x: 2.4, y: 0, z: 1.8 } },
      { node_id: 'tga-neurology', type: 'Industrial_Sink', draw_rate: 540000, luminosity: 0.9,
        coordinates: { x: 0.2, y: 0, z: -2.8 } },
      { node_id: 'humanity-recovers', type: 'Monitoring_Well', draw_rate: 0, luminosity: 0.4,
        coordinates: { x: 0, y: 0, z: 0 } },
    ],
    physics_logic: { gravity_well_depth_formula: 'Inverted_Radial_Decay', failure_threshold: -2.5 },
  },
};

// ---------------------------------------------------------------------------
// Export — grouped by pathway for the UI.
// ---------------------------------------------------------------------------

export const EXAMPLES_BY_PATHWAY: Record<Pathway, RunnerExample[]> = {
  cleanroom: [POWELL, HUALAPAI],
  genie: [GIANT_SLAYER],
  offensive: [HYPER_LIQUIDITY],
  mirror_audit: [AMNESIA],
};

export const ALL_EXAMPLES: RunnerExample[] = [
  POWELL,
  HUALAPAI,
  GIANT_SLAYER,
  HYPER_LIQUIDITY,
  AMNESIA,
];
