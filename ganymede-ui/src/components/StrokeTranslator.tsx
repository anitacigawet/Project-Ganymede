'use client';

/**
 * StrokeTranslator — Pl3 Operator Lens UI per stroke.
 *
 * Adds a small inline translation panel below each stroke. Operator picks
 * a register (plain English / Cube of Space / executive brief), clicks
 * Translate, sees the translated version inline. Per-stroke local cache
 * avoids re-firing the same translation; the operator can refresh
 * explicitly to re-translate.
 *
 * Backed by POST /api/v2/sessions/{id}/translate. Translation runs
 * through the same authenticated Claude CLI analytical substrate.
 *
 * Designed as a self-contained component so it can be mounted anywhere
 * a stroke is rendered without rewriting the parent's state machine.
 * Takes sessionId + strokeNumber + the source text length (for the
 * compression-ratio indicator); fetches its own data, manages its own
 * cache + loading + error states.
 */

import { useCallback, useMemo, useState } from 'react';
import { Languages, RefreshCw, AlertTriangle } from 'lucide-react';
import { getBackendBaseUrl } from '@/lib/backend';

type Register = 'plain_english' | 'cube_of_space' | 'executive_brief';

interface RegisterMeta {
  value: Register;
  label: string;
  description: string;
  badge: string;
  text: string;
}

const REGISTERS: RegisterMeta[] = [
  {
    value: 'plain_english',
    label: 'Plain English',
    description: 'Strip framework jargon; preserve analytical structure.',
    badge: 'border-sky-700/40 bg-sky-950/40',
    text: 'text-sky-200',
  },
  {
    value: 'cube_of_space',
    label: 'Cube of Space',
    description: 'Visceral geometric vocabulary; spatial framing.',
    badge: 'border-violet-700/40 bg-violet-950/40',
    text: 'text-violet-200',
  },
  {
    value: 'executive_brief',
    label: 'Executive Brief',
    description: 'Bottom-line + mechanism + risk + watch-fors; 3-5 paragraphs.',
    badge: 'border-emerald-700/40 bg-emerald-950/40',
    text: 'text-emerald-200',
  },
];

interface CachedTranslation {
  text: string;
  fetchedAt: number;
}

export interface StrokeTranslatorProps {
  sessionId: string | null;
  strokeNumber: number;
  /** Used for the compression-ratio indicator next to the translated text.
   *  Optional — when omitted the ratio is suppressed. */
  sourceLength?: number;
  /** Optional default register to pre-select. Falls back to plain_english. */
  defaultRegister?: Register;
}

export function StrokeTranslator({
  sessionId,
  strokeNumber,
  sourceLength,
  defaultRegister = 'plain_english',
}: StrokeTranslatorProps) {
  const [selectedRegister, setSelectedRegister] = useState<Register>(defaultRegister);
  const [cache, setCache] = useState<Record<Register, CachedTranslation | undefined>>({
    plain_english: undefined,
    cube_of_space: undefined,
    executive_brief: undefined,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentTranslation = cache[selectedRegister];

  const fetchTranslation = useCallback(
    async (register: Register) => {
      if (!sessionId) {
        setError('No active session — cannot translate.');
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const backend = getBackendBaseUrl();
        const res = await fetch(`${backend}/api/v2/sessions/${sessionId}/translate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stroke_number: strokeNumber, register }),
        });
        if (!res.ok) {
          const body = await res.text();
          throw new Error(`HTTP ${res.status}: ${body}`);
        }
        const data = (await res.json()) as {
          translated_text: string;
        };
        setCache((prev) => ({
          ...prev,
          [register]: { text: data.translated_text, fetchedAt: Date.now() },
        }));
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    },
    [sessionId, strokeNumber],
  );

  const handleSelect = useCallback(
    (register: Register) => {
      setSelectedRegister(register);
      // If we don't have a cached translation for this register, fetch it.
      // (Operator can hit "Refresh" to re-fetch a cached register.)
      if (!cache[register] && sessionId) {
        void fetchTranslation(register);
      }
    },
    [cache, fetchTranslation, sessionId],
  );

  const handleRefresh = useCallback(() => {
    void fetchTranslation(selectedRegister);
  }, [fetchTranslation, selectedRegister]);

  const ratioLabel = useMemo(() => {
    if (!currentTranslation || !sourceLength || sourceLength === 0) return null;
    const ratio = currentTranslation.text.length / sourceLength;
    if (ratio < 1) {
      return `${Math.round((1 - ratio) * 100)}% shorter`;
    }
    return `${Math.round((ratio - 1) * 100)}% longer`;
  }, [currentTranslation, sourceLength]);

  return (
    <div className="mt-2 rounded border border-slate-800/60 bg-slate-950/30 p-2 text-[11px]">
      <div className="flex flex-wrap items-center gap-2">
        <Languages className="h-3 w-3 text-slate-500 shrink-0" />
        <span className="text-[10px] uppercase tracking-wide text-slate-500">
          Operator Lens
        </span>
        {REGISTERS.map((r) => {
          const isSelected = selectedRegister === r.value;
          const hasCache = !!cache[r.value];
          return (
            <button
              key={r.value}
              type="button"
              onClick={() => handleSelect(r.value)}
              disabled={loading}
              className={`rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wide transition ${
                isSelected
                  ? `border ${r.badge} ${r.text}`
                  : 'border border-slate-800/60 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              } disabled:opacity-50`}
              title={r.description}
            >
              {r.label}
              {hasCache && !isSelected ? ' ✓' : ''}
            </button>
          );
        })}
        {currentTranslation && (
          <button
            type="button"
            onClick={handleRefresh}
            disabled={loading}
            className="ml-auto inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] text-slate-400 hover:text-slate-200 disabled:opacity-50"
            aria-label="Re-translate"
          >
            <RefreshCw
              className={`h-2.5 w-2.5 ${loading ? 'animate-spin' : ''}`}
            />
            Refresh
          </button>
        )}
      </div>

      {error && (
        <div className="mt-2 flex items-start gap-2 rounded border border-rose-700/40 bg-rose-950/40 p-2 text-rose-200">
          <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
          <span className="text-[10px]">{error}</span>
        </div>
      )}

      {loading && !currentTranslation && (
        <div className="mt-2 text-slate-500 italic">
          Translating into{' '}
          {REGISTERS.find((r) => r.value === selectedRegister)?.label}…
        </div>
      )}

      {currentTranslation && (
        <div className="mt-2 space-y-1.5">
          <div className="flex items-baseline gap-2 text-[10px] text-slate-500">
            <span>
              {REGISTERS.find((r) => r.value === selectedRegister)?.description}
            </span>
            {ratioLabel && (
              <span className="ml-auto text-slate-600">{ratioLabel}</span>
            )}
          </div>
          <pre className="whitespace-pre-wrap font-sans text-slate-200 leading-relaxed text-[11.5px] border-l-2 border-slate-700/60 pl-2">
            {currentTranslation.text}
          </pre>
        </div>
      )}
    </div>
  );
}
