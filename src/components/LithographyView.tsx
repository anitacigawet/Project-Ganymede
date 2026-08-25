'use client';

/**
 * LithographyView — Optics-Box visualisation of an in-progress Cleanroom run.
 *
 * Pipeline → optics mapping
 *   user scenario    →  IR LASER + COLLECTOR
 *   Engine triage    →  PLASMA at the collector focus
 *   Architectural    →  INTERMEDIATE FOCUS  →  ILLUMINATOR
 *     Blueprint
 *   Strategic Hit    →  MASK / RETICLE
 *     List
 *   PKI Oracles      →  PROJECTION OPTICS  (variable 1..5 mirrors, zigzag)
 *   synthesis        →  vertical convergence cone into the magic-circle wafer
 *   Final resolution →  MAGIC-CIRCLE WAFER  (rune ring + lattice + core)
 *
 * Interactivity
 *   • Projection-optics mirrors are GRAB-DRAGGABLE side-to-side.  Beam
 *     paths recompute live as the user nudges them.  A "RE-ALIGN OPTICS"
 *     chip appears at bottom-right while any mirror is off-baseline.
 *
 * Beam rendering
 *   • Each beam is a four-corner cone path filled with two translucent
 *     layers + a longitudinal "wave packet" gradient that animates
 *     source → destination via SMIL animateTransform.  This is the
 *     "true beam shining" — not a perpendicular stripe pattern.
 *
 * Magic-circle wafer
 *   • A tilted disc with multiple concentric rings.  As `progress`
 *     rises (mask patterned → synthesis → etched), rings come online
 *     one by one: outer ring → rune glyphs → middle ring → inner
 *     lattice → glowing core → energy arcs.
 *
 * Tune-points
 *   • Geometry constants       → computeBenchLayout()
 *   • Stage activation         → deriveStages()
 *   • Beam segments + animate  → seg_* in CleanroomBench()
 *   • Magic-circle thresholds  → reveal constants in MagicCircle()
 *   • Drag travel limit        → MIRROR_NUDGE_MAX
 *
 * SVG + CSS only — no WebGL.  Self-contained styled-jsx block at the
 * bottom owns every animation and label style.
 */

import React, { useMemo, useState, useRef, useCallback } from 'react';
import type { RunnerSnapshot, OracleProgress } from './RunnerPanel';

// =============================================================================
// Public API
// =============================================================================

export interface LithographyViewProps {
  snapshot: RunnerSnapshot;
  onSwitchToCanvas?: () => void;
  canvasAvailable?: boolean;
}

type StageStatus = 'idle' | 'active' | 'complete' | 'failed' | 'pending';

interface Stages {
  scenario:  StageStatus;
  plasma:    StageStatus;
  blueprint: StageStatus;
  mask:      StageStatus;
  synthesis: StageStatus;
  wafer:     StageStatus;
  errored:   boolean;
}

interface Point { x: number; y: number; }
interface OracleSlot extends Point { level: 'top' | 'bottom'; index: number; }
interface Layout {
  LASER: Point; COLLECTOR: Point; PLASMA: Point; FOCUS: Point;
  ILLUMINATOR: Point; MASK: Point; oracles: OracleSlot[]; WAFER: Point; N: number;
}

// Lateral nudge travel allowed on each mirror (in svg units, ± from baseline).
const MIRROR_NUDGE_MAX = 36;
// Below this nudge, beam still strikes magic-circle dead-center; past it,
// the beam drifts off-axis and a warning chip appears.
const MISALIGN_THRESHOLD = 16;

/**
 * Per-oracle hue tokens — all in the violet family but with enough hue
 * separation that overlapping cones in the zigzag can be visually traced.
 * Index modulo 5.
 */
interface OracleHue { base: string; dim: string; glow: string; faint: string; }
const ORACLE_HUES: OracleHue[] = [
  { base: 'hsl(265, 88%, 72%)', dim: 'hsl(265, 90%, 80%)', glow: 'hsla(265, 88%, 72%, 0.36)', faint: 'hsla(265, 88%, 72%, 0.18)' },
  { base: 'hsl(295, 78%, 72%)', dim: 'hsl(295, 80%, 80%)', glow: 'hsla(295, 78%, 72%, 0.36)', faint: 'hsla(295, 78%, 72%, 0.18)' },
  { base: 'hsl(243, 86%, 76%)', dim: 'hsl(243, 86%, 82%)', glow: 'hsla(243, 86%, 76%, 0.36)', faint: 'hsla(243, 86%, 76%, 0.18)' },
  { base: 'hsl(218, 78%, 72%)', dim: 'hsl(218, 78%, 80%)', glow: 'hsla(218, 78%, 72%, 0.36)', faint: 'hsla(218, 78%, 72%, 0.18)' },
  { base: 'hsl(278, 70%, 80%)', dim: 'hsl(278, 70%, 86%)', glow: 'hsla(278, 70%, 80%, 0.36)', faint: 'hsla(278, 70%, 80%, 0.18)' },
];
function tintFor(i: number): OracleHue { return ORACLE_HUES[i % ORACLE_HUES.length]; }

// =============================================================================
// Stage derivation
// =============================================================================

// The lithography bench visualizes the Universal Logic Loop pipeline
// (scenario → triage/plasma → blueprint → PKI-oracle optics → synthesis →
// resolution wafer). That pipeline is identical across the three
// oracle-harvest pathways, so the bench renders for all of them — not just
// cleanroom (the original gate was too strict and blanked genie/offensive
// runs to the DESIGN PENDING placeholder). mirror_audit is deliberately
// excluded: it has no blueprint or oracle harvest, and its audit stroke
// would otherwise falsely light the synthesis/wafer stages — so it keeps
// the placeholder.
const OPTICS_PATHWAYS = new Set(['cleanroom', 'genie', 'offensive']);

function deriveStages(snap: RunnerSnapshot): Stages | null {
  if (!OPTICS_PATHWAYS.has(snap.pathway)) return null;
  const running = snap.running;
  const blueprintReady = !!snap.blueprint;
  const oracles = snap.oracles || [];
  const oraclesDone = oracles.length > 0 &&
    oracles.every(o => o.status === 'harvested' || o.status === 'failed');
  const synthesisDone = (snap.strokes || []).length > 0;
  const hasResolution = !!snap.finalText;
  const errored = !!snap.hasError;

  return {
    scenario:  running || blueprintReady ? 'complete' : 'idle',
    plasma:    blueprintReady ? 'complete' : running ? 'active' : 'idle',
    blueprint: blueprintReady && oracles.length > 0 ? 'complete' : blueprintReady ? 'active' : 'idle',
    mask:      oracles.length > 0 && oraclesDone ? 'complete' : oracles.length > 0 ? 'active' : 'idle',
    synthesis: synthesisDone ? 'complete' : oraclesDone ? 'active' : 'idle',
    wafer:     hasResolution ? 'complete' : synthesisDone ? 'active' : 'idle',
    errored,
  };
}

function oracleStageStatus(o: OracleProgress | undefined): StageStatus {
  if (!o) return 'idle';
  if (o.status === 'failed') return 'failed';
  if (o.status === 'harvested') return 'complete';
  if (o.status === 'researching' || o.status === 'created') return 'active';
  return 'pending';
}

function stageLabel(stages: Stages, snap: RunnerSnapshot): string {
  if (stages.errored) return 'Containment Fault';
  if (stages.wafer === 'complete') return 'Etched — Resolution Ready';
  if (stages.synthesis === 'active' || stages.wafer === 'active') return 'Synthesis Convergence';
  if (stages.mask === 'active') {
    const done = snap.oracles.filter(o => o.status === 'harvested' || o.status === 'failed').length;
    return `Projection Optics — ${done}/${snap.oracles.length} mirrors`;
  }
  if (stages.blueprint === 'active') return 'Illuminator — Blueprint Shaping';
  if (stages.blueprint === 'complete' && stages.mask === 'idle') return 'Reticle Patterning';
  if (stages.plasma === 'active') return 'Plasma — Triage Firing';
  if (stages.scenario === 'complete') return 'Laser Cold — Awaiting Plasma';
  return 'Standby';
}

// =============================================================================
// Geometry — viewBox 1400 × 1000, top-left origin
// =============================================================================

function computeBenchLayout(oracleCount: number): Layout {
  // Idle still draws 3 ghosted optics so the machine has structural form.
  const requested = oracleCount > 0 ? oracleCount : 3;
  const N = Math.max(1, Math.min(5, requested));

  const LASER       = { x: 100, y: 600 };
  const COLLECTOR   = { x: 175, y: 600 };
  const PLASMA      = { x: 215, y: 600 };
  const FOCUS       = { x: 380, y: 410 };
  const ILLUMINATOR = { x: 520, y: 820 };
  const MASK        = { x: 740, y: 130 };

  const ORACLE_BOTTOM_Y = 720;
  const ORACLE_TOP_Y    = 200;
  // Wafer x is FIXED — last oracle aligns directly above it so the final
  // synthesis beam strikes the magic-circle dead-centre, straight down.
  const WAFER_X = 1240;
  const xStart  = 880;
  const oracleStep = N === 1 ? 0 : (WAFER_X - xStart) / (N - 1);

  const oracles: OracleSlot[] = Array.from({ length: N }, (_, i) => ({
    x: N === 1 ? WAFER_X : xStart + i * oracleStep,
    y: i % 2 === 0 ? ORACLE_BOTTOM_Y : ORACLE_TOP_Y,
    level: (i % 2 === 0 ? 'bottom' : 'top') as 'bottom' | 'top',
    index: i,
  }));

  const WAFER = { x: WAFER_X, y: 820 };

  return { LASER, COLLECTOR, PLASMA, FOCUS, ILLUMINATOR, MASK, oracles, WAFER, N };
}

function coneQuad(p1: Point, w1: number, p2: Point, w2: number): string {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny =  dx / len;
  const ax = p1.x + (nx * w1) / 2, ay = p1.y + (ny * w1) / 2;
  const bx = p1.x - (nx * w1) / 2, by = p1.y - (ny * w1) / 2;
  const cx = p2.x - (nx * w2) / 2, cy = p2.y - (ny * w2) / 2;
  const dxq = p2.x + (nx * w2) / 2, dyq = p2.y + (ny * w2) / 2;
  return `M${ax.toFixed(2)},${ay.toFixed(2)} L${dxq.toFixed(2)},${dyq.toFixed(2)} L${cx.toFixed(2)},${cy.toFixed(2)} L${bx.toFixed(2)},${by.toFixed(2)} Z`;
}

function mirrorAngleAt(pivot: Point, incoming: Point, outgoing: Point): number {
  const ax = incoming.x - pivot.x, ay = incoming.y - pivot.y;
  const bx = outgoing.x - pivot.x, by = outgoing.y - pivot.y;
  const la = Math.hypot(ax, ay) || 1;
  const lb = Math.hypot(bx, by) || 1;
  const nx = ax / la + bx / lb;
  const ny = ay / la + by / lb;
  return (Math.atan2(ny, nx) * 180) / Math.PI - 90;
}

// =============================================================================
// Component root
// =============================================================================

export function LithographyView({
  snapshot, onSwitchToCanvas, canvasAvailable,
}: LithographyViewProps) {
  const stages = useMemo(() => deriveStages(snapshot), [snapshot]);
  const stageText = stages ? stageLabel(stages, snapshot) : '—';

  return (
    <div className="lv-root">
      <Header
        pathway={snapshot.pathway}
        stageText={stageText}
        onSwitchToCanvas={onSwitchToCanvas}
        canvasAvailable={canvasAvailable}
      />
      <div className="lv-body">
        {stages ? (
          <CleanroomBench snapshot={snapshot} stages={stages} />
        ) : (
          <PathwayPlaceholder pathway={snapshot.pathway} />
        )}
      </div>
      <LithographyStyles />
    </div>
  );
}

function Header({
  pathway, stageText, onSwitchToCanvas, canvasAvailable,
}: {
  pathway: string; stageText: string;
  onSwitchToCanvas?: () => void; canvasAvailable?: boolean;
}) {
  return (
    <div className="lv-header">
      <div className="lv-header-left">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
          <rect x="2" y="2" width="12" height="12" rx="1.5" stroke="rgba(167,139,250,0.95)" strokeWidth="1.2"/>
          <circle cx="8" cy="8" r="2.2" fill="rgba(167,139,250,0.5)" stroke="rgba(196,181,253,1)" strokeWidth="0.8"/>
          <line x1="8" y1="0.5" x2="8" y2="2"   stroke="rgba(167,139,250,0.7)" strokeWidth="1"/>
          <line x1="8" y1="14"  x2="8" y2="15.5" stroke="rgba(167,139,250,0.7)" strokeWidth="1"/>
          <line x1="0.5" y1="8" x2="2" y2="8"   stroke="rgba(167,139,250,0.7)" strokeWidth="1"/>
          <line x1="14"  y1="8" x2="15.5" y2="8" stroke="rgba(167,139,250,0.7)" strokeWidth="1"/>
        </svg>
        <span className="lv-header-title">
          Optics Box · <em>{pathway.replace('_', ' ')}</em>
        </span>
        <span className="lv-header-divider"/>
        <span className="lv-header-id">UNIT 04 · EUV-CLASS · GEN-IV</span>
      </div>
      <div className="lv-header-right">
        <div className="lv-header-stage">
          <span className="lv-header-stage-label">STAGE</span>
          <span className="lv-header-stage-value">{stageText}</span>
        </div>
        {canvasAvailable && (
          <button type="button" className="lv-header-btn" onClick={onSwitchToCanvas}>
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
              <path d="M1 5 Q5 1 9 5 Q5 9 1 5 Z" stroke="currentColor" strokeWidth="1" fill="none"/>
              <circle cx="5" cy="5" r="1.5" fill="currentColor"/>
            </svg>
            Canvas
          </button>
        )}
      </div>
    </div>
  );
}

function PathwayPlaceholder({ pathway }: { pathway: string }) {
  // Only mirror_audit reaches here now that the bench renders for every
  // oracle-harvest pathway (cleanroom / genie / offensive). Mirror Audit
  // runs a single audit pass over a supplied prior resolution — there is no
  // triage → oracle harvest → synthesis pipeline to render on the bench.
  const isMirrorAudit = pathway === 'mirror_audit';
  return (
    <div className="lv-pathway-pending">
      <div className="lv-pp-title">
        {isMirrorAudit ? 'NO BENCH FOR THIS PATHWAY' : 'DESIGN PENDING'}
      </div>
      <div className="lv-pp-sub">
        {isMirrorAudit
          ? 'Mirror Audit reviews a prior resolution in a single pass — there is no oracle-harvest pipeline to visualise. Watch the audit stroke in the runner panel instead.'
          : 'The optics bench renders for the oracle-harvest pathways (Predict / Pathfind / Architect). This pathway has no bench geometry yet.'}
      </div>
    </div>
  );
}

// =============================================================================
// CleanroomBench — the scene + drag state
// =============================================================================

function CleanroomBench({ snapshot, stages }: { snapshot: RunnerSnapshot; stages: Stages; }) {
  const baseLayout = useMemo(
    () => computeBenchLayout(snapshot.oracles?.length || 0),
    [snapshot.oracles?.length]
  );

  // ----- Mirror drag state ---------------------------------------------------
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [dragOffsets, setDragOffsets] = useState<Record<number, number>>({});
  const dragRef = useRef<{ index: number; startSvgX: number; startOffset: number } | null>(null);

  const clientToSvgX = useCallback((clientX: number): number => {
    const svg = svgRef.current;
    if (!svg) return 0;
    const pt = svg.createSVGPoint();
    pt.x = clientX; pt.y = 0;
    const m = svg.getScreenCTM();
    if (!m) return 0;
    return pt.matrixTransform(m.inverse()).x;
  }, []);

  const onMirrorDown = (i: number, e: React.PointerEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const svgX = clientToSvgX(e.clientX);
    dragRef.current = { index: i, startSvgX: svgX, startOffset: dragOffsets[i] || 0 };
    (e.currentTarget as Element).setPointerCapture?.(e.pointerId);
  };
  const onMirrorMove = (e: React.PointerEvent) => {
    if (!dragRef.current) return;
    const svgX = clientToSvgX(e.clientX);
    const { index, startSvgX, startOffset } = dragRef.current;
    const delta = svgX - startSvgX;
    const next = Math.max(-MIRROR_NUDGE_MAX, Math.min(MIRROR_NUDGE_MAX, startOffset + delta));
    setDragOffsets(d => ({ ...d, [index]: next }));
  };
  const onMirrorUp = () => { dragRef.current = null; };
  const resetDrag = () => setDragOffsets({});

  // ----- Hover state (mirrors, illuminator, mask plate + features all
  // share it). Numbers = oracle index; strings = named non-draggable optic.
  const [hoveredIndex, setHoveredIndex] = useState<number | 'illuminator' | 'mask' | null>(null);
  const isOracleHover = typeof hoveredIndex === 'number';

  const layout = useMemo(() => {
    const oracles = baseLayout.oracles.map((o, i) => ({
      ...o,
      x: o.x + (dragOffsets[i] || 0),
    }));
    return { ...baseLayout, oracles };
  }, [baseLayout, dragOffsets]);

  const { LASER, PLASMA, FOCUS, ILLUMINATOR, MASK, oracles, WAFER } = layout;
  const hasAnyActivity =
    snapshot.running ||
    !!snapshot.blueprint ||
    !!snapshot.finalText ||
    (snapshot.strokes?.length ?? 0) > 0 ||
    (snapshot.oracles?.length ?? 0) > 0;
  const hasNudge = Object.values(dragOffsets).some(v => v !== 0);

  // ----- Misalignment of final beam -----------------------------------------
  const lastIdx = oracles.length - 1;
  const lastOffset = dragOffsets[lastIdx] || 0;
  const lastAbs = Math.abs(lastOffset);
  const misalignAmount =
    lastAbs <= MISALIGN_THRESHOLD
      ? 0
      : Math.sign(lastOffset) * (lastAbs - MISALIGN_THRESHOLD) * 5;
  const isMisaligned = misalignAmount !== 0;

  // ----- Beam segments -------------------------------------------------------

  const laserFrom = { x: LASER.x + 50, y: LASER.y };
  const laserTo   = { x: PLASMA.x - 10, y: PLASMA.y };
  const plasmaFrom = { x: PLASMA.x + 10, y: PLASMA.y - 10 };

  const oracleIn = oracles.map((o, i) => {
    const prev = i === 0 ? MASK : oracles[i - 1];
    const prevExitY = prev.y + (prev.y < 400 ? 22 : -22);
    const enterY    = o.y + (o.y > 500 ? -22 : 22);
    return {
      from: { x: prev.x, y: prevExitY },
      to:   { x: o.x, y: enterY },
      fromW: i === 0 ? 22 : 38,
      toW: 50,
    };
  });

  const last = oracles[oracles.length - 1];
  const waferFrom = { x: last.x, y: last.y + (last.y > 500 ? -22 : 22) };
  const waferTo   = { x: WAFER.x + misalignAmount, y: WAFER.y - 4 };

  const illumAngle = mirrorAngleAt(ILLUMINATOR, FOCUS, MASK);
  const oracleAngles = oracles.map((o, i) => {
    const incoming = i === 0 ? MASK : oracles[i - 1];
    const outgoing = i === oracles.length - 1
      ? { x: WAFER.x + misalignAmount, y: WAFER.y }
      : oracles[i + 1];
    return mirrorAngleAt(o, incoming, outgoing);
  });

  return (
    <svg
      ref={svgRef}
      viewBox="0 0 1400 1000"
      preserveAspectRatio="xMidYMid meet"
      className={`lv-svg ${hoveredIndex != null ? 'lv-bench-hover' : ''}`}
      onPointerMove={onMirrorMove}
      onPointerUp={onMirrorUp}
      onPointerLeave={onMirrorUp}
    >
      <Defs />
      <BackgroundChrome />
      <DustMotes />
      <StructuralOutline layout={layout} active={!!hasAnyActivity} />

      {/* Beams */}
      <Beam id="laser"
            from={laserFrom} fromW={14} to={laserTo} toW={8}
            status={stages.plasma === 'idle' ? 'idle' : 'complete'}
            animate={stages.plasma === 'active'} duration="1.0s"
            dim={hoveredIndex != null}/>

      <Beam id="plasma2focus"
            from={plasmaFrom} fromW={18} to={FOCUS} toW={6}
            status={stages.plasma === 'active' || stages.blueprint !== 'idle' ? 'complete' : 'idle'}
            animate={stages.plasma === 'active'} duration="1.4s"
            dim={hoveredIndex != null}/>

      <Beam id="focus2illum"
            from={FOCUS} fromW={8} to={ILLUMINATOR} toW={150}
            status={stages.blueprint === 'idle' ? 'idle' : 'complete'}
            animate={stages.blueprint === 'active'}
            dim={hoveredIndex != null}/>

      <Beam id="illum2mask"
            from={ILLUMINATOR} fromW={150} to={MASK}
            toW={Math.max(80, oracles.length * 32)}
            status={
              stages.mask !== 'idle' ? 'complete' :
              stages.blueprint === 'complete' ? 'complete' : 'idle'
            }
            animate={stages.blueprint === 'complete' && stages.mask === 'idle'}
            dim={hoveredIndex != null}/>

      {oracles.map((_, i) => {
        const data = snapshot.oracles?.[i];
        const oStatus = oracleStageStatus(data);
        const beamStatus: StageStatus =
          oStatus === 'failed'   ? 'failed'   :
          oStatus === 'complete' ? 'complete' :
          oStatus === 'active'   ? 'complete' :
                                   'idle';
        const { from, to, fromW, toW } = oracleIn[i];
        const isThisHovered = hoveredIndex === i;
        const dim = hoveredIndex != null && !isThisHovered;
        return (
          <Beam key={`bin-${i}`} id={`oracle-in-${i}`}
                from={from} fromW={fromW} to={to} toW={toW}
                status={beamStatus} animate={oStatus === 'active'}
                tint={tintFor(i)} dim={dim}/>
        );
      })}

      <Beam id="oracle2wafer"
            from={waferFrom} fromW={50} to={waferTo} toW={isMisaligned ? 70 : 90}
            status={
              stages.wafer === 'complete' ? 'complete' :
              stages.synthesis !== 'idle' ? 'complete' : 'idle'
            }
            animate={stages.synthesis === 'active' || stages.wafer === 'active'}
            duration="2.0s"
            tint={tintFor(lastIdx)}
            dim={hoveredIndex != null}/>

      {/* Components */}
      <LaserSource pos={LASER}    active={stages.plasma !== 'idle'}/>
      <Collector   pos={layout.COLLECTOR} idle={stages.plasma === 'idle'}/>
      <Plasma      cx={PLASMA.x} cy={PLASMA.y} r={28} status={stages.plasma}/>
      <IntermediateFocus pos={FOCUS} active={stages.blueprint !== 'idle'}/>

      <Mirror cx={ILLUMINATOR.x} cy={ILLUMINATOR.y} w={170} h={26}
              angle={illumAngle}
              status={
                stages.blueprint === 'idle'   ? 'idle'   :
                stages.blueprint === 'active' ? 'active' : 'complete'
              }
              hovered={hoveredIndex === 'illuminator'}
              dim={isOracleHover}
              onPointerEnter={() => setHoveredIndex('illuminator')}
              onPointerLeave={() => setHoveredIndex(curr => curr === 'illuminator' ? null : curr)}/>

      <Mask pos={MASK}
            width={Math.max(120, oracles.length * 42)}
            height={14}
            status={stages.mask}
            oracles={snapshot.oracles || []}
            hoveredIndex={isOracleHover ? hoveredIndex : null}
            onFeatureHover={setHoveredIndex}
            plateHovered={hoveredIndex === 'mask'}
            onPlateHover={(on) => setHoveredIndex(curr => on ? 'mask' : (curr === 'mask' ? null : curr))}/>

      {oracles.map((o, i) => {
        const data = snapshot.oracles?.[i];
        const status = oracleStageStatus(data);
        const isThisHovered = hoveredIndex === i;
        const dim = hoveredIndex != null && !isThisHovered;
        return (
          <Mirror key={`mir-${i}`}
                  cx={o.x} cy={o.y} w={130} h={22}
                  angle={oracleAngles[i]}
                  status={status === 'pending' ? 'idle' : status}
                  draggable
                  dragOffset={dragOffsets[i] || 0}
                  onPointerDown={(e) => onMirrorDown(i, e)}
                  tint={tintFor(i)}
                  oracleIndex={i}
                  hovered={isThisHovered}
                  dim={dim}
                  onPointerEnter={() => setHoveredIndex(i)}
                  onPointerLeave={() => setHoveredIndex(curr => (curr === i ? null : curr))}/>
        );
      })}

      <MagicCircle pos={WAFER} rx={108} ry={34}
                   status={stages.wafer}
                   progress={waferProgress(stages)}/>

      <Labels layout={layout} snapshot={snapshot} stages={stages}/>

      {!hasAnyActivity && <EmptyStateBadge/>}
      {isMisaligned && <MisalignWarning/>}
      {isOracleHover && oracles[hoveredIndex as number] && (
        <OracleInspector
          oracle={oracles[hoveredIndex as number]}
          data={snapshot.oracles?.[hoveredIndex as number]}
          index={hoveredIndex as number}
          tint={tintFor(hoveredIndex as number)}/>
      )}
      {hoveredIndex === 'illuminator' && (
        <OpticInspector
          anchor={{ x: ILLUMINATOR.x, y: ILLUMINATOR.y - 18 }}
          side="below"
          tint={ILLUMINATOR_TINT}
          kicker="05 · ILLUMINATOR"
          title="Architectural Blueprint"
          meta={illuminatorMeta(snapshot, stages)}/>
      )}
      {hoveredIndex === 'mask' && (
        <OpticInspector
          anchor={{ x: MASK.x, y: MASK.y + 10 }}
          side="below"
          tint={MASK_TINT}
          kicker="06 · MASK · RETICLE"
          title="Strategic Hit List"
          meta={maskMeta(snapshot, stages, oracles.length)}/>
      )}
      {hasNudge && <NudgeReset onReset={resetDrag}/>}
    </svg>
  );
}

function NudgeReset({ onReset }: { onReset: () => void }) {
  return (
    <g transform="translate(1290 970)" className="lv-reset"
       onClick={onReset} style={{ cursor: 'pointer' }}>
      <rect x="-110" y="-14" width="110" height="22" rx="3"
            fill="rgba(2,6,23,0.85)" stroke="rgba(167,139,250,0.4)" strokeWidth="0.6"/>
      <text x="-55" y="2" textAnchor="middle" className="lv-reset-text">↺ RE-ALIGN OPTICS</text>
    </g>
  );
}

function MisalignWarning() {
  return (
    <g transform="translate(1140 970)" pointerEvents="none">
      <rect x="-110" y="-14" width="110" height="22" rx="3"
            fill="rgba(244,63,94,0.12)" stroke="rgba(244,63,94,0.55)" strokeWidth="0.6"/>
      <text x="-55" y="2" textAnchor="middle" className="lv-warn-text">⚠ BEAM OFF-AXIS</text>
    </g>
  );
}

function waferProgress(stages: Stages): number {
  if (stages.wafer === 'complete') return 1;
  if (stages.synthesis === 'active' || stages.wafer === 'active') return 0.7;
  if (stages.mask !== 'idle') return 0.20;
  return 0;
}

// Distinct neutral tints for non-draggable optics so hover cards still
// feel of the system but visually distinct from the oracle palette.
const ILLUMINATOR_TINT: OracleHue = {
  base: 'hsl(200, 80%, 78%)',
  dim:  'hsl(200, 80%, 84%)',
  glow: 'hsla(200, 80%, 78%, 0.32)',
  faint:'hsla(200, 80%, 78%, 0.16)',
};
const MASK_TINT: OracleHue = {
  base: 'hsl(50, 70%, 78%)',
  dim:  'hsl(50, 70%, 84%)',
  glow: 'hsla(50, 70%, 78%, 0.32)',
  faint:'hsla(50, 70%, 78%, 0.16)',
};

interface InspectorMetaRow { label: string; value: string; color?: string; bold?: boolean; }

function illuminatorMeta(snapshot: RunnerSnapshot, stages: Stages): InspectorMetaRow[] {
  const status =
    stages.blueprint === 'complete' ? 'SHAPED'
    : stages.blueprint === 'active' ? 'SHAPING'
    : 'COLD';
  const meta: InspectorMetaRow[] = [
    { label: 'STATUS', value: status, bold: true,
      color: stages.blueprint !== 'idle' ? ILLUMINATOR_TINT.dim : 'rgba(148,163,184,0.7)' },
    { label: 'ROLE',   value: 'Architectural blueprint → reticle shaping' },
  ];
  if (snapshot.blueprint) {
    meta.push({ label: 'BLUEPRINT', value: `${snapshot.blueprint.length.toLocaleString()} chars` });
  }
  return meta;
}

function maskMeta(snapshot: RunnerSnapshot, stages: Stages, oracleCount: number): InspectorMetaRow[] {
  const status =
    stages.mask === 'complete' ? 'PATTERNED'
    : stages.mask === 'active' ? 'PATTERNING'
    : 'BLANK';
  return [
    { label: 'STATUS',   value: status, bold: true,
      color: stages.mask !== 'idle' ? MASK_TINT.dim : 'rgba(148,163,184,0.7)' },
    { label: 'SUBJECTS', value: `${oracleCount} feature${oracleCount === 1 ? '' : 's'}` },
    { label: 'ROLE',     value: 'One feature per PKI oracle' },
  ];
}

// =============================================================================
// Beam — volumetric cone + longitudinal "wave packet" flow animation
// =============================================================================

function Beam({
  from, fromW, to, toW, status, animate, id, duration, tint, dim,
}: {
  from: Point; fromW: number; to: Point; toW: number;
  status: StageStatus; animate?: boolean; id: string; duration?: string;
  tint?: OracleHue; dim?: boolean;
}) {
  const path = coneQuad(from, fromW, to, toW);
  const idle = status === 'idle' || status === 'pending';
  const failed = status === 'failed';

  let fillOuter: string;
  let fillInner: string;
  let centerline: string | null;
  if (failed) {
    fillOuter  = 'rgba(244,63,94,0.16)';
    fillInner  = 'rgba(244,63,94,0.34)';
    centerline = 'rgba(253,164,175,0.9)';
  } else if (idle) {
    fillOuter  = 'rgba(99,102,241,0.05)';
    fillInner  = 'transparent';
    centerline = null;
  } else if (tint) {
    fillOuter  = tint.faint;
    fillInner  = tint.glow;
    centerline = tint.dim;
  } else {
    fillOuter  = 'rgba(139,92,246,0.20)';
    fillInner  = 'rgba(167,139,250,0.36)';
    centerline = 'rgba(196,181,253,0.95)';
  }

  const flowId = `lv-flow-${id}`;
  const dur = duration || (failed ? '0.9s' : '1.6s');
  const pulseHi = failed ? 'rgba(254,205,211,0.95)' : 'rgba(255,255,255,0.95)';
  const pulseTr = failed ? 'rgba(244,63,94,0)'      : 'rgba(255,255,255,0)';

  return (
    <g className="lv-beam"
       style={{ opacity: dim ? 0.32 : 1, transition: 'opacity 0.18s' }}>
      <path d={path} fill={fillOuter} stroke="none"/>
      <path d={path} fill={fillInner} stroke="none"/>

      {animate && !idle && (
        <>
          <defs>
            <linearGradient
              id={flowId}
              x1={from.x} y1={from.y} x2={to.x} y2={to.y}
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0"    stopColor={pulseTr}/>
              <stop offset="0.42" stopColor={pulseTr}/>
              <stop offset="0.50" stopColor={pulseHi}/>
              <stop offset="0.58" stopColor={pulseTr}/>
              <stop offset="1"    stopColor={pulseTr}/>
              <animateTransform
                attributeName="gradientTransform"
                type="translate"
                from={`${-(to.x - from.x)} ${-(to.y - from.y)}`}
                to={`${(to.x - from.x)} ${(to.y - from.y)}`}
                dur={dur}
                repeatCount="indefinite"
              />
            </linearGradient>
          </defs>
          <path d={path} fill={`url(#${flowId})`}
                style={{ mixBlendMode: 'screen' }} opacity="0.9"/>
        </>
      )}

      {centerline && (
        <line
          x1={from.x} y1={from.y} x2={to.x} y2={to.y}
          stroke={centerline}
          strokeWidth="0.8"
          strokeOpacity="0.35"
        />
      )}
    </g>
  );
}

// =============================================================================
// Mirror — cylindrical face + dark mount strip + drag affordance
// =============================================================================

function Mirror({
  cx, cy, w, h, angle, status,
  draggable, dragOffset, onPointerDown,
  tint, oracleIndex, hovered, dim,
  onPointerEnter, onPointerLeave,
}: {
  cx: number; cy: number; w: number; h: number;
  angle: number; status: StageStatus;
  draggable?: boolean;
  dragOffset?: number;
  onPointerDown?: (e: React.PointerEvent) => void;
  tint?: OracleHue;
  oracleIndex?: number;
  hovered?: boolean;
  dim?: boolean;
  onPointerEnter?: (e: React.PointerEvent) => void;
  onPointerLeave?: (e: React.PointerEvent) => void;
}) {
  const idle = status === 'idle' || status === 'pending';
  const failed = status === 'failed';
  const ring = failed ? 'rgba(244,63,94,0.95)'
             : idle    ? 'rgba(148,163,184,0.45)'
             : tint    ? tint.dim
                       : 'rgba(196,181,253,0.85)';
  const isNudged = (dragOffset || 0) !== 0;

  const cracks = failed && oracleIndex != null
    ? buildCracks(oracleIndex, w, h)
    : null;

  return (
    <g
      transform={`translate(${cx} ${cy}) rotate(${angle})`}
      className={`lv-mirror ${draggable ? 'lv-mirror-drag' : ''} ${isNudged ? 'lv-mirror-nudged' : ''} ${hovered ? 'lv-mirror-hovered' : ''}`}
      style={{
        opacity: dim ? 0.42 : 1,
        cursor: draggable ? 'grab' : 'default',
        transition: 'opacity 0.18s',
      }}
      onPointerDown={onPointerDown}
      onPointerEnter={onPointerEnter}
      onPointerLeave={onPointerLeave}
    >
      {(status === 'active' || hovered) && (
        <ellipse cx="0" cy="0" rx={w/2 + 14} ry={h/2 + 8}
                 fill={hovered && tint ? tint.glow : 'rgba(167,139,250,0.18)'}
                 filter="blur(6px)"/>
      )}
      {draggable && (
        <g className="lv-mirror-handle" pointerEvents="none">
          <line x1={-w/2} y1={-h/2 - 7} x2={w/2} y2={-h/2 - 7}
                stroke="rgba(167,139,250,0.32)" strokeWidth="0.5"
                strokeDasharray="2 3"/>
          <path d={`M${-w/2 - 4},${-h/2 - 7} l-4,-3 l0,6 z`}
                fill="rgba(167,139,250,0.4)"/>
          <path d={`M${ w/2 + 4},${-h/2 - 7} l 4,-3 l0,6 z`}
                fill="rgba(167,139,250,0.4)"/>
        </g>
      )}
      <path
        d={`M${-w/2 + 6},${h/2 - 1} L${w/2 - 6},${h/2 - 1} L${w/2 - 14},${h/2 + 10} L${-w/2 + 14},${h/2 + 10} Z`}
        fill="rgba(30,41,59,0.95)" stroke="rgba(15,23,42,1)" strokeWidth="0.5"/>
      <ellipse cx="0" cy="0" rx={w/2} ry={h/2}
               fill="url(#lv-mirror-face)"
               stroke={ring}
               strokeWidth={hovered ? 1.4 : 0.8}/>
      <path
        d={`M${-w/2 + 4},${-1} A ${w/2 - 4} ${h/2 - 1} 0 0 1 ${w/2 - 4},${-1}`}
        stroke="rgba(255,255,255,0.55)" strokeWidth="0.8" fill="none"/>
      <ellipse cx="0" cy="0" rx={w/2} ry={h/2}
               fill="none" stroke="rgba(15,23,42,0.6)" strokeWidth="0.5"/>
      {cracks && (
        <g pointerEvents="none">
          {cracks.map((c, i) => (
            <path key={`shadow-${i}`} d={c}
                  stroke="rgba(0,0,0,0.6)" strokeWidth="1.2"
                  fill="none" strokeLinecap="round"
                  opacity="0.5"
                  style={{ filter: 'blur(0.4px)' }}/>
          ))}
          {cracks.map((c, i) => (
            <path key={`crack-${i}`} d={c}
                  stroke="rgba(255,250,255,0.85)" strokeWidth="0.5"
                  fill="none" strokeLinecap="round"/>
          ))}
        </g>
      )}
    </g>
  );
}

/**
 * Stable jagged crack path across a broken mirror face.  Uses oracle
 * index as seed so the same failure always shows the same fracture.
 */
function buildCracks(index: number, w: number, h: number): string[] {
  function rand(seed: number) {
    const x = Math.sin(seed * 12.9898 + index * 78.233) * 43758.5453;
    return x - Math.floor(x);
  }
  const halfW = w / 2;
  const halfH = h / 2;

  // Crack 1 — roughly horizontal
  const c1: string[] = [];
  const c1Y = (rand(1) - 0.5) * halfH * 0.8;
  c1.push(`M${-halfW + 4},${c1Y.toFixed(2)}`);
  for (let i = 1; i <= 4; i++) {
    const x = -halfW + 4 + (i / 5) * (w - 8);
    const y = c1Y + (rand(i + 10) - 0.5) * halfH * 0.55;
    c1.push(`L${x.toFixed(2)},${y.toFixed(2)}`);
  }
  c1.push(`L${halfW - 4},${(c1Y + (rand(20) - 0.5) * halfH).toFixed(2)}`);

  // Crack 2 — diagonal
  const c2: string[] = [];
  const c2sx = -halfW * 0.3 + rand(30) * halfW * 0.6;
  const c2sy = -halfH * 0.85;
  const c2ex = c2sx + (rand(31) - 0.5) * halfW * 0.6;
  const c2ey = halfH * 0.85;
  c2.push(`M${c2sx.toFixed(2)},${c2sy.toFixed(2)}`);
  for (let i = 1; i <= 3; i++) {
    const t = i / 4;
    const x = c2sx + (c2ex - c2sx) * t + (rand(40 + i) - 0.5) * halfW * 0.35;
    const y = c2sy + (c2ey - c2sy) * t + (rand(50 + i) - 0.5) * halfH * 0.3;
    c2.push(`L${x.toFixed(2)},${y.toFixed(2)}`);
  }
  c2.push(`L${c2ex.toFixed(2)},${c2ey.toFixed(2)}`);

  return [c1.join(' '), c2.join(' ')];
}

// =============================================================================
// Plasma — radial gradient + rotating flare cross
// =============================================================================

function Plasma({ cx, cy, r, status }: { cx: number; cy: number; r: number; status: StageStatus }) {
  if (status === 'idle') {
    return (
      <circle cx={cx} cy={cy} r={r}
              fill="rgba(76,29,149,0.04)"
              stroke="rgba(148,163,184,0.25)"
              strokeWidth="0.6"
              strokeDasharray="2 3"/>
    );
  }
  const active = status === 'active';
  return (
    <g className={active ? 'lv-plasma-active' : ''}>
      <circle cx={cx} cy={cy} r={r * 2.2} fill="url(#lv-plasma-halo)"/>
      <circle cx={cx} cy={cy} r={r}        fill="url(#lv-plasma-core)"/>
      <circle cx={cx} cy={cy} r={r * 0.35} fill="rgba(255,250,255,0.95)"/>
      <g className="lv-plasma-flare" style={{ transformOrigin: `${cx}px ${cy}px` }}>
        <line x1={cx - r*1.8} y1={cy}        x2={cx + r*1.8} y2={cy}        stroke="rgba(255,250,255,0.55)" strokeWidth="0.6"/>
        <line x1={cx}         y1={cy - r*1.8} x2={cx}        y2={cy + r*1.8} stroke="rgba(255,250,255,0.55)" strokeWidth="0.6"/>
        <line x1={cx - r*1.5} y1={cy - r*1.5} x2={cx + r*1.5} y2={cy + r*1.5} stroke="rgba(255,250,255,0.35)" strokeWidth="0.5"/>
        <line x1={cx - r*1.5} y1={cy + r*1.5} x2={cx + r*1.5} y2={cy - r*1.5} stroke="rgba(255,250,255,0.35)" strokeWidth="0.5"/>
      </g>
    </g>
  );
}

// =============================================================================
// Laser, Collector, Intermediate Focus
// =============================================================================

function LaserSource({ pos, active }: { pos: Point; active: boolean }) {
  return (
    <g transform={`translate(${pos.x} ${pos.y})`}>
      <rect x="-50" y="-22" width="38" height="44" rx="2"
            fill="rgba(30,41,59,0.95)" stroke="rgba(71,85,105,0.8)" strokeWidth="0.6"/>
      <rect x="-12" y="-10" width="48" height="20" rx="3"
            fill="url(#lv-mirror-face)" stroke="rgba(71,85,105,0.8)" strokeWidth="0.5"/>
      <circle cx="38" cy="0" r="6"  fill="rgba(15,23,42,1)" stroke="rgba(148,163,184,0.7)" strokeWidth="0.5"/>
      <circle cx="38" cy="0" r="3.2"
              fill={active ? 'rgba(244,114,182,0.95)' : 'rgba(127,29,29,0.6)'}/>
      {active && <circle cx="38" cy="0" r="3.2" fill="rgba(255,200,220,0.7)" className="lv-pulse-fast"/>}
      <g stroke="rgba(15,23,42,0.95)" strokeWidth="0.5">
        {[-15, -8, 0, 8, 15].map(y => <line key={y} x1="-50" y1={y} x2="-12" y2={y}/>)}
      </g>
    </g>
  );
}

function Collector({ pos, idle }: { pos: Point; idle: boolean }) {
  return (
    <g transform={`translate(${pos.x} ${pos.y})`}>
      <path
        d="M-32,-44 A 50 44 0 0 0 -32,44 L-20,28 A 32 28 0 0 1 -20,-28 Z"
        fill="url(#lv-mirror-face)" stroke="rgba(71,85,105,0.85)" strokeWidth="0.6"/>
      <rect x="-46" y="-10" width="10" height="20"
            fill="rgba(30,41,59,0.95)" stroke="rgba(71,85,105,0.7)" strokeWidth="0.4"/>
      <path d="M-22,-28 A 32 28 0 0 0 -22,28"
            fill="none" opacity="0.85"
            stroke={idle ? 'rgba(148,163,184,0.5)' : 'rgba(196,181,253,0.55)'}
            strokeWidth="0.5"/>
    </g>
  );
}

function IntermediateFocus({ pos, active }: { pos: Point; active: boolean }) {
  return (
    <g transform={`translate(${pos.x} ${pos.y})`}>
      <circle cx="0" cy="0" r="9" fill="rgba(2,6,23,0.95)"
              stroke={active ? 'rgba(196,181,253,0.9)' : 'rgba(148,163,184,0.45)'} strokeWidth="0.6"/>
      <circle cx="0" cy="0" r="2.4" fill={active ? 'rgba(196,181,253,1)' : 'rgba(76,29,149,0.4)'}/>
      <g stroke={active ? 'rgba(196,181,253,0.6)' : 'rgba(148,163,184,0.35)'} strokeWidth="0.5">
        <line x1="-14" y1="0" x2="-10" y2="0"/>
        <line x1="10" y1="0"  x2="14" y2="0"/>
        <line x1="0" y1="-14" x2="0" y2="-10"/>
        <line x1="0" y1="10" x2="0" y2="14"/>
      </g>
    </g>
  );
}

// =============================================================================
// Mask
// =============================================================================

function Mask({
  pos, width, height, status, oracles,
  hoveredIndex, onFeatureHover,
  plateHovered, onPlateHover,
}: {
  pos: Point; width: number; height: number; status: StageStatus;
  oracles: OracleProgress[];
  hoveredIndex?: number | null;
  onFeatureHover?: (i: number | null) => void;
  plateHovered?: boolean;
  onPlateHover?: (on: boolean) => void;
}) {
  const idle = status === 'idle';
  const ring = status === 'failed' ? 'rgba(244,63,94,0.95)'
             : idle    ? 'rgba(148,163,184,0.55)'
                       : 'rgba(226,232,240,0.95)';
  const features = oracles.length || 1;
  return (
    <g transform={`translate(${pos.x} ${pos.y})`}
       onPointerEnter={() => onPlateHover?.(true)}
       onPointerLeave={() => onPlateHover?.(false)}
       style={{ cursor: 'help' }}>
      <line x1={-width/2 - 14} y1="0" x2={-width/2} y2="0"
            stroke="rgba(71,85,105,0.85)" strokeWidth="3"/>
      <line x1={width/2} y1="0" x2={width/2 + 14} y2="0"
            stroke="rgba(71,85,105,0.85)" strokeWidth="3"/>
      {plateHovered && (
        <rect x={-width/2 - 4} y={-height/2 - 4}
              width={width + 8} height={height + 8} rx="2"
              fill="rgba(167,139,250,0.18)"/>
      )}
      <rect x={-width/2} y={-height/2} width={width} height={height} rx="1"
            fill="url(#lv-mirror-face)"
            stroke={plateHovered ? 'rgba(196,181,253,0.95)' : ring}
            strokeWidth={plateHovered ? 1.2 : 0.6}/>
      {Array.from({ length: features }, (_, i) => {
        const o = oracles[i];
        const oStatus = oracleStageStatus(o);
        const tint = tintFor(i);
        const fill =
          oStatus === 'failed'   ? 'rgba(244,63,94,0.95)' :
          oStatus === 'complete' ? tint.dim :
          oStatus === 'active'   ? tint.base :
                                   'rgba(30,41,59,0.95)';
        const x = -width/2 + (i + 1) * (width / (features + 1));
        const isHovered = hoveredIndex === i;
        return (
          <g key={i}
             onPointerEnter={() => onFeatureHover?.(i)}
             onPointerLeave={() => onFeatureHover?.(null)}
             style={{ cursor: o ? 'help' : 'default' }}>
            <rect x={x - 9} y={-height} width="18" height={height * 2} fill="transparent"/>
            <rect x={x - 1.5} y={-height/2 + 2} width="3" height={height - 4} fill={fill}/>
            <rect x={x - 4} y={-height/2 + 4}   width="8" height="1" fill={fill} opacity="0.6"/>
            <rect x={x - 4} y={ height/2 - 5}   width="8" height="1" fill={fill} opacity="0.6"/>
            {isHovered && (
              <g pointerEvents="none">
                <circle cx={x} cy={-height/2 - 8} r="3.5"
                        fill="none" stroke={tint.dim} strokeWidth="0.8"/>
                <circle cx={x} cy={-height/2 - 8} r="1.5" fill={tint.dim}/>
              </g>
            )}
          </g>
        );
      })}
    </g>
  );
}

// =============================================================================
// Magic-Circle Wafer
// =============================================================================

// Rune-glyph alphabet — original geometric primitives, ~10×10 viewbox.
const RUNES = [
  'M-4,3 L0,-4 L4,3 Z',                                    // △
  'M-4,-3 L0,4 L4,-3 Z',                                   // ▽
  'M0,-5 L4,0 L0,5 L-4,0 Z',                               // ◇
  'M-4,-4 L4,-4 L4,4 L-4,4 Z',                             // □
  'M0,-5 L0,5 M-5,0 L5,0',                                 // +
  'M-4,-4 L4,4 M-4,4 L4,-4',                               // ×
  'M-3,-4 L3,-4 L5,0 L3,4 L-3,4 L-5,0 Z',                  // ⬡
  'M-2,-4 L-2,4 M0,-4 L0,4 M2,-4 L2,4',                    // ⫼
  'M0,-5 L0,5 M-4,-3 L4,3 M-4,3 L4,-3',                    // ✱
  'M-4,-4 L4,-4 M0,-4 L0,4',                               // T
  'M-3,-3 L3,-3 L3,3 L-3,3 Z',                             // ▪
  'M0,-4 L3,2 L-3,2 Z M0,4 L3,-2 L-3,-2 Z',                // ✡
];

function MagicCircle({
  pos, rx, ry, status, progress,
}: {
  pos: Point; rx: number; ry: number; status: StageStatus; progress: number;
}) {
  const idle = status === 'idle';
  const lit  = status === 'complete';
  const active = status === 'active';

  // Reveal thresholds — rings come online one by one
  const ringOuter   = progress >= 0.0;
  const ringRunes   = progress >= 0.20;
  const ringMid     = progress >= 0.35;
  const ringLattice = progress >= 0.55;
  const ringCore    = progress >= 0.45;
  const ringSparks  = progress >= 0.92;

  const baseRing  = idle ? 'rgba(148,163,184,0.30)' : 'rgba(196,181,253,0.78)';
  const dimRing   = idle ? 'rgba(148,163,184,0.18)' : 'rgba(167,139,250,0.40)';
  const accent    = lit  ? 'rgba(125,211,252,0.85)' : 'rgba(196,181,253,0.85)';
  const failed    = status === 'failed';

  const N = 12;
  const runeR = { x: rx * 0.86, y: ry * 0.86 };

  return (
    <g transform={`translate(${pos.x} ${pos.y})`} className="lv-magic-circle">
      <ellipse cx="0" cy={ry + 8} rx={rx * 1.05} ry={ry * 0.35}
               fill="rgba(30,41,59,0.95)" stroke="rgba(71,85,105,0.85)" strokeWidth="0.5"/>

      {(active || lit) && (
        <ellipse cx="0" cy="0" rx={rx * 1.25} ry={ry * 1.4}
                 fill="url(#lv-mc-halo)" pointerEvents="none"/>
      )}

      <ellipse cx="0" cy="0" rx={rx} ry={ry}
               fill={idle ? 'rgba(15,23,42,0.75)' : 'rgba(20,12,40,0.9)'}
               stroke={failed ? 'rgba(244,63,94,0.95)' : baseRing}
               strokeWidth="0.8"/>

      {/* Rotor — rings/runes/lattice grouped together. Rotation was removed
          per user feedback; static reads more like a focused etching plate. */}
      <g>

      {ringOuter && (
        <g>
          <ellipse cx="0" cy="0" rx={rx * 0.94} ry={ry * 0.94}
                   fill="none" stroke={accent} strokeWidth="0.6" opacity="0.7"/>
          <ellipse cx="0" cy="0" rx={rx * 0.78} ry={ry * 0.78}
                   fill="none" stroke={dimRing} strokeWidth="0.4"
                   strokeDasharray="2 3"/>
        </g>
      )}

      {ringRunes && (
        <g className={lit ? 'lv-mc-runes-lit' : ''}>
          {Array.from({ length: N }, (_, i) => {
            const a = (i / N) * Math.PI * 2 - Math.PI / 2;
            const x = Math.cos(a) * runeR.x;
            const y = Math.sin(a) * runeR.y;
            const glyph = RUNES[i % RUNES.length];
            const reveal = Math.max(0, Math.min(1, (progress - 0.15) * 3 - i / N));
            const op = lit ? 0.95 : Math.min(1, reveal * 1.8);
            const fill = i % 3 === 0 ? 'rgba(125,211,252,0.9)' :
                         i % 3 === 1 ? 'rgba(196,181,253,0.95)' :
                                       'rgba(134,239,172,0.85)';
            return (
              <g key={i}
                 transform={`translate(${x.toFixed(2)} ${y.toFixed(2)}) rotate(${(a * 180/Math.PI) + 90}) scale(1.7)`}
                 opacity={op}>
                <path d={glyph} fill="none" stroke={fill} strokeWidth="0.6"
                      strokeLinecap="round" strokeLinejoin="round"/>
              </g>
            );
          })}
        </g>
      )}

      {ringMid && (
        <g opacity={lit ? 1 : 0.85}>
          <ellipse cx="0" cy="0" rx={rx * 0.62} ry={ry * 0.62}
                   fill="none" stroke={accent} strokeWidth="0.6"/>
          {Array.from({ length: 24 }, (_, i) => {
            const a = (i / 24) * Math.PI * 2;
            return (
              <line key={i}
                    x1={Math.cos(a) * rx * 0.62} y1={Math.sin(a) * ry * 0.62}
                    x2={Math.cos(a) * rx * 0.66} y2={Math.sin(a) * ry * 0.66}
                    stroke={accent} strokeWidth="0.4" opacity="0.65"/>
            );
          })}
        </g>
      )}

      {ringLattice && (
        <g opacity={lit ? 1 : 0.7}>
          {Array.from({ length: 8 }, (_, i) => {
            const a = (i / 8) * Math.PI * 2;
            return (
              <line key={i}
                    x1={Math.cos(a) * rx * 0.10} y1={Math.sin(a) * ry * 0.10}
                    x2={Math.cos(a) * rx * 0.58} y2={Math.sin(a) * ry * 0.58}
                    stroke="rgba(167,139,250,0.55)" strokeWidth="0.4"/>
            );
          })}
          <ellipse cx="0" cy="0" rx={rx * 0.38} ry={ry * 0.38}
                   fill="none" stroke="rgba(196,181,253,0.55)"
                   strokeWidth="0.4" strokeDasharray="1 2"/>
          <ellipse cx="0" cy="0" rx={rx * 0.22} ry={ry * 0.22}
                   fill="none" stroke="rgba(196,181,253,0.7)" strokeWidth="0.5"/>
        </g>
      )}

      </g>{/* end rotor */}

      {ringCore && (
        <g className={lit ? 'lv-mc-core-lit' : 'lv-mc-core-active'}>
          <circle cx="0" cy="0" r={Math.min(rx, ry) * 0.55}
                  fill="url(#lv-mc-core)" opacity="0.8"/>
          <circle cx="0" cy="0" r={Math.min(rx, ry) * 0.18}
                  fill="rgba(255,250,255,0.95)"/>
        </g>
      )}

      {ringSparks && !failed && (
        <g className="lv-mc-sparks" pointerEvents="none">
          {[0, 1, 2, 3, 4, 5].map(i => {
            const a = (i / 6) * Math.PI * 2 + 0.4;
            const ex = Math.cos(a) * rx * 1.05;
            const ey = Math.sin(a) * ry * 1.05;
            const mid1x = ex * 0.35 + (Math.random() * 2 - 1) * 5;
            const mid1y = ey * 0.35 + (Math.random() * 2 - 1) * 5;
            const mid2x = ex * 0.7  + (Math.random() * 2 - 1) * 5;
            const mid2y = ey * 0.7  + (Math.random() * 2 - 1) * 5;
            const d = `M0,0 L${mid1x.toFixed(2)},${mid1y.toFixed(2)} L${mid2x.toFixed(2)},${mid2y.toFixed(2)} L${ex.toFixed(2)},${ey.toFixed(2)}`;
            return (
              <g key={i} className={`lv-mc-spark lv-mc-spark-${i}`}>
                <path d={d}
                      stroke="rgba(196,181,253,0.85)" strokeWidth="1" fill="none"
                      strokeLinecap="round" strokeLinejoin="round"
                      filter="url(#lv-mc-spark-glow)"/>
                <path d={d}
                      stroke="rgba(255,250,255,0.95)" strokeWidth="0.4" fill="none"
                      strokeLinecap="round" strokeLinejoin="round"/>
              </g>
            );
          })}
        </g>
      )}

      {ringOuter && (
        <g opacity="0.55">
          {[0, Math.PI/2, Math.PI, 3*Math.PI/2].map((a, i) => (
            <circle key={i}
                    cx={Math.cos(a) * rx * 0.94}
                    cy={Math.sin(a) * ry * 0.94}
                    r="1.4" fill={accent}/>
          ))}
        </g>
      )}
    </g>
  );
}

// =============================================================================
// Cleanroom dust motes — slow drifting particles that read as sealed-
// chamber atmosphere.  Paths are pre-baked (stable across re-renders).
// =============================================================================

const DUST_MOTES: Array<{ x0: number; y0: number; x1: number; y1: number; dur: number; r: number; op: number; delay: number }> = [
  { x0:   80, y0: 250, x1: 1320, y1: 380, dur: 38, r: 1.1, op: 0.32, delay:  0  },
  { x0: 1380, y0: 540, x1:   60, y1: 700, dur: 46, r: 0.9, op: 0.28, delay: -8  },
  { x0:   80, y0: 760, x1: 1320, y1: 280, dur: 52, r: 1.4, op: 0.38, delay: -22 },
  { x0: 1380, y0: 200, x1:   60, y1: 880, dur: 60, r: 0.8, op: 0.25, delay: -4  },
  { x0:   80, y0: 480, x1: 1320, y1: 920, dur: 44, r: 1.0, op: 0.30, delay: -18 },
  { x0: 1380, y0: 860, x1:   60, y1: 120, dur: 56, r: 1.2, op: 0.34, delay: -12 },
  { x0:   80, y0: 100, x1: 1320, y1: 600, dur: 48, r: 0.7, op: 0.24, delay: -30 },
  { x0: 1380, y0: 420, x1:   60, y1: 460, dur: 50, r: 1.1, op: 0.30, delay: -6  },
  { x0:   80, y0: 900, x1: 1320, y1: 120, dur: 64, r: 0.9, op: 0.26, delay: -26 },
  { x0: 1380, y0:  80, x1:   60, y1: 740, dur: 42, r: 1.3, op: 0.36, delay: -14 },
];

function DustMotes() {
  return (
    <g className="lv-dust" pointerEvents="none">
      {DUST_MOTES.map((m, i) => (
        <circle key={i} cx={m.x0} cy={m.y0} r={m.r}
                fill="rgba(255,250,255,1)" opacity={m.op}
                style={{ filter: 'blur(0.3px)' }}>
          <animate attributeName="cx"
                   values={`${m.x0};${m.x1};${m.x0}`}
                   dur={`${m.dur}s`}
                   begin={`${m.delay}s`}
                   repeatCount="indefinite"/>
          <animate attributeName="cy"
                   values={`${m.y0};${m.y1};${m.y0}`}
                   dur={`${m.dur}s`}
                   begin={`${m.delay}s`}
                   repeatCount="indefinite"/>
          <animate attributeName="opacity"
                   values={`0;${m.op};${m.op};0`}
                   keyTimes="0;0.15;0.85;1"
                   dur={`${m.dur}s`}
                   begin={`${m.delay}s`}
                   repeatCount="indefinite"/>
        </circle>
      ))}
    </g>
  );
}

// =============================================================================
// OpticInspector — generic hover popover card (shared by oracle / illuminator
// / mask).  Anchor is the point on the optic the leader line attaches to;
// `side` controls whether the card appears above or below the anchor.
// =============================================================================

function OpticInspector({
  anchor, side = 'auto', tint, kicker, title, meta,
}: {
  anchor: Point;
  side?: 'auto' | 'above' | 'below';
  tint: OracleHue;
  kicker: string;
  title: string;
  meta: InspectorMetaRow[];
}) {
  const cardW = 260, cardH = 110;
  const aboveOK = anchor.y > cardH + 80;
  const placeBelow = side === 'below' || (side === 'auto' && !aboveOK);
  const cardX = Math.min(1400 - cardW - 30, Math.max(30, anchor.x - cardW / 2));
  const cardY = placeBelow ? anchor.y + 50 : anchor.y - cardH - 50;

  return (
    <g className="lv-inspector" pointerEvents="none">
      <line x1={anchor.x} y1={anchor.y}
            x2={cardX + cardW / 2} y2={placeBelow ? cardY : cardY + cardH}
            stroke={tint.dim} strokeWidth="0.5" strokeOpacity="0.6"
            strokeDasharray="2 2"/>
      <rect x={cardX} y={cardY} width={cardW} height={cardH} rx="4"
            fill="rgba(2,6,23,0.95)" stroke={tint.dim} strokeWidth="0.8"/>
      <rect x={cardX} y={cardY} width="3" height={cardH} rx="1.5" fill={tint.base}/>
      <text x={cardX + 12} y={cardY + 18}
            className="lv-insp-kicker" fill={tint.dim}>
        {kicker}
      </text>
      <text x={cardX + 12} y={cardY + 36}
            className="lv-insp-title" fill="rgba(244,233,255,0.98)">
        {truncate(title, 32)}
      </text>
      {meta.map((row, i) => (
        <text key={i}
              x={cardX + 12} y={cardY + 56 + i * 16}
              className="lv-insp-meta" fill="rgba(148,163,184,0.85)">
          {row.label} · <tspan fill={row.color || 'rgba(196,181,253,0.85)'}
                                style={row.bold ? { fontWeight: 700 } : undefined}>
            {row.value}
          </tspan>
        </text>
      ))}
    </g>
  );
}

function OracleInspector({
  oracle, data, index, tint,
}: {
  oracle: OracleSlot; data: OracleProgress | undefined; index: number; tint: OracleHue;
}) {
  const status = data?.status || 'idle';
  const meta: InspectorMetaRow[] = [
    { label: 'STATUS', value: status.toUpperCase(), color: tint.dim, bold: true },
  ];
  if (data?.notebook_id) meta.push({ label: 'NOTEBOOK', value: data.notebook_id });
  if (data?.sources_imported != null) {
    meta.push({
      label: 'SOURCES',
      value: `${data.sources_imported}${data.packet_chars != null ? ` · CHARS · ${data.packet_chars.toLocaleString()}` : ''}`,
    });
  } else if (data?.packet_chars != null) {
    meta.push({ label: 'CHARS', value: data.packet_chars.toLocaleString() });
  }
  return (
    <OpticInspector
      anchor={oracle}
      side={oracle.y < 400 ? 'below' : 'above'}
      tint={tint}
      kicker={`PKI ORACLE · M${String(index + 1).padStart(2, '0')}`}
      title={data?.subject || `MIRROR ${index + 1} · PENDING`}
      meta={meta}
    />
  );
}

// =============================================================================
// Schematic labels
// =============================================================================

function SchematicLabel({
  anchorX, anchorY, labelX, labelY, kicker, title, sub,
  align = 'left', tone = 'normal',
}: {
  anchorX: number; anchorY: number; labelX: number; labelY: number;
  kicker?: string; title: string; sub?: string;
  align?: 'left' | 'right'; tone?: 'normal' | 'dim' | 'fail';
}) {
  const color = tone === 'fail' ? 'rgba(244,63,94,0.95)'
              : tone === 'dim'  ? 'rgba(148,163,184,0.45)'
                                : 'rgba(196,181,253,0.78)';
  const textAnchor = align === 'right' ? 'end' : 'start';
  const elbowX = align === 'right' ? labelX + 8 : labelX - 8;
  const tipX = align === 'right' ? labelX - 4 : labelX + 4;
  const path = `M${anchorX},${anchorY} L${elbowX},${anchorY} L${tipX},${labelY - 6}`;
  return (
    <g className="lv-callout">
      <path d={path} stroke={color} strokeWidth="0.6" fill="none" strokeOpacity="0.7"/>
      <circle cx={anchorX} cy={anchorY} r="1.6" fill={color} fillOpacity="0.85"/>
      {kicker && (
        <text x={labelX} y={labelY - 16} className="lv-cl-kicker" textAnchor={textAnchor} fill={color}>
          {kicker}
        </text>
      )}
      <text x={labelX} y={labelY - 4} className="lv-cl-title" textAnchor={textAnchor} fill={color}>
        {title}
      </text>
      {sub && (
        <text x={labelX} y={labelY + 9} className="lv-cl-sub" textAnchor={textAnchor} fill="rgba(148,163,184,0.7)">
          {sub}
        </text>
      )}
    </g>
  );
}

function Labels({
  layout, snapshot, stages,
}: { layout: Layout; snapshot: RunnerSnapshot; stages: Stages }) {
  const { LASER, COLLECTOR, PLASMA, FOCUS, ILLUMINATOR, MASK, oracles, WAFER } = layout;
  const oracleData = snapshot.oracles || [];

  return (
    <g className="lv-labels">
      <SchematicLabel
        anchorX={LASER.x + 38} anchorY={LASER.y - 22}
        labelX={70} labelY={150}
        kicker="01 · SOURCE" title="IR LASER"
        sub="user scenario · ignition"
        tone={stages.scenario === 'complete' ? 'normal' : 'dim'}/>

      <SchematicLabel
        anchorX={COLLECTOR.x - 32} anchorY={COLLECTOR.y - 30}
        labelX={70} labelY={240}
        kicker="02" title="COLLECTOR"
        sub="9D-chess engine"
        tone={stages.plasma !== 'idle' ? 'normal' : 'dim'}/>

      <SchematicLabel
        anchorX={PLASMA.x + 24} anchorY={PLASMA.y - 24}
        labelX={70} labelY={335}
        kicker="03 · TRIAGE" title="PLASMA"
        sub={stages.plasma === 'active' ? 'firing — triage in progress'
           : stages.plasma === 'complete' ? 'steady · blueprint emitted'
           : 'cold'}
        tone={stages.plasma === 'idle' ? 'dim' : 'normal'}/>

      <SchematicLabel
        anchorX={FOCUS.x + 8} anchorY={FOCUS.y - 8}
        labelX={FOCUS.x + 60} labelY={FOCUS.y - 32}
        kicker="04" title="INTERMEDIATE FOCUS"
        sub="architectural blueprint"
        tone={stages.blueprint !== 'idle' ? 'normal' : 'dim'}/>

      <SchematicLabel
        anchorX={ILLUMINATOR.x} anchorY={ILLUMINATOR.y + 22}
        labelX={ILLUMINATOR.x - 80} labelY={970}
        kicker="05" title="ILLUMINATOR"
        sub={snapshot.blueprint
          ? `${snapshot.blueprint.length.toLocaleString()} char blueprint`
          : 'awaiting plasma'}
        tone={stages.blueprint !== 'idle' ? 'normal' : 'dim'}/>

      <SchematicLabel
        anchorX={MASK.x + 30} anchorY={MASK.y - 10}
        labelX={MASK.x + 90} labelY={MASK.y - 30}
        kicker="06" title="MASK (RETICLE)"
        sub={`${oracles.length || 0} subject${oracles.length === 1 ? '' : 's'} · strategic hit list`}
        tone={stages.mask !== 'idle' ? 'normal' : 'dim'}/>

      {oracles.map((o, i) => {
        const data = oracleData[i];
        const status = oracleStageStatus(data);
        const tone: 'normal' | 'dim' | 'fail' =
          status === 'failed' ? 'fail' :
          status === 'pending' || !data ? 'dim' : 'normal';
        const toTop = o.y > 500;
        const labelY = toTop ? 70 + i * 36 : 950 - (oracles.length - 1 - i) * 26;
        return (
          <SchematicLabel
            key={`olbl-${i}`}
            anchorX={o.x + 56} anchorY={o.y + (toTop ? -10 : 10)}
            labelX={1330}     labelY={labelY}
            align="right"
            kicker={`PKI ORACLE · M${String(i + 1).padStart(2, '0')}`}
            title={data?.subject ? truncate(data.subject.toUpperCase(), 28) : `MIRROR ${i + 1} · PENDING`}
            sub={oracleSubLabel(data)}
            tone={tone}/>
        );
      })}

      {oracles.length > 0 && (
        <text
          x={(oracles[0].x + oracles[oracles.length - 1].x) / 2}
          y="500"
          textAnchor="middle"
          className="lv-group-label">
          PROJECTION OPTICS
        </text>
      )}

      <SchematicLabel
        anchorX={WAFER.x + 70} anchorY={WAFER.y + 18}
        labelX={WAFER.x + 130} labelY={WAFER.y + 50}
        kicker="07 · WAFER"
        title={stages.wafer === 'complete' ? 'ETCHED' : 'STAGE'}
        sub={snapshot.finalText
          ? `${snapshot.finalText.length.toLocaleString()} char resolution`
          : stages.wafer === 'active' ? 'patterning…' : 'awaiting synthesis'}
        tone={stages.wafer !== 'idle' ? 'normal' : 'dim'}/>

      <g transform="translate(1290 30)" className="lv-legend">
        <text x="0" y="0"  textAnchor="end" className="lv-legend-title">OPTICAL BENCH · TOP VIEW</text>
        <text x="0" y="12" textAnchor="end" className="lv-legend-sub">λ = 13.5 nm · vac. 10⁻⁶ Pa</text>
      </g>
    </g>
  );
}

function oracleSubLabel(o?: OracleProgress): string {
  if (!o) return 'idle';
  switch (o.status) {
    case 'requested':   return 'requested';
    case 'created':     return `notebook ${o.notebook_id?.slice(0, 6) || 'created'}`;
    case 'researching': return `researching · ${o.sources_imported ?? '—'} sources`;
    case 'harvested':   return `${o.sources_imported ?? '?'} src · ${(o.packet_chars ?? 0).toLocaleString()} chars`;
    case 'failed':      return 'failed';
    default:            return o.status;
  }
}

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + '…' : s;
}

function EmptyStateBadge() {
  return (
    <g className="lv-empty-badge">
      <rect x="500" y="450" width="400" height="100" rx="3"
            fill="rgba(2,6,23,0.65)" stroke="rgba(167,139,250,0.3)"
            strokeWidth="0.6" strokeDasharray="4 4"/>
      <text x="700" y="478" textAnchor="middle" className="lv-empty-kicker">── STANDBY ──</text>
      <text x="700" y="510" textAnchor="middle" className="lv-empty-title">AWAITING STRATEGIC SIGNAL</text>
      <text x="700" y="528" textAnchor="middle" className="lv-empty-sub">
        Bench cooled · plasma chamber evacuated · optics aligned
      </text>
    </g>
  );
}

// =============================================================================
// SVG defs + chrome
// =============================================================================

function Defs() {
  return (
    <defs>
      {/* Plasma */}
      <radialGradient id="lv-plasma-core" cx="50%" cy="50%" r="50%">
        <stop offset="0%"   stopColor="rgba(255,250,255,1)"/>
        <stop offset="22%"  stopColor="rgba(220,200,255,0.95)"/>
        <stop offset="55%"  stopColor="rgba(139,92,246,0.6)"/>
        <stop offset="100%" stopColor="rgba(76,29,149,0)"/>
      </radialGradient>
      <radialGradient id="lv-plasma-halo" cx="50%" cy="50%" r="50%">
        <stop offset="0%"   stopColor="rgba(167,139,250,0.45)"/>
        <stop offset="60%"  stopColor="rgba(139,92,246,0.12)"/>
        <stop offset="100%" stopColor="rgba(76,29,149,0)"/>
      </radialGradient>

      {/* Mirror metallic */}
      <linearGradient id="lv-mirror-face" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%"   stopColor="rgba(241,245,249,1)"/>
        <stop offset="15%"  stopColor="rgba(226,232,240,0.95)"/>
        <stop offset="50%"  stopColor="rgba(148,163,184,0.8)"/>
        <stop offset="85%"  stopColor="rgba(71,85,105,0.85)"/>
        <stop offset="100%" stopColor="rgba(30,41,59,0.95)"/>
      </linearGradient>

      {/* Magic-circle */}
      <radialGradient id="lv-mc-halo" cx="50%" cy="50%" r="50%">
        <stop offset="0%"   stopColor="rgba(167,139,250,0.45)"/>
        <stop offset="40%"  stopColor="rgba(139,92,246,0.20)"/>
        <stop offset="100%" stopColor="rgba(76,29,149,0)"/>
      </radialGradient>
      <radialGradient id="lv-mc-core" cx="50%" cy="50%" r="50%">
        <stop offset="0%"   stopColor="rgba(255,250,255,1)"/>
        <stop offset="22%"  stopColor="rgba(220,200,255,0.95)"/>
        <stop offset="55%"  stopColor="rgba(139,92,246,0.7)"/>
        <stop offset="100%" stopColor="rgba(76,29,149,0)"/>
      </radialGradient>
      <filter id="lv-mc-spark-glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="1.2"/>
      </filter>

      {/* Background */}
      <pattern id="lv-bench-grid" patternUnits="userSpaceOnUse" width="40" height="40">
        <path d="M40 0H0V40" stroke="rgba(167,139,250,0.04)" strokeWidth="0.5" fill="none"/>
      </pattern>
      <pattern id="lv-scanlines" patternUnits="userSpaceOnUse" width="2" height="3">
        <rect width="2" height="3" fill="rgba(0,0,0,0)"/>
        <line x1="0" y1="0" x2="2" y2="0" stroke="rgba(167,139,250,0.025)" strokeWidth="1"/>
      </pattern>
      <radialGradient id="lv-vignette" cx="50%" cy="50%" r="65%">
        <stop offset="60%"  stopColor="rgba(0,0,0,0)"/>
        <stop offset="100%" stopColor="rgba(0,0,0,0.55)"/>
      </radialGradient>
    </defs>
  );
}

function BackgroundChrome() {
  const corners: Array<['TL'|'TR'|'BL'|'BR', number, number]> = [
    ['TL', 24, 24], ['TR', 1376, 24], ['BL', 24, 976], ['BR', 1376, 976],
  ];
  return (
    <g className="lv-chrome">
      <rect x="0" y="0" width="1400" height="1000" fill="#020617"/>
      <rect x="0" y="0" width="1400" height="1000" fill="url(#lv-bench-grid)"/>
      <rect x="0" y="0" width="1400" height="1000" fill="url(#lv-vignette)"/>
      {corners.map(([id, x, y]) => {
        const dx = id.includes('R') ? -12 : 12;
        const dy = id.includes('B') ? -12 : 12;
        return (
          <g key={id} stroke="rgba(167,139,250,0.25)" strokeWidth="0.8" fill="none">
            <path d={`M${x},${y + dy} L${x},${y} L${x + dx},${y}`}/>
          </g>
        );
      })}
      <rect x="0" y="0" width="1400" height="1000" fill="url(#lv-scanlines)" pointerEvents="none"/>
    </g>
  );
}

function StructuralOutline({ layout, active }: { layout: Layout; active: boolean }) {
  const op = active ? 0.13 : 0.22;
  return (
    <g stroke={`rgba(148,163,184,${op})`} strokeWidth="0.6" fill="none">
      <line x1="40" y1="900" x2="1360" y2="900"/>
      <line x1="40" y1="908" x2="1360" y2="908" strokeOpacity="0.4"/>
      <line x1="40" y1="60"  x2="1360" y2="60"  strokeOpacity="0.5"/>
      <path d="M40 60 Q40 30 70 30 L1330 30 Q1360 30 1360 60 L1360 940 Q1360 970 1330 970 L70 970 Q40 970 40 940 Z"
            strokeOpacity={active ? 0.18 : 0.3} strokeDasharray="6 8"/>
      <line x1={layout.WAFER.x - 130} y1={layout.WAFER.y + 30} x2={layout.WAFER.x + 130} y2={layout.WAFER.y + 30}/>
      <line x1={layout.WAFER.x - 130} y1={layout.WAFER.y + 38} x2={layout.WAFER.x + 130} y2={layout.WAFER.y + 38} strokeOpacity="0.4"/>
    </g>
  );
}

// =============================================================================
// Styles
// =============================================================================

function LithographyStyles() {
  return (
    <style jsx global>{`
      .lv-root {
        position: relative;
        width: 100%;
        height: 100%;
        background: #020617;
        display: flex;
        flex-direction: column;
        font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
        color: #cbd5e1;
        overflow: hidden;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.08);
      }
      .lv-header {
        position: relative;
        z-index: 10;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 22px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.08);
        background: rgba(2, 6, 23, 0.6);
        backdrop-filter: blur(8px);
        /* Earlier padding-right:224px was a workaround for the floating
           PREDICTIONS chip at top-right; that chip is now consolidated into
           the SettingsTray popup at bottom-right, so the header gets its
           full width back. */
      }
      .lv-header-left  { display: flex; align-items: center; gap: 12px; }
      .lv-header-right { display: flex; align-items: center; gap: 18px; }
      .lv-header-title {
        font-size: 11px; font-weight: 700; letter-spacing: 0.18em;
        text-transform: uppercase; color: #f1f5f9;
      }
      .lv-header-title em { font-style: normal; color: rgba(196, 181, 253, 0.95); }
      .lv-header-divider { width: 1px; height: 14px; background: rgba(148, 163, 184, 0.18); }
      .lv-header-id {
        font-size: 9.5px; letter-spacing: 0.2em; font-weight: 500;
        color: rgba(148, 163, 184, 0.55);
      }
      .lv-header-stage { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
      .lv-header-stage-label {
        font-size: 8.5px; letter-spacing: 0.25em;
        color: rgba(148, 163, 184, 0.6); text-transform: uppercase;
      }
      .lv-header-stage-value {
        font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
        color: rgba(196, 181, 253, 0.95);
      }
      .lv-header-btn {
        appearance: none;
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 10px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 4px;
        color: rgba(148, 163, 184, 0.85);
        font: inherit; font-size: 10px; letter-spacing: 0.18em;
        text-transform: uppercase; cursor: pointer; transition: all .15s;
      }
      .lv-header-btn:hover {
        border-color: rgba(167, 139, 250, 0.45);
        color: rgba(196, 181, 253, 1);
      }

      .lv-body { flex: 1; position: relative; min-height: 0; }
      .lv-svg  { width: 100%; height: 100%; display: block; }

      .lv-cl-kicker { font-size: 8px;  letter-spacing: 0.22em; text-transform: uppercase; opacity: 0.65; }
      .lv-cl-title  { font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; }
      .lv-cl-sub    { font-size: 9px;  letter-spacing: 0.04em; }
      .lv-group-label {
        font-size: 10px; font-weight: 600; letter-spacing: 0.45em;
        fill: rgba(148, 163, 184, 0.3); text-transform: uppercase;
      }
      .lv-legend-title {
        font-size: 9px; font-weight: 600; letter-spacing: 0.22em;
        fill: rgba(196, 181, 253, 0.55); text-transform: uppercase;
      }
      .lv-legend-sub {
        font-size: 8.5px; letter-spacing: 0.06em;
        fill: rgba(148, 163, 184, 0.45);
      }
      .lv-empty-kicker {
        font-size: 10px; letter-spacing: 0.4em;
        fill: rgba(148, 163, 184, 0.55); text-transform: uppercase;
      }
      .lv-empty-title {
        font-size: 16px; font-weight: 700; letter-spacing: 0.3em;
        fill: rgba(196, 181, 253, 0.85); text-transform: uppercase;
      }
      .lv-empty-sub {
        font-size: 9px; letter-spacing: 0.18em;
        fill: rgba(148, 163, 184, 0.5); text-transform: uppercase;
      }

      /* Plasma */
      @keyframes lv-plasma-pulse {
        0%, 100% { transform: scale(1);    opacity: 0.92; }
        50%      { transform: scale(1.06); opacity: 1; }
      }
      .lv-plasma-active {
        transform-box: fill-box; transform-origin: center;
        animation: lv-plasma-pulse 1.6s ease-in-out infinite;
      }
      @keyframes lv-plasma-flare-spin {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
      }
      .lv-plasma-flare {
        transform-box: fill-box;
        animation: lv-plasma-flare-spin 12s linear infinite;
        opacity: 0.55;
      }
      @keyframes lv-pulse-fast {
        0%, 100% { opacity: 0.2; }
        50%      { opacity: 1; }
      }
      .lv-pulse-fast { animation: lv-pulse-fast .6s ease-in-out infinite; }

      .lv-beam { transition: opacity .25s; }

      /* Re-align optics reset chip */
      .lv-reset-text {
        font-size: 9px; letter-spacing: 0.16em;
        fill: rgba(196, 181, 253, 0.85);
      }
      .lv-reset:hover rect { stroke: rgba(196, 181, 253, 0.85); }
      .lv-reset:hover .lv-reset-text { fill: rgba(244, 233, 255, 1); }

      /* Misalignment warning */
      .lv-warn-text {
        font-size: 9px; letter-spacing: 0.16em; font-weight: 600;
        fill: rgba(253, 164, 175, 0.95);
      }

      /* Magic-circle slow rotation when lit */
      @keyframes lv-mc-rotor-spin {
        to { transform: rotate(360deg); }
      }
      .lv-magic-circle-rotor {
        transform-box: fill-box;
        transform-origin: center;
        animation: lv-mc-rotor-spin 32s linear infinite;
      }

      /* Inspector card */
      .lv-insp-kicker {
        font-size: 8.5px; letter-spacing: 0.18em; font-weight: 600;
        text-transform: uppercase;
      }
      .lv-insp-title {
        font-size: 12px; font-weight: 700; letter-spacing: 0.04em;
      }
      .lv-insp-meta {
        font-size: 9px; letter-spacing: 0.06em;
      }

      /* Dust motes */
      .lv-dust circle { will-change: cx, cy, opacity; }

      /* Hovered mirror highlight */
      .lv-mirror-drag { transition: filter .15s; }
      .lv-mirror-drag:active { cursor: grabbing !important; }
      .lv-mirror-drag:hover ellipse { filter: drop-shadow(0 0 8px rgba(167,139,250,0.5)); }
      .lv-mirror-nudged .lv-mirror-handle path,
      .lv-mirror-nudged .lv-mirror-handle line {
        stroke: rgba(196, 181, 253, 0.85);
        fill: rgba(196, 181, 253, 0.85);
      }

      /* Magic-circle */
      @keyframes lv-mc-runes-pulse {
        0%, 100% { opacity: 0.85; }
        50%      { opacity: 1; }
      }
      .lv-mc-runes-lit { animation: lv-mc-runes-pulse 3.4s ease-in-out infinite; }
      @keyframes lv-mc-core-pulse {
        0%, 100% { transform: scale(1);    opacity: 0.9; }
        50%      { transform: scale(1.08); opacity: 1; }
      }
      .lv-mc-core-lit,
      .lv-mc-core-active {
        transform-box: fill-box; transform-origin: center;
        animation: lv-mc-core-pulse 2.6s ease-in-out infinite;
      }
      .lv-mc-core-active { animation-duration: 1.5s; }
      @keyframes lv-mc-spark-flicker {
        0%, 49%  { opacity: 0.05; }
        50%, 100% { opacity: 1; }
      }
      .lv-mc-spark { animation: lv-mc-spark-flicker 0.32s steps(2) infinite; }
      .lv-mc-spark-0 { animation-delay: 0.00s; }
      .lv-mc-spark-1 { animation-delay: 0.05s; }
      .lv-mc-spark-2 { animation-delay: 0.10s; }
      .lv-mc-spark-3 { animation-delay: 0.15s; }
      .lv-mc-spark-4 { animation-delay: 0.20s; }
      .lv-mc-spark-5 { animation-delay: 0.25s; }

      .lv-pathway-pending {
        position: absolute; inset: 0;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center;
        color: rgba(148, 163, 184, 0.65);
      }
      .lv-pp-kicker { font-size: 10px; letter-spacing: 0.4em; opacity: 0.65; text-transform: uppercase; }
      .lv-pp-title  { font-size: 18px; letter-spacing: 0.3em; margin: 14px 0; color: rgba(196, 181, 253, 0.85); }
      .lv-pp-sub    { font-size: 11px; max-width: 360px; line-height: 1.6; opacity: 0.7; }
    `}</style>
  );
}
