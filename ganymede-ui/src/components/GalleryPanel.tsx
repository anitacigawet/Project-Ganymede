'use client';

import React, { useState, useEffect } from 'react';
import { Database, Beaker, Activity } from 'lucide-react';

const EXHIBITS = [
  { title: "Exhibit 01: Geopolitical Encirclement", desc: "Modeling resource denial and border pressure." },
  { title: "Exhibit 02: Healthcare Resource Collapse", desc: "Pandemic-induced triage and cascading failure." },
  { title: "Exhibit 03: Hostile Corporate Takeover", desc: "Capital mobilization against community defense." },
  { title: "Exhibit 04: Algorithmic Market Squeeze", desc: "Automated trading traps in high-frequency markets." },
  { title: "Exhibit 05: Regulatory Capture", desc: "Lobbying influence warping competitive topology." },
  { title: "Exhibit 06: Infrastructure Cyber Attack", desc: "Cascading grid failure via hidden vulnerabilities." },
  { title: "Exhibit 07: Education Restructuring", desc: "Funding allocation vs. academic output balance." },
  { title: "Exhibit 08: Carbon Accord Defection", desc: "Game theory of climate treaties and free riders." },
  { title: "Exhibit 09: Wrongful Conviction Paradigm", desc: "Legal system optimization vs truth distortion." },
  { title: "Exhibit 10: AI Governance Crisis", desc: "Speed of capability vs safety alignment drag." }
];

interface GalleryPanelProps {
  currentExhibit: number;
  onSelect: (idx: number) => void;
}

export function GalleryPanel({ currentExhibit, onSelect }: GalleryPanelProps) {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(timer);
  }, [currentExhibit]);

  return (
    <div className="w-full h-full flex flex-col bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-800 shadow-2xl overflow-hidden font-mono text-sm">
      
      {/* Top Section: Project Overview */}
      <div className="p-6 border-b border-slate-800 bg-slate-950/60 shrink-0 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl" />
        <div className="flex items-center gap-3 mb-2 relative z-10">
          <Database className="text-indigo-400 w-5 h-5" />
          <h1 className="text-slate-100 font-semibold tracking-wide text-lg uppercase">Project Overview</h1>
        </div>
        <p className="text-slate-400 text-xs leading-relaxed relative z-10">
          Welcome to the 9D Strategic Museum. Select an exhibit below to observe how different multidimensional interactions warp the theoretical topology in real-time.
        </p>
      </div>

      {/* List of Strategic Scenario Exhibits */}
      <div className="flex-grow overflow-y-auto p-4 space-y-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {EXHIBITS.map((exhibit, idx) => {
          const isActive = idx === currentExhibit;
          return (
            <div key={idx} className="flex flex-col group">
              <button 
                onClick={() => onSelect(idx)}
                className={`w-full text-left p-4 rounded-lg border transition-all duration-300 flex items-center justify-between ${
                  isActive 
                    ? 'bg-indigo-900/30 border-indigo-500/50 text-indigo-200 shadow-[0_0_15px_rgba(99,102,241,0.15)]' 
                    : 'bg-slate-800/20 border-transparent text-slate-500 hover:bg-slate-800/60 hover:text-slate-300 hover:border-slate-700/50'
                }`}
              >
                <span className="font-semibold text-xs tracking-wider uppercase truncate pr-4">{exhibit.title}</span>
                {isActive && <Activity className="w-4 h-4 text-indigo-400 animate-pulse shrink-0" />}
              </button>
              
              {isActive && (
                <div className="mt-2 ml-4 mb-4 p-4 border-l-2 border-indigo-500/50 bg-slate-900/60 text-xs rounded-r-lg shadow-inner overflow-hidden relative">
                  <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-indigo-500/5 to-transparent pointer-events-none" />
                  
                  {loading ? (
                    <div className="flex items-center gap-3 text-emerald-400 animate-pulse font-semibold tracking-widest uppercase py-2">
                      <Beaker className="w-4 h-4" /> Data Loading...
                    </div>
                  ) : (
                    <div className="text-slate-300 animate-in fade-in slide-in-from-left-2 duration-500 relative z-10">
                      <p className="mb-2 font-semibold text-indigo-300/80 uppercase tracking-widest text-[10px]">Scenario Analysis:</p>
                      <p className="leading-relaxed">{exhibit.desc}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
