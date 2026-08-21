'use client';

/**
 * Pre-registered predictions bulletin board.
 *
 * Reads from `src/data/predictions.ts` and renders each entry as a card.
 * Pending predictions show a live countdown to the resolution date;
 * resolved predictions show the outcome.
 *
 * Pre-registration discipline matters because it's what separates
 * "we predicted X and reality matched X" from "we'd been saying X was
 * likely all along." The board surfaces that timestamping visibly.
 *
 * Adding a new prediction: edit `src/data/predictions.ts`. The page
 * picks up new entries on next render (no backend round-trip — static
 * data file).
 */

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
  PREDICTIONS,
  daysUntilResolution,
  type Prediction,
  type PredictionStatus,
} from '@/data/predictions';
import {
  Sparkles,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  HelpCircle,
  ArrowLeft,
  ExternalLink,
} from 'lucide-react';

const STATUS_META: Record<
  PredictionStatus,
  {
    label: string;
    icon: React.ComponentType<{ className?: string; size?: number }>;
    chip: string;
    border: string;
  }
> = {
  pending: {
    label: 'Pending',
    icon: Clock,
    chip: 'text-amber-300 bg-amber-950/40 border-amber-700/60',
    border: 'border-amber-700/30',
  },
  validated: {
    label: 'Validated',
    icon: CheckCircle2,
    chip: 'text-emerald-300 bg-emerald-950/40 border-emerald-700/60',
    border: 'border-emerald-700/30',
  },
  falsified: {
    label: 'Falsified',
    icon: XCircle,
    chip: 'text-rose-300 bg-rose-950/40 border-rose-700/60',
    border: 'border-rose-700/30',
  },
  partial: {
    label: 'Partial',
    icon: AlertCircle,
    chip: 'text-cyan-300 bg-cyan-950/40 border-cyan-700/60',
    border: 'border-cyan-700/30',
  },
  inconclusive: {
    label: 'Inconclusive',
    icon: HelpCircle,
    chip: 'text-slate-300 bg-slate-800/60 border-slate-700/60',
    border: 'border-slate-700/30',
  },
};

const CONFIDENCE_META: Record<Prediction['confidence'], string> = {
  low: 'text-slate-400',
  medium: 'text-indigo-300',
  'medium-high': 'text-cyan-300',
  high: 'text-emerald-300',
};

export default function PredictionsPage() {
  const pendingCount = PREDICTIONS.filter((p) => p.status === 'pending').length;
  const resolvedCount = PREDICTIONS.length - pendingCount;

  return (
    <main className="min-h-screen w-full bg-[#030712] text-slate-200 p-6 md:p-10">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <header className="mb-8 flex flex-col gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors w-fit"
          >
            <ArrowLeft size={12} />
            Back to runner
          </Link>
          <div className="flex items-end gap-3 flex-wrap">
            <h1 className="text-3xl font-semibold tracking-tight text-slate-100 flex items-center gap-2">
              <Sparkles size={24} className="text-indigo-400" />
              Pre-registered predictions
            </h1>
            <span className="text-[11px] uppercase tracking-widest text-slate-500 font-mono">
              {pendingCount} pending · {resolvedCount} resolved
            </span>
          </div>
          <p className="text-sm text-slate-400 leading-relaxed max-w-2xl">
            Cleanroom-pathway predictions made BEFORE their resolution date.
            Pre-registration discipline is what separates &ldquo;we predicted X
            and reality matched X&rdquo; from &ldquo;we&rsquo;d been saying X
            all along.&rdquo; Each card shows what was claimed, the audited
            mechanism, and a live countdown to validation.
          </p>
        </header>

        {/* Cards */}
        <section className="space-y-6">
          {PREDICTIONS.length === 0 ? (
            <EmptyState />
          ) : (
            PREDICTIONS.map((p) => <PredictionCard key={p.id} prediction={p} />)
          )}
        </section>

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-slate-800/60 text-[11px] text-slate-600 leading-relaxed">
          Add a prediction by editing{' '}
          <code className="font-mono text-slate-400">src/data/predictions.ts</code>
          . Update a prediction&rsquo;s status when its resolution date arrives;
          fill in the <code className="font-mono text-slate-400">outcome</code>{' '}
          field. The underlying run record in{' '}
          <code className="font-mono text-slate-400">docs/experiments/runs/</code>{' '}
          is the source of truth for methodology + verbatim Stroke outputs.
        </footer>
      </div>
    </main>
  );
}

function PredictionCard({ prediction }: { prediction: Prediction }) {
  const status = STATUS_META[prediction.status];
  const StatusIcon = status.icon;

  return (
    <article
      className={`rounded-xl border ${status.border} bg-slate-900/40 backdrop-blur-sm overflow-hidden`}
    >
      {/* Card header — status pill + scenario one-liner */}
      <div className="p-5 border-b border-slate-800/60">
        <div className="flex items-start justify-between gap-3 mb-3 flex-wrap">
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[10px] uppercase tracking-widest font-mono ${status.chip}`}
          >
            <StatusIcon size={11} />
            {status.label}
          </span>
          <div className="flex items-center gap-3 text-[10px] uppercase tracking-widest text-slate-500 font-mono">
            <span>{prediction.pathway}</span>
            <span>·</span>
            <span className={CONFIDENCE_META[prediction.confidence]}>
              {prediction.confidence} confidence
            </span>
            {prediction.audited && (
              <>
                <span>·</span>
                <span className="text-amber-300">
                  audited{prediction.bridge_extended ? ' + bridge' : ''}
                </span>
              </>
            )}
          </div>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed">
          {prediction.scenario}
        </p>
      </div>

      {/* Countdown or outcome */}
      {prediction.status === 'pending' ? (
        <Countdown prediction={prediction} />
      ) : prediction.outcome ? (
        <div className="p-5 border-b border-slate-800/60">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono mb-1.5">
            Outcome
          </div>
          <p className="text-sm text-slate-200 leading-relaxed">
            {prediction.outcome}
          </p>
        </div>
      ) : null}

      {/* Primary claim */}
      <div className="p-5 border-b border-slate-800/60">
        <div className="text-[10px] uppercase tracking-widest text-indigo-400 font-mono mb-1.5">
          Claim
        </div>
        <p className="text-sm text-slate-200 leading-relaxed">
          {prediction.primary_claim}
        </p>
      </div>

      {/* Mechanism (audited) */}
      <div className="p-5 border-b border-slate-800/60">
        <div className="text-[10px] uppercase tracking-widest text-emerald-400 font-mono mb-1.5">
          Mechanism (audited Stroke 3)
        </div>
        <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
          {prediction.mechanism}
        </p>
      </div>

      {/* Risk mechanisms */}
      {prediction.risk_mechanisms.length > 0 && (
        <div className="p-5 border-b border-slate-800/60">
          <div className="text-[10px] uppercase tracking-widest text-rose-400 font-mono mb-2">
            Falsification triggers
          </div>
          <ul className="space-y-2">
            {prediction.risk_mechanisms.map((rm, i) => (
              <li key={i} className="flex flex-col gap-0.5">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">
                  {rm.side}
                </span>
                <span className="text-sm text-slate-300 leading-relaxed">
                  {rm.watch_for}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Notes */}
      {prediction.notes && (
        <div className="p-5 border-b border-slate-800/60 bg-slate-950/40">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono mb-1.5">
            Notes
          </div>
          <p className="text-xs text-slate-400 leading-relaxed italic">
            {prediction.notes}
          </p>
        </div>
      )}

      {/* Footer — pre-registration timestamp + run record link */}
      <div className="px-5 py-3 flex items-center justify-between text-[10px] uppercase tracking-widest text-slate-500 font-mono flex-wrap gap-2">
        <span>
          Pre-registered{' '}
          {new Date(prediction.pre_registered_at).toLocaleString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'UTC',
            timeZoneName: 'short',
          })}
        </span>
        <a
          href={`https://github.com/anitacigawet/9D-Chess/blob/main/${prediction.run_record}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-300 transition-colors"
          title={prediction.run_record}
        >
          <span className="truncate max-w-[300px]">{prediction.run_record}</span>
          <ExternalLink size={10} />
        </a>
      </div>
    </article>
  );
}

function Countdown({ prediction }: { prediction: Prediction }) {
  // Re-render once per minute so the countdown stays fresh without
  // burning a frame budget. Resolution dates are day-granular; minute
  // refresh is more than enough.
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = window.setInterval(() => setTick((t) => t + 1), 60_000);
    return () => window.clearInterval(id);
  }, []);
  // ESLint thinks tick is unused, but its only job is to trigger re-render.
  void tick;

  const days = daysUntilResolution(prediction);
  const resolutionLabel = new Date(prediction.resolution_date).toLocaleDateString(
    undefined,
    { year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC' },
  );

  return (
    <div className="p-5 border-b border-slate-800/60 bg-amber-950/10">
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-amber-300 font-mono tabular-nums">
            {days > 0 ? days : days === 0 ? 'Today' : `${Math.abs(days)}d past`}
          </span>
          {days > 0 && (
            <span className="text-xs uppercase tracking-widest text-amber-500/70">
              {days === 1 ? 'day' : 'days'} to resolution
            </span>
          )}
        </div>
        <span className="text-[11px] text-slate-400">
          Resolves {resolutionLabel}
        </span>
      </div>
      {days < 0 && (
        <p className="mt-2 text-[11px] text-rose-300 leading-relaxed">
          Past resolution date — please update this prediction&rsquo;s status
          in{' '}
          <code className="font-mono text-rose-200">
            src/data/predictions.ts
          </code>{' '}
          with the observed outcome.
        </p>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-10 text-center">
      <Sparkles size={32} className="text-slate-600 mx-auto mb-3" />
      <p className="text-sm text-slate-400 mb-1">No predictions on the board yet.</p>
      <p className="text-xs text-slate-600">
        Add one in{' '}
        <code className="font-mono">src/data/predictions.ts</code>.
      </p>
    </div>
  );
}
