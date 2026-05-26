'use client';

/**
 * OrchestratorMindMap — live mind-map of the universal-logic-loop pipeline.
 *
 * Companion to LithographyView.  Both consume the same RunnerSnapshot; the
 * Lithography view is the metaphorical optics-box rendering (artistic),
 * this is the literal data-structure rendering (debuggable).  Lithography
 * is what you watch for the feel of a run; this is what you watch when you
 * need to know which oracle is on which subject and what came back.
 *
 *   scenario root   →  oracle cards (fanned, one per subject)  →  synthesis
 *
 * Adapts to the run mode:
 *   • triage     → scenario + blueprint card (single right node)
 *   • full_loop  → full fan-out (scenario → N oracles → synthesis)
 *   • synthesis  → scenario → synthesis (no oracle column)
 *   • idle       → empty-state placeholder
 *
 * Pure SVG, no library.  Edges are cubic béziers with status-driven colour
 * and a marching-ant animation while their target is in-flight.
 */

import React, { useMemo } from 'react';
import type { RunnerSnapshot, OracleProgress } from './RunnerPanel';

export interface OrchestratorMindMapProps {
  snapshot: RunnerSnapshot;
  onSwitchToRunner?: () => void;
}

// ── viewBox geometry (vertical / portrait) ──────────────────────────────────
// Scenario stacks at the top, oracles cascade down the middle, synthesis
// lands at the bottom.  Oracles alternate slightly left / right of centre so
// the edges fan visibly instead of all collapsing onto the same central
// trunk.  Layout matches the natural top-to-bottom reading order.
const VBW = 700;
const VBH = 1100;

const SCENARIO = { x: 190, y: 40,  w: 320, h: 130 };
const SYNTH    = { x: 190, y: 930, w: 320, h: 130 };

const ORACLE_W = 320;
const ORACLE_H = 84;
const ORACLE_X_CENTER = (VBW - ORACLE_W) / 2;   // 190
const ORACLE_X_OFFSET = 56;                      // alternation half-amplitude
const ORACLE_Y_MIN = 220;
const ORACLE_Y_MAX = 832;                        // slot top — slot bottom = 916

// Single-blueprint card used in triage mode (no oracle column, no synth).
const BLUEPRINT = { x: 160, y: 380, w: 380, h: 200 };

// ── helpers ─────────────────────────────────────────────────────────────────
function center(rect: { x: number; y: number; w: number; h: number }) {
  return { cx: rect.x + rect.w / 2, cy: rect.y + rect.h / 2 };
}

function oracleSlot(i: number, n: number): { x: number; y: number; w: number; h: number } {
  if (n <= 1) {
    return {
      x: ORACLE_X_CENTER,
      y: (ORACLE_Y_MIN + ORACLE_Y_MAX) / 2,
      w: ORACLE_W,
      h: ORACLE_H,
    };
  }
  const yRange = ORACLE_Y_MAX - ORACLE_Y_MIN;
  const y = ORACLE_Y_MIN + (yRange * i) / (n - 1);
  // Alternate left/right of the central trunk so edges to/from each oracle
  // have visibly distinct paths instead of stacking on the same vertical line.
  const xOffset = i % 2 === 0 ? -ORACLE_X_OFFSET : ORACLE_X_OFFSET;
  return {
    x: ORACLE_X_CENTER + xOffset,
    y,
    w: ORACLE_W,
    h: ORACLE_H,
  };
}

function oracleStatusColor(o: OracleProgress | undefined): {
  border: string; glow: string; label: string;
} {
  if (!o) return { border: 'rgba(100,116,139,0.55)', glow: 'rgba(100,116,139,0.25)', label: 'pending' };
  switch (o.status) {
    case 'requested':
      return { border: 'rgba(148,163,184,0.7)', glow: 'rgba(148,163,184,0.30)', label: 'requested' };
    case 'created':
      return { border: 'rgba(96,165,250,0.8)', glow: 'rgba(96,165,250,0.35)', label: 'created' };
    case 'researching':
      return { border: 'rgba(251,191,36,0.85)', glow: 'rgba(251,191,36,0.40)', label: 'researching' };
    case 'harvested':
      return { border: 'rgba(52,211,153,0.85)', glow: 'rgba(52,211,153,0.45)', label: 'harvested' };
    case 'failed':
      return { border: 'rgba(244,114,128,0.85)', glow: 'rgba(244,114,128,0.45)', label: 'failed' };
  }
}

function edgePath(from: { x: number; y: number }, to: { x: number; y: number }): string {
  // Vertical-orientation bezier — control points share x with their respective
  // endpoint, so when endpoints differ in x the curve eases smoothly into an
  // S-shape, and when endpoints share x it degenerates to a straight vertical
  // line.  Used for both scenario→oracle (down-fan) and oracle→synth (down-
  // converge) edges in the portrait layout.
  const dy = to.y - from.y;
  const cp1y = from.y + dy * 0.45;
  const cp2y = to.y - dy * 0.45;
  return `M${from.x},${from.y} C${from.x},${cp1y} ${to.x},${cp2y} ${to.x},${to.y}`;
}

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + '…' : s;
}

// ── root component ─────────────────────────────────────────────────────────
export function OrchestratorMindMap({
  snapshot, onSwitchToRunner,
}: OrchestratorMindMapProps) {
  const oracles = snapshot.oracles || [];
  const oracleN = oracles.length;
  const strokes = snapshot.strokes || [];
  const hasSynthesis = strokes.length > 0;
  const hasBlueprint = !!snapshot.blueprint;
  const isTriageOnly = snapshot.runMode === 'triage';
  const isSynthesisOnly = snapshot.runMode === 'synthesis';

  // Oracle slots resolved once per render so edge geometry shares them.
  const slots = useMemo(
    () => oracles.map((_, i) => oracleSlot(i, oracleN)),
    [oracles, oracleN],
  );

  // Scene composition mode.  Decides which nodes/edges appear.
  type Mode = 'idle' | 'triage' | 'synthesis_direct' | 'full';
  const mode: Mode = useMemo(() => {
    if (isTriageOnly && hasBlueprint) return 'triage';
    if (oracleN > 0) return 'full';
    if (isSynthesisOnly || hasSynthesis) return 'synthesis_direct';
    if (snapshot.running) return 'full'; // pre-blueprint, show pipe scaffold
    return 'idle';
  }, [isTriageOnly, isSynthesisOnly, hasBlueprint, hasSynthesis, oracleN, snapshot.running]);

  const stageText = useMemo(() => {
    if (snapshot.hasError) return 'Errored';
    if (hasSynthesis) return 'Synthesised';
    if (mode === 'triage') return 'Triage Complete';
    if (oracleN > 0) {
      const done = oracles.filter(o => o.status === 'harvested' || o.status === 'failed').length;
      return `Harvesting ${done}/${oracleN}`;
    }
    if (snapshot.running) return 'Triage Firing';
    if (snapshot.scenarioSummary?.trim()) return 'Awaiting Run';
    return 'Empty';
  }, [snapshot.hasError, snapshot.running, snapshot.scenarioSummary, hasSynthesis, mode, oracles, oracleN]);

  return (
    <div className="omm-root">
      <div className="omm-header">
        <div className="omm-header-left">
          <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden>
            <circle cx="3"  cy="7"  r="1.6" fill="rgba(196,181,253,0.9)"/>
            <circle cx="7"  cy="3"  r="1.2" fill="rgba(196,181,253,0.7)"/>
            <circle cx="7"  cy="11" r="1.2" fill="rgba(196,181,253,0.7)"/>
            <circle cx="11" cy="7"  r="1.6" fill="rgba(196,181,253,0.9)"/>
            <path d="M3 7 L7 3 M3 7 L7 11 M3 7 L11 7" stroke="rgba(167,139,250,0.6)" strokeWidth="0.7" fill="none"/>
          </svg>
          <span className="omm-title">Orchestrator Mind Map</span>
          <span className="omm-divider"/>
          <span className="omm-pathway">{snapshot.pathway.replace('_', ' ')}</span>
        </div>
        <div className="omm-header-right">
          <span className="omm-stage-label">STATE</span>
          <span className="omm-stage-value">{stageText}</span>
          {onSwitchToRunner && (
            <button type="button" className="omm-btn" onClick={onSwitchToRunner}>
              <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden>
                <rect x="1" y="2" width="8" height="6" rx="1" stroke="currentColor" fill="none" strokeWidth="0.9"/>
                <line x1="3" y1="4" x2="7" y2="4" stroke="currentColor" strokeWidth="0.7"/>
                <line x1="3" y1="6" x2="6" y2="6" stroke="currentColor" strokeWidth="0.7"/>
              </svg>
              Runner
            </button>
          )}
        </div>
      </div>

      <div className="omm-body">
        {mode === 'idle' ? (
          <EmptyState />
        ) : (
          <svg
            viewBox={`0 0 ${VBW} ${VBH}`}
            preserveAspectRatio="xMidYMid meet"
            className="omm-svg"
          >
            <Defs/>
            <Backdrop/>

            {/* Edges first so nodes draw on top of any path under them.
                In the portrait layout, edges run TOP→BOTTOM: scenario bottom-
                centre to oracle top-centre, then oracle bottom-centre to
                synth top-centre. */}
            {mode === 'full' && (
              <>
                {slots.map((slot, i) => {
                  const from = { x: center(SCENARIO).cx, y: SCENARIO.y + SCENARIO.h };
                  const to = { x: slot.x + slot.w / 2, y: slot.y };
                  return (
                    <Edge
                      key={`s2o-${i}`}
                      from={from}
                      to={to}
                      state={edgeStateForOracleArrival(oracles[i])}
                    />
                  );
                })}
                {slots.map((slot, i) => {
                  const from = { x: slot.x + slot.w / 2, y: slot.y + slot.h };
                  const to = { x: center(SYNTH).cx, y: SYNTH.y };
                  return (
                    <Edge
                      key={`o2syn-${i}`}
                      from={from}
                      to={to}
                      state={edgeStateForSynthArrival(oracles[i], hasSynthesis)}
                    />
                  );
                })}
              </>
            )}
            {mode === 'triage' && (
              <Edge
                from={{ x: center(SCENARIO).cx, y: SCENARIO.y + SCENARIO.h }}
                to={{ x: center(BLUEPRINT).cx, y: BLUEPRINT.y }}
                state="active-complete"
              />
            )}
            {mode === 'synthesis_direct' && (
              <Edge
                from={{ x: center(SCENARIO).cx, y: SCENARIO.y + SCENARIO.h }}
                to={{ x: center(SYNTH).cx, y: SYNTH.y }}
                state={hasSynthesis ? 'active-complete' : 'active-inflight'}
              />
            )}

            {/* Nodes */}
            <ScenarioNode snapshot={snapshot} />

            {mode === 'full' && oracles.map((o, i) => (
              <OracleNode key={o.subject} oracle={o} slot={slots[i]} />
            ))}
            {mode === 'full' && oracleN === 0 && snapshot.running && (
              // Pre-blueprint scaffold: a single faded "awaiting" oracle slot.
              <OracleNode oracle={undefined} slot={oracleSlot(0, 1)} />
            )}

            {mode === 'triage' && (
              <BlueprintNode blueprint={snapshot.blueprint ?? ''} />
            )}

            {(mode === 'full' || mode === 'synthesis_direct') && (
              <SynthesisNode
                hasSynthesis={hasSynthesis}
                finalText={snapshot.finalText}
                strokes={strokes.length}
              />
            )}
          </svg>
        )}
      </div>

      <Styles/>
    </div>
  );
}

// ── edge state derivation ───────────────────────────────────────────────────
type EdgeState = 'idle' | 'active-inflight' | 'active-complete' | 'failed';

function edgeStateForOracleArrival(o: OracleProgress | undefined): EdgeState {
  if (!o) return 'idle';
  if (o.status === 'failed') return 'failed';
  if (o.status === 'harvested') return 'active-complete';
  return 'active-inflight';
}

function edgeStateForSynthArrival(o: OracleProgress | undefined, hasSynth: boolean): EdgeState {
  if (!o) return 'idle';
  if (o.status === 'failed') return 'idle'; // failed oracles don't feed synth
  if (o.status !== 'harvested') return 'idle';
  return hasSynth ? 'active-complete' : 'active-inflight';
}

// ── sub-components ──────────────────────────────────────────────────────────
function Defs() {
  return (
    <defs>
      <linearGradient id="omm-bg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%"   stopColor="rgba(15,23,42,0.4)"/>
        <stop offset="100%" stopColor="rgba(30,27,75,0.25)"/>
      </linearGradient>
      <radialGradient id="omm-scenario-glow" cx="50%" cy="50%" r="60%">
        <stop offset="0%"   stopColor="rgba(129,140,248,0.30)"/>
        <stop offset="100%" stopColor="rgba(129,140,248,0)"/>
      </radialGradient>
      <radialGradient id="omm-synth-glow" cx="50%" cy="50%" r="60%">
        <stop offset="0%"   stopColor="rgba(167,139,250,0.32)"/>
        <stop offset="100%" stopColor="rgba(167,139,250,0)"/>
      </radialGradient>
    </defs>
  );
}

function Backdrop() {
  return (
    <>
      <rect x={0} y={0} width={VBW} height={VBH} fill="url(#omm-bg)"/>
      {/* faint grid */}
      <g opacity={0.07} stroke="rgba(148,163,184,0.6)" strokeWidth="0.4">
        {Array.from({ length: 10 }).map((_, i) => (
          <line key={`v-${i}`} x1={(i + 1) * (VBW / 11)} y1={0} x2={(i + 1) * (VBW / 11)} y2={VBH}/>
        ))}
        {Array.from({ length: 7 }).map((_, i) => (
          <line key={`h-${i}`} x1={0} y1={(i + 1) * (VBH / 8)} x2={VBW} y2={(i + 1) * (VBH / 8)}/>
        ))}
      </g>
    </>
  );
}

function ScenarioNode({ snapshot }: { snapshot: RunnerSnapshot }) {
  const { x, y, w, h } = SCENARIO;
  const summary = snapshot.scenarioSummary?.trim() || 'No scenario supplied';
  return (
    <g className="omm-node omm-scenario">
      <circle cx={x + w / 2} cy={y + h / 2} r={130} fill="url(#omm-scenario-glow)"/>
      <rect x={x} y={y} width={w} height={h} rx={10} ry={10}
        fill="rgba(15,23,42,0.85)"
        stroke="rgba(129,140,248,0.8)" strokeWidth="1.4"/>
      <foreignObject x={x + 12} y={y + 10} width={w - 24} height={h - 20}>
        <div className="omm-fo">
          <div className="omm-kicker indigo">01 · SCENARIO</div>
          <div className="omm-node-title">{snapshot.pathway.replace('_', ' ')}</div>
          <div className="omm-node-body">{truncate(summary, 220)}</div>
        </div>
      </foreignObject>
    </g>
  );
}

function OracleNode({ oracle, slot }: {
  oracle: OracleProgress | undefined;
  slot: { x: number; y: number; w: number; h: number };
}) {
  const { x, y, w, h } = slot;
  const c = oracleStatusColor(oracle);
  const cx = x + w / 2;
  const cy = y + h / 2;
  return (
    <g className={`omm-node omm-oracle omm-status-${oracle?.status ?? 'pending'}`}>
      <circle cx={cx} cy={cy} r={75} fill={c.glow} opacity={0.45}/>
      <rect x={x} y={y} width={w} height={h} rx={9} ry={9}
        fill="rgba(15,23,42,0.85)"
        stroke={c.border} strokeWidth="1.3"/>
      <foreignObject x={x + 10} y={y + 8} width={w - 20} height={h - 14}>
        <div className="omm-fo">
          <div className="omm-oracle-row">
            <span className="omm-kicker violet">PKI ORACLE</span>
            <span className="omm-badge" style={{ borderColor: c.border, color: c.border }}>
              {c.label}
            </span>
          </div>
          <div className="omm-oracle-subject">
            {oracle?.subject ? truncate(oracle.subject, 60) : 'awaiting subject'}
          </div>
          <div className="omm-oracle-meta">
            {oracle?.notebook_id && <span>nb {oracle.notebook_id.slice(0, 8)}…</span>}
            {oracle?.sources_imported !== undefined && <span>{oracle.sources_imported} src</span>}
            {oracle?.packet_chars !== undefined && <span>{oracle.packet_chars.toLocaleString()} chars</span>}
          </div>
          {oracle?.error && (
            // Show truncated error inline; full text in title for hover.
            // Previously only a tiny "err" tag was rendered, which made
            // diagnosing a FAILED oracle require flipping back to the Runner
            // view to read the OracleCard.
            <div className="omm-oracle-err-row" title={oracle.error}>
              {truncate(oracle.error, 90)}
            </div>
          )}
        </div>
      </foreignObject>
    </g>
  );
}

function BlueprintNode({ blueprint }: { blueprint: string }) {
  const { x, y, w, h } = BLUEPRINT;
  return (
    <g className="omm-node omm-blueprint">
      <rect x={x} y={y} width={w} height={h} rx={9} ry={9}
        fill="rgba(15,23,42,0.85)"
        stroke="rgba(99,102,241,0.75)" strokeWidth="1.3"/>
      <foreignObject x={x + 12} y={y + 10} width={w - 24} height={h - 20}>
        <div className="omm-fo">
          <div className="omm-kicker indigo">BLUEPRINT</div>
          <div className="omm-node-title">Architectural Plan</div>
          <div className="omm-node-body">{truncate(blueprint, 360)}</div>
        </div>
      </foreignObject>
    </g>
  );
}

function SynthesisNode({
  hasSynthesis, finalText, strokes,
}: {
  hasSynthesis: boolean; finalText: string | null; strokes: number;
}) {
  const { x, y, w, h } = SYNTH;
  const border = hasSynthesis ? 'rgba(167,139,250,0.85)' : 'rgba(100,116,139,0.55)';
  return (
    <g className={`omm-node omm-synthesis ${hasSynthesis ? 'omm-synthesis-on' : ''}`}>
      <circle cx={x + w / 2} cy={y + h / 2} r={130} fill="url(#omm-synth-glow)"/>
      <rect x={x} y={y} width={w} height={h} rx={10} ry={10}
        fill="rgba(15,23,42,0.85)"
        stroke={border} strokeWidth="1.4"/>
      <foreignObject x={x + 12} y={y + 10} width={w - 24} height={h - 20}>
        <div className="omm-fo">
          <div className="omm-kicker violet">SYNTHESIS</div>
          <div className="omm-node-title">
            {hasSynthesis ? `${strokes} stroke${strokes === 1 ? '' : 's'}` : 'awaiting'}
          </div>
          <div className="omm-node-body">
            {finalText
              ? `${finalText.length.toLocaleString()} chars · ${truncate(finalText, 160)}`
              : hasSynthesis
                ? 'stroke recorded · no final text yet'
                : 'will fire once oracles harvest'}
          </div>
        </div>
      </foreignObject>
    </g>
  );
}

function Edge({
  from, to, state,
}: { from: { x: number; y: number }; to: { x: number; y: number }; state: EdgeState }) {
  const d = edgePath(from, to);
  if (state === 'idle') {
    return <path d={d} className="omm-edge omm-edge-idle" fill="none"/>;
  }
  if (state === 'failed') {
    return <path d={d} className="omm-edge omm-edge-failed" fill="none"/>;
  }
  if (state === 'active-complete') {
    return <path d={d} className="omm-edge omm-edge-complete" fill="none"/>;
  }
  return <path d={d} className="omm-edge omm-edge-inflight" fill="none"/>;
}

function EmptyState() {
  return (
    <div className="omm-empty">
      <div className="omm-empty-glyph">
        <svg width="48" height="48" viewBox="0 0 48 48" aria-hidden>
          <circle cx="10" cy="24" r="4"  fill="none" stroke="rgba(148,163,184,0.55)" strokeWidth="1.2"/>
          <circle cx="38" cy="10" r="3"  fill="none" stroke="rgba(148,163,184,0.4)"  strokeWidth="1.2"/>
          <circle cx="38" cy="24" r="3"  fill="none" stroke="rgba(148,163,184,0.4)"  strokeWidth="1.2"/>
          <circle cx="38" cy="38" r="3"  fill="none" stroke="rgba(148,163,184,0.4)"  strokeWidth="1.2"/>
          <path d="M14 24 L35 10 M14 24 L35 24 M14 24 L35 38"
            stroke="rgba(148,163,184,0.35)" strokeWidth="0.9" fill="none"/>
        </svg>
      </div>
      <div className="omm-empty-title">No run in flight</div>
      <div className="omm-empty-sub">
        Click <span className="text-emerald">Run</span> in the runner to populate this canvas.
      </div>
    </div>
  );
}

// ── styled-jsx — visual language and animations ────────────────────────────
function Styles() {
  return (
    <style jsx>{`
      .omm-root {
        width: 100%; height: 100%;
        display: flex; flex-direction: column;
        background: rgba(15,23,42,0.8);
        border: 1px solid rgb(30,41,59);
        border-radius: 12px;
        overflow: hidden;
        font-family: var(--font-mono, ui-monospace, monospace);
        color: rgb(226,232,240);
        backdrop-filter: blur(6px);
      }
      .omm-header {
        flex-shrink: 0;
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 16px;
        background: rgb(2,6,23);
        border-bottom: 1px solid rgb(30,41,59);
        font-size: 12px;
      }
      .omm-header-left { display: flex; align-items: center; gap: 10px; }
      .omm-title { font-weight: 600; letter-spacing: 0.04em; color: rgb(226,232,240); }
      .omm-divider {
        width: 1px; height: 14px;
        background: rgba(148,163,184,0.25);
      }
      .omm-pathway {
        font-size: 10px; text-transform: uppercase; letter-spacing: 0.16em;
        color: rgb(167,139,250); font-style: italic;
      }
      .omm-header-right { display: flex; align-items: center; gap: 10px; }
      .omm-stage-label {
        font-size: 9px; letter-spacing: 0.18em;
        color: rgb(100,116,139);
      }
      .omm-stage-value {
        font-size: 11px; color: rgb(196,181,253); font-weight: 500;
      }
      .omm-btn {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 4px 10px;
        background: rgba(30,41,59,0.6);
        border: 1px solid rgba(71,85,105,0.5);
        border-radius: 6px;
        font-size: 10px; color: rgb(203,213,225);
        cursor: pointer; transition: background 120ms;
      }
      .omm-btn:hover {
        background: rgba(51,65,85,0.8);
        color: rgb(196,181,253);
      }

      .omm-body {
        flex: 1; min-height: 0;
        position: relative;
        background:
          radial-gradient(ellipse at center, rgba(67,56,202,0.06) 0%, transparent 70%),
          rgb(7,11,23);
      }
      .omm-svg { width: 100%; height: 100%; display: block; }

      /* foreignObject text wrappers */
      :global(.omm-fo) {
        height: 100%;
        display: flex; flex-direction: column;
        gap: 4px;
        color: rgb(226,232,240);
        font-size: 12px; line-height: 1.35;
        overflow: hidden;
      }
      :global(.omm-kicker) {
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        font-weight: 600;
      }
      :global(.omm-kicker.indigo) { color: rgb(129,140,248); }
      :global(.omm-kicker.violet) { color: rgb(167,139,250); }
      :global(.omm-node-title) {
        font-size: 12px; font-weight: 600;
        color: rgb(241,245,249);
        text-transform: uppercase; letter-spacing: 0.05em;
      }
      :global(.omm-node-body) {
        font-size: 10.5px;
        color: rgb(148,163,184);
        line-height: 1.4;
        flex: 1;
        overflow: hidden;
      }
      :global(.omm-oracle-row) {
        display: flex; align-items: center; justify-content: space-between;
        gap: 8px;
      }
      :global(.omm-badge) {
        font-size: 8.5px;
        padding: 1px 6px;
        border-radius: 4px;
        border: 1px solid;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        background: rgba(2,6,23,0.6);
      }
      :global(.omm-oracle-subject) {
        font-size: 11.5px;
        color: rgb(241,245,249);
        font-weight: 500;
        line-height: 1.3;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }
      :global(.omm-oracle-meta) {
        display: flex; gap: 10px;
        font-size: 9.5px;
        color: rgb(100,116,139);
        font-family: var(--font-mono, ui-monospace, monospace);
      }
      :global(.omm-oracle-err) { color: rgb(244,114,128); }
      :global(.omm-oracle-err-row) {
        font-size: 9.5px;
        color: rgb(244,114,128);
        line-height: 1.25;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-top: 2px;
      }
      :global(.text-emerald) { color: rgb(52,211,153); }

      /* Edge styles */
      :global(.omm-edge) { stroke-width: 1.6; fill: none; }
      :global(.omm-edge-idle) {
        stroke: rgba(100,116,139,0.30);
        stroke-dasharray: 4 6;
      }
      :global(.omm-edge-inflight) {
        stroke: rgba(251,191,36,0.85);
        stroke-dasharray: 6 5;
        animation: omm-march 1.4s linear infinite;
        filter: drop-shadow(0 0 4px rgba(251,191,36,0.4));
      }
      :global(.omm-edge-complete) {
        stroke: rgba(52,211,153,0.78);
        filter: drop-shadow(0 0 3px rgba(52,211,153,0.35));
      }
      :global(.omm-edge-failed) {
        stroke: rgba(244,114,128,0.85);
        stroke-dasharray: 3 4;
      }

      /* Node animations — researching oracle gets a soft pulse on its glow. */
      :global(.omm-status-researching) circle {
        animation: omm-pulse 2.4s ease-in-out infinite;
      }
      :global(.omm-synthesis-on) circle {
        animation: omm-pulse 3.2s ease-in-out infinite;
      }

      @keyframes omm-march {
        from { stroke-dashoffset: 0; }
        to   { stroke-dashoffset: -22; }
      }
      @keyframes omm-pulse {
        0%,100% { opacity: 0.45; transform-origin: center; }
        50%     { opacity: 0.85; }
      }

      /* Empty state */
      .omm-empty {
        position: absolute; inset: 0;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        gap: 12px;
      }
      .omm-empty-glyph { opacity: 0.7; }
      .omm-empty-title {
        font-size: 13px; font-weight: 600;
        color: rgb(203,213,225);
        text-transform: uppercase;
        letter-spacing: 0.15em;
      }
      .omm-empty-sub {
        font-size: 11px; color: rgb(100,116,139);
      }
    `}</style>
  );
}
