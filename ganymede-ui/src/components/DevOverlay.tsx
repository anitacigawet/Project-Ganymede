'use client';

/**
 * DevOverlay — the Cortex Clipboard.
 *
 * Two-stage manual handoff between the 9D-Chess Engine and the GSS 3D viz:
 *   1. Strategic Pre-Processor — Gemini-Pro-ready prompt block; user copies
 *      this and runs it against Gemini Pro manually (Hard Guardrail #4).
 *   2. Simulation Listener — user pastes the GSS JSON Gemini returned;
 *      "Apply To Topology" deserialises and hands off to PhysicsCanvas.
 *
 * Controlled component: parent owns ``promptBlock`` and ``isOpen``. The
 * RunnerPanel fills the prompt block and opens the overlay in one step
 * via the parent's state, then the user copies → pastes → applies.
 */

import React, { useState } from 'react';
import { Terminal, Copy, X, Play } from 'lucide-react';

import { GSSState } from '../types/ganymede';
import { isGSSState } from '../lib/gss';

const DEFAULT_PROMPT_BLOCK = `# SYSTEM DIRECTIVE
You are the Ganymede Compiler. Your task is to visualize and model the strategic landscape based on the following factual 9D analysis and the suggested visualization parameters from the Umpire.

# INSTRUCTION
Based on the specific strategy provided by the Umpire, provide the final simulation parameters in our standardized GSS (Ganymede Strategic Schema) JSON format.

# OUTPUT FORMAT (Strict JSON Only)
{
  "metadata": { "compiler_version": "G-3.0", "classification": "STRATEGIC_SITREP", "timestamp": "..." },
  "environmental_baseline": { "ambient_depletion": 2.4, "unit": "ft/yr" },
  "legislative_framework": { "bill_id": "...", "mitigation_coefficient": 0.15, "status": "Active" },
  "topological_entities": [
    { "node_id": "...", "type": "Industrial_Sink", "draw_rate": 400000, "luminosity": 0.95, "coordinates": { "x": 0, "y": 0, "z": 0 } }
  ],
  "physics_logic": { "gravity_well_depth_formula": "Inverted_Radial_Decay", "failure_threshold": -4.5 }
}`;

const DEFAULT_JSON_PLACEHOLDER = `{
  "metadata": { "compiler_version": "G-3.0", "classification": "STRATEGIC_SITREP", "timestamp": "..." },
  "environmental_baseline": { "ambient_depletion": 2.4, "unit": "ft/yr" },
  "legislative_framework": { "bill_id": "...", "mitigation_coefficient": 0.15, "status": "Active" },
  "topological_entities": [ ... ],
  "physics_logic": { "gravity_well_depth_formula": "Inverted_Radial_Decay", "failure_threshold": -4.5 }
}`;

interface DevOverlayProps {
  onApplyGSS: (config: GSSState) => void;
  /** Controlled open state. Parent sets true when handing off from RunnerPanel. */
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  /** Controlled prompt block — Runner fills this when it has an Engine resolution. */
  promptBlock?: string;
  /** When true, skip rendering the standalone floating Terminal button at
   *  bottom-right. The SettingsTray now owns that corner and triggers
   *  ``onOpenChange(true)`` itself, so the legacy floating trigger would
   *  duplicate the button. */
  hideFloatingTrigger?: boolean;
}

export function DevOverlay({ onApplyGSS, isOpen, onOpenChange, promptBlock, hideFloatingTrigger }: DevOverlayProps) {
  const [jsonInput, setJsonInput] = useState('');

  const displayedPromptBlock = promptBlock && promptBlock.length > 0 ? promptBlock : DEFAULT_PROMPT_BLOCK;

  const handleCopy = () => {
    navigator.clipboard.writeText(displayedPromptBlock);
  };

  const handleApply = () => {
    try {
      const parsed: unknown = JSON.parse(jsonInput);
      if (isGSSState(parsed)) {
        onApplyGSS(parsed);
      } else {
        alert('JSON must conform to the Ganymede Strategic Schema (GSS).');
      }
    } catch {
      alert('Invalid JSON formatting. Ensure it is strict JSON.');
    }
  };

  if (!isOpen) {
    if (hideFloatingTrigger) return null;
    return (
      <button
        onClick={() => onOpenChange(true)}
        className="absolute bottom-6 right-6 z-50 p-4 bg-slate-900/80 hover:bg-slate-800 backdrop-blur-xl border border-slate-700/50 rounded-full text-indigo-400 hover:text-indigo-300 shadow-2xl transition-all"
        title="Open Cortex Clipboard"
      >
        <Terminal className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div className="absolute right-0 top-0 bottom-0 w-[450px] bg-slate-950/95 backdrop-blur-3xl border-l border-slate-800 z-50 shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col font-mono text-sm animate-in slide-in-from-right duration-300">
      <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
        <div className="flex items-center gap-2 text-indigo-400">
          <Terminal className="w-4 h-4" />
          <span className="font-bold tracking-wider uppercase text-xs">Cortex Clipboard</span>
        </div>
        <button onClick={() => onOpenChange(false)} className="text-slate-500 hover:text-slate-300 transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-8 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">

        {/* Output from Backend */}
        <div className="space-y-3">
          <div className="flex justify-between items-end">
            <div>
              <h3 className="text-xs text-slate-400 uppercase tracking-widest font-semibold">1. Schema Reference</h3>
              <p className="text-[10px] text-slate-500 mt-1">
                Generic GSS scaffold for reference. The Live Runner has its own
                "Copy Engine Output" button — you drive Gemini freely from there.
              </p>
            </div>
            <button onClick={handleCopy} className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-900/30 hover:bg-indigo-900/50 border border-indigo-500/30 rounded text-indigo-300 hover:text-indigo-200 transition-colors text-xs">
              <Copy className="w-3 h-3" /> Copy Block
            </button>
          </div>
          <textarea
            readOnly
            value={displayedPromptBlock}
            className="w-full h-64 bg-slate-900 border border-slate-800 rounded-md p-3 text-slate-300 text-xs resize-none focus:outline-none shadow-inner"
          />
        </div>

        <div className="h-px w-full bg-gradient-to-r from-transparent via-slate-800 to-transparent" />

        {/* Input for Simulation */}
        <div className="space-y-3">
          <div>
            <h3 className="text-xs text-emerald-500 uppercase tracking-widest font-semibold">2. Simulation Listener</h3>
            <p className="text-[10px] text-slate-500 mt-1">Paste the GSS JSON output from Gemini Pro here.</p>
          </div>
          <textarea
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            placeholder={DEFAULT_JSON_PLACEHOLDER}
            className="w-full h-48 bg-slate-900 border border-slate-800 rounded-md p-3 text-emerald-400 text-xs resize-none focus:outline-none focus:border-emerald-500/50 shadow-inner"
          />
          <button
            onClick={handleApply}
            className="w-full py-3 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 rounded-md flex items-center justify-center gap-2 transition-colors uppercase tracking-widest text-xs font-bold"
          >
            <Play className="w-4 h-4" /> Apply To Topology
          </button>
        </div>
      </div>
    </div>
  );
}
