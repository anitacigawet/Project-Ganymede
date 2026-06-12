'use client';

import React, { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { GravityWell } from './GravityWell';
import { Radio, Activity, ShieldCheck, Zap } from 'lucide-react';
import { GSSState } from '../types/ganymede';

interface PhysicsCanvasProps {
  scanTrigger: number;
  gssConfig?: GSSState | null;
}

export function PhysicsCanvas({ scanTrigger, gssConfig }: PhysicsCanvasProps) {
  const [baseColor, setBaseColor] = useState<string>('#3b82f6');
  
  const [localDrawRate, setLocalDrawRate] = useState<number>(0);
  const [localMitigation, setLocalMitigation] = useState<number>(0);

  useEffect(() => {
    if (gssConfig) {
      const sink = gssConfig.topological_entities.find(e => e.type === 'Industrial_Sink');
      setLocalDrawRate(sink?.draw_rate || 0);
      setLocalMitigation(gssConfig.legislative_framework.mitigation_coefficient);
    }
  }, [gssConfig]);

  useEffect(() => {
    if (scanTrigger > 0) {
      const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f43f5e', '#f59e0b', '#06b6d4'];
      const nextColor = colors[scanTrigger % colors.length];
      setBaseColor(nextColor);
    }
  }, [scanTrigger]);

  const activeDimensions = gssConfig ? 9 : 0;
  const isFractured = gssConfig && (-(localDrawRate / 180000) / 0.8 * (1 - localMitigation) < gssConfig.physics_logic.failure_threshold);

  // Derived labels — read from the loaded GSS so every example renders its
  // own identity instead of the legacy hard-coded Hualapai placeholders.
  const primarySink = gssConfig?.topological_entities.find(e => e.type === 'Industrial_Sink');
  const primarySinkLabel = (primarySink?.node_id ?? 'Industrial').toUpperCase().replace(/[-_]/g, ' ');
  const billLabel = gssConfig?.legislative_framework.bill_id ?? 'NONE';
  const drawUnit = gssConfig?.environmental_baseline.unit?.includes('/yr') ? 'k af/yr'
    : gssConfig?.environmental_baseline.unit?.includes('sec') ? 'k order/sec'
    : 'k';
  const drawRateDisplay = `${(localDrawRate / 1000).toFixed(0)} ${drawUnit}`;

  return (
    <div className="relative w-full h-full bg-[#020617] rounded-xl overflow-hidden border border-slate-800 shadow-2xl flex flex-col font-mono">
      
      {/* Scanning HUD Overlay (Animated Lines) */}
      <div className="absolute inset-0 pointer-events-none z-20">
        <div className="w-full h-full opacity-[0.03]" 
             style={{ backgroundImage: 'linear-gradient(0deg, transparent 0%, #fff 50%, transparent 100%)', backgroundSize: '100% 4px' }} />
        <div className="absolute top-0 left-0 w-full h-1 bg-indigo-500/10 animate-[scan_4s_linear_infinite]" />
      </div>

      {/* Header: System Readout. pr-44 reserves clearance on the right so the
          GRID STATUS / SENSOR DENSITY readouts don't slide under the floating
          PREDICTIONS chip pinned at top-right of the page. */}
      <div className="absolute top-0 left-0 right-0 z-30 flex justify-between items-center p-5 pr-44 bg-slate-950/60 backdrop-blur-xl border-b border-white/5">
        <div className="flex items-center gap-3">
          <Radio className="w-5 h-5 text-indigo-400" style={{ color: baseColor }} />
          <h2 className="text-slate-100 text-sm tracking-[0.2em] font-bold uppercase">GSS Strategic Engine</h2>
        </div>
        
        <div className="flex gap-8 text-[10px]">
          <div className="flex flex-col items-end">
            <span className="text-slate-500 uppercase tracking-widest mb-1">Grid Status</span>
            <span className={`font-bold transition-colors duration-500 ${isFractured ? 'text-red-500 animate-pulse' : 'text-emerald-500'}`}>
              {isFractured ? 'TOPOLOGICAL FAILURE' : 'STABLE'}
            </span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-slate-500 uppercase tracking-widest mb-1">Sensor Density</span>
            <span className="font-bold text-slate-200">{activeDimensions}/9 Mapped</span>
          </div>
        </div>
      </div>

      {/* Body — 3D canvas ONLY when a GSS is loaded. Otherwise the body
          stays empty (no deformation-plane grid, no stars) and just shows
          the "Awaiting Strategic Signal" placeholder. Frees up the canvas
          area for non-3D content when no scenario is loaded yet. */}
      {gssConfig ? (
        <div className="flex-grow w-full relative">
          <Canvas camera={{ position: [0, 18, 28], fov: 40 }}>
            <ambientLight intensity={0.4} />
            <pointLight position={[0, -10, 0]} intensity={3} color={baseColor} />
            <Stars radius={100} depth={50} count={6000} factor={4} saturation={0} fade speed={1} />

            <GravityWell
              config={gssConfig}
              overrides={{ drawRate: localDrawRate, mitigation: localMitigation }}
              scanColor={baseColor}
            />

            <OrbitControls
              enablePan={false}
              minPolarAngle={Math.PI / 6}
              maxPolarAngle={Math.PI / 2.1}
              minDistance={15}
              maxDistance={60}
            />
          </Canvas>
        </div>
      ) : (
        <div className="flex-grow w-full relative flex items-center justify-center pt-16">
          <div className="text-slate-700 text-xs tracking-[0.4em] uppercase animate-pulse text-center">
            Awaiting Strategic Signal...
            <div className="text-[10px] text-slate-800 mt-2 tracking-normal normal-case">
              Double-click an example chip on the left, or run a scenario.
            </div>
          </div>
        </div>
      )}

      {/* Unified Command Panel (Left Aligned to avoid Sidebar) — only when GSS loaded */}
      {gssConfig && (
        <div className="absolute bottom-6 left-6 z-30 flex flex-col gap-4">
          
          {/* Metadata Readout */}
          <div className="w-[420px] bg-slate-950/80 backdrop-blur-2xl border border-white/10 rounded-lg p-5 shadow-2xl animate-in slide-in-from-left-4 duration-700">
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-indigo-400 text-[10px] font-bold uppercase tracking-[0.2em]">{gssConfig.metadata.classification}</span>
                <span className="text-slate-600 text-[9px]">{gssConfig.metadata.timestamp}</span>
              </div>
              
              <div className="grid grid-cols-2 gap-6">
                {/* Sliders Integrated Here */}
                <div className="flex flex-col gap-4 border-r border-white/5 pr-4">
                   <div className="flex flex-col gap-2">
                    <div className="flex justify-between text-[9px] uppercase tracking-tighter text-slate-500">
                      <span>{primarySinkLabel} Draw</span>
                      <span className="text-slate-300">{drawRateDisplay}</span>
                    </div>
                    <input
                      type="range" min="0" max="2000000" step="10000"
                      value={localDrawRate}
                      onChange={(e) => setLocalDrawRate(Number(e.target.value))}
                      className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between text-[9px] uppercase tracking-tighter text-slate-500">
                      <span>{billLabel} Mitigation</span>
                      <span className="text-slate-300">{(localMitigation * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range" min="0" max="1" step="0.01"
                      value={localMitigation}
                      onChange={(e) => setLocalMitigation(Number(e.target.value))}
                      className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-3 justify-center">
                  <div className="flex flex-col">
                    <span className="text-[9px] text-slate-500 uppercase tracking-widest">Ambient Depth</span>
                    <span className="text-xs text-red-400 font-bold">{gssConfig.environmental_baseline.ambient_depletion} {gssConfig.environmental_baseline.unit}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[9px] text-slate-500 uppercase tracking-widest">Logic Model</span>
                    <span className="text-[10px] text-indigo-300 font-bold">{gssConfig.physics_logic.gravity_well_depth_formula}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      )}

      <style jsx global>{`
        @keyframes scan {
          from { transform: translateY(0); }
          to { transform: translateY(600px); }
        }
      `}</style>
    </div>
  );
}
