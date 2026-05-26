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

import React, { useCallback, useEffect, useRef, useState } from 'react';
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
  started_at: string;
  completed_at: string;
}

const DEFAULT_BACKEND =
  process.env.NEXT_PUBLIC_GANYMEDE_BASE_URL ?? 'http://127.0.0.1:8000';

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
}

type PanelPhase = 'input' | 'dispatching' | 'review' | 'running' | 'done' | 'error';

export function DispatcherPanel({
  backendUrl = DEFAULT_BACKEND,
  onConfirm,
}: DispatcherPanelProps) {
  const [phase, setPhase] = useState<PanelPhase>('input');
  const [text, setText] = useState('');
  const [dispatch, setDispatch] = useState<DispatchResponse | null>(null);
  const [editedScenario, setEditedScenario] = useState<DispatchScenario>({});
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [strokes, setStrokes] = useState<StrokeResult[]>([]);
  const [finalText, setFinalText] = useState<string | null>(null);
  const [iterative, setIterative] = useState(true);

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-grow the input textarea while in the input phase.
  useEffect(() => {
    if (phase === 'input' && textareaRef.current) {
      const ta = textareaRef.current;
      ta.style.height = 'auto';
      ta.style.height = `${Math.min(ta.scrollHeight, 360)}px`;
    }
  }, [text, phase]);

  const reset = useCallback(() => {
    setPhase('input');
    setText('');
    setDispatch(null);
    setEditedScenario({});
    setErrorMessage(null);
    setStrokes([]);
    setFinalText(null);
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

    // Local run: create a session, drive /iterate (or /synthesize), display the result.
    setPhase('running');
    setStrokes([]);
    setFinalText(null);

    try {
      // 1. Create session.
      const createRes = await fetch(`${backendUrl}/api/v2/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario: { dream_state: true, ...scenario },
          pathway: dispatch.pathway,
          iterative,
          max_strokes: iterative ? 3 : 1,
        }),
      });
      if (!createRes.ok) {
        const body = await createRes.text();
        throw new Error(`Create session failed: HTTP ${createRes.status}: ${body}`);
      }
      const { session_id: sessionId } = await createRes.json();

      // 2. Build a single Truth Packet from the operator's text + extracted scenario.
      const truthPacket = {
        subject: 'Scenario',
        content: text.trim(),
        source_label: 'Dispatcher (operator-supplied)',
      };

      // 3. Drive iterate or synthesize.
      const endpoint = iterative
        ? `/api/v2/sessions/${sessionId}/iterate`
        : `/api/v2/sessions/${sessionId}/synthesize`;
      const driveRes = await fetch(`${backendUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ truth_packets: [truthPacket] }),
      });
      if (!driveRes.ok) {
        const body = await driveRes.text();
        throw new Error(`Run failed: HTTP ${driveRes.status}: ${body}`);
      }
      const driveData = await driveRes.json();

      const runStrokes: StrokeResult[] = iterative
        ? (driveData.strokes ?? [])
        : driveData.stroke
          ? [driveData.stroke]
          : [];
      setStrokes(runStrokes);

      // 4. Complete to seal the final resolution.
      const completeRes = await fetch(`${backendUrl}/api/v2/sessions/${sessionId}/complete`, {
        method: 'POST',
      });
      if (completeRes.ok) {
        const completeData = await completeRes.json();
        setFinalText(completeData?.final_resolution?.final_text ?? null);
      }

      setPhase('done');
    } catch (exc) {
      setErrorMessage(exc instanceof Error ? exc.message : String(exc));
      setPhase('error');
    }
  }, [dispatch, editedScenario, text, iterative, onConfirm, backendUrl]);

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
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
              <input
                type="checkbox"
                checked={iterative}
                onChange={(e) => setIterative(e.target.checked)}
                className="accent-indigo-500"
              />
              Iterative 3-stroke run (Thesis → Audit → Synthesis)
            </label>
            <button
              onClick={submitDispatch}
              disabled={!text.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40 transition-colors"
            >
              <Send size={14} />
              Classify intent
            </button>
          </div>
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
            Engine running. {iterative ? '3-stroke loop' : 'Single-pass synthesis'} — several minutes.
          </p>
          <p className="text-[10px] text-slate-600 max-w-md text-center leading-relaxed">
            Each stroke includes an 8-second cooldown floor plus the Engine's response time. The
            iterative loop fires three strokes back-to-back; the single-pass mode fires once.
          </p>
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

          {strokes.map((s) => (
            <div
              key={s.stroke_number}
              className="rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3"
            >
              <div className="flex items-center gap-2 border-b border-slate-800/60 pb-2 mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400">
                  Stroke {s.stroke_number}
                </span>
                <span className="text-[10px] text-slate-500">{s.pathway}</span>
              </div>
              <pre className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap font-sans">
                {s.raw_response}
              </pre>
            </div>
          ))}

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
