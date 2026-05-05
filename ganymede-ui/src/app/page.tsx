'use client';

import { useState } from 'react';
import { GalleryPanel } from '@/components/GalleryPanel';
import { PhysicsCanvas } from '@/components/PhysicsCanvas';
import { DevOverlay } from '@/components/DevOverlay';
import { GSSState } from '@/types/ganymede';

export default function Home() {
  const [currentExhibit, setCurrentExhibit] = useState(0);
  const [scanTrigger, setScanTrigger] = useState(0);
  const [gssConfig, setGssConfig] = useState<GSSState | null>(null);

  const handleSelectExhibit = (index: number) => {
    if (index !== currentExhibit) {
      setCurrentExhibit(index);
      setScanTrigger(prev => prev + 1);
      setGssConfig(null); // Reset config on new exhibit
    }
  };

  const handleApplyGSS = (config: GSSState) => {
    setGssConfig(config);
  };

  return (
    <main className="flex h-screen w-full bg-[#030712] p-4 gap-4 overflow-hidden relative">
      {/* Dynamic Background Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#030712] to-[#030712] pointer-events-none" />

      {/* Left Panel: The Gallery (40%) */}
      <div className="w-[40%] h-full flex-shrink-0 z-10">
        <GalleryPanel currentExhibit={currentExhibit} onSelect={handleSelectExhibit} />
      </div>

      {/* Right Panel: The Physics Engine (60%) */}
      <div className="w-[60%] h-full flex-shrink-0 z-10">
        <PhysicsCanvas scanTrigger={scanTrigger} gssConfig={gssConfig} />
      </div>

      {/* Dev Overlay for Agent-Driven Workflow */}
      <DevOverlay onApplyGSS={handleApplyGSS} />
    </main>
  );
}
