'use client';

/**
 * Bridge notebook management page (P1-04).
 *
 * Auto-provisioned Bridge notebooks accumulate as the orchestrator runs
 * /iterate and /bicameral-loop calls. Per the 2026-06-06 operator
 * decision (Option C — operator-managed with categorized suggestions),
 * the operator handles deletion explicitly via this page; the backend
 * surfaces categorization heuristics + per-row delete buttons.
 *
 * Reads from `GET /api/v2/bridge/notebooks` via the
 * BridgeNotebookManager component. No SSR data fetching — the component
 * fetches on mount + on refresh button click.
 */

import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

import { BridgeNotebookManager } from '@/components/BridgeNotebookManager';

export default function BridgeNotebooksPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-4xl">
        <div className="border-b border-slate-800/50 p-4">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Ganymede
          </Link>
        </div>
        <BridgeNotebookManager />
      </div>
    </main>
  );
}
