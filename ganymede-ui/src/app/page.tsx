'use client';

import { useState, useEffect, useRef } from 'react';
import { RunnerPanel, type RunnerSnapshot } from '@/components/RunnerPanel';
import { DispatcherPanel } from '@/components/DispatcherPanel';
import { PhysicsCanvas } from '@/components/PhysicsCanvas';
import { LithographyView } from '@/components/LithographyView';
import { OrchestratorMindMap } from '@/components/OrchestratorMindMap';
import { DevOverlay } from '@/components/DevOverlay';
import { GSSState } from '@/types/ganymede';

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
  const prevSnapshotRef = useRef<RunnerSnapshot | null>(null);

  // Auto-switch to optics view the moment a run starts (or a run has
  // emitted blueprint/oracle data we want to see live).
  // Also drives the left-panel auto-switch using edge detection on the
  // previous snapshot — running false→true flips to mindmap, finalText
  // null→string flips back to runner.
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
    // Only auto-flip when the operator is in the Runner-driven path. Don't
    // pull them out of Dispatcher mid-run — Dispatcher renders its own
    // results inside its own component.
    if (runStarted && leftPanelMode === 'runner') {
      setLeftPanelMode('mindmap');
    }
    if (runEnded && leftPanelMode === 'mindmap') {
      // Covers normal completion (final text lands), errors, and the
      // synthesis-only case where strokes land without a separate finalText
      // step.  Whatever happened, processing is over and the runner panel
      // is where the user needs to be to read it.
      setLeftPanelMode('runner');
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
    <main className="flex h-screen w-full bg-[#030712] p-4 gap-4 overflow-hidden relative">
      {/* Dynamic Background Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#030712] to-[#030712] pointer-events-none" />

      {/* Left Panel: Dispatcher / Runner / Mind Map (40%).
          Dispatcher and Runner stay mounted under the hood (display:none
          when inactive) so neither's state is lost when the operator
          toggles. The mind-map is layered on top via absolute positioning
          when active. */}
      <div className="w-[40%] h-full flex-shrink-0 z-10 relative">
        <div
          style={{ display: leftPanelMode === 'dispatcher' ? 'block' : 'none' }}
          className="h-full"
        >
          <DispatcherPanel />
        </div>
        <div
          style={{ display: leftPanelMode === 'runner' ? 'block' : 'none' }}
          className="h-full"
        >
          <RunnerPanel
            onLoadExampleGss={handleLoadExampleGss}
            onRunnerStateChange={setRunnerSnapshot}
          />
        </div>
        {leftPanelMode === 'mindmap' && runnerSnapshot && (
          <div className="absolute inset-0">
            <OrchestratorMindMap
              snapshot={runnerSnapshot}
              onSwitchToRunner={() => setLeftPanelMode('runner')}
            />
          </div>
        )}

        {/* Floating toggle — always visible so the operator can find the
            advanced (Runner) mode from the dispatcher entry. Map button
            only appears once a Runner run has something to visualise. */}
        <div className="absolute bottom-6 left-6 z-40 flex gap-1 bg-slate-900/80 backdrop-blur-xl border border-slate-700/60 rounded-md p-1 font-mono">
          <button
            type="button"
            onClick={() => setLeftPanelMode('dispatcher')}
            className={[
              'px-3 py-1.5 rounded text-[10px] uppercase tracking-widest transition-colors',
              leftPanelMode === 'dispatcher'
                ? 'bg-indigo-600/30 text-indigo-200 border border-indigo-500/50'
                : 'text-slate-400 hover:text-slate-200',
            ].join(' ')}
          >
            Ask
          </button>
          <button
            type="button"
            onClick={() => setLeftPanelMode('runner')}
            className={[
              'px-3 py-1.5 rounded text-[10px] uppercase tracking-widest transition-colors',
              leftPanelMode === 'runner'
                ? 'bg-emerald-600/30 text-emerald-200 border border-emerald-500/50'
                : 'text-slate-400 hover:text-slate-200',
            ].join(' ')}
          >
            Runner
          </button>
          {mapAvailable && (
            <button
              type="button"
              onClick={() => setLeftPanelMode('mindmap')}
              className={[
                'px-3 py-1.5 rounded text-[10px] uppercase tracking-widest transition-colors',
                leftPanelMode === 'mindmap'
                  ? 'bg-violet-600/30 text-violet-200 border border-violet-500/50'
                  : 'text-slate-400 hover:text-slate-200',
              ].join(' ')}
            >
              Map
            </button>
          )}
        </div>
      </div>

      {/* Right Panel: choose between the 3D GSS canvas (museum/render mode)
          and the LithographyView (live run "inside the machine" mode). */}
      <div className="w-[60%] h-full flex-shrink-0 z-10 relative">
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
        {opticsAvailable && canvasAvailable && (
          <div className="absolute bottom-6 right-6 z-40 flex gap-1 bg-slate-900/80 backdrop-blur-xl border border-slate-700/60 rounded-md p-1 font-mono">
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

      {/* Cortex Clipboard — paste-back point for GSS JSON when Gemini gives
          you something the gravity well can render. */}
      <DevOverlay
        onApplyGSS={handleApplyGSS}
        isOpen={clipboardOpen}
        onOpenChange={setClipboardOpen}
      />
    </main>
  );
}
