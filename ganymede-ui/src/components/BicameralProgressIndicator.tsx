'use client';

/**
 * BicameralProgressIndicator — live-progress UI for Bicameral Convergence Level 2 loops.
 *
 * Renders iteration counter, current side (Engine synthesizing / Bridge auditing),
 * cancel button, and terminal-state messaging (CONVERGED / HARD_CAP_REACHED).
 *
 * The five mandatory operator control surfaces for Bicameral Convergence Level 2
 * per docs/concepts/Bicameral_Convergence.md:
 *   1. Visual transparency — this component (iteration counter + side indicator)
 *   2. Cancel endpoint — wired via onCancel prop → backend's
 *      POST /api/v2/sessions/{id}/cancel
 *   3. Minimum inter-iteration delay — backend-enforced
 *   4. Hard iteration cap — backend-enforced; surfaced here on HARD_CAP_REACHED
 *   5. Operator approval gate for new Oracle spawn — Level 3, stubbed here
 *
 * Designed to be self-contained: takes pure data props, no fetch or state
 * machinery of its own. Parent (RunnerPanel) owns the WebSocket subscription
 * and translates BICAMERAL_ITERATION_START/END/CONVERGED/HARD_CAP_REACHED
 * events into the prop shape this component renders.
 *
 * E1-05 in the ROADMAP's Silo 2 Phase E1.
 */

import { Activity, AlertTriangle, CheckCircle2, X } from 'lucide-react';

export type BicameralSide = 'engine' | 'bridge' | 'idle';
export type ConvergenceCriterion = 'no_new_structural' | 'resolution_stable';

export interface BicameralProgressState {
  /** Is a Bicameral loop currently running on the session? */
  running: boolean;
  /** Current iteration number (1-indexed) when running; null when idle. */
  currentIteration: number | null;
  /** Operator-supplied iteration cap. */
  maxIterations: number | null;
  /** Which side of the mirror-bounce is currently active. */
  currentSide: BicameralSide;
  /** Number of new STRUCTURAL/IMPLIED bridges surfaced in the most recent
   *  completed iteration, per BICAMERAL_ITERATION_END payload. Null while
   *  the iteration is still mid-flight. */
  newBridgesSurfaced: number | null;
  /** Set when the loop converged. */
  convergenceCriterion: ConvergenceCriterion | null;
  /** Set when the loop hit max_iterations without converging. */
  hardCapReached: boolean;
}

export interface BicameralProgressIndicatorProps extends BicameralProgressState {
  /** Cancel button click handler. Parent fires POST /api/v2/sessions/{id}/cancel.
   *  Disabled (button hidden) when the loop is not running. */
  onCancel: () => void;
  /** Session ID for display + the cancel call's target. Null hides the
   *  indicator entirely. */
  sessionId: string | null;
}

/**
 * Map current side to a short label + an animated icon.
 */
function sideMeta(side: BicameralSide): { label: string; icon: React.ReactNode; tint: string } {
  switch (side) {
    case 'engine':
      return {
        label: 'Engine synthesizing',
        icon: <Activity className="h-3.5 w-3.5 animate-pulse" />,
        tint: 'text-amber-300',
      };
    case 'bridge':
      return {
        label: 'Bridge auditing',
        icon: <Activity className="h-3.5 w-3.5 animate-pulse" />,
        tint: 'text-cyan-300',
      };
    case 'idle':
    default:
      return {
        label: 'Idle',
        icon: <Activity className="h-3.5 w-3.5 opacity-40" />,
        tint: 'text-slate-400',
      };
  }
}

function criterionLabel(criterion: ConvergenceCriterion): string {
  switch (criterion) {
    case 'no_new_structural':
      return 'No new structural bridges surfaced';
    case 'resolution_stable':
      return 'Final resolution stabilized across iterations';
  }
}

export function BicameralProgressIndicator(props: BicameralProgressIndicatorProps) {
  const {
    running,
    currentIteration,
    maxIterations,
    currentSide,
    newBridgesSurfaced,
    convergenceCriterion,
    hardCapReached,
    onCancel,
    sessionId,
  } = props;

  // Hide when there's no session AND no terminal-state to surface.
  if (!sessionId && !convergenceCriterion && !hardCapReached) {
    return null;
  }

  // Terminal: CONVERGED
  if (convergenceCriterion && !running) {
    return (
      <div className="flex items-start gap-3 rounded-md border border-emerald-700/40 bg-emerald-950/40 p-3 text-sm">
        <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-300" />
        <div className="flex-1">
          <div className="font-medium text-emerald-200">Bicameral loop converged</div>
          <div className="mt-0.5 text-xs text-emerald-300/80">
            Criterion: {criterionLabel(convergenceCriterion)}
            {currentIteration !== null && (
              <span>
                {' '}· after {currentIteration} iteration
                {currentIteration === 1 ? '' : 's'}
              </span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Terminal: HARD_CAP_REACHED
  if (hardCapReached && !running) {
    return (
      <div className="flex items-start gap-3 rounded-md border border-amber-700/40 bg-amber-950/40 p-3 text-sm">
        <AlertTriangle className="h-4 w-4 shrink-0 text-amber-300" />
        <div className="flex-1">
          <div className="font-medium text-amber-200">
            Bicameral loop hit hard cap without converging
          </div>
          <div className="mt-0.5 text-xs text-amber-300/80">
            Reached {maxIterations ?? '?'} iterations. The partial result is
            preserved on the session; re-run with a higher iteration cap or
            accept the partial.
          </div>
        </div>
      </div>
    );
  }

  // Running: live progress.
  if (!running) return null;

  const side = sideMeta(currentSide);
  const iterationLabel =
    currentIteration !== null && maxIterations !== null
      ? `Iteration ${currentIteration} of ${maxIterations}`
      : 'Iteration —';

  return (
    <div className="flex items-center gap-3 rounded-md border border-slate-700/50 bg-slate-900/60 p-3 text-sm">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-200">{iterationLabel}</span>
          <span className="text-slate-500">·</span>
          <span className={`inline-flex items-center gap-1.5 ${side.tint}`}>
            {side.icon}
            <span>{side.label}</span>
          </span>
        </div>
        {newBridgesSurfaced !== null && (
          <div className="mt-1 text-xs text-slate-400">
            Last iteration surfaced {newBridgesSurfaced} new bridge
            {newBridgesSurfaced === 1 ? '' : 's'}
          </div>
        )}
      </div>
      <button
        type="button"
        onClick={onCancel}
        className="inline-flex items-center gap-1.5 rounded border border-rose-700/40 bg-rose-950/40 px-2.5 py-1.5 text-xs font-medium text-rose-200 transition hover:bg-rose-900/50"
        aria-label="Cancel the running Bicameral loop"
      >
        <X className="h-3.5 w-3.5" />
        <span>Cancel</span>
      </button>
    </div>
  );
}

/**
 * The neutral initial state for the indicator — useful as RunnerPanel's
 * starting value so the indicator can be unconditionally mounted without
 * null-shape checks.
 */
export const IDLE_BICAMERAL_STATE: BicameralProgressState = {
  running: false,
  currentIteration: null,
  maxIterations: null,
  currentSide: 'idle',
  newBridgesSurfaced: null,
  convergenceCriterion: null,
  hardCapReached: false,
};
