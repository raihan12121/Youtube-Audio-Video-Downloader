import React from 'react';
import {
  Video,
  ListVideo,
  Layers,
  DownloadCloud,
  Library,
  Settings,
  CheckCircle2,
  AlertCircle,
  HardDrive
} from 'lucide-react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  queueCount = 0,
  systemStatus = null,
  onOpenFolder
}) {
  const navItems = [
    { id: 'single', label: 'Single Media', icon: Video },
    { id: 'playlist', label: 'Playlist & Channel', icon: ListVideo },
    { id: 'bulk', label: 'Bulk URLs', icon: Layers },
    { id: 'queue', label: 'Active Queue', icon: DownloadCloud, badge: queueCount },
    { id: 'library', label: 'Library & History', icon: Library },
    { id: 'settings', label: 'Settings & Tools', icon: Settings },
  ];

  const ffmpegReady = systemStatus?.ffmpeg?.available;

  return (
    <div className="w-64 bg-[#0d121c] border-r border-white/5 flex flex-col justify-between p-3 select-none">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          Navigation
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm shadow-blue-500/10'
                  : 'text-slate-300 hover:text-white hover:bg-white/5 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>

              {Boolean(item.badge && item.badge > 0) && (
                <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-blue-600 text-white animate-pulse">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Engine Health & Quick Open Folder */}
      <div className="space-y-2 pt-4 border-t border-white/5">
        <button
          onClick={onOpenFolder}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-colors border border-white/5"
        >
          <HardDrive className="w-3.5 h-3.5 text-slate-400" />
          <span>Open Downloads Folder</span>
        </button>

        <div className="px-3 py-2 rounded-lg bg-black/30 border border-white/5 space-y-1.5 text-[11px]">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">FFmpeg Engine</span>
            <div className="flex items-center gap-1.5">
              {ffmpegReady ? (
                <>
                  <span className="text-emerald-400 font-medium">Ready</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                </>
              ) : (
                <>
                  <span className="text-red-400 font-medium">Missing</span>
                  <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                </>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">yt-dlp Core</span>
            <span className="text-slate-200 font-mono text-[10px]">
              {systemStatus?.ytdlp?.version ? `v${systemStatus.ytdlp.version}` : 'Active'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
