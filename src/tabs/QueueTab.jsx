import React from 'react';
import {
  DownloadCloud,
  Folder,
  Trash2,
  XCircle,
  RotateCcw,
  Zap,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
  Video,
  Music
} from 'lucide-react';
import { formatDuration } from '../utils/formatters';

export default function QueueTab({
  queue,
  onCancelTask,
  onCancelAll,
  onClearFinished,
  onRetryTask,
  onRetryAllFailed,
  onOpenFolder,
  onRevealFile
}) {
  const activeTasks = queue.filter((t) => t.status === 'DOWNLOADING' || t.status === 'PROCESSING');
  const queuedTasks = queue.filter((t) => t.status === 'QUEUED');
  const failedTasks = queue.filter((t) => t.status === 'FAILED');
  const finishedTasks = queue.filter(
    (t) => t.status === 'COMPLETED' || t.status === 'FAILED' || t.status === 'CANCELLED'
  );

  return (
    <div className="h-full flex flex-col p-6 space-y-4 overflow-hidden">
      {/* Header & Overall Bandwidth */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <span>Active Download Queue</span>
            <DownloadCloud className="w-5 h-5 text-blue-400" />
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-threaded download manager with live speed and progress metrics.
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-medium">
          <div className="px-3 py-1.5 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400 flex items-center gap-2">
            <Zap className="w-4 h-4" />
            <span>{activeTasks.length} Active • {queuedTasks.length} Queued</span>
          </div>
        </div>
      </div>

      {/* Action Toolbar */}
      <div className="p-3 rounded-xl bg-[#121824] border border-white/5 shadow-md flex items-center justify-between text-xs shrink-0">
        <div className="text-slate-400">
          Total items in queue: <span className="font-semibold text-slate-200">{queue.length}</span>
        </div>

        <div className="flex items-center gap-2">
          {failedTasks.length > 0 && (
            <button
              onClick={onRetryAllFailed}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 transition-colors font-medium"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retry All Failed ({failedTasks.length})</span>
            </button>
          )}

          {finishedTasks.length > 0 && (
            <button
              onClick={onClearFinished}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear Finished</span>
            </button>
          )}

          {activeTasks.length > 0 && (
            <button
              onClick={onCancelAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 transition-colors"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Cancel All</span>
            </button>
          )}

          <button
            onClick={onOpenFolder}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
          >
            <Folder className="w-3.5 h-3.5" />
            <span>Downloads Folder</span>
          </button>
        </div>
      </div>

      {/* Queue Cards List */}
      <div className="flex-1 bg-[#121824] border border-white/5 rounded-xl p-4 shadow-lg overflow-y-auto space-y-3">
        {queue.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-500">
            <DownloadCloud className="w-12 h-12 stroke-1 mb-2 text-slate-600" />
            <p className="text-sm font-medium text-slate-400">
              No active downloads
            </p>
            <p className="text-xs max-w-sm mt-1">
              Add individual videos, playlists, or bulk URLs from the tabs on the left to start downloading.
            </p>
          </div>
        ) : (
          queue.map((task) => {
            const isDownloading = task.status === 'DOWNLOADING';
            const isProcessing = task.status === 'PROCESSING';
            const isCompleted = task.status === 'COMPLETED';
            const isFailed = task.status === 'FAILED';
            const isCancelled = task.status === 'CANCELLED';

            return (
              <div
                key={task.id}
                className="p-3.5 rounded-xl bg-[#0e141f] border border-white/5 shadow-md flex items-center justify-between gap-4 transition-all"
              >
                {/* Left Thumbnail */}
                <div className="w-24 h-14 rounded-lg bg-black/40 overflow-hidden shrink-0 border border-white/5 relative">
                  {task.thumbnail ? (
                    <img
                      src={task.thumbnail}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      {task.mode === 'audio' ? (
                        <Music className="w-5 h-5 text-purple-400" />
                      ) : (
                        <Video className="w-5 h-5 text-blue-400" />
                      )}
                    </div>
                  )}

                  {task.duration > 0 && (
                    <span className="absolute bottom-1 right-1 px-1 rounded bg-black/80 text-[9px] font-mono font-medium text-white">
                      {formatDuration(task.duration)}
                    </span>
                  )}
                </div>

                {/* Middle Info & Progress */}
                <div className="flex-1 min-w-0 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-xs font-semibold text-slate-100 truncate">
                      {task.title}
                    </h3>
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400 border border-white/5 shrink-0">
                      {task.quality} • {task.container}
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full h-1.5 bg-black/50 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 rounded-full ${
                        isCompleted
                          ? 'bg-emerald-500'
                          : isFailed
                          ? 'bg-red-500'
                          : isCancelled
                          ? 'bg-amber-500'
                          : 'bg-gradient-to-r from-blue-500 to-indigo-500'
                      }`}
                      style={{ width: `${Math.max(2, task.progress || 0)}%` }}
                    />
                  </div>

                  {/* Sub stats */}
                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                    <div className="flex items-center gap-3">
                      <span>{task.progress ? `${task.progress.toFixed(1)}%` : '0%'}</span>
                      {task.totalStr && <span>of {task.totalStr}</span>}
                      {isDownloading && task.speedStr && (
                        <span className="text-blue-400 font-semibold flex items-center gap-1">
                          <Zap className="w-3 h-3" />
                          {task.speedStr}
                        </span>
                      )}
                      {isProcessing && (
                        <span className="text-purple-400 flex items-center gap-1">
                          <Loader2 className="w-3 h-3 animate-spin" />
                          Converting / Muxing with FFmpeg...
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3">
                      {isDownloading && task.etaStr && (
                        <span className="flex items-center gap-1 text-slate-500">
                          <Clock className="w-3 h-3" />
                          ETA: {task.etaStr}
                        </span>
                      )}

                      {/* Status Badges */}
                      {isCompleted && (
                        <span className="text-emerald-400 font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Completed
                        </span>
                      )}
                      {isFailed && (
                        <div className="flex items-center gap-1.5 text-red-400">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                          <span className="font-semibold">Failed</span>
                          {task.error && (
                            <span className="text-[10px] text-red-400/80 max-w-[200px] truncate" title={task.error}>
                              ({task.error.replace(/^ERROR:\s*/i, '').slice(0, 30)})
                            </span>
                          )}
                        </div>
                      )}
                      {isCancelled && (
                        <span className="text-amber-400 font-semibold">
                          Cancelled
                        </span>
                      )}
                      {task.status === 'QUEUED' && (
                        <span className="text-slate-500">
                          Waiting in queue...
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Action Buttons */}
                <div className="flex items-center gap-2 shrink-0">
                  {(isDownloading || task.status === 'QUEUED' || isProcessing) && (
                    <button
                      onClick={() => onCancelTask(task.id)}
                      className="p-2 rounded-lg bg-white/5 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                      title="Cancel download"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  )}

                  {isCompleted && (
                    <button
                      onClick={() => onRevealFile(task.finalPath)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/20 text-xs font-medium transition-colors"
                    >
                      <Folder className="w-3.5 h-3.5" />
                      <span>Reveal</span>
                    </button>
                  )}

                  {(isFailed || isCancelled) && (
                    <button
                      onClick={() => onRetryTask(task)}
                      className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
                      title="Retry"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
