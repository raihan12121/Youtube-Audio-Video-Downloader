import React, { useState } from 'react';
import {
  ListVideo,
  Search,
  Clipboard,
  Download,
  Video,
  Music,
  CheckSquare,
  Square,
  Sparkles,
  Loader2,
  FolderPlus,
  Hash,
  Filter
} from 'lucide-react';
import { formatDuration, sanitizeFilename } from '../utils/formatters';

export default function PlaylistTab({
  settings,
  onAddBatchDownloads,
  showToast
}) {
  const [url, setUrl] = useState('');
  const [limit, setLimit] = useState('All Videos');
  const [isScanning, setIsScanning] = useState(false);
  const [playlistData, setPlaylistData] = useState(null);
  const [entries, setEntries] = useState([]);
  const [filterQuery, setFilterQuery] = useState('');

  // Bulk presets
  const [mode, setMode] = useState('video');
  const [quality, setQuality] = useState('Best Available');
  const [createSubfolder, setCreateSubfolder] = useState(settings?.organizePlaylistsInSubfolders ?? true);
  const [numberItems, setNumberItems] = useState(settings?.numberPlaylistItems ?? true);

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
        scanPlaylist(text.trim());
      }
    } catch (e) {
      showToast({ type: 'error', message: 'Could not access clipboard' });
    }
  };

  const scanPlaylist = async (targetUrl = url) => {
    const cleanUrl = (targetUrl || '').trim();
    if (!cleanUrl) {
      showToast({ type: 'error', message: 'Please enter a playlist or channel URL' });
      return;
    }

    setIsScanning(true);
    setPlaylistData(null);
    setEntries([]);

    let maxItems = null;
    if (limit === 'First 25') maxItems = 25;
    else if (limit === 'First 50') maxItems = 50;
    else if (limit === 'First 100') maxItems = 100;
    else if (limit === 'First 200') maxItems = 200;

    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.extractPlaylist(
          cleanUrl,
          maxItems,
          settings?.browserCookies || 'none'
        );
        setPlaylistData(result);
        setEntries(result.entries || []);
        showToast({
          type: 'success',
          message: `Loaded ${result.entries?.length || 0} videos from ${result.type}!`
        });
      }
    } catch (err) {
      showToast({ type: 'error', message: `Scan error: ${err.message || 'Failed'}` });
    } finally {
      setIsScanning(false);
    }
  };

  const toggleSelectAll = (select) => {
    setEntries((prev) => prev.map((e) => ({ ...e, selected: select })));
  };

  const toggleItem = (idx) => {
    setEntries((prev) =>
      prev.map((e) => (e.index === idx ? { ...e, selected: !e.selected } : e))
    );
  };

  const filteredEntries = entries.filter((e) =>
    e.title.toLowerCase().includes(filterQuery.toLowerCase())
  );

  const selectedCount = entries.filter((e) => e.selected).length;

  const handleDownloadSelected = () => {
    const selected = entries.filter((e) => e.selected);
    if (!selected.length) {
      showToast({ type: 'error', message: 'No videos selected for download' });
      return;
    }

    const subfolderName = createSubfolder && playlistData?.title
      ? sanitizeFilename(playlistData.title)
      : null;

    const tasks = selected.map((item) => ({
      id: Date.now().toString() + Math.random().toString(36).substring(2, 7),
      url: item.url,
      title: item.title,
      channel: item.uploader || playlistData?.uploader || '',
      thumbnail: item.thumbnail || '',
      duration: item.duration || 0,
      mode,
      quality: mode === 'audio' ? '320 kbps' : quality,
      container: mode === 'audio' ? 'mp3' : 'mp4',
      outputDir: settings?.downloadDir,
      subfolder: subfolderName,
      filenamePrefix: numberItems ? String(item.index).padStart(2, '0') : '',
      embedThumbnail: true,
      embedMetadata: true,
    }));

    onAddBatchDownloads(tasks);
    showToast({
      type: 'success',
      message: `Queued ${tasks.length} videos from ${playlistData?.title || 'batch'}!`
    });
  };

  return (
    <div className="h-full flex flex-col p-6 space-y-4 overflow-hidden">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <span>Playlist & Channel Bulk Downloader</span>
          <ListVideo className="w-5 h-5 text-blue-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Scan full playlists or entire YouTube channel video uploads with batch selection and automated naming.
        </p>
      </div>

      {/* URL Scanner Card */}
      <div className="p-4 rounded-xl bg-[#121824] border border-white/5 space-y-3 shadow-lg shrink-0">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Paste Playlist or Channel URL (e.g., https://www.youtube.com/@Veritasium or playlist?list=...)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && scanPlaylist()}
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

          <select
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            className="bg-[#0a0e17] border border-white/10 rounded-lg px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500/50"
          >
            <option value="All Videos">All Videos</option>
            <option value="First 25">First 25</option>
            <option value="First 50">First 50</option>
            <option value="First 100">First 100</option>
            <option value="First 200">First 200</option>
          </select>

          <button
            onClick={() => scanPlaylist()}
            disabled={isScanning}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 transition-all disabled:opacity-50"
          >
            {isScanning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Scanning...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Scan Videos</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Bulk Configuration Bar */}
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

          <label className="flex items-center gap-1.5 text-slate-300 cursor-pointer ml-2">
            <input
              type="checkbox"
              checked={createSubfolder}
              onChange={(e) => setCreateSubfolder(e.target.checked)}
              className="rounded border-white/20 bg-black/40 text-blue-600 focus:ring-0"
            />
            <FolderPlus className="w-3.5 h-3.5 text-slate-400" />
            <span>Create Subfolder</span>
          </label>

          <label className="flex items-center gap-1.5 text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={numberItems}
              onChange={(e) => setNumberItems(e.target.checked)}
              className="rounded border-white/20 bg-black/40 text-blue-600 focus:ring-0"
            />
            <Hash className="w-3.5 h-3.5 text-slate-400" />
            <span>Number (01 - )</span>
          </label>
        </div>

        {/* Selection buttons & search */}
        <div className="flex items-center gap-2">
          {entries.length > 0 && (
            <>
              <button
                onClick={() => toggleSelectAll(true)}
                className="px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
              >
                Select All
              </button>
              <button
                onClick={() => toggleSelectAll(false)}
                className="px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
              >
                Deselect All
              </button>
            </>
          )}

          <div className="relative">
            <input
              type="text"
              placeholder="Filter videos..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="w-40 bg-[#0a0e17] border border-white/10 rounded-lg pl-7 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none"
            />
            <Filter className="w-3 h-3 text-slate-500 absolute left-2.5 top-2.5" />
          </div>
        </div>
      </div>

      {/* Videos Checklist Table */}
      <div className="flex-1 bg-[#121824] border border-white/5 rounded-xl overflow-hidden shadow-lg flex flex-col">
        {/* Table Header */}
        <div className="px-4 py-2.5 bg-[#0e141f] border-b border-white/5 flex items-center justify-between text-xs font-semibold text-slate-400 shrink-0">
          <div className="flex items-center gap-3">
            <span className="w-6 text-center">#</span>
            <span className="w-20">Preview</span>
            <span>Video Title</span>
          </div>

          <div className="flex items-center gap-6">
            <span>Duration</span>
            <span className="text-blue-400">
              Selected: {selectedCount} / {entries.length}
            </span>
          </div>
        </div>

        {/* Scrollable Rows */}
        <div className="flex-1 overflow-y-auto divide-y divide-white/5">
          {entries.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-500">
              <ListVideo className="w-12 h-12 stroke-1 mb-2 text-slate-600" />
              <p className="text-sm font-medium text-slate-400">
                No playlist scanned yet
              </p>
              <p className="text-xs max-w-sm mt-1">
                Paste any YouTube playlist or channel link above and click "Scan Videos" to preview and bulk download.
              </p>
            </div>
          ) : filteredEntries.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No videos matching "{filterQuery}"
            </div>
          ) : (
            filteredEntries.map((item) => (
              <div
                key={item.index}
                onClick={() => toggleItem(item.index)}
                className={`px-4 py-2.5 flex items-center justify-between gap-4 cursor-pointer hover:bg-white/5 transition-colors select-none ${
                  item.selected ? 'bg-blue-600/5' : ''
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <button className="text-blue-400">
                    {item.selected ? (
                      <CheckSquare className="w-4 h-4 fill-blue-600 text-white" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-600" />
                    )}
                  </button>

                  <span className="w-6 text-center text-xs font-mono text-slate-500">
                    {item.index}
                  </span>

                  <div className="w-16 h-9 rounded bg-black/40 overflow-hidden shrink-0 border border-white/5">
                    {item.thumbnail ? (
                      <img
                        src={item.thumbnail}
                        alt=""
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Video className="w-3.5 h-3.5 text-slate-600" />
                      </div>
                    )}
                  </div>

                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-200 truncate">
                      {item.title}
                    </p>
                    {item.uploader && (
                      <p className="text-[10px] text-slate-500 truncate">
                        {item.uploader}
                      </p>
                    )}
                  </div>
                </div>

                <div className="shrink-0 text-xs font-mono text-slate-400">
                  {formatDuration(item.duration)}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Bottom Download Action */}
      <button
        onClick={handleDownloadSelected}
        disabled={selectedCount === 0}
        className="w-full py-3.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-2 transition-all disabled:opacity-40 shrink-0"
      >
        <Download className="w-4 h-4" />
        <span>Download Selected Videos ({selectedCount})</span>
      </button>
    </div>
  );
}
