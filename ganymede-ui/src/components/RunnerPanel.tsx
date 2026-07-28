'use client';

/**
 * RunnerPanel — the integrated end-to-end demo flow.
 *
 *   Scenario input → v2 session API → Engine resolution → "Send to Cortex
 *   Clipboard" → DevOverlay opens with a Gemini-Pro-ready prompt block →
 *   you paste into Gemini Pro by hand → paste GSS JSON back → 3D renders.
 *
 * Replaces the static `GalleryPanel` in the left 40% of the layout. Drives
 * the v2 API (`POST /api/v2/sessions` → `/synthesize` or `/iterate` →
 * `/complete`) and subscribes to the WebSocket event stream so strokes
 * appear as they land instead of after a single long-blocking call.
 *
 * Pathway support: Cleanroom (question), Genie (current/wished pair),
 * Offensive (target/objective), Mirror Audit (prior_resolution).
 *
 * Gemini Pro automation is intentionally NOT done here — Hard Guardrail #4
 * historically locked it down after a browser-automation incident burned
 * Pro queries. The "Send to Cortex Clipboard" handoff preserves that as a
 * deliberate human paste step.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Play, Loader2, Zap, BrainCircuit, ShieldQuestion, Crosshair, Terminal, AlertTriangle, Sparkles, Copy, Check } from 'lucide-react';
import { getBackendBaseUrl } from '@/lib/backend';

import { EXAMPLES_BY_PATHWAY, type RunnerExample } from '@/data/examples';
import type { GSSState } from '@/types/ganymede';
import {
  BicameralProgressIndicator,
  type BicameralProgressState,
  type BicameralSide,
  type ConvergenceCriterion,
  IDLE_BICAMERAL_STATE,
} from './BicameralProgressIndicator';
import { StrokeTranslator } from './StrokeTranslator';

type Pathway = 'cleanroom' | 'genie' | 'offensive' | 'mirror_audit';
type RunMode = 'triage' | 'full_loop' | 'synthesis';
type ResearchMode = 'fast' | 'deep';

export interface OracleProgress {
  subject: string;
  notebook_id?: string;
  surgical_prompt?: string;
  status: 'requested' | 'created' | 'researching' | 'harvested' | 'failed';
  sources_imported?: number;
  packet_chars?: number;
  error?: string;
}

export interface RunnerSnapshot {
  pathway: Pathway;
  runMode: RunMode;
  /** Plain-text rendering of the user's pathway-shaped inputs. Drives the
   *  scenario node in the live mind-map view. */
  scenarioSummary: string;
  blueprint: string | null;
  oracles: OracleProgress[];
  strokes: StrokeResult[];
  finalText: string | null;
  running: boolean;
  hasError: boolean;
  /** Last few events for the timeline. Not the full history. */
  recentEvents: SessionEvent[];
}

interface RunnerPanelProps {
  /** Backend HTTP base. Defaults to `getBackendBaseUrl()` — the explicit
   *  NEXT_PUBLIC_GANYMEDE_BASE_URL override if set, else derived from the
   *  page's own host so localhost and LAN both work unconfigured. */
  backendUrl?: string;
  /** Called when the user clicks an example chip — loads the museum-style
   *  GSS preset into PhysicsCanvas immediately, before the user runs anything. */
  onLoadExampleGss?: (gss: GSSState) => void;
  /** Mirrors the runner's internal state up to the parent, so the right
   *  panel can render a live optics-box visualisation driven by the same
   *  events. Called whenever any tracked piece of state changes. */
  onRunnerStateChange?: (snapshot: RunnerSnapshot) => void;
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
  /** P1-03b: cleaned text when a trailing chatbot-CTA was stripped from
   *  raw_response. UI prefers cleaned_response when present. */
  cleaned_response?: string | null;
  /** P1-03b: the stripped CTA text, preserved for forensic visibility. */
  stripped_cta?: string | null;
  started_at: string;
  completed_at: string;
}

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
    | 'oracle_harvested'
    // Bicameral Convergence Level 2 events (E1-02). Emitted by
    // backend.run_bicameral_loop around each closed-loop iteration so
    // the frontend can render live progress + offer cancel.
    | 'bicameral_iteration_start'
    | 'bicameral_iteration_end'
    | 'bicameral_converged'
    | 'bicameral_hard_cap_reached';
  stroke_number: number | null;
  payload: Record<string, unknown>;
  emitted_at: string;
}

const PATHWAY_META: Record<
  Pathway,
  { label: string; description: string; icon: React.ComponentType<{ className?: string }> }
> = {
  cleanroom: {
    label: 'Cleanroom (Predict)',
    description: 'Engine returns probability + Strategic Lasso.',
    icon: Zap,
  },
  genie: {
    label: 'Genie (Pathfind)',
    description: 'Engine designs the Inadvertent Path between the two states.',
    icon: BrainCircuit,
  },
  offensive: {
    label: 'Offensive (Architect)',
    description: 'Engine designs a Strategic Funnel toward the objective.',
    icon: Crosshair,
  },
  mirror_audit: {
    label: 'Mirror Audit',
    description: 'Hand the Mirror Auditor an existing Stroke-1 analysis; receive fault enumeration.',
    icon: ShieldQuestion,
  },
};

function buildScenarioPayload(pathway: Pathway, inputs: Record<string, string>) {
  const scenario: Record<string, unknown> = { dream_state: true };
  switch (pathway) {
    case 'cleanroom':
      scenario.question = inputs.question || '';
      break;
    case 'genie':
      scenario.current_state = inputs.current_state || '';
      scenario.wished_for_state = inputs.wished_for_state || '';
      break;
    case 'offensive':
      scenario.target = inputs.target || '';
      scenario.objective_state = inputs.objective_state || '';
      break;
    case 'mirror_audit':
      scenario.prior_resolution = inputs.prior_resolution || '';
      scenario.dream_state = false; // auditor doesn't want dream framing
      break;
  }
  if (inputs.extra_context && inputs.extra_context.trim().length > 0) {
    scenario.extra_context = inputs.extra_context;
  }
  return scenario;
}

function summarizeForPacket(pathway: Pathway, inputs: Record<string, string>): string {
  switch (pathway) {
    case 'cleanroom':
      return inputs.question || '';
    case 'genie':
      return `CURRENT STATE:\n${inputs.current_state}\n\nWISHED-FOR STATE:\n${inputs.wished_for_state}`;
    case 'offensive':
      return `TARGET:\n${inputs.target}\n\nOBJECTIVE STATE:\n${inputs.objective_state}`;
    case 'mirror_audit':
      return inputs.prior_resolution || '';
  }
}

/**
 * Compose the text we copy to the clipboard after a run.
 *
 * Just the Engine's raw output — no Gemini scaffolding, no schema, no
 * instructions. User pastes this into Gemini Pro (or any model) with their
 * own freeform prompt ("visualize this") and we iterate based on what
 * comes back. The original Hualapai render came out of this exact flow.
 *
 * For iterative runs we concatenate all strokes so the user sees the full
 * Thesis → Audit → Synthesis arc; for single-pass runs it's just the one
 * raw_response.
 */
function composeEngineOutputForCopy(strokes: StrokeResult[]): string {
  if (strokes.length === 0) return '';
  if (strokes.length === 1) {
    return strokes[0].raw_response;
  }
  return strokes
    .map((s) => `=== STROKE ${s.stroke_number} (${s.pathway}) ===\n${s.raw_response}`)
    .join('\n\n');
}

export function RunnerPanel({
  backendUrl = getBackendBaseUrl(),
  onLoadExampleGss,
  onRunnerStateChange,
}: RunnerPanelProps) {
  const [pathway, setPathway] = useState<Pathway>('cleanroom');
  const [iterative, setIterative] = useState(false);
  // Bicameral Convergence Level 1 — when iterative is on and Mirror Audit is
  // not the pathway, the iterate loop also runs Connection Bridge as an
  // orthogonal-lens audit (Stroke 2b). Default ON; toggle off for the
  // historic 3-stroke shape. Adds ~3 min of Bridge-notebook provisioning.
  const [includeBridge, setIncludeBridge] = useState(true);
  const [runMode, setRunMode] = useState<RunMode>('full_loop');
  const [maxSubjects, setMaxSubjects] = useState<number>(3);
  // Research mode for the Phase-2 Oracle harvest. 'deep' is the historic
  // Powell-class flow (multi-minute web-grounded Deep Research, ~5-20 min
  // per oracle). 'fast' is the single-pass variant — much smaller source
  // pool but completes in seconds-to-minutes. Useful for iterating on the
  // scenario text without burning 20-30 min per test.
  const [researchMode, setResearchMode] = useState<ResearchMode>('deep');
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [strokes, setStrokes] = useState<StrokeResult[]>([]);
  const [finalText, setFinalText] = useState<string | null>(null);
  const [loadedExampleId, setLoadedExampleId] = useState<string | null>(null);
  const [blueprint, setBlueprint] = useState<string | null>(null);
  const [oracles, setOracles] = useState<Record<string, OracleProgress>>({});
  // Bicameral Convergence Level 2 live-progress state (E1-05). Updated by
  // handleEvent as BICAMERAL_ITERATION_START/END/CONVERGED/HARD_CAP_REACHED
  // events arrive on the WebSocket. Consumed by BicameralProgressIndicator
  // for the iteration counter, side indicator, and terminal-state messaging.
  // When the operator-driven loop is a Level 1 /iterate (no bicameral
  // events), this state stays at IDLE_BICAMERAL_STATE and the indicator
  // renders nothing — it's gated by sessionId + state shape.
  const [bicameralState, setBicameralState] = useState<BicameralProgressState>(
    IDLE_BICAMERAL_STATE,
  );
  // Example chips require two clicks to fire — guards the right panel
  // against accidental topology loads. `primedExampleId` is the chip
  // currently waiting for its confirming click; auto-clears after 3s.
  const [primedExampleId, setPrimedExampleId] = useState<string | null>(null);
  const primeTimerRef = useRef<number | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  const setInput = (key: string, val: string) =>
    setInputs((s) => ({ ...s, [key]: val }));

  const handleLoadExample = (example: RunnerExample) => {
    setPathway(example.pathway);
    setInputs(example.inputs);
    setLoadedExampleId(example.id);
    // Wipe previous run state (and close any in-flight WS) so the user
    // starts fresh with the example.
    reset();
    if (onLoadExampleGss) {
      onLoadExampleGss(example.gss);
    }
  };

  // Two-step chip activation. First click primes the chip and shows a
  // "click again to load" hint; second click within 3s fires the load
  // and resets the prime. Guards against accidental loads while the
  // right-panel may be doing something else.
  const handleChipClick = (example: RunnerExample) => {
    if (primeTimerRef.current !== null) {
      window.clearTimeout(primeTimerRef.current);
      primeTimerRef.current = null;
    }
    if (primedExampleId === example.id) {
      setPrimedExampleId(null);
      handleLoadExample(example);
      return;
    }
    setPrimedExampleId(example.id);
    primeTimerRef.current = window.setTimeout(() => {
      setPrimedExampleId(null);
      primeTimerRef.current = null;
    }, 3000);
  };

  useEffect(() => {
    return () => {
      if (primeTimerRef.current !== null) {
        window.clearTimeout(primeTimerRef.current);
      }
    };
  }, []);

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

  const reset = useCallback(() => {
    // Close any in-flight WS so we don't leak subscribers across runs.
    closeWs();
    setError(null);
    setSessionId(null);
    setEvents([]);
    setStrokes([]);
    setFinalText(null);
    setBlueprint(null);
    setOracles({});
    setBicameralState(IDLE_BICAMERAL_STATE);
  }, [closeWs]);

  // Cancel in-flight session. Fires POST /api/v2/sessions/{id}/cancel;
  // backend transitions the session to "cancelled" and emits
  // SESSION_CANCELLED on the WebSocket. The WS event handler clears
  // bicameralState.running and closes the WS. Idempotent on the backend
  // — safe to fire even if the loop just finished on its own.
  const handleCancel = useCallback(async () => {
    if (!sessionId) return;
    const backendUrl = getBackendBaseUrl();
    try {
      const res = await fetch(
        `${backendUrl}/api/v2/sessions/${sessionId}/cancel`,
        { method: 'POST' },
      );
      if (!res.ok) {
        // 404 means the session evaporated (process restart?). Surface
        // as a soft error; the user can reset and re-run.
        const body = await res.text();
        setError(`Cancel failed: ${res.status} ${body}`);
      }
      // On success, the SESSION_CANCELLED event flows through the WS
      // and the handler clears running state. No further work needed
      // here — explicit return.
    } catch (err) {
      setError(
        `Cancel request failed: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  }, [sessionId]);

  useEffect(() => closeWs, [closeWs]);

  // Mirror Audit is a single-stroke pathway. If the user had iterative on
  // from a prior pathway, force it off so we don't submit an invalid
  // (iterative=true, pathway=mirror_audit) request.
  useEffect(() => {
    if (pathway === 'mirror_audit' && iterative) {
      setIterative(false);
    }
  }, [pathway, iterative]);

  const handleEvent = useCallback((event: SessionEvent) => {
    setEvents((prev) => [...prev, event]);

    // Stroke contents come from the HTTP responses (synthesis_complete's
    // WS payload is just {stroke_number, response_chars} metadata).
    //
    // Blueprint and per-Oracle progress, on the other hand, ARE on the WS:
    // the only way the UI learns about them in real time.
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
          surgical_prompt: (p.surgical_prompt as string) ?? prev[subject]?.surgical_prompt,
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
          notebook_id: (p.notebook_id as string) ?? prev[subject]?.notebook_id,
          status: 'researching', // create → starts Deep Research immediately
        },
      }));
    }
    if (event.type === 'oracle_harvested' && typeof p.subject === 'string') {
      const subject = p.subject as string;
      const status = (p.status as string) === 'ok' ? 'harvested' : 'failed';
      setOracles((prev) => ({
        ...prev,
        [subject]: {
          ...(prev[subject] ?? { subject, status: status as OracleProgress['status'] }),
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

    // Bicameral Convergence Level 2 — iteration boundaries + terminal
    // outcomes. Backend's run_bicameral_loop emits these around each
    // Engine ↔ Bridge iteration so the frontend can render live
    // progress + a cancel button.
    if (event.type === 'bicameral_iteration_start') {
      const iteration = typeof p.iteration === 'number' ? p.iteration : null;
      const maxIterations =
        typeof p.max_iterations === 'number' ? p.max_iterations : null;
      setBicameralState((prev) => ({
        ...prev,
        running: true,
        currentIteration: iteration,
        maxIterations,
        // First half of the iteration is always Engine; END will flip to
        // bridge before the BICAMERAL_ITERATION_END fires.
        currentSide: 'engine' as BicameralSide,
        // Clear stale bridge-count from the prior iteration once a new
        // one starts.
        newBridgesSurfaced: null,
        convergenceCriterion: null,
        hardCapReached: false,
      }));
    }
    if (event.type === 'bicameral_iteration_end') {
      const newBridges =
        typeof p.new_bridges_surfaced === 'number'
          ? p.new_bridges_surfaced
          : null;
      setBicameralState((prev) => ({
        ...prev,
        // Iteration finished — go idle until the next ITERATION_START
        // (which flips back to engine) or a terminal event fires.
        currentSide: 'idle' as BicameralSide,
        newBridgesSurfaced: newBridges,
      }));
    }
    // synthesis_complete fires after the Engine finishes a stroke. Inside
    // a bicameral iteration (currentSide=='engine'), the next phase is the
    // Bridge audit — flip the side indicator. The backend doesn't emit an
    // explicit "bridge starting" event, so this is the cleanest signal we
    // have. Outside a bicameral iteration (Level 1 /iterate), this is a
    // no-op because currentSide stays at 'idle' and the condition fails.
    if (event.type === 'synthesis_complete') {
      setBicameralState((prev) =>
        prev.running && prev.currentSide === 'engine'
          ? { ...prev, currentSide: 'bridge' as BicameralSide }
          : prev,
      );
    }
    if (event.type === 'bicameral_converged') {
      const criterion =
        typeof p.criterion === 'string'
          ? (p.criterion as ConvergenceCriterion)
          : null;
      setBicameralState((prev) => ({
        ...prev,
        running: false,
        currentSide: 'idle' as BicameralSide,
        convergenceCriterion: criterion,
        hardCapReached: false,
      }));
    }
    if (event.type === 'bicameral_hard_cap_reached') {
      setBicameralState((prev) => ({
        ...prev,
        running: false,
        currentSide: 'idle' as BicameralSide,
        hardCapReached: true,
      }));
    }

    if (
      event.type === 'session_complete' ||
      event.type === 'session_cancelled' ||
      event.type === 'error'
    ) {
      // Terminal event from the backend's perspective. Stop the loop
      // visually and close the WS. session_cancelled fires when the
      // operator clicked Cancel and the backend's loop observed the
      // flag at its next check point.
      setBicameralState((prev) => ({
        ...prev,
        running: false,
        currentSide: 'idle' as BicameralSide,
      }));
      closeWs();
    }
  }, [closeWs]);

  // Mirror Audit pathway ignores runMode — it operates on supplied
  // prior_resolution text and goes straight to /synthesize.
  const effectiveMode: RunMode = pathway === 'mirror_audit' ? 'synthesis' : runMode;

  // Mirror the runner's state up to the parent so the right panel can
  // render the optics-box live. Fires on every meaningful change.
  useEffect(() => {
    if (!onRunnerStateChange) return;
    onRunnerStateChange({
      pathway,
      runMode: effectiveMode,
      scenarioSummary: summarizeForPacket(pathway, inputs),
      blueprint,
      oracles: Object.values(oracles),
      strokes,
      finalText,
      running,
      hasError: error !== null,
      recentEvents: events.slice(-12),
    });
  }, [pathway, effectiveMode, inputs, blueprint, oracles, strokes, finalText, running, error, events, onRunnerStateChange]);

  const handleRun = async () => {
    reset();

    const summary = summarizeForPacket(pathway, inputs);
    if (!summary.trim()) {
      setError('Fill in the scenario fields before running.');
      return;
    }

    setRunning(true);
    try {
      if (effectiveMode === 'triage') {
        await runTriageOnly(summary);
      } else if (effectiveMode === 'full_loop') {
        await runFullLoop();
      } else {
        await runSynthesisOnly(summary);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'unknown error';
      setError(msg);
    } finally {
      setRunning(false);
    }
  };

  // Triage-only — single Engine call, returns the Architectural Blueprint
  // as raw text. Fast (~30s). Useful preview before kicking off a real
  // Full Loop run.
  const runTriageOnly = async (scenarioText: string) => {
    const resp = await fetch(`${backendUrl}/api/triage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: scenarioText,
        max_subjects: maxSubjects,
      }),
    });
    if (!resp.ok) {
      throw new Error(`Triage failed: HTTP ${resp.status} ${await resp.text()}`);
    }
    const data = (await resp.json()) as { hit_list_raw: string };
    setBlueprint(data.hit_list_raw);
    // Synthesise a "stroke" shape so the Copy Engine Output button works.
    const nowIso = new Date().toISOString();
    setStrokes([
      {
        stroke_number: 1,
        pathway: pathway as Pathway,
        raw_response: data.hit_list_raw,
        final_resolution: data.hit_list_raw,
        started_at: nowIso,
        completed_at: nowIso,
      },
    ]);
    setFinalText(data.hit_list_raw);
  };

  // Full Universal Logic Loop — Triage → Oracle swarm → Synthesis. Slow
  // (15-60 min). The backend runs it as a background task and emits
  // structured progress events over the session's WebSocket.
  const runFullLoop = async () => {
    const scenario = buildScenarioPayload(pathway, inputs);

    // 1. Create session
    const createResp = await fetch(`${backendUrl}/api/v2/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario,
        pathway,
        iterative: false,
        max_strokes: 1,
      }),
    });
    if (!createResp.ok) {
      throw new Error(`Create session failed: HTTP ${createResp.status} ${await createResp.text()}`);
    }
    const created = (await createResp.json()) as { session_id: string };
    setSessionId(created.session_id);

    // 2. Subscribe to events FIRST so we don't miss the early blueprint/oracle events
    const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/api/v2/sessions/${created.session_id}/events/stream`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    // Wait for the WS to actually be open before kicking off the loop, so
    // history replay + live stream both reach us.
    await new Promise<void>((resolve, reject) => {
      const t = setTimeout(() => reject(new Error('WS open timeout')), 5000);
      ws.onopen = () => { clearTimeout(t); resolve(); };
      ws.onerror = () => { clearTimeout(t); reject(new Error('WS error')); };
    });

    // Track the session_complete promise so we can wait on it before
    // fetching /complete. The handleEvent callback closes the WS on
    // terminal events; here we listen to the same stream to know WHEN.
    const terminalReached = new Promise<void>((resolve, reject) => {
      const orig = ws.onmessage;
      ws.onmessage = (msg) => {
        if (orig) orig.call(ws, msg);
        try {
          const ev = JSON.parse(msg.data) as SessionEvent;
          handleEvent(ev);
          if (ev.type === 'session_complete') resolve();
          if (ev.type === 'error') reject(new Error(
            typeof ev.payload?.message === 'string' ? (ev.payload.message as string) : 'session errored',
          ));
        } catch {
          /* ignore */
        }
      };
    });

    // 3. Kick off the full loop on the backend (returns 202 immediately).
    const kickoffResp = await fetch(
      `${backendUrl}/api/v2/sessions/${created.session_id}/run-full-loop`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_subjects: maxSubjects,
          research_mode: researchMode,
        }),
      },
    );
    if (!kickoffResp.ok) {
      throw new Error(`Kickoff failed: HTTP ${kickoffResp.status} ${await kickoffResp.text()}`);
    }

    // 4. Wait for the session to terminate (could be 15-60 min for big runs).
    await terminalReached;

    // 5. Fetch /complete to get the canonical FinalResolution.
    const completeResp = await fetch(
      `${backendUrl}/api/v2/sessions/${created.session_id}/complete`,
      { method: 'POST' },
    );
    if (!completeResp.ok) {
      throw new Error(`Complete fetch failed: HTTP ${completeResp.status} ${await completeResp.text()}`);
    }
    const finalJson = (await completeResp.json()) as {
      final_resolution: { final_text: string; strokes: StrokeResult[] };
    };
    setStrokes(finalJson.final_resolution.strokes);
    setFinalText(finalJson.final_resolution.final_text);
  };

  // Synthesis-only — legacy single-Engine-call path. For Mirror Audit
  // (which audits supplied prior_resolution) and for any future
  // "pre-harvested truth packets" UI work. Cleanroom/Genie/Offensive
  // without truth packets will produce "I have no data" responses —
  // surfaced as a warning before kicking off.
  const runSynthesisOnly = async (scenarioText: string) => {
    const scenario = buildScenarioPayload(pathway, inputs);
    const createResp = await fetch(`${backendUrl}/api/v2/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario, pathway, iterative, max_strokes: iterative ? 3 : 1,
      }),
    });
    if (!createResp.ok) {
      throw new Error(`Create session failed: HTTP ${createResp.status} ${await createResp.text()}`);
    }
    const created = (await createResp.json()) as { session_id: string };
    setSessionId(created.session_id);

    const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/api/v2/sessions/${created.session_id}/events/stream`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.onmessage = (msg) => {
      try {
        const ev = JSON.parse(msg.data) as SessionEvent;
        handleEvent(ev);
      } catch { /* ignore */ }
    };

    const packets = [{
      subject: 'Scenario',
      content: scenarioText,
      source_label: 'User input via Live Runner',
    }];
    const driveUrl = iterative
      ? `${backendUrl}/api/v2/sessions/${created.session_id}/iterate`
      : `${backendUrl}/api/v2/sessions/${created.session_id}/synthesize`;
    // Bicameral Convergence — pass the Bridge toggle to /iterate. The
    // /synthesize path is single-pass so the flag doesn't apply.
    const driveBody = iterative
      ? { truth_packets: packets, include_bridge: includeBridge }
      : { truth_packets: packets };
    const driveResp = await fetch(driveUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(driveBody),
    });
    if (!driveResp.ok) {
      throw new Error(`Engine run failed: HTTP ${driveResp.status} ${await driveResp.text()}`);
    }
    const driveJson = (await driveResp.json()) as
      | { stroke: StrokeResult; state: unknown }
      | { strokes: StrokeResult[]; state: unknown };
    if ('strokes' in driveJson) setStrokes(driveJson.strokes);
    else if ('stroke' in driveJson) setStrokes([driveJson.stroke]);

    const completeResp = await fetch(
      `${backendUrl}/api/v2/sessions/${created.session_id}/complete`,
      { method: 'POST' },
    );
    if (!completeResp.ok) {
      throw new Error(`Complete failed: HTTP ${completeResp.status} ${await completeResp.text()}`);
    }
    const finalJson = (await completeResp.json()) as {
      final_resolution: { final_text: string; strokes: StrokeResult[] };
    };
    setStrokes(finalJson.final_resolution.strokes);
    setFinalText(finalJson.final_resolution.final_text);
  };

  // Copy the Engine's raw output to the clipboard. The user takes it to
  // Gemini Pro (or any model) with their own prompt — historically just
  // "visualize this" — and Gemini sets the table for the visualization
  // without us pre-constraining the schema. The original Hualapai render
  // came out of this exact flow. If Gemini returns GSS-shaped JSON, paste
  // it into the Cortex Clipboard's Simulation Listener to render.
  const [copyDone, setCopyDone] = useState(false);
  const handleCopyOutput = async () => {
    if (strokes.length === 0) return;
    const text = composeEngineOutputForCopy(strokes);
    try {
      await navigator.clipboard.writeText(text);
      setCopyDone(true);
      setTimeout(() => setCopyDone(false), 1800);
    } catch {
      /* navigator.clipboard may be denied; ignore silently */
    }
  };

  const PathwayIcon = PATHWAY_META[pathway].icon;

  return (
    <div className="w-full h-full flex flex-col bg-slate-900/80 rounded-xl border border-slate-800 shadow-xl overflow-hidden font-mono text-sm backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-950 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Terminal className="text-emerald-400 w-5 h-5" />
          <h1 className="text-slate-100 font-semibold tracking-wide">Live Runner</h1>
        </div>
        <div className="text-[10px] text-slate-500">
          {sessionId ? `session ${sessionId.slice(0, 8)}…` : 'no session'}
        </div>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
        {/* Pathway selector — each pathway button has example chips above it.
            Clicking a chip switches pathway + loads the curated example
            inputs + previews the example's GSS on PhysicsCanvas. */}
        <div className="space-y-2">
          <label className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold flex items-center gap-1.5">
            <span>Pathway</span>
            <Sparkles className="w-3 h-3 text-amber-400" />
            <span className="text-slate-500 normal-case tracking-normal text-amber-400/70">
              click examples twice to load
            </span>
          </label>
          <div className="grid grid-cols-2 gap-2">
            {(Object.keys(PATHWAY_META) as Pathway[]).map((p) => {
              const meta = PATHWAY_META[p];
              const Icon = meta.icon;
              const active = pathway === p;
              const examples = EXAMPLES_BY_PATHWAY[p] ?? [];
              return (
                <div key={p} className="flex flex-col">
                  {/* Example chips row — TWO-CLICK to fire:
                      1st click = primes the chip (emerald glow, "click again")
                      2nd click = loads the example
                      Auto-resets after 3s of inactivity. */}
                  {examples.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-1">
                      {examples.map((ex) => {
                        const loaded = loadedExampleId === ex.id;
                        const primed = primedExampleId === ex.id;
                        return (
                          <button
                            key={ex.id}
                            type="button"
                            onClick={() => handleChipClick(ex)}
                            title={primed ? 'Click again to load this example' : ex.blurb}
                            className={[
                              'flex items-center gap-1 px-1.5 py-0.5 rounded-t-md border-b-0 border text-[10px] font-mono transition-colors',
                              primed
                                ? 'bg-emerald-500/15 border-emerald-500/60 text-emerald-200 ring-1 ring-emerald-500/40'
                                : loaded
                                  ? 'bg-amber-500/15 border-amber-500/60 text-amber-200'
                                  : 'bg-slate-900/60 border-slate-800 text-slate-500 hover:bg-amber-500/10 hover:text-amber-300 hover:border-amber-500/30',
                            ].join(' ')}
                          >
                            <Sparkles className="w-2.5 h-2.5" />
                            <span>{primed ? `${ex.title} · click again` : ex.title}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                  {/* Pathway button */}
                  <button
                    type="button"
                    onClick={() => {
                      setPathway(p);
                      setLoadedExampleId(null);
                    }}
                    className={[
                      'flex items-center gap-2 px-3 py-2 rounded-md border text-xs transition-colors text-left',
                      active
                        ? 'bg-indigo-900/40 border-indigo-500/60 text-indigo-100'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800/60',
                    ].join(' ')}
                  >
                    <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                    <span className="truncate">{meta.label}</span>
                  </button>
                </div>
              );
            })}
          </div>
          <p className="text-[10px] text-slate-500 leading-relaxed flex items-start gap-1.5">
            <PathwayIcon className="w-3 h-3 mt-0.5 flex-shrink-0 text-indigo-400" />
            <span>
              {loadedExampleId
                ? `Example loaded — fields prefilled and topology previewing on the right. Edit the fields and click Run to query the Engine live, or use as-is.`
                : PATHWAY_META[pathway].description}
            </span>
          </p>
        </div>

        {/* Pathway-specific inputs */}
        <div className="space-y-3">
          {pathway === 'cleanroom' && (
            <Field
              label="Question"
              hint='Falsifiable, with a resolution date. e.g. "Will Powell be removed as Fed chair by 2026-09-01?"'
              value={inputs.question || ''}
              onChange={(v) => setInput('question', v)}
            />
          )}

          {pathway === 'genie' && (
            <>
              <Field
                label="Current State"
                hint="Where you are now."
                value={inputs.current_state || ''}
                onChange={(v) => setInput('current_state', v)}
              />
              <Field
                label="Wished-for State"
                hint="Where you want to end up."
                value={inputs.wished_for_state || ''}
                onChange={(v) => setInput('wished_for_state', v)}
              />
            </>
          )}

          {pathway === 'offensive' && (
            <>
              <Field
                label="Target"
                hint="The actor / structure being analysed."
                value={inputs.target || ''}
                onChange={(v) => setInput('target', v)}
              />
              <Field
                label="Objective State"
                hint="Where you want the target to end up (the SDS you're constructing)."
                value={inputs.objective_state || ''}
                onChange={(v) => setInput('objective_state', v)}
              />
            </>
          )}

          {pathway === 'mirror_audit' && (
            <Field
              label="Prior Resolution (Stroke-1 text)"
              hint="Paste an existing strategic resolution; the auditor will enumerate faults."
              value={inputs.prior_resolution || ''}
              onChange={(v) => setInput('prior_resolution', v)}
              rows={8}
            />
          )}

          <Field
            label="Extra context (optional)"
            hint="Background info that doesn't fit a specific field."
            value={inputs.extra_context || ''}
            onChange={(v) => setInput('extra_context', v)}
            rows={3}
          />

          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={iterative}
              onChange={(e) => setIterative(e.target.checked)}
              className="accent-indigo-500"
              disabled={pathway === 'mirror_audit' || runMode === 'full_loop' || runMode === 'triage'}
            />
            <span className={runMode !== 'synthesis' && pathway !== 'mirror_audit' ? 'text-slate-600' : ''}>
              Iterative Engine (3 strokes — synthesis mode only)
            </span>
          </label>
          <label
            className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none pl-5"
            title="Connection Bridge runs as an orthogonal-lens audit alongside the Mirror Auditor (Bicameral Convergence Level 1). Adds ~3 min of Bridge-notebook provisioning per run."
          >
            <input
              type="checkbox"
              checked={includeBridge}
              onChange={(e) => setIncludeBridge(e.target.checked)}
              className="accent-cyan-500"
              disabled={!iterative}
            />
            <span className={iterative ? 'text-slate-300' : 'text-slate-600'}>
              + Connection Bridge audit (Bicameral)
            </span>
          </label>
          {pathway === 'mirror_audit' && (
            <p className="text-[10px] text-slate-500">Mirror Audit is a single-stroke pathway. Run mode below ignored.</p>
          )}
        </div>

        {/* Run mode selector — only for non-Mirror-Audit pathways. Mirror
            Audit's Engine call is always synthesis on the supplied
            prior_resolution. */}
        {pathway !== 'mirror_audit' && (
          <div className="space-y-2">
            <label className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">Run mode</label>
            <div className="grid grid-cols-1 gap-1.5">
              <ModeRadio
                value="full_loop"
                checked={runMode === 'full_loop'}
                onChange={setRunMode}
                title="Full Universal Logic Loop"
                blurb="Triage → spawn PKI Oracles → Deep Research per subject (programmatic Import) → Synthesis. Real-world facts. 15-60 min."
              />
              <ModeRadio
                value="triage"
                checked={runMode === 'triage'}
                onChange={setRunMode}
                title="Triage Only (Architectural Blueprint)"
                blurb="Single Engine call. Returns the 9D research plan: which subjects to gather, what dimensions matter. Fast (~30s)."
              />
              <ModeRadio
                value="synthesis"
                checked={runMode === 'synthesis'}
                onChange={setRunMode}
                title="Synthesis Only (no Oracles)"
                blurb="Skip Triage and harvest. Engine reasons on its corpus alone. Without real-world facts it will say so. Mostly for module-consumer testing."
              />
            </div>
            {(runMode === 'full_loop' || runMode === 'triage') && (
              <div className="flex items-center gap-3 pt-1">
                <label className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
                  Max subjects
                </label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  step={1}
                  value={maxSubjects}
                  onChange={(e) => setMaxSubjects(Number(e.target.value))}
                  className="flex-1 accent-indigo-500"
                />
                <span className="text-xs text-slate-200 w-4 text-right">{maxSubjects}</span>
              </div>
            )}
            {runMode === 'full_loop' && (
              <div className="flex items-center gap-3 pt-1">
                <label className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold whitespace-nowrap">
                  Research
                </label>
                <div className="flex flex-1 gap-1 bg-slate-950 border border-slate-800 rounded-md p-0.5">
                  {(['fast', 'deep'] as ResearchMode[]).map((mode) => {
                    const active = researchMode === mode;
                    return (
                      <button
                        key={mode}
                        type="button"
                        onClick={() => setResearchMode(mode)}
                        className={[
                          'flex-1 px-2 py-1 rounded text-[10px] uppercase tracking-widest transition-colors',
                          active
                            ? mode === 'deep'
                              ? 'bg-indigo-600/30 text-indigo-100 border border-indigo-500/50'
                              : 'bg-amber-600/30 text-amber-100 border border-amber-500/50'
                            : 'text-slate-500 hover:text-slate-300',
                        ].join(' ')}
                        title={mode === 'deep'
                          ? 'Web-grounded multi-minute Deep Research — historic Powell-class flow, ~5-20 min/oracle'
                          : 'Single-pass research — much smaller source pool, completes in seconds-to-minutes'}
                      >
                        {mode}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Run button */}
        <div className="space-y-2">
          <button
            type="button"
            onClick={handleRun}
            disabled={running}
            className={[
              'w-full py-3 rounded-md flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-widest transition-colors',
              running
                ? 'bg-slate-800 text-slate-500 cursor-wait'
                : 'bg-emerald-600/15 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40',
            ].join(' ')}
          >
            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {running
              ? effectiveMode === 'full_loop' ? 'Running Full Loop…' : 'Running…'
              : effectiveMode === 'full_loop'
                ? `Run Full Loop (${maxSubjects} Oracle${maxSubjects === 1 ? '' : 's'}, ${researchMode === 'deep' ? '15-60' : '2-10'} min)`
                : effectiveMode === 'triage'
                  ? 'Run Triage'
                  : 'Run Synthesis'}
          </button>

          {error && (
            <div className="flex items-start gap-2 p-3 rounded-md bg-rose-950/40 border border-rose-500/40 text-rose-200 text-[11px]">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span className="leading-relaxed break-words">{error}</span>
            </div>
          )}
        </div>

        {/* Event timeline (compact) */}
        {events.length > 0 && (
          <div className="space-y-1.5">
            <h3 className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">Timeline</h3>
            <div className="space-y-1 max-h-32 overflow-y-auto text-[10px] font-mono text-slate-400 border border-slate-800 rounded-md p-2 bg-slate-950/60">
              {events.map((ev, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-slate-600">{new Date(ev.emitted_at).toLocaleTimeString()}</span>
                  <span className={ev.type === 'error' ? 'text-rose-400' : 'text-slate-400'}>
                    {ev.type}
                  </span>
                  {ev.stroke_number !== null && (
                    <span className="text-slate-600">stroke {ev.stroke_number}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Architectural Blueprint — from Triage (Phase 1). Always shown
            when the Engine produced one. Collapsible because it can be long. */}
        {blueprint && (
          <details className="rounded-md border border-indigo-500/30 bg-indigo-950/20 text-xs" open>
            <summary className="cursor-pointer px-3 py-2 text-[10px] uppercase tracking-widest text-indigo-300 font-semibold">
              Architectural Blueprint (Phase 1)
            </summary>
            <pre className="px-3 pb-3 whitespace-pre-wrap break-words text-slate-300 text-[11px] leading-relaxed max-h-80 overflow-y-auto">
              {blueprint}
            </pre>
          </details>
        )}

        {/* Per-Oracle progress (Phase 2). One card per subject as it's
            requested → created → researching → harvested. */}
        {Object.values(oracles).length > 0 && (
          <div className="space-y-1.5">
            <h3 className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
              PKI Oracle Swarm (Phase 2)
            </h3>
            <div className="space-y-1.5">
              {Object.values(oracles).map((o) => (
                <OracleCard key={o.subject} oracle={o} />
              ))}
            </div>
          </div>
        )}

        {/* Bicameral Convergence Level 2 live-progress (E1-05). Renders
            only when a bicameral loop is in flight or has just terminated.
            Hidden during Level 1 /iterate runs (those don't emit
            bicameral_* events). Provides the iteration counter, current
            side indicator, cancel button (wired to POST /sessions/{id}/cancel
            per E1-01), and convergence/hard-cap terminal messaging. */}
        <BicameralProgressIndicator
          {...bicameralState}
          sessionId={sessionId}
          onCancel={handleCancel}
        />

        {/* Stroke results */}
        {strokes.map((stroke) => (
          <StrokeCard
            key={stroke.stroke_number}
            stroke={stroke}
            sessionId={sessionId}
          />
        ))}

        {/* Output handoff. Single behaviour for every pathway: copy the
            Engine's raw output to your clipboard. Take it to Gemini Pro
            yourself with whatever prompt you want — we don't pre-cast
            the visualization. If Gemini returns GSS-shaped JSON, paste
            it into the Cortex Clipboard (bottom-right) to render. */}
        {strokes.length > 0 && (
          <div className="space-y-2">
            <button
              type="button"
              onClick={handleCopyOutput}
              className={[
                'w-full py-3 rounded-md flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-widest border transition-colors',
                copyDone
                  ? 'bg-emerald-600/15 border-emerald-500/50 text-emerald-200'
                  : 'bg-indigo-600/15 hover:bg-indigo-600/30 text-indigo-300 border-indigo-500/40',
              ].join(' ')}
            >
              {copyDone ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copyDone ? 'Copied to clipboard' : 'Copy Engine Output'}
            </button>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              Paste into Gemini Pro and ask it to visualize. If Gemini
              returns GSS-shaped JSON, paste it into the Cortex Clipboard
              (bottom-right) and click <span className="text-emerald-400">Apply&nbsp;To&nbsp;Topology</span> to render.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

interface FieldProps {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
}

function Field({ label, hint, value, onChange, rows = 4 }: FieldProps) {
  return (
    <div className="space-y-1">
      <label className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="w-full bg-slate-950 border border-slate-800 rounded-md p-3 text-slate-200 text-xs resize-none focus:outline-none focus:border-indigo-500/60 placeholder-slate-600"
        placeholder={hint}
      />
    </div>
  );
}

function StrokeCard({
  stroke,
  sessionId,
}: {
  stroke: StrokeResult;
  sessionId: string | null;
}) {
  // Audit-style strokes (pathway=mirror_audit) split into Mirror Auditor and
  // Connection Bridge by audit_kind. Auditor strokes carry a parsed
  // audit_findings list (four fault categories); Bridge strokes leave that
  // null and render raw_response directly (connection-enumeration prose).
  const isAudit = stroke.pathway === 'mirror_audit';
  const isBridge = isAudit && stroke.audit_kind === 'bridge';
  const accentColor = isBridge ? 'cyan' : isAudit ? 'amber' : 'slate';
  const auditLabel = isBridge ? 'Connection Bridge' : isAudit ? 'Mirror Auditor' : null;
  return (
    <div className={`rounded-md border bg-slate-950/70 p-3 space-y-2 text-xs ${
      isBridge ? 'border-cyan-700/40' : isAudit ? 'border-amber-700/40' : 'border-slate-800'
    }`}>
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-widest">
          <span className="text-slate-500">Stroke {stroke.stroke_number} ·</span>{' '}
          <span className={
            isBridge ? 'text-cyan-300' : isAudit ? 'text-amber-300' : 'text-slate-500'
          }>
            {auditLabel ?? stroke.pathway}
          </span>
        </div>
        <div className="text-[10px] text-slate-600">
          {Math.round(
            (new Date(stroke.completed_at).getTime() - new Date(stroke.started_at).getTime()) / 1000,
          )}
          s
        </div>
      </div>

      {!isAudit && stroke.strategic_lasso && (
        <Section label="Strategic Lasso" body={stroke.strategic_lasso} />
      )}
      {!isAudit && stroke.incomprehensible_move && (
        <Section label="Incomprehensible Move" body={stroke.incomprehensible_move} />
      )}
      {!isAudit && stroke.final_resolution && (
        <Section label="Final Resolution" body={stroke.final_resolution} accent />
      )}

      {isAudit && !isBridge && (stroke.audit_findings?.length ?? 0) > 0 && (
        <div className="space-y-1.5">
          <div className="text-[10px] uppercase tracking-widest text-amber-400">Audit Findings</div>
          {stroke.audit_findings!.map((finding, i) => (
            <div key={i} className="text-slate-300 text-[11px] leading-relaxed border-l-2 border-amber-500/40 pl-2">
              {finding}
            </div>
          ))}
        </div>
      )}

      {isAudit && isBridge && (
        <div className="space-y-1.5">
          <div className="text-[10px] uppercase tracking-widest text-cyan-400">Missed Connections</div>
          <pre className="text-slate-300 text-[11px] leading-relaxed whitespace-pre-wrap font-sans border-l-2 border-cyan-500/40 pl-2">
            {stroke.raw_response}
          </pre>
        </div>
      )}

      <details className={`text-[10px] ${
        accentColor === 'cyan' ? 'text-cyan-700/70' : accentColor === 'amber' ? 'text-amber-700/70' : 'text-slate-500'
      }`}>
        <summary className="cursor-pointer hover:text-slate-300">raw response</summary>
        <pre className="whitespace-pre-wrap break-words mt-1 text-slate-400 text-[10px]">
          {stroke.raw_response}
        </pre>
      </details>

      {/* Pl3 Operator Lens — per-stroke translation panel. Sits below the
          raw-response details so it's discoverable but doesn't dominate
          the card. Each register's translation is fetched lazily on
          selection and cached for the session's life. */}
      {sessionId && (
        <StrokeTranslator
          sessionId={sessionId}
          strokeNumber={stroke.stroke_number}
          sourceLength={
            (stroke.cleaned_response ?? stroke.raw_response).length
          }
        />
      )}
    </div>
  );
}

function Section({ label, body, accent }: { label: string; body: string; accent?: boolean }) {
  return (
    <div className="space-y-1">
      <div
        className={[
          'text-[10px] uppercase tracking-widest',
          accent ? 'text-emerald-400' : 'text-indigo-400',
        ].join(' ')}
      >
        {label}
      </div>
      <div className="text-slate-200 text-[11px] leading-relaxed whitespace-pre-wrap break-words">
        {body}
      </div>
    </div>
  );
}

interface ModeRadioProps {
  value: RunMode;
  checked: boolean;
  onChange: (v: RunMode) => void;
  title: string;
  blurb: string;
}

function ModeRadio({ value, checked, onChange, title, blurb }: ModeRadioProps) {
  return (
    <label
      className={[
        'flex items-start gap-2 px-3 py-2 rounded-md border text-xs cursor-pointer transition-colors',
        checked
          ? 'bg-indigo-900/40 border-indigo-500/60 text-indigo-100'
          : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800/60',
      ].join(' ')}
    >
      <input
        type="radio"
        name="runMode"
        value={value}
        checked={checked}
        onChange={() => onChange(value)}
        className="mt-0.5 accent-indigo-500"
      />
      <span className="flex-1">
        <span className={['block font-semibold', checked ? 'text-indigo-100' : 'text-slate-300'].join(' ')}>
          {title}
        </span>
        <span className="block text-[10px] text-slate-500 leading-relaxed mt-0.5">{blurb}</span>
      </span>
    </label>
  );
}

function OracleCard({ oracle }: { oracle: OracleProgress }) {
  const statusBadge: Record<OracleProgress['status'], { label: string; cls: string }> = {
    requested:   { label: 'requested',   cls: 'bg-slate-700/40 text-slate-300 border-slate-600' },
    created:     { label: 'created',     cls: 'bg-blue-700/30 text-blue-200 border-blue-500/40' },
    researching: { label: 'researching', cls: 'bg-amber-600/20 text-amber-200 border-amber-500/40' },
    harvested:   { label: 'harvested',   cls: 'bg-emerald-700/30 text-emerald-200 border-emerald-500/40' },
    failed:      { label: 'failed',      cls: 'bg-rose-700/30 text-rose-200 border-rose-500/40' },
  };
  const badge = statusBadge[oracle.status];
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950/60 p-2.5 space-y-1.5">
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold text-slate-200 truncate">{oracle.subject}</div>
        <span className={['text-[9px] uppercase tracking-widest px-1.5 py-0.5 rounded border font-mono', badge.cls].join(' ')}>
          {badge.label}
        </span>
      </div>
      {oracle.surgical_prompt && (
        <div className="text-[10px] text-slate-500 leading-relaxed italic line-clamp-2">
          {oracle.surgical_prompt}
        </div>
      )}
      <div className="flex items-center gap-3 text-[10px] text-slate-500 font-mono">
        {oracle.notebook_id && <span>nb {oracle.notebook_id.slice(0, 8)}…</span>}
        {oracle.sources_imported !== undefined && <span>{oracle.sources_imported} src</span>}
        {oracle.packet_chars !== undefined && <span>{oracle.packet_chars.toLocaleString()} chars</span>}
      </div>
      {oracle.error && (
        <div className="text-[10px] text-rose-300 leading-relaxed">
          {oracle.error}
        </div>
      )}
    </div>
  );
}
