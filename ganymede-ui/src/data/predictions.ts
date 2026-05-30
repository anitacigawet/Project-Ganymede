/**
 * Pre-registered predictions ledger.
 *
 * The bulletin board at `/predictions` reads from this file. Each entry
 * represents a Cleanroom-pathway prediction the project has made BEFORE
 * its resolution date — pre-registration discipline per
 * `docs/experiments/pathways/prediction_cleanroom.md`.
 *
 * Predictions get added here when they land in a run record. When a
 * prediction's resolution date arrives:
 *   1. Validate against reality (LMArena rank / Polymarket price / etc).
 *   2. Update `status` to "validated" | "falsified" | "partial" | "inconclusive".
 *   3. Fill in `outcome` with the observed result.
 *   4. Update the underlying run record in `docs/experiments/runs/`.
 *
 * The file is hand-edited. Could later become a backend endpoint that
 * scans run records automatically (see TASKS.md § P1-05).
 */

export type PredictionStatus =
  | 'pending'
  | 'validated'
  | 'falsified'
  | 'partial'
  | 'inconclusive';

export interface RiskMechanism {
  side: string;
  /** What to watch for that would trigger this mechanism. */
  watch_for: string;
}

export interface Prediction {
  id: string;
  scenario: string;
  /** One-line statement of what we expect to happen. */
  primary_claim: string;
  /** Mechanism = WHY we expect this outcome. Audited Stroke 3 reasoning. */
  mechanism: string;
  /** Risk mechanisms that would falsify the prediction. */
  risk_mechanisms: RiskMechanism[];
  /** ISO 8601 date when the prediction can be validated. */
  resolution_date: string;
  /** When the prediction was timestamp-locked. */
  pre_registered_at: string;
  confidence: 'low' | 'medium' | 'medium-high' | 'high';
  pathway: 'cleanroom' | 'genie' | 'offensive';
  /** Whether this prediction was audited (Mirror Auditor + optionally Bridge). */
  audited: boolean;
  /** Did the Connection Bridge contribute to the prediction? */
  bridge_extended: boolean;
  /** Link to the run record (path inside docs/). */
  run_record: string;
  status: PredictionStatus;
  /** Filled in when status leaves "pending". */
  outcome?: string;
  /** Additional notes — historical context, methodology notes, etc. */
  notes?: string;
}

export const PREDICTIONS: Prediction[] = [
  {
    id: 'lmarena-2026-06-30',
    scenario:
      'Will Anthropic still be ranked #1 on the LMArena public AI model leaderboard at the end of June 2026? Polymarket pricing: Anthropic 77%, Google 20%.',
    primary_claim:
      'Polymarket’s 77% Anthropic confidence is approximately accurate. Anthropic retains #1 on LMArena at end-of-June 2026.',
    mechanism:
      'Anthropic’s #1 position reflects real social/market capital from Go-like benchmark mindshare capture + Horus-like legitimacy as industry standard. The Bridge’s catch: Anthropic’s metacognitive adaptation capability means they’re not locked into a static ROEM trajectory — they can shift their own dimensional awareness mid-cycle in response to Google’s moves.',
    risk_mechanisms: [
      {
        side: 'Anthropic',
        watch_for:
          'Tunnel-vision failure — over-optimizes for LMArena to the detriment of broader capabilities. Watch for notable capability regression on non-LMArena benchmarks during May–June.',
      },
      {
        side: 'Google',
        watch_for:
          'Architectural disruption — substantially novel architecture (not just minor Gemini-N+1) during May–June. Watch for paradigm-shift announcements or evaluation-framework changes.',
      },
      {
        side: 'Anthropic (safety mechanism)',
        watch_for:
          'Per Bridge: Anthropic’s metacognitive adaptation is a MOAT, not a vulnerability. Watch whether they visibly demonstrate mid-cycle adaptation during May–June.',
      },
    ],
    resolution_date: '2026-06-30',
    pre_registered_at: '2026-05-26T06:08:00Z',
    confidence: 'medium-high',
    pathway: 'cleanroom',
    audited: true,
    bridge_extended: true,
    run_record: 'docs/experiments/runs/06_LMArena_Anthropic_Cleanroom.md',
    status: 'pending',
    notes:
      'First Cleanroom run to exercise full pre-registration discipline + Bicameral Convergence Level 1 audit. Audited Stroke 3 supersedes the un-audited Stroke 1 (which predicted Set-like usurpation against the market) — the contrast itself is the methodological win.',
  },
];

/**
 * Days until a prediction resolves. Negative if past.
 * Uses the time of day the resolution_date denotes (00:00 UTC).
 */
export function daysUntilResolution(prediction: Prediction): number {
  const target = new Date(prediction.resolution_date).getTime();
  const now = Date.now();
  return Math.floor((target - now) / (1000 * 60 * 60 * 24));
}
