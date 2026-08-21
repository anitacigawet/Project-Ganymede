'use client';

/**
 * DispatcherPanel — the single-text-box "Intent Router" UX.
 *
 * Replaces the pathway-selector + per-pathway form fields of [RunnerPanel]
 * with one large text box. On submit, calls POST /api/v2/dispatch which uses
 * a lightweight Gemini Flash call to classify the scenario into a pathway
 * (cleanroom / genie / offensive / mirror_audit) and extract the matching
 * parameters from the operator's prose. The operator reviews the classified
 * scenario, can edit any field, then clicks Run to fire the 3-stroke loop.
 *
 * Hides the framework jargon (DAP, SDS, ROEM, Lasso, Cleanroom/Genie
 * distinctions) so non-technical users don't have to learn the vocabulary
 * to use the system. The opinionated wrapper on top of the open v2 API.
 *
 * Architectural sibling to [RunnerPanel] — both live in the left panel of
 * page.tsx; the parent chooses one at a time (advanced vs. natural-language).
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getBackendBaseUrl } from '@/lib/backend';
import {
  GANYMEDE_DEMO_MODE,
  GANYMEDE_DEMO_PROMPT,
  GANYMEDE_DEMO_STROKES,
  classifyDemoIntent,
  waitForDemoBeat,
} from '@/data/demoMode';
import type { RunnerSnapshot } from './RunnerPanel';
import {
  Send,
  Loader2,
  Zap,
  BrainCircuit,
  ShieldQuestion,
  Crosshair,
  Sparkles,
  RefreshCw,
  Play,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Network,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types — mirror the backend contracts in app/contracts.py and v2_routes.py.
// ---------------------------------------------------------------------------

type Pathway = 'cleanroom' | 'genie' | 'offensive' | 'mirror_audit';

interface DispatchScenario {
  question?: string;
  current_state?: string;
  wished_for_state?: string;
  target?: string;
  objective_state?: string;
  prior_resolution?: string;
  dream_state?: boolean;
  extra_context?: string;
}

interface DispatchResponse {
  pathway: Pathway;
  confidence: number;
  scenario: DispatchScenario;
  /** True when the scenario references real-world entities (companies, people,
   *  markets, current events) the Engine's 9D-theory grounding corpus would
   *  not know about. Drives the routing decision: true → Universal Logic Loop
   *  (Triage → Oracle swarm → harvest → Synthesis, 15-30 min); false →
   *  Iterative Engine (3-stroke loop on framework-internal grounding, 5 min).
   *  mirror_audit always false. */
  needs_external_knowledge: boolean;
  rationale: string;
  clarifying_questions: string[];
}

interface StrokeResult {
  stroke_number: number;
  pathway: Pathway;
  raw_response: string;
  strategic_lasso?: string | null;
  incomprehensible_move?: string | null;
  final_resolution?: string | null;
  audit_findings?: string[] | null;
  /** Which audit instance produced this stroke, when pathway is mirror_audit.
   *  "mirror_auditor" or "bridge". Null for synthesis strokes. */
  audit_kind?: 'mirror_auditor' | 'bridge' | null;
  started_at: string;
  completed_at: string;
}

/** Per-Oracle progress emitted on the WebSocket during a Universal Logic Loop
 *  run. Mirrors the shape RunnerPanel uses so OrchestratorMindMap renders the
 *  same Oracle-spawn animation for both panels. */
interface OracleProgress {
  subject: string;
  notebook_id?: string;
  surgical_prompt?: string;
  status: 'requested' | 'created' | 'researching' | 'harvested' | 'failed';
  sources_imported?: number;
  packet_chars?: number;
  error?: string;
}

/** WebSocket event shape published by the backend on
 *  /api/v2/sessions/{id}/events/stream. The dispatcher subscribes during a
 *  run so the visualizer animates as the Universal Logic Loop progresses
 *  (Triage blueprint → Oracle requests → Oracle created → harvested →
 *  Synthesis), and so iterative runs reach the same render path. */
interface SessionEvent {
  type:
    | 'session_created'
    | 'stroke_started'
    | 'synthesis_complete'
    | 'stroke_completed'
    | 'session_complete'
    | 'session_cancelled'
    | 'error'
    | 'blueprint_ready'
    | 'oracle_request'
    | 'oracle_created'
    | 'oracle_harvested';
  stroke_number: number | null;
  payload: Record<string, unknown>;
  emitted_at: string;
}

const PATHWAY_META: Record<
  Pathway,
  {
    label: string;
    description: string;
    icon: React.ComponentType<{ className?: string; size?: number }>;
    accent: string;
  }
> = {
  cleanroom: {
    label: 'Predict',
    description: 'Falsifiable question about whether a specific outcome will happen.',
    icon: Zap,
    accent: 'text-emerald-300 border-emerald-700 bg-emerald-950/40',
  },
  genie: {
    label: 'Pathfind',
    description: 'Get from a current state to a wished-for state.',
    icon: BrainCircuit,
    accent: 'text-cyan-300 border-cyan-700 bg-cyan-950/40',
  },
  offensive: {
    label: 'Strategise vs. Target',
    description: 'Design a structural funnel toward an objective against a named target.',
    icon: Crosshair,
    accent: 'text-red-300 border-red-700 bg-red-950/40',
  },
  mirror_audit: {
    label: 'Audit Analysis',
    description: 'Stress-test an existing piece of strategic analysis for failure modes.',
    icon: ShieldQuestion,
    accent: 'text-purple-300 border-purple-700 bg-purple-950/40',
  },
};

// Pathway-specific field shape — labels for the review UI.
const FIELD_META: Record<
  Pathway,
  { key: keyof DispatchScenario; label: string; multiline: boolean }[]
> = {
  cleanroom: [{ key: 'question', label: 'Question', multiline: true }],
  genie: [
    { key: 'current_state', label: 'Current state', multiline: true },
    { key: 'wished_for_state', label: 'Wished-for state', multiline: true },
  ],
  offensive: [
    { key: 'target', label: 'Target', multiline: false },
    { key: 'objective_state', label: 'Objective state for the target', multiline: true },
  ],
  mirror_audit: [
    { key: 'prior_resolution', label: 'Analysis to audit', multiline: true },
  ],
};

interface DispatcherPanelProps {
  backendUrl?: string;
  /** Optional handoff: parent decides what to do with a confirmed dispatch.
   *  When provided, "Run with this" calls back to the parent instead of
   *  firing the iterate flow internally. Useful for routing the result into
   *  the existing RunnerPanel's state. */
  onConfirm?: (pathway: Pathway, scenario: DispatchScenario) => void;
  /** Mirrors the dispatcher's internal state up to the parent so the
   *  page's mind-map view can render live progress driven by the same
   *  events. Snapshot shape matches what RunnerPanel.onRunnerStateChange
   *  emits, so the parent can wire both into a single setRunnerSnapshot
   *  call. Called on every state mutation that affects what the
   *  visualizer would render (phase, dispatch result, strokes, final). */
  onSnapshotChange?: (snapshot: RunnerSnapshot) => void;
}

type PanelPhase = 'input' | 'dispatching' | 'review' | 'running' | 'done' | 'error';

export function DispatcherPanel({
  backendUrl = getBackendBaseUrl(),
  onConfirm,
  onSnapshotChange,
}: DispatcherPanelProps) {
  const [phase, setPhase] = useState<PanelPhase>('input');
  const [text, setText] = useState(
    GANYMEDE_DEMO_MODE ? GANYMEDE_DEMO_PROMPT : '',
  );
  const [dispatch, setDispatch] = useState<DispatchResponse | null>(null);
  const [editedScenario, setEditedScenario] = useState<DispatchScenario>({});
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [strokes, setStrokes] = useState<StrokeResult[]>([]);
  const [finalText, setFinalText] = useState<string | null>(null);
  const [iterative, setIterative] = useState(true);
  const [includeBridge, setIncludeBridge] = useState(true);
  // Universal Logic Loop wiring (structural fix 2026-06-10).
  // The dispatcher's friendly entry needs to route real-world Cleanroom/Genie/
  // Offensive questions to the harvest path (Triage → Oracle swarm → Synthesis)
  // because the Engine's grounding corpus is 9D-theory-only. Without harvest,
  // those questions hit the "no information" failure mode. The classifier
  // returns needs_external_knowledge; this panel honours it unless the operator
  // explicitly overrides via forceQuickPath.
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [blueprint, setBlueprint] = useState<string | null>(null);
  const [oracles, setOracles] = useState<Record<string, OracleProgress>>({});
  const [forceQuickPath, setForceQuickPath] = useState(false);
  /** WebSocket reference for the live event stream. The visualizer reads
   *  blueprint + oracles + strokes incrementally as events arrive, which is
   *  why this panel previously rendered a frozen Stage-1 placeholder: no
   *  subscription, no incremental data. Mirrors RunnerPanel's wsRef pattern. */
  const wsRef = useRef<WebSocket | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  /** Closes any in-flight WebSocket so we don't leak subscribers across
   *  runs or component-unmount. Called from reset() and the unmount cleanup
   *  effect below. */
  const closeWs = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      try {
        wsRef.current.close();
      } catch {
        /* ignore */
      }
    }
    wsRef.current = null;
  }, []);

  // Close the WS when the panel unmounts so we don't leak a subscriber.
  useEffect(() => closeWs, [closeWs]);

  // Auto-grow the input textarea while in the input phase.
  useEffect(() => {
    if (phase === 'input' && textareaRef.current) {
      const ta = textareaRef.current;
      ta.style.height = 'auto';
      ta.style.height = `${Math.min(ta.scrollHeight, 360)}px`;
    }
  }, [text, phase]);

  // Whether the resolved path for the current dispatch (after operator
  // override) is the Universal Logic Loop. Computed here so the snapshot
  // mirror, the review-phase UI, and handleConfirm all share one source of
  // truth.
  const useUniversalLoop =
    !!dispatch && dispatch.needs_external_knowledge && !forceQuickPath;

  // Memoized snapshot. Without useMemo, every render recreated the
  // object (and `Object.values(oracles)` returned a fresh array), forcing
  // the parent to re-render on every keystroke — which combined with the
  // parent's auto-flip useEffect floods the console with "Maximum update
  // depth exceeded" React warnings. Memoizing makes the snapshot identity
  // stable when its contents don't change.
  const snapshot = useMemo<RunnerSnapshot>(() => {
    const summary = text.trim() || Object.values(editedScenario)
      .filter((v): v is string => typeof v === 'string' && v.length > 0)
      .join(' · ');
    return {
      pathway: (dispatch?.pathway ?? 'cleanroom') as Pathway as RunnerSnapshot['pathway'],
      runMode: (useUniversalLoop ? 'full_loop' : 'synthesis') as RunnerSnapshot['runMode'],
      scenarioSummary: summary,
      blueprint,
      oracles: Object.values(oracles) as unknown as RunnerSnapshot['oracles'],
      strokes: strokes as unknown as RunnerSnapshot['strokes'],
      finalText,
      running: phase === 'running',
      hasError: phase === 'error',
      recentEvents: [],
    };
  }, [
    phase, text, editedScenario, dispatch, useUniversalLoop,
    blueprint, oracles, strokes, finalText,
  ]);

  // Mirror the memoized snapshot up to the parent's runnerSnapshot so the
  // mind-map view can render live progress while the run is in flight.
  // Shape matches what RunnerPanel emits — page.tsx wires both panels into
  // the same setRunnerSnapshot. The visualizer's bicameral mode detection
  // triggers on `oracles.length === 0 && running` (Engine ↔ PKI ↔ Anti);
  // when oracles.length > 0 it renders the Universal-Logic-Loop oracle
  // spawn graph instead.
  useEffect(() => {
    if (!onSnapshotChange) return;
    onSnapshotChange(snapshot);
  }, [onSnapshotChange, snapshot]);

  const reset = useCallback(() => {
    // Close any in-flight WS before zeroing state so we don't leak
    // subscribers across runs.
    closeWs();
    setPhase('input');
    setText('');
    setDispatch(null);
    setEditedScenario({});
    setErrorMessage(null);
    setStrokes([]);
    setFinalText(null);
    setSessionId(null);
    setBlueprint(null);
    setOracles({});
    setForceQuickPath(false);
  }, [closeWs]);

  /** Apply a WebSocket event to local state. Mirrors RunnerPanel.handleEvent
   *  so OrchestratorMindMap receives the same incremental Blueprint /
   *  Oracle / Stroke updates regardless of which panel drove the run.
   *
   *  Stroke contents come from the HTTP responses (`synthesis_complete`'s WS
   *  payload is just `{stroke_number, response_chars}` metadata). Blueprint
   *  and per-Oracle progress, on the other hand, ARE on the WS — they are the
   *  only way the UI learns about them in real time during a Universal Logic
   *  Loop run. */
  const handleEvent = useCallback((event: SessionEvent) => {
    const p = event.payload || {};
    if (event.type === 'blueprint_ready' && typeof p.blueprint === 'string') {
      setBlueprint(p.blueprint as string);
    }
    if (event.type === 'oracle_request' && typeof p.subject === 'string') {
      const subject = p.subject as string;
      setOracles((prev) => ({
        ...prev,
        [subject]: {
          ...(prev[subject] ?? { subject, status: 'requested' as const }),
          subject,
          surgical_prompt:
            (p.surgical_prompt as string) ?? prev[subject]?.surgical_prompt,
          status: 'requested',
        },
      }));
    }
    if (event.type === 'oracle_created' && typeof p.subject === 'string') {
      const subject = p.subject as string;
      setOracles((prev) => ({
        ...prev,
        [subject]: {
          ...(prev[subject] ?? { subject, status: 'created' as const }),
          subject,
          notebook_id:
            (p.notebook_id as string) ?? prev[subject]?.notebook_id,
          status: 'researching',
        },
      }));
    }
    if (event.type === 'oracle_harvested' && typeof p.subject === 'string') {
      const subject = p.subject as string;
      const status: OracleProgress['status'] =
        (p.status as string) === 'ok' ? 'harvested' : 'failed';
      setOracles((prev) => ({
        ...prev,
        [subject]: {
          ...(prev[subject] ?? { subject, status }),
          subject,
          status,
          sources_imported:
            typeof p.sources_imported === 'number'
              ? (p.sources_imported as number)
              : prev[subject]?.sources_imported,
          packet_chars:
            typeof p.packet_chars === 'number'
              ? (p.packet_chars as number)
              : prev[subject]?.packet_chars,
          error: typeof p.error === 'string' ? (p.error as string) : undefined,
        },
      }));
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Dispatch: classify the user's text into a pathway + scenario.
  // ---------------------------------------------------------------------------

  const submitDispatch = useCallback(async () => {
    const trimmed = text.trim();
    if (!trimmed) return;

    setPhase('dispatching');
    setErrorMessage(null);

    try {
      if (GANYMEDE_DEMO_MODE) {
        await waitForDemoBeat(650);
        const data = classifyDemoIntent(trimmed) as DispatchResponse;
        setDispatch(data);
        setEditedScenario({ ...data.scenario });
        setPhase('review');
        return;
      }

      const res = await fetch(`${backendUrl}/api/v2/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: trimmed }),
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(`HTTP ${res.status}: ${body || res.statusText}`);
      }
      const data: DispatchResponse = await res.json();
      setDispatch(data);
      setEditedScenario({ ...data.scenario });
      setPhase('review');
    } catch (exc) {
      setErrorMessage(exc instanceof Error ? exc.message : String(exc));
      setPhase('error');
    }
  }, [text, backendUrl]);

  // ---------------------------------------------------------------------------
  // Run: hand off to the parent OR drive /sessions + /iterate locally.
  // ---------------------------------------------------------------------------

  const handleConfirm = useCallback(async () => {
    if (!dispatch) return;
    const scenario = editedScenario;

    if (onConfirm) {
      onConfirm(dispatch.pathway, scenario);
      return;
    }

    // Local run. Branch on the dispatcher's harvest signal (post operator
    // override): real-world Cleanroom/Genie/Offensive routes to the Universal
    // Logic Loop so the Engine has external Truth Packets to reason against;
    // everything else routes to the existing Iterative Engine path. Both
    // paths open a WebSocket BEFORE kickoff so the visualizer sees Blueprint
    // / Oracle / Stroke events as they fire (the panel previously had no WS
    // subscription, which is why the visualizer rendered a frozen Stage-1
    // placeholder for the full run wall-time).
    setPhase('running');
    setStrokes([]);
    setFinalText(null);
    setSessionId(null);
    setBlueprint(null);
    setOracles({});

    try {
      if (GANYMEDE_DEMO_MODE) {
        const demoSessionId = 'showroom-ganymede-001';
        setSessionId(demoSessionId);

        const staged: StrokeResult[] = [];
        for (const stroke of GANYMEDE_DEMO_STROKES) {
          await waitForDemoBeat(stroke.stroke_number === 1 ? 1000 : 1250);
          staged.push(stroke as StrokeResult);
          setStrokes([...staged]);
        }

        setFinalText(GANYMEDE_DEMO_STROKES.at(-1)?.raw_response ?? null);
        await waitForDemoBeat(500);
        setPhase('done');
        return;
      }

      // 1. Create session. Iterative path supports the iterative + bridge
      // toggles; Universal Logic Loop ignores them (it manages its own
      // synthesis stroke at the end of the swarm).
      const createBody = useUniversalLoop
        ? {
            scenario: { dream_state: true, ...scenario },
            pathway: dispatch.pathway,
            iterative: false,
            max_strokes: 1,
          }
        : {
            scenario: { dream_state: true, ...scenario },
            pathway: dispatch.pathway,
            iterative,
            max_strokes: iterative ? 3 : 1,
          };
      const createRes = await fetch(`${backendUrl}/api/v2/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createBody),
      });
      if (!createRes.ok) {
        const body = await createRes.text();
        throw new Error(`Create session failed: HTTP ${createRes.status}: ${body}`);
      }
      const { session_id: newSessionId } = await createRes.json() as {
        session_id: string;
      };
      setSessionId(newSessionId);

      // 2. Open WebSocket BEFORE kickoff so we don't miss early Blueprint /
      // Oracle events. RunnerPanel uses the same wait-for-open pattern; on
      // disconnect the backend replays history, so even a slow open is safe
      // up to its 5s timeout.
      const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/api/v2/sessions/${newSessionId}/events/stream`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      await new Promise<void>((resolve, reject) => {
        const t = setTimeout(() => reject(new Error('WS open timeout')), 5000);
        ws.onopen = () => { clearTimeout(t); resolve(); };
        ws.onerror = () => { clearTimeout(t); reject(new Error('WS error')); };
      });

      if (useUniversalLoop) {
        // ----- Universal Logic Loop path -----
        // Backend runs run_universal_loop as a background task (Triage →
        // PKI Oracle swarm → Synthesis); we wait on session_complete via WS
        // before fetching /complete for the canonical strokes.
        const terminalReached = new Promise<void>((resolve, reject) => {
          ws.onmessage = (msg) => {
            try {
              const ev = JSON.parse(msg.data) as SessionEvent;
              handleEvent(ev);
              if (ev.type === 'session_complete') resolve();
              if (ev.type === 'session_cancelled') resolve();
              if (ev.type === 'error') reject(new Error(
                typeof ev.payload?.message === 'string'
                  ? (ev.payload.message as string)
                  : 'session errored',
              ));
            } catch {
              /* ignore malformed event */
            }
          };
        });

        const kickoffRes = await fetch(
          `${backendUrl}/api/v2/sessions/${newSessionId}/run-full-loop`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ max_subjects: 3, research_mode: 'deep' }),
          },
        );
        if (!kickoffRes.ok) {
          const body = await kickoffRes.text();
          throw new Error(`Full-loop kickoff failed: HTTP ${kickoffRes.status}: ${body}`);
        }

        await terminalReached;

        const completeRes = await fetch(
          `${backendUrl}/api/v2/sessions/${newSessionId}/complete`,
          { method: 'POST' },
        );
        if (completeRes.ok) {
          const completeData = await completeRes.json() as {
            final_resolution?: { final_text?: string; strokes?: StrokeResult[] };
          };
          setStrokes(completeData?.final_resolution?.strokes ?? []);
          setFinalText(completeData?.final_resolution?.final_text ?? null);
        }
      } else {
        // ----- Iterative Engine path (existing flow) -----
        // The /iterate (or /synthesize) endpoint is blocking; the WS still
        // fires Blueprint-less events the visualizer can react to (the
        // bicameral mode renders Engine ↔ PKI ↔ Anti without oracles).
        ws.onmessage = (msg) => {
          try {
            const ev = JSON.parse(msg.data) as SessionEvent;
            handleEvent(ev);
          } catch {
            /* ignore */
          }
        };

        const truthPacket = {
          subject: 'Scenario',
          content: text.trim(),
          source_label: 'Dispatcher (operator-supplied)',
        };
        const endpoint = iterative
          ? `/api/v2/sessions/${newSessionId}/iterate`
          : `/api/v2/sessions/${newSessionId}/synthesize`;
        const driveBody = iterative
          ? { truth_packets: [truthPacket], include_bridge: includeBridge }
          : { truth_packets: [truthPacket] };
        const driveRes = await fetch(`${backendUrl}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(driveBody),
        });
        if (!driveRes.ok) {
          const body = await driveRes.text();
          throw new Error(`Run failed: HTTP ${driveRes.status}: ${body}`);
        }
        const driveData = await driveRes.json() as
          | { stroke: StrokeResult; state: unknown }
          | { strokes: StrokeResult[]; state: unknown };
        const runStrokes: StrokeResult[] = 'strokes' in driveData
          ? (driveData.strokes ?? [])
          : 'stroke' in driveData && driveData.stroke
            ? [driveData.stroke]
            : [];
        setStrokes(runStrokes);

        const completeRes = await fetch(
          `${backendUrl}/api/v2/sessions/${newSessionId}/complete`,
          { method: 'POST' },
        );
        if (completeRes.ok) {
          const completeData = await completeRes.json() as {
            final_resolution?: { final_text?: string };
          };
          setFinalText(completeData?.final_resolution?.final_text ?? null);
        }
      }

      closeWs();
      setPhase('done');
    } catch (exc) {
      closeWs();
      setErrorMessage(exc instanceof Error ? exc.message : String(exc));
      setPhase('error');
    }
  }, [
    dispatch, editedScenario, text, iterative, includeBridge, onConfirm,
    backendUrl, useUniversalLoop, handleEvent, closeWs,
  ]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="w-full h-full flex flex-col gap-4 p-6 bg-slate-950 text-slate-100">
      <header className="flex items-center gap-2 border-b border-slate-800/60 pb-3">
        <Sparkles size={18} className="text-indigo-400" />
        <h2 className="text-lg font-semibold tracking-tight">
          Describe what you want to figure out
        </h2>
        <span className="ml-auto text-[10px] text-slate-500 uppercase tracking-wider">
          Intent Router
        </span>
      </header>

      {/* ---------------- INPUT PHASE ---------------- */}
      {phase === 'input' && (
        <div className="flex flex-col gap-3">
          {GANYMEDE_DEMO_MODE && (
            <div className="rounded-lg border border-cyan-800/60 bg-cyan-950/25 px-3 py-2.5 text-xs leading-relaxed text-cyan-100">
              This showroom build runs the real Ganymede interface against a
              fixed fictional scenario. Edit the prompt if you like; no model,
              account, or external service is contacted.
            </div>
          )}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={
              'In plain language. For example:\n' +
              '  "Will Anthropic still hold the #1 spot on LMArena at end of June 2026?"\n' +
              '  "I run a small consultancy with no marketing budget; how do I take share from an entrenched competitor?"\n' +
              '  "Audit this analysis: <paste the text>"\n' +
              '  "How do I outmaneuver an entrenched market leader before they recognize me as a threat?"'
            }
            rows={8}
            className="w-full resize-none rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 leading-relaxed"
          />
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex flex-col gap-1.5">
              <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={iterative}
                  disabled={GANYMEDE_DEMO_MODE}
                  onChange={(e) => setIterative(e.target.checked)}
                  className="accent-indigo-500"
                />
                Iterative run (Thesis → Audit → Synthesis)
              </label>
              <label
                className={`flex items-center gap-2 text-xs cursor-pointer ${
                  iterative ? 'text-slate-400' : 'text-slate-600'
                }`}
                title="Connection Bridge runs as an orthogonal-lens audit alongside the Mirror Auditor (Bicameral Convergence Level 1). Adds ~3 min of Bridge-notebook provisioning per run."
              >
                <input
                  type="checkbox"
                  checked={includeBridge}
                  onChange={(e) => setIncludeBridge(e.target.checked)}
                  disabled={GANYMEDE_DEMO_MODE || !iterative}
                  className="accent-indigo-500"
                />
                + Connection Bridge audit (Bicameral)
              </label>
              <p className="text-[10px] text-slate-500 italic mt-0.5">
                These apply to the quick concept-analysis path. Knowledge-harvest runs ignore them.
              </p>
            </div>
            <button
              onClick={submitDispatch}
              disabled={!text.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40 transition-colors"
            >
              <Send size={14} />
              Classify intent
            </button>
          </div>
          {GANYMEDE_DEMO_MODE && text !== GANYMEDE_DEMO_PROMPT && (
            <button
              type="button"
              onClick={() => setText(GANYMEDE_DEMO_PROMPT)}
              className="self-start text-[11px] text-cyan-300 hover:text-cyan-200 underline underline-offset-4"
            >
              Restore the sample scenario
            </button>
          )}
        </div>
      )}

      {/* ---------------- DISPATCHING PHASE ---------------- */}
      {phase === 'dispatching' && (
        <div className="flex flex-col items-center gap-3 py-12 text-slate-400">
          <Loader2 size={32} className="animate-spin text-indigo-400" />
          <p className="text-sm">Classifying intent…</p>
        </div>
      )}

      {/* ---------------- REVIEW PHASE ---------------- */}
      {phase === 'review' && dispatch && (
        <div className="flex flex-col gap-4">
          {/* Classification summary */}
          <div className={`rounded-lg border px-4 py-3 ${PATHWAY_META[dispatch.pathway].accent}`}>
            <div className="flex items-center gap-2">
              {(() => {
                const Icon = PATHWAY_META[dispatch.pathway].icon;
                return <Icon size={18} />;
              })()}
              <span className="text-sm font-semibold uppercase tracking-wide">
                {PATHWAY_META[dispatch.pathway].label}
              </span>
              <span className="ml-auto text-[10px] font-mono opacity-70">
                confidence {(dispatch.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <p className="mt-1 text-xs opacity-80">{dispatch.rationale}</p>
          </div>

          {/* Path-choice indicator. Surfaces which orchestration route this
              run will take so the operator isn't surprised by a 15-30 min
              harvest when they expected a 5 min concept analysis. Override
              available below when the harvest path was flagged but the
              operator has their own grounding context. */}
          <div
            className={`rounded-lg border px-4 py-3 ${
              useUniversalLoop
                ? 'border-emerald-700/60 bg-emerald-950/30 text-emerald-200'
                : 'border-slate-700 bg-slate-900/40 text-slate-200'
            }`}
          >
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide">
              {useUniversalLoop ? <Network size={14} /> : <Zap size={14} />}
              {useUniversalLoop
                ? 'Knowledge harvest path'
                : 'Quick concept-analysis path'}
            </div>
            <p className="mt-1.5 text-[11px] leading-relaxed opacity-90">
              {useUniversalLoop ? (
                <>
                  The scenario references real-world entities the
                  9D-theory grounding corpus doesn&apos;t know. Running
                  Triage → PKI Oracle swarm → Deep Research per subject →
                  Synthesis. Wall time ~15-30 min, ~3 NotebookLM notebooks
                  spawned.
                </>
              ) : dispatch.needs_external_knowledge ? (
                <>
                  Harvest was flagged but you&apos;ve chosen to override.
                  Running the 3-stroke Iterative Engine directly on
                  framework-internal grounding. The Engine may refuse with
                  &quot;no information&quot; if it has no Truth Packets to
                  reason against. Wall time ~5-10 min.
                </>
              ) : (
                <>
                  The scenario engages framework primitives abstractly,
                  no external harvest needed. Running the 3-stroke
                  Iterative Engine. Wall time ~5-10 min.
                </>
              )}
            </p>
            {dispatch.needs_external_knowledge && (
              <label className="mt-2.5 flex items-center gap-2 text-[11px] cursor-pointer opacity-90">
                <input
                  type="checkbox"
                  checked={forceQuickPath}
                  onChange={(e) => setForceQuickPath(e.target.checked)}
                  className="accent-indigo-500"
                />
                Override: skip harvest, run quick path anyway
              </label>
            )}
          </div>

          {/* Clarifying questions (if any) */}
          {dispatch.clarifying_questions.length > 0 && (
            <div className="rounded-lg border border-amber-700/60 bg-amber-950/30 px-4 py-3 text-amber-200">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide">
                <HelpCircle size={14} />
                Clarifying questions
              </div>
              <ul className="mt-2 space-y-1 text-xs leading-relaxed">
                {dispatch.clarifying_questions.map((q, i) => (
                  <li key={i} className="list-disc list-inside">
                    {q}
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-[10px] opacity-70">
                Edit the extracted fields below to answer, or click Refine to retype the scenario.
              </p>
            </div>
          )}

          {/* Extracted scenario fields (editable) */}
          <div className="flex flex-col gap-3">
            <p className="text-[10px] uppercase font-semibold tracking-wider text-slate-500">
              Extracted parameters (edit if needed)
            </p>
            {FIELD_META[dispatch.pathway].map(({ key, label, multiline }) => {
              const value = (editedScenario[key] as string | undefined) ?? '';
              return (
                <label key={String(key)} className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-slate-400">{label}</span>
                  {multiline ? (
                    <textarea
                      value={value}
                      onChange={(e) =>
                        setEditedScenario((s) => ({ ...s, [key]: e.target.value }))
                      }
                      rows={3}
                      className="rounded-md border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 leading-relaxed"
                    />
                  ) : (
                    <input
                      value={value}
                      onChange={(e) =>
                        setEditedScenario((s) => ({ ...s, [key]: e.target.value }))
                      }
                      className="rounded-md border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  )}
                </label>
              );
            })}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              onClick={reset}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors"
            >
              <RefreshCw size={12} />
              Refine
            </button>
            <button
              onClick={handleConfirm}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
            >
              <Play size={14} />
              Run with this
            </button>
          </div>
        </div>
      )}

      {/* ---------------- RUNNING PHASE ---------------- */}
      {phase === 'running' && (
        <div className="flex flex-col items-center gap-3 py-12 text-slate-400">
          <Loader2 size={32} className="animate-spin text-indigo-400" />
          <p className="text-sm">
            {useUniversalLoop ? (
              <>Universal Logic Loop running — harvest then synthesis.</>
            ) : (
              <>
                Engine running.{' '}
                {iterative
                  ? includeBridge
                    ? 'Bicameral 4-stroke loop'
                    : '3-stroke loop'
                  : 'Single-pass synthesis'}
                {' '}— several minutes.
              </>
            )}
          </p>
          <p className="text-[10px] text-slate-600 max-w-md text-center leading-relaxed">
            {useUniversalLoop ? (
              <>
                Triage stroke identifies subjects → PKI Oracles spawn and
                run NotebookLM Deep Research per subject → harvested Truth
                Packets feed the final synthesis. Watch the mind-map for
                live progress; this typically takes 15-30 minutes depending
                on how many subjects the triage picks.
              </>
            ) : (
              <>
                Each stroke includes an 8-second cooldown floor plus the Engine&apos;s response time.{' '}
                {iterative && includeBridge
                  ? 'Bicameral runs also provision a fresh Connection Bridge notebook (~3 min, 14 NotebookLM calls) before Stroke 2b fires.'
                  : iterative
                    ? 'The iterative loop fires three strokes back-to-back.'
                    : 'Single-pass mode fires once.'}
              </>
            )}
          </p>
          {sessionId && (
            <p className="text-[9px] font-mono text-slate-700">
              session {sessionId}
            </p>
          )}
        </div>
      )}

      {/* ---------------- DONE PHASE ---------------- */}
      {phase === 'done' && (
        <div className="flex flex-col gap-4 overflow-y-auto">
          <div className="flex items-center gap-2 text-emerald-300">
            <CheckCircle2 size={18} />
            <span className="text-sm font-semibold">Resolution ready</span>
            <button
              onClick={reset}
              className="ml-auto inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-1 text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors"
            >
              <RefreshCw size={12} />
              New scenario
            </button>
          </div>

          {strokes.map((s) => {
            // Per-stroke heading + accent. Audit strokes (mirror_audit
            // pathway) split into Mirror Auditor vs Connection Bridge by
            // audit_kind; synthesis strokes (Stroke 1 / Stroke 3) keep
            // the indigo accent and the pathway label.
            const isAudit = s.pathway === 'mirror_audit';
            const isBridge = isAudit && s.audit_kind === 'bridge';
            const accent = isBridge
              ? 'text-cyan-300 border-cyan-700/50'
              : isAudit
                ? 'text-amber-300 border-amber-700/50'
                : 'text-indigo-400 border-slate-800';
            const headerLabel = isBridge
              ? 'Connection Bridge'
              : isAudit
                ? 'Mirror Auditor'
                : s.pathway;
            return (
              <div
                key={s.stroke_number}
                className={`rounded-lg border bg-slate-900/50 px-4 py-3 ${accent.split(' ')[1]}`}
              >
                <div className="flex items-center gap-2 border-b border-slate-800/60 pb-2 mb-2">
                  <span
                    className={`text-[10px] font-mono uppercase tracking-wider ${
                      accent.split(' ')[0]
                    }`}
                  >
                    Stroke {s.stroke_number}
                  </span>
                  <span className="text-[10px] text-slate-500">{headerLabel}</span>
                </div>
                <pre className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap font-sans">
                  {s.raw_response}
                </pre>
              </div>
            );
          })}

          {strokes.length > 0 && !strokes[strokes.length - 1]?.raw_response?.trim() && (
            <div className="rounded-lg border border-amber-700/60 bg-amber-950/30 px-4 py-3 text-amber-200">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle size={14} />
                <span className="text-xs font-semibold uppercase tracking-wide">
                  Stroke {strokes[strokes.length - 1]?.stroke_number} returned no content
                </span>
              </div>
              <p className="text-[11px] leading-relaxed opacity-90">
                The NotebookLM call completed but produced an empty response.
                Most often this is a silent rejection (rate-limit or content
                filter); the backend retries up to 3 times before giving up.
                See <code className="font-mono">ganymede-backend/backend.log</code> for the
                attempt-by-attempt detail.
              </p>
            </div>
          )}

          {finalText && finalText !== strokes[strokes.length - 1]?.raw_response && (
            <div className="rounded-lg border border-emerald-700/60 bg-emerald-950/20 px-4 py-3">
              <div className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 mb-2">
                Final resolution
              </div>
              <pre className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
                {finalText}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* ---------------- ERROR PHASE ---------------- */}
      {phase === 'error' && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-red-700/60 bg-red-950/30 px-4 py-3 text-red-300">
            <AlertTriangle size={18} />
            <div className="flex-1 text-xs leading-relaxed">
              <div className="text-sm font-semibold mb-1">Something went wrong</div>
              <div className="font-mono text-[11px] text-red-400/80">
                {errorMessage}
              </div>
            </div>
          </div>
          <button
            onClick={reset}
            className="self-end inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors"
          >
            <RefreshCw size={12} />
            Start over
          </button>
        </div>
      )}
    </div>
  );
}
