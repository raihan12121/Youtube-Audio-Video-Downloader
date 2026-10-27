import React, { useEffect } from 'react';
import { X, Play, Music, Video as VideoIcon } from 'lucide-react';

export default function MediaPlayerModal({ media, onClose }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!media) return null;

  const isAudio = media.mode === 'audio' || (media.filePath && (media.filePath.endsWith('.mp3') || media.filePath.endsWith('.m4a') || media.filePath.endsWith('.wav') || media.filePath.endsWith('.flac')));
  const mediaSrc = `file://${media.filePath.replace(/\\/g, '/')}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-6 animate-in fade-in duration-200">
      <div className="bg-[#121824] border border-white/10 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-[#0d121c]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
              {isAudio ? <Music className="w-4 h-4" /> : <VideoIcon className="w-4 h-4" />}
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100 line-clamp-1 max-w-lg">
                {media.title || 'Media Player'}
              </h3>
              <p className="text-[11px] text-slate-400">
                {media.channel ? `${media.channel} • ` : ''}{media.format?.toUpperCase() || ''}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Media Container */}
        <div className="p-6 flex flex-col items-center justify-center bg-black/40 min-h-[300px]">
          {isAudio ? (
            <div className="w-full flex flex-col items-center justify-center gap-6 py-6">
              {media.thumbnail ? (
                <img
                  src={media.thumbnail}
                  alt={media.title}
                  className="w-48 h-48 rounded-xl object-cover shadow-xl border border-white/10"
                />
              ) : (
                <div className="w-40 h-40 rounded-xl bg-gradient-to-br from-indigo-900 to-purple-900 flex items-center justify-center shadow-xl border border-white/10">
                  <Music className="w-16 h-16 text-indigo-300" />
                </div>
              )}

              <audio
                controls
                autoPlay
                src={mediaSrc}
                className="w-full max-w-md accent-blue-500"
              >
                Your browser does not support the audio element.
              </audio>
            </div>
          ) : (
            <div className="w-full aspect-video bg-black rounded-xl overflow-hidden flex items-center justify-center shadow-inner">
              <video
                controls
                autoPlay
                src={mediaSrc}
                className="w-full h-full object-contain"
              >
                Your browser does not support the video tag.
              </video>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 bg-[#0d121c] border-t border-white/10 flex justify-end gap-3 text-xs">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/15 text-slate-200 transition-colors"
          >
            Close Player
          </button>
        </div>
      </div>
    </div>
  );
}
