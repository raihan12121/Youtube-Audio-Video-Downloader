import React, { useState, useEffect } from 'react';
import {
  Settings,
  Folder,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Save,
  Key,
  ShieldCheck,
  Cpu,
  Layers
} from 'lucide-react';

export default function SettingsTab({
  settings,
  systemStatus,
  onSaveSettings,
  onSelectFolder,
  showToast
}) {
  const [formData, setFormData] = useState(settings || {});

  useEffect(() => {
    if (settings) setFormData(settings);
  }, [settings]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    onSaveSettings(formData);
    showToast({ type: 'success', message: 'Preferences saved successfully!' });
  };

  const ffmpegOk = systemStatus?.ffmpeg?.available;
  const nodeOk = systemStatus?.nodejs?.available;
  const ytdlpOk = systemStatus?.ytdlp?.available;

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <span>Settings & System Diagnostics</span>
          <Settings className="w-5 h-5 text-slate-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure default formats, worker threads, paths, browser cookies, and verify system dependencies.
        </p>
      </div>

      {/* Diagnostics Card */}
      <div className="p-5 rounded-xl bg-[#121824] border border-white/5 space-y-4 shadow-lg">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-blue-400" />
          <span>Core Engine Health</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          {/* FFmpeg */}
          <div className="p-3 rounded-lg bg-[#0e141f] border border-white/5 flex items-start justify-between">
            <div>
              <p className="font-semibold text-slate-200">FFmpeg 9.0.1</p>
              <p className="text-[11px] text-slate-500 mt-0.5 truncate max-w-[180px]">
                {systemStatus?.ffmpeg?.path || 'Checking...'}
              </p>
            </div>
            {ffmpegOk ? (
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                Active
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-medium">
                Missing
              </span>
            )}
          </div>

          {/* Node.js */}
          <div className="p-3 rounded-lg bg-[#0e141f] border border-white/5 flex items-start justify-between">
            <div>
              <p className="font-semibold text-slate-200">Node.js Runtime</p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {systemStatus?.nodejs?.version || 'Challenge Solver'}
              </p>
            </div>
            {nodeOk ? (
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                Active
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                Optional
              </span>
            )}
          </div>

          {/* yt-dlp */}
          <div className="p-3 rounded-lg bg-[#0e141f] border border-white/5 flex items-start justify-between">
            <div>
              <p className="font-semibold text-slate-200">yt-dlp Extractor</p>
              <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
                {systemStatus?.ytdlp?.version ? `v${systemStatus.ytdlp.version}` : 'Active'}
              </p>
            </div>
            {ytdlpOk ? (
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                Active
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-medium">
                Missing
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Download Preferences */}
      <div className="p-5 rounded-xl bg-[#121824] border border-white/5 space-y-4 shadow-lg text-xs">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Folder className="w-4 h-4 text-emerald-400" />
          <span>Storage & Threading</span>
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-slate-400 mb-1.5">
              Default Download Destination
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value={formData.downloadDir || ''}
                className="flex-1 bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-2 text-slate-200 font-mono text-[11px]"
              />
              <button
                onClick={onSelectFolder}
                className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/5 font-medium transition-colors"
              >
                Browse...
              </button>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-slate-400">
                Max Concurrent Downloads
              </label>
              <span className="font-bold text-blue-400 font-mono">
                {formData.maxConcurrentDownloads || 3} threads
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="6"
              step="1"
              value={formData.maxConcurrentDownloads || 3}
              onChange={(e) => handleChange('maxConcurrentDownloads', parseInt(e.target.value))}
              className="w-full accent-blue-500 cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Media Defaults */}
      <div className="p-5 rounded-xl bg-[#121824] border border-white/5 space-y-4 shadow-lg text-xs">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Sliders className="w-4 h-4 text-purple-400" />
          <span>Format & Tagging Defaults</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-slate-400 mb-1.5">Default Video Quality</label>
            <select
              value={formData.defaultVideoResolution || 'Best Available'}
              onChange={(e) => handleChange('defaultVideoResolution', e.target.value)}
              className="w-full bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-2 text-slate-200 focus:outline-none"
            >
              <option value="Best Available">Best Available</option>
              <option value="2160p (4K)">2160p (4K)</option>
              <option value="1440p (2K)">1440p (2K)</option>
              <option value="1080p (Full HD)">1080p (Full HD)</option>
              <option value="720p (HD)">720p (HD)</option>
              <option value="480p">480p</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1.5">Default Audio Format</label>
            <select
              value={formData.defaultAudioFormat || 'mp3'}
              onChange={(e) => handleChange('defaultAudioFormat', e.target.value)}
              className="w-full bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-2 text-slate-200 focus:outline-none uppercase"
            >
              <option value="mp3">MP3</option>
              <option value="m4a">M4A</option>
              <option value="wav">WAV</option>
              <option value="flac">FLAC</option>
              <option value="opus">OPUS</option>
            </select>
          </div>
        </div>

        <div className="space-y-2 pt-2 text-slate-300">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.embedThumbnail ?? true}
              onChange={(e) => handleChange('embedThumbnail', e.target.checked)}
              className="rounded border-white/20 bg-black/40 text-blue-600 focus:ring-0"
            />
            <span>Automatically embed album art & video thumbnail</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.embedMetadata ?? true}
              onChange={(e) => handleChange('embedMetadata', e.target.checked)}
              className="rounded border-white/20 bg-black/40 text-blue-600 focus:ring-0"
            />
            <span>Automatically embed artist, album, and track metadata</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.organizePlaylistsInSubfolders ?? true}
              onChange={(e) => handleChange('organizePlaylistsInSubfolders', e.target.checked)}
              className="rounded border-white/20 bg-black/40 text-blue-600 focus:ring-0"
            />
            <span>Create named subfolders for playlists and channels by default</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.numberPlaylistItems ?? true}
              onChange={(e) => handleChange('numberPlaylistItems', e.target.checked)}
              className="rounded border-white/20 bg-black/40 text-blue-600 focus:ring-0"
            />
            <span>Prepend sequential index numbers (01 -, 02 -) to playlist items</span>
          </label>
        </div>
      </div>

      {/* Authentication / YouTube Cookies */}
      <div className="p-5 rounded-xl bg-[#121824] border border-white/5 space-y-4 shadow-lg text-xs">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Key className="w-4 h-4 text-amber-400" />
          <span>YouTube Authentication & Cookies</span>
        </h2>
        <p className="text-[11px] text-slate-400">
          Required only if you wish to download age-restricted, private, or channel-member-only videos.
        </p>

        <div>
          <label className="block text-slate-400 mb-1.5">Load Cookies from Browser</label>
          <select
            value={formData.browserCookies || 'none'}
            onChange={(e) => handleChange('browserCookies', e.target.value)}
            className="w-full max-w-sm bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-2 text-slate-200 focus:outline-none capitalize"
          >
            <option value="none">None (Public downloads)</option>
            <option value="chrome">Google Chrome</option>
            <option value="firefox">Mozilla Firefox</option>
            <option value="edge">Microsoft Edge</option>
            <option value="brave">Brave Browser</option>
          </select>
        </div>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-lg shadow-blue-600/25 flex items-center justify-center gap-2 transition-all"
      >
        <Save className="w-4 h-4" />
        <span>Save All Preferences</span>
      </button>
    </div>
  );
}
