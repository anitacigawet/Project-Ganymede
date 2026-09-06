'use client';

import { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, RefreshCw, TerminalSquare, XCircle } from 'lucide-react';
import { getBackendBaseUrl } from '@/lib/backend';

interface ProviderStatus {
  available: boolean;
  executable?: string | null;
  model?: string;
  provider?: string;
  research_tool?: string;
}

export interface AuthPillProps {
  embedded?: boolean;
}

export function AuthPill({ embedded = false }: AuthPillProps) {
  const [status, setStatus] = useState<ProviderStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${getBackendBaseUrl()}/api/v2/health`, {
        cache: 'no-store',
      });
      if (!response.ok) throw new Error(`Backend returned HTTP ${response.status}`);
      const payload = await response.json() as { provider: ProviderStatus };
      setStatus(payload.provider);
      setError(null);
    } catch (caught) {
      setStatus(null);
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const ready = status?.available === true;
  return (
    <div className={embedded ? 'w-full' : 'rounded-lg border border-slate-800 bg-slate-950/90 p-3'}>
      <div className="flex items-center gap-2">
        {ready ? (
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
        ) : error ? (
          <XCircle className="h-4 w-4 text-rose-400" />
        ) : (
          <TerminalSquare className="h-4 w-4 text-amber-400" />
        )}
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-semibold text-slate-200">
            {ready ? 'Claude CLI ready' : error ? 'Backend unavailable' : 'Claude CLI setup required'}
          </div>
          <div className="truncate text-[9.5px] text-slate-500">
            {ready
              ? `${status?.model ?? 'sonnet'} · WebSearch available for research`
              : error ?? 'Install Claude Code and run claude once to authenticate.'}
          </div>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          className="rounded p-1 text-slate-500 hover:text-slate-200"
          title="Refresh provider status"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </div>
  );
}
