'use client';

/**
 * SettingsTray — the gear-button at bottom-right of the main layout.
 *
 * Replaces the legacy standalone floating elements that James flagged as
 * "clumped together" in the corners:
 *   - PREDICTIONS chip (top-right) → now a slot in the tray popup
 *   - AuthPill (bottom-left) → now a slot in the tray popup
 *   - Console "Cortex Clipboard" trigger (bottom-right) → now a slot in the
 *     tray popup, and the legacy floating Terminal button is suppressed via
 *     `hideFloatingTrigger` on DevOverlay
 *
 * Architecturally a status-tray pattern: the tray button stays in the corner
 * permanently, and clicking it surfaces the operator's small set of utility
 * controls without permanently consuming screen real estate.
 *
 * The Next.js dev error overlay ("X Issues" red badge) is NOT consolidated
 * here — it's a Next.js-internal HUD that surfaces React errors during
 * development and auto-hides in production builds. There's no public API
 * to embed its count in a custom popup, so it stays where Next.js places it.
 */

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Settings, Terminal, X, Sparkles } from 'lucide-react';
import { AuthPill } from './AuthPill';
import { PREDICTIONS } from '@/data/predictions';
import { GANYMEDE_DEMO_MODE } from '@/data/demoMode';

export interface SettingsTrayProps {
  /** Called when the Console slot is clicked. Parent should set its
   *  DevOverlay isOpen state to true. */
  onConsoleClick: () => void;
  /** Force the mobile positioning (top-right + downward popup) even at
   *  desktop widths. Set from page.tsx via the `?mobile=1` URL param so
   *  the whole mobile layout can be QA'd in a desktop Chrome. */
  forceMobile?: boolean;
}

export function SettingsTray({ onConsoleClick, forceMobile = false }: SettingsTrayProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  // Click-outside closes the popup. Mirrors the AuthPill pattern.
  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [open]);

  const pendingPredictions = PREDICTIONS.filter((p) => p.status === 'pending').length;

  return (
    // Gear position: top-right on narrow screens (avoids overlapping the bottom
    // nav — an overlap where the gear covered the right side of the CANVAS/OPTICS
    // buttons and swallowed their taps), bottom-right on desktop where the nav
    // is a small floating chip on the LEFT and doesn't compete. The popup flips
    // direction to match (opens down from the top position, up from bottom).
    <div
      ref={rootRef}
      className={[
        'absolute right-6 z-50 font-mono text-xs',
        forceMobile ? 'top-6' : 'top-6 lg:top-auto lg:bottom-6',
      ].join(' ')}
    >
      {/* Popup — opens down on mobile (gear is at top), upward on desktop. */}
      {open && (
        <div
          className={[
            'absolute right-0 w-72 rounded-xl border border-slate-700/60 bg-slate-950/95 backdrop-blur-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] p-3',
            forceMobile ? 'top-full mt-3' : 'top-full mt-3 lg:top-auto lg:mt-0 lg:bottom-full lg:mb-3',
          ].join(' ')}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-3 px-1">
            <span className="text-[10px] uppercase tracking-widest text-slate-500">
              Status &amp; Tools
            </span>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-slate-500 hover:text-slate-200 transition-colors"
              title="Close"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Console slot — opens the Cortex Clipboard / DevOverlay. */}
          <button
            type="button"
            onClick={() => {
              onConsoleClick();
              setOpen(false);
            }}
            className="w-full mb-2 flex items-center gap-3 px-3 py-2.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800/70 hover:border-indigo-700/50 transition-colors group"
          >
            <Terminal className="w-4 h-4 text-indigo-400 group-hover:text-indigo-300" />
            <div className="flex flex-col items-start">
              <span className="text-[11px] font-semibold text-slate-200 group-hover:text-slate-100">
                Cortex Clipboard
              </span>
              <span className="text-[9.5px] text-slate-500">
                Open the GSS prompt panel
              </span>
            </div>
          </button>

          {/* Predictions slot — Link to /predictions, shows pending count. */}
          <Link
            href="/predictions"
            onClick={() => setOpen(false)}
            className="w-full mb-2 flex items-center gap-3 px-3 py-2.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800/70 hover:border-amber-700/50 transition-colors group"
          >
            <Sparkles className="w-4 h-4 text-amber-400 group-hover:text-amber-300" />
            <div className="flex flex-col items-start flex-1">
              <span className="text-[11px] font-semibold text-slate-200 group-hover:text-slate-100">
                Predictions
              </span>
              <span className="text-[9.5px] text-slate-500">
                Pre-registered prediction ledger
              </span>
            </div>
            {pendingPredictions > 0 && (
              <span className="ml-1 px-1.5 py-0.5 rounded bg-amber-950/60 border border-amber-700/60 text-amber-300 text-[10px]">
                {pendingPredictions}
              </span>
            )}
          </Link>

          {/* Auth slot — AuthPill embedded inline; its dropdown opens upward. */}
          {GANYMEDE_DEMO_MODE ? (
            <div className="rounded-lg border border-cyan-900/60 bg-cyan-950/20 px-3 py-2.5 text-[10px] leading-relaxed text-cyan-100/80">
              Showroom mode uses fixed fictional data. External accounts and
              model services are disconnected.
            </div>
          ) : (
            <div className="px-1 pt-1">
              <span className="text-[9.5px] text-slate-500 uppercase tracking-widest mb-1.5 block">
                NotebookLM Auth
              </span>
              <AuthPill embedded />
            </div>
          )}
        </div>
      )}

      {/* Gear button — always visible. */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`p-4 backdrop-blur-xl border rounded-full shadow-2xl transition-all ${
          open
            ? 'bg-indigo-950/70 border-indigo-600/60 text-indigo-300'
            : 'bg-slate-900/80 hover:bg-slate-800 border-slate-700/50 text-indigo-400 hover:text-indigo-300'
        }`}
        title="Settings &amp; tools"
      >
        <Settings className="w-6 h-6" />
      </button>
    </div>
  );
}
