import React, { useState } from 'react';
import {
  Search,
  Clipboard,
  Download,
  Video,
  Music,
  Folder,
  Eye,
  Clock,
  User,
  Sparkles,
  Loader2,
  CheckCircle2
} from 'lucide-react';
import { formatDuration, formatNumber } from '../utils/formatters';

export default function SingleTab({
  settings,
  onAddDownload,
  onOpenFolder,
  onSelectFolder,
  showToast
}) {
  const [url, setUrl] = useState('');
  const [isInspecting, setIsInspecting] = useState(false);
  const [videoInfo, setVideoInfo] = useState(null);

  // Form options
  const [mode, setMode] = useState(settings?.defaultMode || 'video');
  const [quality, setQuality] = useState(settings?.defaultVideoResolution || 'Best Available');
  const [container, setContainer] = useState(settings?.defaultVideoContainer || 'mp4');
  const [audioFormat, setAudioFormat] = useState(settings?.defaultAudioFormat || 'mp3');
  const [audioQuality, setAudioQuality] = useState(settings?.defaultAudioQuality || '320 kbps');
  const [downloadSubtitles, setDownloadSubtitles] = useState(settings?.downloadSubtitles || false);
  const [embedThumbnail, setEmbedThumbnail] = useState(settings?.embedThumbnail ?? true);
  const [embedMetadata, setEmbedMetadata] = useState(settings?.embedMetadata ?? true);

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
        inspectUrl(text.trim());
      }
    } catch (e) {
      showToast({ type: 'error', message: 'Could not access clipboard' });
    }
  };

  const inspectUrl = async (targetUrl = url) => {
    const cleanUrl = (targetUrl || '').trim();
    if (!cleanUrl) {
      showToast({ type: 'error', message: 'Please enter a valid YouTube URL' });
      return;
    }

    setIsInspecting(true);
    setVideoInfo(null);

    try {
      if (window.electronAPI) {
        const info = await window.electronAPI.extractInfo(
          cleanUrl,
          settings?.browserCookies || 'none',
          settings?.customCookiesPath || ''
        );
        setVideoInfo(info);
        if (info.resolutions && info.resolutions.length > 0) {
          setQuality(info.resolutions[0]);
        }
        showToast({ type: 'success', message: 'Video details loaded!' });
      }
    } catch (err) {
      showToast({ type: 'error', message: `Inspection error: ${err.message || 'Failed'}` });
    } finally {
      setIsInspecting(false);
    }
  };

  const handleDownload = () => {
    const cleanUrl = url.trim();
    if (!cleanUrl) {
      showToast({ type: 'error', message: 'Please provide a YouTube URL' });
      return;
    }

    const task = {
      id: Date.now().toString() + Math.random().toString(36).substring(2, 7),
      url: cleanUrl,
      title: videoInfo?.title || 'YouTube Media',
      channel: videoInfo?.uploader || '',
      thumbnail: videoInfo?.thumbnail || '',
      duration: videoInfo?.duration || 0,
      mode,
      quality: mode === 'audio' ? audioQuality : quality,
      container: mode === 'audio' ? audioFormat : container,
      outputDir: settings?.downloadDir,
      downloadSubtitles: mode === 'video' ? downloadSubtitles : false,
      embedThumbnail,
      embedMetadata,
    };

    onAddDownload(task);
    showToast({ type: 'success', message: 'Added to download queue!' });
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <span>Single Video & Audio Downloader</span>
          <Sparkles className="w-4 h-4 text-amber-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Paste any YouTube video or short URL for real-time analysis and ultra-high quality downloading.
        </p>
      </div>

      {/* URL Input Bar */}
      <div className="p-4 rounded-xl bg-[#121824] border border-white/5 space-y-3 shadow-lg">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Paste YouTube URL here (e.g., https://www.youtube.com/watch?v=...)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && inspectUrl()}
              className="w-full bg-[#0a0e17] border border-white/10 rounded-lg pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
          </div>

          <button
            onClick={handlePaste}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/5 text-xs font-medium transition-colors"
          >
            <Clipboard className="w-3.5 h-3.5" />
            <span>Paste</span>
          </button>

          <button
            onClick={() => inspectUrl()}
            disabled={isInspecting}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 transition-all disabled:opacity-50"
          >
            {isInspecting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Inspecting...</span>
              </>
            ) : (
              <>
                <Search className="w-3.5 h-3.5" />
                <span>Inspect Video</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Video Details Card (When inspected) */}
      {videoInfo && (
        <div className="p-4 rounded-xl bg-[#121824] border border-white/5 shadow-xl flex gap-5 animate-in fade-in duration-300">
          <div className="relative w-64 h-36 rounded-lg overflow-hidden shrink-0 bg-black/50 border border-white/10 shadow-md">
            {videoInfo.thumbnail ? (
              <img
                src={videoInfo.thumbnail}
                alt={videoInfo.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Video className="w-10 h-10 text-slate-600" />
              </div>
            )}
            {videoInfo.duration > 0 && (
              <span className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/80 backdrop-blur-sm text-[11px] font-mono font-medium text-white">
                {formatDuration(videoInfo.duration)}
              </span>
            )}
          </div>

          <div className="flex-1 min-w-0 flex flex-col justify-between py-1">
            <div className="space-y-1.5">
              <h2 className="text-base font-semibold text-white leading-snug line-clamp-2">
                {videoInfo.title}
              </h2>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1.5 text-slate-300">
                  <User className="w-3.5 h-3.5 text-blue-400" />
                  {videoInfo.uploader}
                </span>
                <span className="flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-slate-500" />
                  {formatNumber(videoInfo.view_count)} views
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {formatDuration(videoInfo.duration)}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2 text-xs">
              <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                ✓ Ready for Download
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Preset & Output Options */}
      <div className="p-5 rounded-xl bg-[#121824] border border-white/5 space-y-5 shadow-lg">
        <h3 className="text-sm font-semibold text-slate-200">
          Format & Output Configuration
        </h3>

        {/* Mode Selector */}
        <div className="grid grid-cols-2 gap-3 max-w-md">
          <button
            onClick={() => setMode('video')}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-semibold border transition-all ${
              mode === 'video'
                ? 'bg-blue-600/20 border-blue-500/50 text-blue-400 shadow-sm shadow-blue-500/10'
                : 'bg-black/30 border-white/5 text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Video className="w-4 h-4" />
            <span>Video + Audio</span>
          </button>

          <button
            onClick={() => setMode('audio')}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-semibold border transition-all ${
              mode === 'audio'
                ? 'bg-purple-600/20 border-purple-500/50 text-purple-400 shadow-sm shadow-purple-500/10'
                : 'bg-black/30 border-white/5 text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Music className="w-4 h-4" />
            <span>Audio Only (MP3/M4A)</span>
          </button>
        </div>

        {/* Dynamic Controls depending on Video vs Audio */}
        {mode === 'video' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Resolution Quality
              </label>
              <select
                value={quality}
                onChange={(e) => setQuality(e.target.value)}
                className="w-full bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500/50"
              >
                {(videoInfo?.resolutions || [
                  'Best Available',
                  '2160p (4K)',
                  '1440p (2K)',
                  '1080p (Full HD)',
                  '720p (HD)',
                  '480p',
                  '360p'
                ]).map((res) => (
                  <option key={res} value={res}>
                    {res}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Video Container
              </label>
              <select
                value={container}
                onChange={(e) => setContainer(e.target.value)}
                className="w-full bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500/50 uppercase"
              >
                <option value="mp4">MP4 (Recommended)</option>
                <option value="mkv">MKV (Matroska)</option>
                <option value="webm">WebM</option>
              </select>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Audio Format
              </label>
              <select
                value={audioFormat}
                onChange={(e) => setAudioFormat(e.target.value)}
                className="w-full bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500/50 uppercase"
              >
                <option value="mp3">MP3 (Universal)</option>
                <option value="m4a">M4A (Apple AAC)</option>
                <option value="wav">WAV (Lossless PCM)</option>
                <option value="flac">FLAC (Lossless)</option>
                <option value="opus">OPUS (High Efficiency)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Bitrate Quality
              </label>
              <select
                value={audioQuality}
                onChange={(e) => setAudioQuality(e.target.value)}
                className="w-full bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500/50"
              >
                <option value="320 kbps">320 kbps (High Fidelity)</option>
                <option value="256 kbps">256 kbps</option>
                <option value="192 kbps">192 kbps</option>
                <option value="128 kbps">128 kbps</option>
              </select>
            </div>
          </div>
        )}

        {/* Toggles */}
        <div className="flex flex-wrap gap-6 pt-2 text-xs text-slate-300">
          {mode === 'video' && (
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={downloadSubtitles}
                onChange={(e) => setDownloadSubtitles(e.target.checked)}
                className="rounded border-white/20 bg-black/40 text-blue-600 focus:ring-0"
              />
              <span>Download & Embed English subtitles</span>
            </label>
          )}

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={embedThumbnail}
              onChange={(e) => setEmbedThumbnail(e.target.checked)}
              className="rounded border-white/20 bg-black/40 text-blue-600 focus:ring-0"
            />
            <span>Embed Cover Art / Thumbnail</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={embedMetadata}
              onChange={(e) => setEmbedMetadata(e.target.checked)}
              className="rounded border-white/20 bg-black/40 text-blue-600 focus:ring-0"
            />
            <span>Embed Artist & Title ID3 Metadata</span>
          </label>
        </div>

        {/* Download Location row */}
        <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <Folder className="w-3.5 h-3.5 text-slate-500" />
            <span>Save Location:</span>
            <span className="text-slate-200 font-mono text-[11px] truncate max-w-md">
              {settings?.downloadDir || 'Default'}
            </span>
          </div>

          <button
            onClick={onSelectFolder}
            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/5 transition-colors"
          >
            Change Folder...
          </button>
        </div>
      </div>

      {/* Main Download Action Button */}
      <button
        onClick={handleDownload}
        disabled={!url.trim()}
        className="w-full py-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-2 transition-all disabled:opacity-40"
      >
        <Download className="w-4 h-4" />
        <span>Add to Queue & Download</span>
      </button>
    </div>
  );
}
