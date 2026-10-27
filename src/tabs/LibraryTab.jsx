import React, { useState } from 'react';
import {
  Library,
  Search,
  Trash2,
  Play,
  Folder,
  Music,
  Video,
  Clock,
  ExternalLink
} from 'lucide-react';
import { formatBytes, formatDuration } from '../utils/formatters';

export default function LibraryTab({
  history,
  onClearHistory,
  onDeleteHistoryItem,
  onPlayInApp,
  onOpenDefaultPlayer,
  onRevealFile,
  showToast
}) {
  const [filterMode, setFilterMode] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = history.filter((item) => {
    if (filterMode === 'video' && item.mode !== 'video') return false;
    if (filterMode === 'audio' && item.mode !== 'audio') return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.title?.toLowerCase().includes(q);
      const matchChannel = item.channel?.toLowerCase().includes(q);
      return matchTitle || matchChannel;
    }
    return true;
  });

  return (
    <div className="h-full flex flex-col p-6 space-y-4 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <span>Completed Downloads Library</span>
            <Library className="w-5 h-5 text-emerald-400" />
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Access, stream, and locate all previously downloaded videos and audio tracks.
          </p>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          {filtered.length} {filtered.length === 1 ? 'file' : 'files'}
        </span>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-3.5 rounded-xl bg-[#121824] border border-white/5 shadow-md flex items-center justify-between gap-4 text-xs shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex bg-black/40 rounded-lg p-0.5 border border-white/5">
            <button
              onClick={() => setFilterMode('all')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                filterMode === 'all'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              All Files
            </button>
            <button
              onClick={() => setFilterMode('video')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                filterMode === 'video'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Videos
            </button>
            <button
              onClick={() => setFilterMode('audio')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                filterMode === 'audio'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Audio
            </button>
          </div>

          <div className="relative">
            <input
              type="text"
              placeholder="Search downloads..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-56 bg-[#0a0e17] border border-white/10 rounded-lg pl-7 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
            />
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
          </div>
        </div>

        {history.length > 0 && (
          <button
            onClick={onClearHistory}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/5 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* History Grid / List */}
      <div className="flex-1 bg-[#121824] border border-white/5 rounded-xl p-4 shadow-lg overflow-y-auto space-y-2.5">
        {filtered.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-500">
            <Library className="w-12 h-12 stroke-1 mb-2 text-slate-600" />
            <p className="text-sm font-medium text-slate-400">
              No files in library
            </p>
            <p className="text-xs max-w-sm mt-1">
              Completed video and audio downloads will automatically appear here with quick playback and explorer actions.
            </p>
          </div>
        ) : (
          filtered.map((item) => {
            const isAudio = item.mode === 'audio';

            return (
              <div
                key={item.id}
                className="p-3 rounded-xl bg-[#0e141f] border border-white/5 hover:border-white/10 transition-all flex items-center justify-between gap-4"
              >
                {/* Left Thumbnail / Icon */}
                <div className="w-20 h-12 rounded-lg bg-black/40 overflow-hidden shrink-0 border border-white/5 relative">
                  {item.thumbnail ? (
                    <img
                      src={item.thumbnail}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      {isAudio ? (
                        <Music className="w-4 h-4 text-purple-400" />
                      ) : (
                        <Video className="w-4 h-4 text-blue-400" />
                      )}
                    </div>
                  )}

                  {item.duration > 0 && (
                    <span className="absolute bottom-1 right-1 px-1 rounded bg-black/80 text-[8px] font-mono text-white">
                      {formatDuration(item.duration)}
                    </span>
                  )}
                </div>

                {/* Details */}
                <div className="flex-1 min-w-0">
                  <h3 className="text-xs font-semibold text-slate-200 truncate">
                    {item.title}
                  </h3>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
                    {item.channel && <span className="truncate">{item.channel}</span>}
                    <span className="text-slate-600">•</span>
                    <span className="uppercase font-mono text-blue-400">
                      {item.format} {item.quality ? `(${item.quality})` : ''}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="font-mono">{formatBytes(item.fileSize)}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => onPlayInApp(item)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium shadow-sm transition-all"
                  >
                    <Play className="w-3 h-3 fill-white" />
                    <span>Play In-App</span>
                  </button>

                  <button
                    onClick={() => onOpenDefaultPlayer(item.filePath)}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
                    title="Open in default media player"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => onRevealFile(item.filePath)}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
                    title="Reveal in File Explorer"
                  >
                    <Folder className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => onDeleteHistoryItem(item.id)}
                    className="p-2 rounded-lg bg-white/5 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                    title="Remove from history"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
