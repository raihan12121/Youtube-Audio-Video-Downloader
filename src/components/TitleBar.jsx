import React, { useState, useEffect } from 'react';
import { Minus, Square, Copy, X, Play } from 'lucide-react';

export default function TitleBar({ title = "YouTube Downloader Pro" }) {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.isMaximized().then(setIsMaximized);
    }
  }, []);

  const handleMinimize = () => {
    if (window.electronAPI) window.electronAPI.minimize();
  };

  const handleMaximize = async () => {
    if (window.electronAPI) {
      await window.electronAPI.maximize();
      const max = await window.electronAPI.isMaximized();
      setIsMaximized(max);
    }
  };

  const handleClose = () => {
    if (window.electronAPI) window.electronAPI.close();
  };

  return (
    <div className="h-10 bg-[#070a10] border-b border-white/5 flex items-center justify-between select-none titlebar-drag z-50 px-3">
      {/* App Brand */}
      <div className="flex items-center gap-2 titlebar-nodrag">
        <div className="w-5 h-5 rounded-md bg-red-600 flex items-center justify-center shadow-sm shadow-red-600/40">
          <Play className="w-3 h-3 fill-white text-white ml-0.5" />
        </div>
        <span className="text-xs font-semibold tracking-wide text-slate-200">
          {title}
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-slate-400 font-mono">
          v2.0
        </span>
      </div>

      {/* Center Drag Area */}
      <div className="flex-1 h-full titlebar-drag" />

      {/* Windows 11 Native Controls */}
      <div className="flex items-center titlebar-nodrag h-full -mr-3">
        <button
          onClick={handleMinimize}
          className="h-full px-4 text-slate-400 hover:text-white hover:bg-white/10 transition-colors flex items-center justify-center"
          title="Minimize"
        >
          <Minus className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={handleMaximize}
          className="h-full px-4 text-slate-400 hover:text-white hover:bg-white/10 transition-colors flex items-center justify-center"
          title={isMaximized ? "Restore" : "Maximize"}
        >
          {isMaximized ? (
            <Copy className="w-3 h-3 rotate-180" />
          ) : (
            <Square className="w-3 h-3" />
          )}
        </button>

        <button
          onClick={handleClose}
          className="h-full px-4 text-slate-400 hover:text-white hover:bg-[#e81123] transition-colors flex items-center justify-center"
          title="Close"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
