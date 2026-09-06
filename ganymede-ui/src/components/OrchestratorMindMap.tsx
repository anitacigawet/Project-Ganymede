'use client';

/**
 * OrchestratorMindMap — landscape mind-map of the bicameral pipeline.
 *
 * Layout (per operator 2026-06-10 brain-metaphor diagram):
 *
 *       ╭──────╮            (4) top arc — Anti → Engine            ╭──────╮
 *       │      │ ◄ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │      │
 *       │ 9d   │                                                    │ Anti │
 *       │ Eng- │ ◄─── (1) bilateral ──► PKI substrate ◄── (3) ──► │ Con- │
 *       │ ine  │            ▲                                       │trast │
 *       │      │            │  (2) Engine sends synthesis to Anti  │      │
 *       ╰──────╯            ╰────────────────────────────────────►  ╰──────╯
 *
 * Four animated stages, driven by stroke landings:
 *   1. 9d ↔ PKIs:    Engine consults the substrate (Truth Packets or
 *                    Oracle harvest). Bilateral arrows light up during
 *                    Stroke 1 / 3 (synthesis strokes).
 *   2. 9d → Anti:    Engine sends its synthesis state to Anti when a
 *                    Mirror Auditor / Connection Bridge stroke begins.
 *   3. Anti ↔ PKIs:  Anti consults the same substrate to find missed
 *                    connections or audit faults. Bilateral arrows light
 *                    up during Stroke 2 / 2b (audit strokes).
 *   4. Anti → 9d:    Top arc — Anti's findings feed back to Engine for
 *                    the re-synthesis stroke (Stroke 3).
 *
 * Adapts to the run mode:
 *   • triage           → Engine + blueprint card (no PKIs / Anti)
 *   • synthesis_direct → Engine → synth (no PKIs / Anti)
 *   • full (legacy)    → Engine → PKI Oracle column → synth
 *                        (the original Oracle-harvest flow)
 *   • bicameral (new)  → Engine ↔ PKI substrate ↔ Anti + top arc
 *                        (the Truth-Packet iterate / managed-run flow)
 *   • idle             → empty-state placeholder
 *
 * Pure SVG, no library. Edges are cubic béziers with status-driven colour
 * and a marching-ant animation while their target is in-flight.
 */

import React, { useMemo } from 'react';
import type { RunnerSnapshot, OracleProgress } from './RunnerPanel';

// Minimal stroke shape — keep loose to avoid coupling to RunnerPanel's
// internal type (we only read `audit_kind`).
interface StrokeLike { audit_kind?: 'mirror_auditor' | 'bridge' | null }

export interface OrchestratorMindMapProps {
  snapshot: RunnerSnapshot;
  onSwitchToRunner?: () => void;
}

// ── viewBox geometry (horizontal / landscape) ──────────────────────────────
// Engine sits at the left, the PKI substrate column runs vertically in the
// middle, Anti/Contrast (or legacy synth) sits at the right. The big top
// arc runs from Anti back to Engine for Stroke 3 re-synthesis feedback.
const VBW = 1320;
const VBH = 720;

const ENGINE = { x: 50,   y: 240, w: 270, h: 240 } as const;
const ANTI   = { x: 1000, y: 240, w: 270, h: 240 } as const;
const SYNTH  = { x: 1000, y: 240, w: 270, h: 240 } as const;   // same slot as Anti; legacy mode
const BLUEPRINT = { x: 480, y: 240, w: 360, h: 240 } as const;

// PKI substrate column (middle)
const PKI_W = 240;
const PKI_H = 68;
const PKI_X = (VBW - PKI_W) / 2;          // 540
const PKI_Y_MIN = 60;
const PKI_Y_MAX = 600;

// ── helpers ────────────────────────────────────────────────────────────────
function pkiSlot(i: number, n: number): { x: number; y: number; w: number; h: number } {
  if (n <= 1) {
    return {
      x: PKI_X,
      y: (PKI_Y_MIN + PKI_Y_MAX) / 2,
      w: PKI_W,
      h: PKI_H,
    };
  }
  const yRange = PKI_Y_MAX - PKI_Y_MIN;
  const y = PKI_Y_MIN + (yRange * i) / (n - 1);
  return { x: PKI_X, y, w: PKI_W, h: PKI_H };
}

function center(rect: { x: number; y: number; w: number; h: number }) {
  return { cx: rect.x + rect.w / 2, cy: rect.y + rect.h / 2 };
}
function leftEdge(rect: { x: number; y: number; w: number; h: number }) {
  return { x: rect.x, y: rect.y + rect.h / 2 };
}
function rightEdge(rect: { x: number; y: number; w: number; h: number }) {
  return { x: rect.x + rect.w, y: rect.y + rect.h / 2 };
}
function topMid(rect: { x: number; y: number; w: number; h: number }) {
  return { x: rect.x + rect.w / 2, y: rect.y };
}

// Horizontal-bias bezier: control points share Y with their endpoints so
// when endpoints differ in y the curve eases into an S-shape, and when
// endpoints share y it degenerates to a straight horizontal line. Used for
// Engine ↔ PKI and PKI ↔ Anti edges in the landscape layout.
function horizPath(from: { x: number; y: number }, to: { x: number; y: number }): string {
  const dx = to.x - from.x;
  const cp1x = from.x + dx * 0.45;
  const cp2x = to.x - dx * 0.45;
  return `M${from.x},${from.y} C${cp1x},${from.y} ${cp2x},${to.y} ${to.x},${to.y}`;
}

// Big top arc for Anti→Engine feedback. Lift control points well above the
// node tops so the arc bows up dramatically rather than passing through
// the substrate column.
function arcPath(from: { x: number; y: number }, to: { x: number; y: number }): string {
  const arcHeight = 220;
  const cp1y = from.y - arcHeight;
  const cp2y = to.y - arcHeight;
  return `M${from.x},${from.y} C${from.x},${cp1y} ${to.x},${cp2y} ${to.x},${to.y}`;
}

// Vertical-bias bezier for legacy modes (scenario top → synth bottom).
// Kept for the synthesis_direct fallback.
function vertPath(from: { x: number; y: number }, to: { x: number; y: number }): string {
  const dy = to.y - from.y;
  const cp1y = from.y + dy * 0.45;
  const cp2y = to.y - dy * 0.45;
  return `M${from.x},${from.y} C${from.x},${cp1y} ${to.x},${cp2y} ${to.x},${to.y}`;
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

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + '…' : s;
}

// ── root component ─────────────────────────────────────────────────────────
export function OrchestratorMindMap({
  snapshot, onSwitchToRunner,
}: OrchestratorMindMapProps) {
  const oracles = snapshot.oracles || [];
  const oracleN = oracles.length;
  const strokes: StrokeLike[] = snapshot.strokes || [];
  const hasSynthesis = strokes.length > 0;
  const hasBlueprint = !!snapshot.blueprint;
  const isTriageOnly = snapshot.runMode === 'triage';
  const isSynthesisOnly = snapshot.runMode === 'synthesis';

  // Bicameral detection: truth-packet driven iterate/managed-run flows
  // have no Oracle column but do produce audit strokes (audit_kind set on
  // Stroke 2 / 2b). Show the Anti node + bilateral edges when this is the
  // shape we're in, OR when a running session hasn't yet produced any
  // strokes and there's no Oracle work (default-to-bicameral for the new
  // flows).
  const isIterativeFlow = oracleN === 0 && (hasSynthesis || snapshot.running);

  type Mode = 'idle' | 'triage' | 'synthesis_direct' | 'bicameral' | 'full';
  const mode: Mode = useMemo(() => {
    if (isTriageOnly && hasBlueprint) return 'triage';
    if (oracleN > 0) return 'full';
    if (isIterativeFlow) return 'bicameral';
    if (isSynthesisOnly || hasSynthesis) return 'synthesis_direct';
    if (snapshot.running) return 'bicameral';
    return 'idle';
  }, [
    isTriageOnly, isSynthesisOnly, hasBlueprint, hasSynthesis,
    oracleN, snapshot.running, isIterativeFlow,
  ]);

  // PKI / substrate column slot count. Legacy full mode uses one slot
  // per Oracle. Bicameral mode (iterate / managed-run with pre-harvested
  // Truth Packets) shows ONE substrate node — the dispatcher panel
  // ships a single packet, and the visualizer should reflect reality
  // rather than render decorative placeholders. If the snapshot later
  // carries an actual packet count we can lift this.
  const pkiN = mode === 'full' ? oracleN : 1;
  const slots = useMemo(() => {
    if (mode === 'full') {
      return oracles.map((_, i) => pkiSlot(i, oracleN));
    }
    return Array.from({ length: pkiN }).map((_, i) => pkiSlot(i, pkiN));
  }, [mode, oracles, oracleN, pkiN]);

  // ── Stage detection for bicameral mode ───────────────────────────────────
  // The pipeline is Stroke 1 (synthesis) → Stroke 2 (audit / Mirror) →
  // Stroke 2b (audit / Bridge) → Stroke 3 (re-synthesis). We classify each
  // edge as idle / in-flight / complete / failed by counting how many of
  // each kind have landed.
  const synthesisStrokeCount = strokes.filter(s => !s.audit_kind).length;
  const auditStrokeCount = strokes.filter(s => !!s.audit_kind).length;
  const lastStrokeEvent = snapshot.recentEvents?.filter(event =>
    event.type === 'stroke_started' || event.type === 'stroke_completed',
  ).at(-1);
  const activeKind = lastStrokeEvent?.type === 'stroke_started'
    ? lastStrokeEvent.payload.kind : null;
  // Show the live provider phase as soon as it starts. Counts remain the
  // fallback for the deterministic showcase, which has no backend events.
  const hasPhaseEvents = !!lastStrokeEvent;

  const stage1Active   = snapshot.running && synthesisStrokeCount === 0 && (!hasPhaseEvents || activeKind === 'synthesis');
  const stage1Complete = synthesisStrokeCount >= 1;
  const stage2Active   = snapshot.running && (hasPhaseEvents ? activeKind === 'audit' : synthesisStrokeCount >= 1 && auditStrokeCount === 0);
  const stage2Complete = auditStrokeCount >= 1;
  const stage3Active   = snapshot.running && (hasPhaseEvents ? activeKind === 'audit' || activeKind === 'bridge_audit' : synthesisStrokeCount >= 1 && auditStrokeCount >= 1 && synthesisStrokeCount < 2);
  const stage3Complete = auditStrokeCount >= 1 && synthesisStrokeCount >= 2;
  const stage4Active   = snapshot.running && (hasPhaseEvents ? activeKind === 'synthesis' && (lastStrokeEvent.stroke_number ?? 0) > 1 : synthesisStrokeCount >= 1 && auditStrokeCount >= 1 && synthesisStrokeCount < 2);
  const stage4Complete = synthesisStrokeCount >= 2;

  const stateFor = (active: boolean, complete: boolean): EdgeState => {
    if (snapshot.hasError) return 'failed';
    if (active) return 'active-inflight';
    if (complete) return 'active-complete';
    return 'idle';
  };

  const stage1Edge = stateFor(stage1Active, stage1Complete);
  const stage2Edge = stateFor(stage2Active, stage2Complete);
  const stage3Edge = stateFor(stage3Active, stage3Complete);
  const stage4Edge = stateFor(stage4Active, stage4Complete);

  // ── Progressive reveal — the "brain growing neurons" choreography ─────
  // Render each node only when its corresponding stroke is in flight or
  // has landed. Before Stroke 1 fires, only the Engine bubble is on
  // screen. The substrate node fades in when Stroke 1 starts; the Anti
  // node fades in when an audit stroke starts; the top arc only renders
  // once Stroke 3 fires or has fired. Edges suppressed entirely between
  // nodes that aren't both visible.
  const showSubstrate =
    mode === 'bicameral' &&
    (snapshot.running || synthesisStrokeCount >= 1 || auditStrokeCount >= 1);
  const showAnti =
    mode === 'bicameral' &&
    (auditStrokeCount >= 1 || stage2Active || stage3Active);
  const showTopArc =
    mode === 'bicameral' &&
    (stage4Active || stage4Complete);

  const stageText = useMemo(() => {
    if (snapshot.hasError) return 'Errored';
    if (mode === 'triage') return 'Triage Complete';
    if (mode === 'full') {
      if (hasSynthesis) return 'Synthesised';
      if (oracleN > 0) {
        const done = oracles.filter(o => o.status === 'harvested' || o.status === 'failed').length;
        return `Harvesting ${done}/${oracleN}`;
      }
      if (snapshot.running) return 'Triage Firing';
    }
    if (mode === 'bicameral') {
      if (snapshot.running && activeKind === 'audit') return 'Mirror Auditor reviewing';
      if (snapshot.running && activeKind === 'bridge_audit') return 'Connection Bridge reviewing';
      if (stage4Complete) return 'Re-synthesised';
      if (stage4Active)   return 'Re-synthesising';
      if (stage3Active || (stage3Complete && !stage4Complete)) return 'Anti consulting substrate';
      if (stage2Active)   return 'Engine → Anti handoff';
      if (stage1Active)   return 'Engine synthesising';
      if (snapshot.running) return 'Initialising';
    }
    if (mode === 'synthesis_direct') {
      return hasSynthesis ? 'Synthesised' : 'Synthesising';
    }
    if (snapshot.scenarioSummary?.trim()) return 'Awaiting Run';
    return 'Empty';
  }, [
    snapshot.hasError, snapshot.running, snapshot.scenarioSummary,
    hasSynthesis, mode, oracles, oracleN,
    stage1Active, stage2Active, stage3Active, stage3Complete,
    stage4Active, stage4Complete,
    activeKind,
  ]);

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

            {/* === Bicameral mode (truth-packet iterate / managed-run) ===
                Edges and nodes appear progressively as the actual strokes
                land — brain-building-neurons choreography. No skeleton. */}
            {mode === 'bicameral' && (
              <>
                {/* (1) Bilateral Engine ↔ PKI edges — only when substrate visible */}
                {showSubstrate && slots.map((slot, i) => {
                  const engineR = rightEdge(ENGINE);
                  const pkiL = leftEdge(slot);
                  const off = 14;
                  return (
                    <React.Fragment key={`e2pki-${i}`}>
                      <Edge
                        from={engineR}
                        to={pkiL}
                        state={stage1Edge}
                        pathFn={horizPath}
                      />
                      <Edge
                        from={{ x: pkiL.x, y: pkiL.y + off }}
                        to={{ x: engineR.x, y: engineR.y + off }}
                        state={stage1Edge}
                        pathFn={horizPath}
                      />
                    </React.Fragment>
                  );
                })}

                {/* (3) Bilateral PKI ↔ Anti edges — only when Anti visible */}
                {showSubstrate && showAnti && slots.map((slot, i) => {
                  const pkiR = rightEdge(slot);
                  const antiL = leftEdge(ANTI);
                  const off = 14;
                  return (
                    <React.Fragment key={`pki2a-${i}`}>
                      <Edge
                        from={pkiR}
                        to={antiL}
                        state={stage3Edge}
                        pathFn={horizPath}
                      />
                      <Edge
                        from={{ x: antiL.x, y: antiL.y + off }}
                        to={{ x: pkiR.x, y: pkiR.y + off }}
                        state={stage3Edge}
                        pathFn={horizPath}
                      />
                    </React.Fragment>
                  );
                })}

                {/* (2) Engine → Anti direct handoff — only when Anti visible */}
                {showAnti && (
                  <Edge
                    from={{ x: rightEdge(ENGINE).x, y: ENGINE.y + ENGINE.h - 24 }}
                    to={{ x: leftEdge(ANTI).x, y: ANTI.y + ANTI.h - 24 }}
                    state={stage2Edge}
                    pathFn={horizPath}
                  />
                )}

                {/* (4) Top arc — Anti → Engine, only when Stroke 3 fires */}
                {showTopArc && (
                  <ArcEdge
                    from={topMid(ANTI)}
                    to={topMid(ENGINE)}
                    state={stage4Edge}
                  />
                )}
              </>
            )}

            {/* === Full mode (legacy Oracle harvest flow) ===
                Engine on left, Oracle column in middle, Synth on right. */}
            {mode === 'full' && (
              <>
                {slots.map((slot, i) => {
                  const engineR = rightEdge(ENGINE);
                  const pkiL = leftEdge(slot);
                  return (
                    <Edge
                      key={`s2o-${i}`}
                      from={engineR}
                      to={pkiL}
                      state={edgeStateForOracleArrival(oracles[i])}
                      pathFn={horizPath}
                    />
                  );
                })}
                {slots.map((slot, i) => {
                  const pkiR = rightEdge(slot);
                  const synthL = leftEdge(SYNTH);
                  return (
                    <Edge
                      key={`o2syn-${i}`}
                      from={pkiR}
                      to={synthL}
                      state={edgeStateForSynthArrival(oracles[i], hasSynthesis)}
                      pathFn={horizPath}
                    />
                  );
                })}
              </>
            )}

            {/* === Triage mode === */}
            {mode === 'triage' && (
              <Edge
                from={rightEdge(ENGINE)}
                to={leftEdge(BLUEPRINT)}
                state="active-complete"
                pathFn={horizPath}
              />
            )}

            {/* === Synthesis-direct mode === */}
            {mode === 'synthesis_direct' && (
              <Edge
                from={rightEdge(ENGINE)}
                to={leftEdge(SYNTH)}
                state={hasSynthesis ? 'active-complete' : 'active-inflight'}
                pathFn={horizPath}
              />
            )}

            {/* === Nodes === */}
            <EngineNode snapshot={snapshot} />

            {mode === 'full' && oracles.map((o, i) => (
              <OracleNode key={o.subject} oracle={o} slot={slots[i]} />
            ))}
            {mode === 'full' && oracleN === 0 && snapshot.running && (
              <OracleNode oracle={undefined} slot={pkiSlot(0, 1)} />
            )}

            {mode === 'bicameral' && showSubstrate && slots.map((slot, i) => (
              <PkiPlaceholderNode key={`pki-ph-${i}`} slot={slot} index={i} />
            ))}

            {mode === 'triage' && (
              <BlueprintNode blueprint={snapshot.blueprint ?? ''} />
            )}

            {mode === 'bicameral' && showAnti && (
              <AntiNode strokes={strokes} />
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

// ── edge state derivation (legacy full mode) ───────────────────────────────
type EdgeState = 'idle' | 'active-inflight' | 'active-complete' | 'failed';

function edgeStateForOracleArrival(o: OracleProgress | undefined): EdgeState {
  if (!o) return 'idle';
  if (o.status === 'failed') return 'failed';
  if (o.status === 'harvested') return 'active-complete';
  return 'active-inflight';
}

function edgeStateForSynthArrival(o: OracleProgress | undefined, hasSynth: boolean): EdgeState {
  if (!o) return 'idle';
  if (o.status === 'failed') return 'idle';
  if (o.status !== 'harvested') return 'idle';
  return hasSynth ? 'active-complete' : 'active-inflight';
}

// ── sub-components ─────────────────────────────────────────────────────────
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
      <radialGradient id="omm-anti-glow" cx="50%" cy="50%" r="60%">
        <stop offset="0%"   stopColor="rgba(251,191,36,0.30)"/>
        <stop offset="100%" stopColor="rgba(251,191,36,0)"/>
      </radialGradient>
    </defs>
  );
}

function Backdrop() {
  return (
    <>
      <rect x={0} y={0} width={VBW} height={VBH} fill="url(#omm-bg)"/>
      <g opacity={0.07} stroke="rgba(148,163,184,0.6)" strokeWidth="0.4">
        {Array.from({ length: 12 }).map((_, i) => (
          <line key={`v-${i}`} x1={(i + 1) * (VBW / 13)} y1={0} x2={(i + 1) * (VBW / 13)} y2={VBH}/>
        ))}
        {Array.from({ length: 7 }).map((_, i) => (
          <line key={`h-${i}`} x1={0} y1={(i + 1) * (VBH / 8)} x2={VBW} y2={(i + 1) * (VBH / 8)}/>
        ))}
      </g>
    </>
  );
}

function EngineNode({ snapshot }: { snapshot: RunnerSnapshot }) {
  const { x, y, w, h } = ENGINE;
  const summary = snapshot.scenarioSummary?.trim() || 'No scenario supplied';
  const cx = x + w / 2;
  const cy = y + h / 2;
  // True bubble: an ellipse covering the same footprint as the rect.
  // foreignObject still positions text inside the inscribed rect; the
  // ellipse just provides the bubble outline + glow halo.
  const rx = w / 2;
  const ry = h / 2;
  // Inscribed rect for text content — set inside the ellipse's inscribed
  // box (a smaller axis-aligned rect that fits inside the ellipse).
  const insetX = w * 0.16;
  const insetY = h * 0.16;
  return (
    <g className="omm-node omm-scenario">
      <circle cx={cx} cy={cy} r={Math.max(rx, ry) + 40} fill="url(#omm-scenario-glow)"/>
      <ellipse cx={cx} cy={cy} rx={rx} ry={ry}
        fill="rgba(15,23,42,0.88)"
        stroke="rgba(129,140,248,0.85)" strokeWidth="1.6"/>
      <foreignObject x={x + insetX} y={y + insetY} width={w - 2 * insetX} height={h - 2 * insetY}>
        <div className="omm-fo">
          <div className="omm-kicker indigo">9D · ENGINE</div>
          <div className="omm-node-title">{snapshot.pathway.replace('_', ' ')}</div>
          <div className="omm-node-body">{truncate(summary, 240)}</div>
        </div>
      </foreignObject>
    </g>
  );
}

function PkiPlaceholderNode({
  slot, index,
}: {
  slot: { x: number; y: number; w: number; h: number };
  index: number;
}) {
  const { x, y, w, h } = slot;
  return (
    <g className="omm-node omm-pki-placeholder omm-node-appearing">
      <rect x={x} y={y} width={w} height={h} rx={h / 2} ry={h / 2}
        fill="rgba(15,23,42,0.9)"
        stroke="rgba(167,139,250,0.65)" strokeWidth="1.3"/>
      <foreignObject x={x + 14} y={y + 8} width={w - 28} height={h - 16}>
        <div className="omm-fo">
          <div className="omm-pki-row">
            <span className="omm-kicker violet">SUBSTRATE</span>
            <span className="omm-pki-index">#{index + 1}</span>
          </div>
          <div className="omm-pki-subject">Truth Packet</div>
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
      <foreignObject x={x + 10} y={y + 6} width={w - 20} height={h - 12}>
        <div className="omm-fo">
          <div className="omm-oracle-row">
            <span className="omm-kicker violet">PKI ORACLE</span>
            <span className="omm-badge" style={{ borderColor: c.border, color: c.border }}>
              {c.label}
            </span>
          </div>
          <div className="omm-oracle-subject">
            {oracle?.subject ? truncate(oracle.subject, 50) : 'awaiting subject'}
          </div>
          {oracle?.error && (
            <div className="omm-oracle-err-row" title={oracle.error}>
              {truncate(oracle.error, 70)}
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
      <rect x={x} y={y} width={w} height={h} rx={10} ry={10}
        fill="rgba(15,23,42,0.85)"
        stroke="rgba(99,102,241,0.75)" strokeWidth="1.3"/>
      <foreignObject x={x + 14} y={y + 12} width={w - 28} height={h - 24}>
        <div className="omm-fo">
          <div className="omm-kicker indigo">BLUEPRINT</div>
          <div className="omm-node-title">Architectural Plan</div>
          <div className="omm-node-body">{truncate(blueprint, 420)}</div>
        </div>
      </foreignObject>
    </g>
  );
}

function AntiNode({ strokes }: { strokes: StrokeLike[] }) {
  const { x, y, w, h } = ANTI;
  const auditorPresent = strokes.some(s => s.audit_kind === 'mirror_auditor');
  const bridgePresent  = strokes.some(s => s.audit_kind === 'bridge');
  const isActive = auditorPresent || bridgePresent;
  const border = isActive ? 'rgba(251,191,36,0.9)' : 'rgba(167,139,250,0.7)';
  const auditCount = strokes.filter(s => !!s.audit_kind).length;
  const cx = x + w / 2;
  const cy = y + h / 2;
  const rx = w / 2;
  const ry = h / 2;
  const insetX = w * 0.16;
  const insetY = h * 0.16;
  return (
    <g className={`omm-node omm-anti omm-node-appearing ${isActive ? 'omm-anti-on' : ''}`}>
      <circle cx={cx} cy={cy} r={Math.max(rx, ry) + 40} fill="url(#omm-anti-glow)"/>
      <ellipse cx={cx} cy={cy} rx={rx} ry={ry}
        fill="rgba(15,23,42,0.88)"
        stroke={border} strokeWidth="1.6"/>
      <foreignObject x={x + insetX} y={y + insetY} width={w - 2 * insetX} height={h - 2 * insetY}>
        <div className="omm-fo">
          <div className="omm-kicker amber">ANTI · CONTRAST</div>
          <div className="omm-node-title">
            {auditCount === 0 ? 'Engaging' : `${auditCount} audit${auditCount === 1 ? '' : 's'}`}
          </div>
          <div className="omm-anti-list">
            <div className={`omm-anti-row ${auditorPresent ? 'on' : ''}`}>
              <span className="omm-anti-marker">{auditorPresent ? '●' : '○'}</span>
              Mirror Auditor
            </div>
            <div className={`omm-anti-row ${bridgePresent ? 'on' : ''}`}>
              <span className="omm-anti-marker">{bridgePresent ? '●' : '○'}</span>
              Connection Bridge
            </div>
          </div>
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
      <circle cx={x + w / 2} cy={y + h / 2} r={150} fill="url(#omm-synth-glow)"/>
      <rect x={x} y={y} width={w} height={h} rx={12} ry={12}
        fill="rgba(15,23,42,0.85)"
        stroke={border} strokeWidth="1.4"/>
      <foreignObject x={x + 14} y={y + 12} width={w - 28} height={h - 24}>
        <div className="omm-fo">
          <div className="omm-kicker violet">SYNTHESIS</div>
          <div className="omm-node-title">
            {hasSynthesis ? `${strokes} stroke${strokes === 1 ? '' : 's'}` : 'awaiting'}
          </div>
          <div className="omm-node-body">
            {finalText
              ? `${finalText.length.toLocaleString()} chars · ${truncate(finalText, 220)}`
              : hasSynthesis
                ? 'stroke recorded · no final text yet'
                : 'will fire once substrate is consulted'}
          </div>
        </div>
      </foreignObject>
    </g>
  );
}

function Edge({
  from, to, state, pathFn,
}: {
  from: { x: number; y: number };
  to: { x: number; y: number };
  state: EdgeState;
  pathFn?: (a: { x: number; y: number }, b: { x: number; y: number }) => string;
}) {
  const d = (pathFn ?? vertPath)(from, to);
  if (state === 'idle')          return <path d={d} className="omm-edge omm-edge-idle"    fill="none"/>;
  if (state === 'failed')        return <path d={d} className="omm-edge omm-edge-failed"  fill="none"/>;
  if (state === 'active-complete') return <path d={d} className="omm-edge omm-edge-complete" fill="none"/>;
  return <path d={d} className="omm-edge omm-edge-inflight" fill="none"/>;
}

function ArcEdge({
  from, to, state,
}: {
  from: { x: number; y: number };
  to: { x: number; y: number };
  state: EdgeState;
}) {
  const d = arcPath(from, to);
  if (state === 'idle')          return <path d={d} className="omm-edge omm-edge-idle"    fill="none"/>;
  if (state === 'failed')        return <path d={d} className="omm-edge omm-edge-failed"  fill="none"/>;
  if (state === 'active-complete') return <path d={d} className="omm-edge omm-edge-complete" fill="none"/>;
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
        Click <span className="text-emerald">Run</span> in the dispatcher to populate this canvas.
      </div>
    </div>
  );
}

// ── styled-jsx ────────────────────────────────────────────────────────────
// NOTE: must be `<style jsx global>` not `<style jsx>` — styled-jsx
// scopes locally to the component the <style> tag is rendered in, and
// this Styles helper has no children of its own. Without `global`, only
// rules wrapped in :global(...) would apply, leaving layout rules like
// .omm-header / .omm-title without their flex + spacing. All class
// names are prefixed `omm-` so global scope is collision-safe.
function Styles() {
  return (
    <style jsx global>{`
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
      :global(.omm-kicker.amber)  { color: rgb(251,191,36); }
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
      :global(.omm-pki-row) {
        display: flex; align-items: center; justify-content: space-between;
      }
      :global(.omm-pki-index) {
        font-size: 9px; color: rgb(100,116,139);
        font-family: var(--font-mono, ui-monospace, monospace);
      }
      :global(.omm-pki-subject) {
        font-size: 11px; color: rgb(203,213,225);
        font-weight: 500;
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
      :global(.omm-anti-list) {
        display: flex; flex-direction: column; gap: 4px;
        margin-top: 4px;
      }
      :global(.omm-anti-row) {
        display: flex; align-items: center; gap: 6px;
        font-size: 11px; color: rgb(148,163,184);
      }
      :global(.omm-anti-row.on) {
        color: rgb(251,191,36);
        font-weight: 600;
      }
      :global(.omm-anti-marker) {
        display: inline-block; width: 10px;
        font-size: 11px;
      }
      :global(.text-emerald) { color: rgb(52,211,153); }

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

      :global(.omm-status-researching) circle {
        animation: omm-pulse 2.4s ease-in-out infinite;
      }
      :global(.omm-synthesis-on) circle,
      :global(.omm-anti-on) circle {
        animation: omm-pulse 3.2s ease-in-out infinite;
      }

      /* Brain-growing-neurons: nodes fade + grow in when first rendered.
         transform-box + transform-origin make scale() work correctly on
         SVG <g> in modern browsers. */
      :global(.omm-node-appearing) {
        transform-box: fill-box;
        transform-origin: center;
        animation: omm-node-appear 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) both;
      }

      @keyframes omm-march {
        from { stroke-dashoffset: 0; }
        to   { stroke-dashoffset: -22; }
      }
      @keyframes omm-pulse {
        0%,100% { opacity: 0.45; transform-origin: center; }
        50%     { opacity: 0.85; }
      }
      @keyframes omm-node-appear {
        0%   { opacity: 0; transform: scale(0.55); }
        60%  { opacity: 1; transform: scale(1.06); }
        100% { opacity: 1; transform: scale(1); }
      }

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
