'use client';

import { useState, useEffect, useRef } from 'react';
import { RunnerPanel, type RunnerSnapshot } from '@/components/RunnerPanel';
import { DispatcherPanel } from '@/components/DispatcherPanel';
import { PhysicsCanvas } from '@/components/PhysicsCanvas';
import { LithographyView } from '@/components/LithographyView';
import { OrchestratorMindMap } from '@/components/OrchestratorMindMap';
import { DevOverlay } from '@/components/DevOverlay';
import { SettingsTray } from '@/components/SettingsTray';
import { GSSState } from '@/types/ganymede';
import { GANYMEDE_DEMO_MODE } from '@/data/demoMode';

// Shared style for the bottom nav buttons. Roomier on touch screens (44px
// tall, meeting Apple/Google's touch-target guideline; iOS refuses to
// register some taps below 44px reliably) and back to the compact desktop
// chrome size at `lg`, where the pointer is a mouse. `touch-action:
// manipulation` disables iOS Safari's double-tap-to-zoom delay so the FIRST
// tap fires immediately instead of feeling dead. `select-none` prevents
// accidental text-selection on long-press. `min-h-[44px]` guarantees the
// hit area even if the font metrics shrink the padding.
const NAV_BTN =
  'shrink-0 px-3 py-3 min-h-[44px] lg:min-h-0 lg:py-1.5 rounded text-xs lg:text-[10px] uppercase tracking-widest transition-colors select-none [touch-action:manipulation]';

type RightPanelMode = 'canvas' | 'optics';
// 'dispatcher' is the natural-language entry mode (single text box -> LLM
// classifies into pathway + scenario, then runs locally). 'runner' is the
// power-user mode with explicit pathway selection + per-pathway form fields.
// 'mindmap' is the auto-flip view during a Runner-driven run.
type LeftPanelMode = 'dispatcher' | 'runner' | 'mindmap';

export default function Home() {
  const [scanTrigger, setScanTrigger] = useState(0);
  const [gssConfig, setGssConfig] = useState<GSSState | null>(null);
  const [clipboardOpen, setClipboardOpen] = useState(false);

  // Dev/debug: append `?mobile=1` to the URL to force the mobile stacked
  // layout at ANY viewport width. Lets a desktop browser reproduce exactly
  // what a phone user sees, so the mobile layout can actually be QA'd
  // without needing to physically shrink the window. No effect at SSR
  // (window guard); read once at mount and never re-checked.
  const [forceMobile, setForceMobile] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    setForceMobile(new URLSearchParams(window.location.search).has('mobile'));
  }, []);

  // Runner state mirror — lifted up so the right panel can render the
  // optics-box visualisation driven by the same events.
  const [runnerSnapshot, setRunnerSnapshot] = useState<RunnerSnapshot | null>(null);

  // Right-panel mode. Auto-flips to 'optics' when a run kicks off,
  // and the user can switch back to 'canvas' when there's a GSS to view.
  const [rightPanelMode, setRightPanelMode] = useState<RightPanelMode>('canvas');

  // Left-panel mode. Auto-flips to 'mindmap' the moment a Runner-driven run
  // starts (the dead-space-during-processing problem), then back to 'runner'
  // when the final synthesis text lands so the user can read strokes at the
  // bottom of the runner panel. The user can override both auto-switches via
  // the floating toggle in the corner; the in-header button on the mind-map
  // also flips back to runner.
  //
  // 'dispatcher' is the new default — the single-text-box natural-language
  // entry. Auto-flip logic does not move out of dispatcher (the dispatcher
  // has its own internal run state).
  const [leftPanelMode, setLeftPanelMode] = useState<LeftPanelMode>('dispatcher');

  // Which of the two panels is on screen when the viewport is too narrow to
  // show them side by side (below `lg`). The desktop layout ignores this
  // entirely — both panels are always visible there. Only ever changed by an
  // explicit tap on the bottom nav, never by the auto-flip effects below, so
  // a run starting can't yank the surface out from under the operator.
  const [mobileSurface, setMobileSurface] = useState<'left' | 'right'>('left');
  const prevSnapshotRef = useRef<RunnerSnapshot | null>(null);
  // Remember where we flipped from so we can flip back. Updated only on
  // the run-started transition, so the run-ended transition routes back
  // to the correct origin panel (dispatcher → mindmap → dispatcher,
  // runner → mindmap → runner).
  const returnPanelRef = useRef<'dispatcher' | 'runner'>('runner');

  // Auto-switch to optics view the moment a run starts (or a run has
  // emitted blueprint/oracle data we want to see live).
  // Also drives the left-panel auto-switch using edge detection on the
  // previous snapshot — running false→true flips to mindmap, finalText
  // null→string flips back to the origin panel.
  useEffect(() => {
    if (!runnerSnapshot) return;
    const prev = prevSnapshotRef.current;
    prevSnapshotRef.current = runnerSnapshot;

    const hasLiveRunData =
      runnerSnapshot.running ||
      runnerSnapshot.blueprint !== null ||
      runnerSnapshot.oracles.length > 0;
    if (hasLiveRunData) {
      setRightPanelMode('optics');
    }

    const runStarted = !prev?.running && runnerSnapshot.running;
    const runEnded = !!prev?.running && !runnerSnapshot.running;
    // Auto-flip to mindmap from both Runner AND Dispatcher modes so the
    // brain-metaphor visualizer (Engine ↔ PKI substrate ↔ Anti) lights
    // up the moment a run starts, regardless of which entry surface
    // launched it. The dispatcher's own internal results render inline
    // when we flip back at run-end.
    if (runStarted && (leftPanelMode === 'runner' || leftPanelMode === 'dispatcher')) {
      returnPanelRef.current = leftPanelMode;
      setLeftPanelMode('mindmap');
    }
    if (runEnded && leftPanelMode === 'mindmap') {
      // Covers normal completion (final text lands), errors, and the
      // synthesis-only case where strokes land without a separate
      // finalText step. Whatever happened, processing is over and the
      // origin panel is where the user needs to be to read the result.
      setLeftPanelMode(returnPanelRef.current);
    }
  }, [runnerSnapshot, leftPanelMode]);

  const handleApplyGSS = (config: GSSState) => {
    setGssConfig(config);
    setScanTrigger((prev) => prev + 1);
    // After applying a GSS, switch the right panel to canvas so the
    // user sees their freshly-rendered topology.
    setRightPanelMode('canvas');
  };

  // Example chip → preview the curated topology on PhysicsCanvas immediately.
  // No engine call burned; this is the "museum" mode living inside the Runner.
  const handleLoadExampleGss = (config: GSSState) => {
    setGssConfig(config);
    setScanTrigger((prev) => prev + 1);
    setRightPanelMode('canvas');
  };

  const canvasAvailable = gssConfig !== null;
  const opticsAvailable =
    runnerSnapshot !== null &&
    (runnerSnapshot.running ||
      runnerSnapshot.blueprint !== null ||
      runnerSnapshot.oracles.length > 0 ||
      runnerSnapshot.strokes.length > 0);

  // Mind-map is available the moment there's anything to draw on it — a
  // scenario string is enough to anchor the root node.  This is looser
  // than opticsAvailable on purpose so the toggle exists during the
  // pre-Run-click "Awaiting Run" state too.
  const mapAvailable =
    runnerSnapshot !== null &&
    (!!runnerSnapshot.scenarioSummary?.trim() ||
      runnerSnapshot.running ||
      runnerSnapshot.blueprint !== null ||
      runnerSnapshot.oracles.length > 0 ||
      runnerSnapshot.strokes.length > 0);

  return (
    // Side-by-side once there's room (lg+), stacked one-at-a-time below it.
    // `100dvh` rather than `h-screen`/100vh: on mobile browsers the address
    // bar grows and shrinks, and vh doesn't account for it — the bottom nav
    // would sit off-screen behind the chrome. dvh tracks the real viewport.
    <main
      className={[
        'flex h-[100dvh] w-full bg-[#030712] p-4 gap-4 overflow-hidden relative',
        forceMobile ? 'flex-col' : 'flex-col lg:flex-row',
      ].join(' ')}
    >
      {/* Dynamic Background Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#030712] to-[#030712] pointer-events-none" />

      {GANYMEDE_DEMO_MODE && (
        <div className="absolute left-1/2 top-2 z-[60] hidden -translate-x-1/2 rounded-full border border-cyan-700/60 bg-slate-950/90 px-3 py-1 text-[10px] font-mono tracking-wide text-cyan-200 backdrop-blur-xl sm:block">
          Showroom mode · fictional data · external services disconnected
        </div>
      )}

      {/* Predictions link, AuthPill, and the Cortex Clipboard trigger have all
          moved into the SettingsTray at the bottom-right corner. The tray
          consolidates the floating chrome into a single gear button + popup
          so the operator surface stays clean. See SettingsTray.tsx. */}

      {/* Left Panel: Dispatcher / Runner / Mind Map (40%).
          Dispatcher and Runner stay mounted under the hood (display:none
          when inactive) so neither's state is lost when the operator
          toggles. The mind-map is layered on top via absolute positioning
          when active. */}
      <div
        className={[
          mobileSurface === 'left' ? 'flex flex-col' : 'hidden',
          forceMobile ? 'w-full flex-1 min-h-0' : 'lg:block w-full lg:w-[40%] flex-1 min-h-0 lg:flex-none lg:h-full',
          'z-10 relative',
        ].join(' ')}
      >
        <div
          style={{ display: leftPanelMode === 'dispatcher' ? 'block' : 'none' }}
          className="h-full"
        >
          <DispatcherPanel onSnapshotChange={setRunnerSnapshot} />
        </div>
        {!GANYMEDE_DEMO_MODE && (
          <div
            style={{ display: leftPanelMode === 'runner' ? 'block' : 'none' }}
            className="h-full"
          >
            <RunnerPanel
              onLoadExampleGss={handleLoadExampleGss}
              onRunnerStateChange={setRunnerSnapshot}
            />
          </div>
        )}
        {leftPanelMode === 'mindmap' && runnerSnapshot && (
          <div className="absolute inset-0">
            <OrchestratorMindMap
              snapshot={runnerSnapshot}
              onSwitchToRunner={() => setLeftPanelMode('runner')}
            />
          </div>
        )}

      </div>

      {/* Right Panel: choose between the 3D GSS canvas (museum/render mode)
          and the LithographyView (live run "inside the machine" mode). */}
      <div
        className={[
          mobileSurface === 'right' ? 'flex flex-col' : 'hidden',
          forceMobile ? 'w-full flex-1 min-h-0' : 'lg:block w-full lg:w-[60%] flex-1 min-h-0 lg:flex-none lg:h-full',
          'z-10 relative',
        ].join(' ')}
      >
        {rightPanelMode === 'optics' && runnerSnapshot ? (
          <LithographyView
            snapshot={runnerSnapshot}
            canvasAvailable={canvasAvailable}
            onSwitchToCanvas={() => setRightPanelMode('canvas')}
          />
        ) : (
          <PhysicsCanvas
            scanTrigger={scanTrigger}
            gssConfig={gssConfig}
          />
        )}

        {/* Floating toggle in the bottom-right of the right panel — only
            shows when both views have content to display. Lets the user
            flip between the optics-box and the GSS render without losing
            either piece of state. */}
        {opticsAvailable && canvasAvailable && !forceMobile && (
          <div className="hidden lg:flex absolute bottom-6 right-6 z-40 gap-1 bg-slate-900/80 backdrop-blur-xl border border-slate-700/60 rounded-md p-1 font-mono">
            <button
              type="button"
              onClick={() => setRightPanelMode('optics')}
              className={[
                'px-3 py-1.5 rounded text-[10px] uppercase tracking-widest transition-colors',
                rightPanelMode === 'optics'
                  ? 'bg-violet-600/30 text-violet-200 border border-violet-500/50'
                  : 'text-slate-400 hover:text-slate-200',
              ].join(' ')}
            >
              Optics
            </button>
            <button
              type="button"
              onClick={() => setRightPanelMode('canvas')}
              className={[
                'px-3 py-1.5 rounded text-[10px] uppercase tracking-widest transition-colors',
                rightPanelMode === 'canvas'
                  ? 'bg-emerald-600/30 text-emerald-200 border border-emerald-500/50'
                  : 'text-slate-400 hover:text-slate-200',
              ].join(' ')}
            >
              Canvas
            </button>
          </div>
        )}
      </div>

      {/* Panel toggle (Ask / Runner / Map) — always visible so the operator
          can reach the advanced Runner mode from the dispatcher entry.
          Map appears once a run has something to visualise.

          Deliberately a TOP-LEVEL sibling of both panels rather than a child
          of the left one. As a child it was clipped and un-clickable on
          narrow screens: it sat at a fixed `left-32` offset sized for a
          desktop-width left panel, so on a ~375-770px viewport the Runner /
          Map buttons overflowed past the 40%-wide panel's edge — and since
          the right panel is a later sibling with the same `z-10`, it painted
          over them and swallowed the clicks (a child's z-index can't escape
          its parent's stacking context). Rendering it last, anchored to the
          page, keeps every button hit-testable at any width. */}
      {/* Bottom nav on mobile / floating chrome on desktop. Horizontal-scroll
          on overflow instead of wrapping (a wrapped second row would push the
          nav into the panel area, and iOS can drop taps on wrapped flex items
          that end up in ambiguous rows). No right-padding dead zone: the
          Settings gear moves to the top-right on mobile so nothing competes
          for the bottom-right tap area. */}
      <div
        className={[
          'z-50 shrink-0 flex items-center gap-1 bg-slate-900/80 backdrop-blur-xl border border-slate-700/60 rounded-md p-1 font-mono overflow-x-auto',
          forceMobile ? 'relative' : 'relative lg:absolute lg:bottom-6 lg:left-6',
        ].join(' ')}
      >
        <button
          type="button"
          onClick={() => {
            setLeftPanelMode('dispatcher');
            setMobileSurface('left');
          }}
          className={[
            NAV_BTN,
            leftPanelMode === 'dispatcher' && mobileSurface === 'left'
              ? 'bg-indigo-600/30 text-indigo-200 border border-indigo-500/50'
              : 'text-slate-400 hover:text-slate-200',
          ].join(' ')}
        >
          Ask
        </button>
        {!GANYMEDE_DEMO_MODE && (
          <button
            type="button"
            onClick={() => {
              setLeftPanelMode('runner');
              setMobileSurface('left');
            }}
            className={[
              NAV_BTN,
              leftPanelMode === 'runner' && mobileSurface === 'left'
                ? 'bg-emerald-600/30 text-emerald-200 border border-emerald-500/50'
                : 'text-slate-400 hover:text-slate-200',
            ].join(' ')}
          >
            Runner
          </button>
        )}
        {mapAvailable && (
          <button
            type="button"
            onClick={() => {
              setLeftPanelMode('mindmap');
              setMobileSurface('left');
            }}
            className={[
              NAV_BTN,
              leftPanelMode === 'mindmap' && mobileSurface === 'left'
                ? 'bg-violet-600/30 text-violet-200 border border-violet-500/50'
                : 'text-slate-400 hover:text-slate-200',
            ].join(' ')}
          >
            Map
          </button>
        )}

        {/* Right-panel views. Only on narrow screens — on desktop both panels
            are on screen at once and the right panel carries its own
            Optics/Canvas toggle, so duplicating them here would be noise. */}
        {opticsAvailable && (
          <button
            type="button"
            onClick={() => {
              setRightPanelMode('optics');
              setMobileSurface('right');
            }}
            className={[
              NAV_BTN,
              forceMobile ? '' : 'lg:hidden',
              rightPanelMode === 'optics' && mobileSurface === 'right'
                ? 'bg-violet-600/30 text-violet-200 border border-violet-500/50'
                : 'text-slate-400 hover:text-slate-200',
            ].join(' ')}
          >
            Optics
          </button>
        )}
        <button
          type="button"
          onClick={() => {
            setRightPanelMode('canvas');
            setMobileSurface('right');
          }}
          className={[
            NAV_BTN,
            forceMobile ? '' : 'lg:hidden',
            rightPanelMode === 'canvas' && mobileSurface === 'right'
              ? 'bg-emerald-600/30 text-emerald-200 border border-emerald-500/50'
              : 'text-slate-400 hover:text-slate-200',
          ].join(' ')}
        >
          Canvas
        </button>
      </div>

      {/* Cortex Clipboard — paste-back point for GSS JSON when Gemini gives
          you something the gravity well can render. The legacy floating
          Terminal button at bottom-right is suppressed; the SettingsTray now
          owns that corner and triggers `setClipboardOpen(true)` from its
          Console slot. */}
      <DevOverlay
        onApplyGSS={handleApplyGSS}
        isOpen={clipboardOpen}
        onOpenChange={setClipboardOpen}
        hideFloatingTrigger
      />

      {/* Settings tray — bottom-right gear button + popup hosting the
          Console, Predictions, and Auth slots. Consolidates the floating
          chrome elements James flagged as "clumped" and "overlapping". */}
      <SettingsTray onConsoleClick={() => setClipboardOpen(true)} forceMobile={forceMobile} />
    </main>
  );
}
