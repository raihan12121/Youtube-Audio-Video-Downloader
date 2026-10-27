import React, { useState } from 'react';
import {
  Layers,
  Clipboard,
  Trash2,
  Download,
  Video,
  Music,
  FolderPlus
} from 'lucide-react';
import { sanitizeFilename } from '../utils/formatters';

export default function BulkTab({
  settings,
  onAddBatchDownloads,
  showToast
}) {
  const [text, setText] = useState('');
  const [mode, setMode] = useState('video');
  const [quality, setQuality] = useState('Best Available');
  const [subfolder, setSubfolder] = useState('');

  const parseUrls = () => {
    return text
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter((l) => l && (l.includes('youtube.com') || l.includes('youtu.be') || l.startsWith('http')));
  };

  const urls = parseUrls();

  const handlePaste = async () => {
    try {
      const cb = await navigator.clipboard.readText();
      if (cb) {
        setText((prev) => (prev ? `${prev}\n${cb.trim()}` : cb.trim()));
      }
    } catch (e) {
      showToast({ type: 'error', message: 'Could not access clipboard' });
    }
  };

  const handleClear = () => {
    setText('');
  };

  const handleQueueAll = () => {
    if (!urls.length) {
      showToast({ type: 'error', message: 'Please enter valid YouTube URLs' });
      return;
    }

    const subfolderName = subfolder.trim() ? sanitizeFilename(subfolder.trim()) : null;

    const tasks = urls.map((url, idx) => ({
      id: Date.now().toString() + Math.random().toString(36).substring(2, 7) + idx,
      url,
      title: `Bulk Item #${idx + 1}`,
      channel: '',
      thumbnail: '',
      duration: 0,
      mode,
      quality: mode === 'audio' ? '320 kbps' : quality,
      container: mode === 'audio' ? 'mp3' : 'mp4',
      outputDir: settings?.downloadDir,
      subfolder: subfolderName,
      embedThumbnail: true,
      embedMetadata: true,
    }));

    onAddBatchDownloads(tasks);
    setText('');
    showToast({
      type: 'success',
      message: `Queued ${tasks.length} URLs for batch download!`
    });
  };

  return (
    <div className="h-full flex flex-col p-6 space-y-4 overflow-hidden">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <span>Multi-URL Bulk Downloader</span>
          <Layers className="w-5 h-5 text-indigo-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Paste any number of individual YouTube links (one per line) to download in batch simultaneously.
        </p>
      </div>

      {/* Preset Toolbar */}
      <div className="p-3.5 rounded-xl bg-[#121824] border border-white/5 shadow-md flex flex-wrap items-center justify-between gap-4 text-xs shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex bg-black/40 rounded-lg p-0.5 border border-white/5">
            <button
              onClick={() => setMode('video')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                mode === 'video'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Video className="w-3.5 h-3.5" />
              <span>Video</span>
            </button>
            <button
              onClick={() => setMode('audio')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                mode === 'audio'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Music className="w-3.5 h-3.5" />
              <span>Audio MP3</span>
            </button>
          </div>

          {mode === 'video' && (
            <select
              value={quality}
              onChange={(e) => setQuality(e.target.value)}
              className="bg-[#0a0e17] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
            >
              <option value="Best Available">Best Available</option>
              <option value="1080p (Full HD)">1080p (Full HD)</option>
              <option value="720p (HD)">720p (HD)</option>
              <option value="480p">480p</option>
              <option value="360p">360p</option>
            </select>
          )}

          <div className="flex items-center gap-1.5">
            <FolderPlus className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Optional subfolder name..."
              value={subfolder}
              onChange={(e) => setSubfolder(e.target.value)}
              className="bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none w-48"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handlePaste}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/5 transition-colors"
          >
            <Clipboard className="w-3.5 h-3.5" />
            <span>Paste Clipboard</span>
          </button>

          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/5 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Textarea Area */}
      <div className="flex-1 bg-[#121824] border border-white/5 rounded-xl p-4 shadow-lg flex flex-col min-h-0">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span>Enter or paste YouTube URLs (one URL per line):</span>
          <span className="font-semibold text-blue-400">
            {urls.length} valid links detected
          </span>
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={`https://www.youtube.com/watch?v=...\nhttps://youtu.be/...\nhttps://www.youtube.com/shorts/...`}
          className="flex-1 w-full bg-[#0a0e17] border border-white/10 rounded-lg p-3 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50 resize-none leading-relaxed"
        />
      </div>

      {/* Submit Button */}
      <button
        onClick={handleQueueAll}
        disabled={urls.length === 0}
        className="w-full py-3.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-2 transition-all disabled:opacity-40 shrink-0"
      >
        <Download className="w-4 h-4" />
        <span>Add All URLs to Download Queue ({urls.length})</span>
      </button>
    </div>
  );
}
