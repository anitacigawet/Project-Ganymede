'use client';

import React, { useState } from 'react';
import { Terminal, Send, Cpu, ShieldAlert, Sparkles } from 'lucide-react';

export function AnalystStream() {
  const [input, setInput] = useState('');
  
  // Dummy conversation for the prototype
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'system',
      content: '9D-Chess Umpire initialized. Secure authentication verified. Ready for strategic input.',
      timestamp: '00:00:00',
    },
    {
      id: 2,
      role: 'user',
      content: 'I am planning to launch a hostile takeover of a mid-sized healthcare tech firm. I have enough capital to corner the board, but their CEO has strong community ties.',
      timestamp: '00:01:23',
    },
    {
      id: 3,
      role: 'assistant',
      content: 'Analyzing scenario topology...\n\nVisible Dimension (Economic): You possess overwhelming capital advantage. This is a standard 2D play.\n\nHidden Dimensions (Social & Political): The target CEO\'s community ties represent a deep gravity well. If you force an economic buyout, the CEO will leverage the Social dimension to trigger Political scrutiny (local legislature, antitrust media backlash). \n\nStrategic Output: You are currently blind to the Social-Political cross-bleed. Your capital advantage will be absorbed by legal attrition. You are stepping into an SDS (Set of Disadvantageous States).',
      timestamp: '00:01:45',
    }
  ]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const newMsg = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })
    };
    
    setMessages([...messages, newMsg]);
    setInput('');
    
    // Simulate thinking response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'system',
        content: 'Simulation engine processing new variables. Calculating multi-dimensional bleed...',
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })
      }]);
    }, 1000);
  };

  return (
    <div className="w-full h-full flex flex-col bg-slate-900 rounded-xl border border-slate-800 shadow-xl overflow-hidden font-mono text-sm">
      
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-950 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Terminal className="text-emerald-400 w-5 h-5" />
          <h1 className="text-slate-100 font-semibold tracking-wide">The Analyst</h1>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="flex items-center gap-1"><Cpu size={12}/> Kernel: Active</span>
        </div>
      </div>

      {/* Chat Stream */}
      <div className="flex-grow p-4 overflow-y-auto space-y-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <span className="text-[10px] text-slate-500 mb-1 tracking-wider">{msg.timestamp} | {msg.role.toUpperCase()}</span>
            <div className={`p-4 rounded-lg max-w-[90%] ${
              msg.role === 'user' 
                ? 'bg-indigo-900/30 border border-indigo-500/30 text-indigo-100' 
                : msg.role === 'system'
                  ? 'bg-slate-950 border border-slate-800 text-slate-400 text-xs italic'
                  : 'bg-slate-800/50 border border-slate-700 text-slate-300'
            }`}>
              {msg.role === 'assistant' && <ShieldAlert className="w-4 h-4 text-red-400 mb-2 inline-block mr-2" />}
              {msg.content.split('\n').map((line, i) => (
                <span key={i} className="block mb-2 last:mb-0">{line}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-slate-950 border-t border-slate-800">
        <form onSubmit={handleSend} className="relative flex items-center">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Input strategic scenario..."
            className="w-full bg-slate-900 border border-slate-700 rounded-md py-3 pl-4 pr-12 text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 transition-all"
          />
          <button 
            type="submit" 
            className="absolute right-2 p-2 bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 rounded transition-colors"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
