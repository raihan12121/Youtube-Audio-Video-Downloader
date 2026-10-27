import React, { useState, useEffect, useRef } from 'react';
import TitleBar from './components/TitleBar';
import Sidebar from './components/Sidebar';
import MediaPlayerModal from './components/MediaPlayerModal';
import Toast from './components/Toast';

import SingleTab from './tabs/SingleTab';
import PlaylistTab from './tabs/PlaylistTab';
import BulkTab from './tabs/BulkTab';
import QueueTab from './tabs/QueueTab';
import LibraryTab from './tabs/LibraryTab';
import SettingsTab from './tabs/SettingsTab';

export default function App() {
  const [activeTab, setActiveTab] = useState('single');
  const [settings, setSettings] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [queue, setQueue] = useState([]);
  const [previewMedia, setPreviewMedia] = useState(null);
  const [toast, setToast] = useState(null);

  const queueRef = useRef(queue);
  queueRef.current = queue;

  const settingsRef = useRef(settings);
  settingsRef.current = settings;

  // Initialize data on mount
  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.getSettings().then(setSettings);
      window.electronAPI.getSystemStatus().then(setSystemStatus);
      window.electronAPI.getHistory().then(setHistory);

      // Event listeners from Main process
      const unbindProgress = window.electronAPI.onDownloadProgress((data) => {
        setQueue((prev) =>
          prev.map((t) =>
            t.id === data.taskId
              ? {
                  ...t,
                  progress: data.progress,
                  speedStr: data.speedStr,
                  totalStr: data.totalStr,
                  etaStr: data.etaStr,
                  status: data.status,
                }
              : t
          )
        );
      });

      const unbindStatus = window.electronAPI.onDownloadStatus((data) => {
        setQueue((prev) =>
          prev.map((t) =>
            t.id === data.taskId ? { ...t, status: data.status, speedStr: data.message } : t
          )
        );
      });

      const unbindComplete = window.electronAPI.onDownloadComplete((data) => {
        setQueue((prev) =>
          prev.map((t) =>
            t.id === data.taskId
              ? {
                  ...t,
                  status: 'COMPLETED',
                  progress: 100,
                  finalPath: data.finalPath,
                  fileSize: data.fileSize,
                  speedStr: 'Done',
                  etaStr: '00:00',
                }
              : t
          )
        );
        // Refresh history
        window.electronAPI.getHistory().then(setHistory);
      });

      const unbindError = window.electronAPI.onDownloadError((data) => {
        setQueue((prev) =>
          prev.map((t) =>
            t.id === data.taskId
              ? {
                  ...t,
                  status: 'FAILED',
                  error: data.error,
                  speedStr: 'Failed',
                }
              : t
          )
        );
      });

      return () => {
        unbindProgress();
        unbindStatus();
        unbindComplete();
        unbindError();
      };
    }
  }, []);

  // Worker Queue Scheduler
  useEffect(() => {
    const maxConcurrency = settings?.maxConcurrentDownloads || 3;
    const activeCount = queue.filter(
      (t) => t.status === 'DOWNLOADING' || t.status === 'PROCESSING'
    ).length;

    if (activeCount < maxConcurrency) {
      const nextTask = queue.find((t) => t.status === 'QUEUED');
      if (nextTask && window.electronAPI) {
        // Mark as DOWNLOADING
        setQueue((prev) =>
          prev.map((t) => (t.id === nextTask.id ? { ...t, status: 'DOWNLOADING' } : t))
        );

        // Execute download via IPC
        window.electronAPI.startDownload(nextTask);
      }
    }
  }, [queue, settings]);

  const showToast = (toastObj) => {
    setToast(toastObj);
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  const handleAddDownload = (task) => {
    setQueue((prev) => [...prev, { ...task, status: 'QUEUED', progress: 0 }]);
    setActiveTab('queue');
  };

  const handleAddBatchDownloads = (tasks) => {
    setQueue((prev) => [
      ...prev,
      ...tasks.map((t) => ({ ...t, status: 'QUEUED', progress: 0 })),
    ]);
    setActiveTab('queue');
  };

  const handleCancelTask = (taskId) => {
    if (window.electronAPI) window.electronAPI.cancelDownload(taskId);
    setQueue((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: 'CANCELLED' } : t))
    );
  };

  const handleCancelAll = () => {
    queue.forEach((t) => {
      if (t.status === 'DOWNLOADING' || t.status === 'QUEUED' || t.status === 'PROCESSING') {
        if (window.electronAPI) window.electronAPI.cancelDownload(t.id);
      }
    });
    setQueue((prev) =>
      prev.map((t) =>
        t.status === 'DOWNLOADING' || t.status === 'QUEUED' || t.status === 'PROCESSING'
          ? { ...t, status: 'CANCELLED' }
          : t
      )
    );
  };

  const handleClearFinished = () => {
    setQueue((prev) =>
      prev.filter(
        (t) => t.status !== 'COMPLETED' && t.status !== 'CANCELLED' && t.status !== 'FAILED'
      )
    );
  };

  const handleRetryTask = (task) => {
    setQueue((prev) =>
      prev.map((t) => (t.id === task.id ? { ...t, status: 'QUEUED', progress: 0, error: null } : t))
    );
  };

  const handleRetryAllFailed = () => {
    setQueue((prev) =>
      prev.map((t) =>
        t.status === 'FAILED' || t.status === 'CANCELLED'
          ? { ...t, status: 'QUEUED', progress: 0, error: null }
          : t
      )
    );
  };

  const handleSelectFolder = async () => {
    if (window.electronAPI) {
      const selected = await window.electronAPI.selectDirectory(settings?.downloadDir);
      if (selected) {
        const updated = { ...settings, downloadDir: selected };
        setSettings(updated);
        await window.electronAPI.saveSettings(updated);
        showToast({ type: 'success', message: 'Download directory updated!' });
      }
    }
  };

  const handleOpenFolder = () => {
    if (window.electronAPI && settings?.downloadDir) {
      window.electronAPI.openPath(settings.downloadDir);
    }
  };

  const handleRevealFile = (filePath) => {
    if (window.electronAPI && filePath) {
      window.electronAPI.showItemInFolder(filePath);
    }
  };

  const handleOpenDefaultPlayer = (filePath) => {
    if (window.electronAPI && filePath) {
      window.electronAPI.openPath(filePath);
    }
  };

  const handleSaveSettings = async (newSettings) => {
    setSettings(newSettings);
    if (window.electronAPI) {
      await window.electronAPI.saveSettings(newSettings);
    }
  };

  const handleClearHistory = async () => {
    if (window.electronAPI) {
      await window.electronAPI.clearHistory();
      setHistory([]);
      showToast({ type: 'success', message: 'History cleared' });
    }
  };

  const handleDeleteHistoryItem = async (id) => {
    if (window.electronAPI) {
      await window.electronAPI.deleteHistory(id);
      setHistory((prev) => prev.filter((item) => item.id !== id));
    }
  };

  const activeQueueCount = queue.filter(
    (t) => t.status === 'DOWNLOADING' || t.status === 'QUEUED' || t.status === 'PROCESSING'
  ).length;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#0b0f17] text-slate-100 select-none">
      {/* Frameless Windows 11 Titlebar */}
      <TitleBar title="YouTube Video & Bulk Downloader Pro" />

      {/* Main Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          queueCount={activeQueueCount}
          systemStatus={systemStatus}
          onOpenFolder={handleOpenFolder}
        />

        {/* Tab View Container */}
        <main className="flex-1 overflow-hidden bg-[#090d15] relative">
          {activeTab === 'single' && (
            <SingleTab
              settings={settings}
              onAddDownload={handleAddDownload}
              onOpenFolder={handleOpenFolder}
              onSelectFolder={handleSelectFolder}
              showToast={showToast}
            />
          )}

          {activeTab === 'playlist' && (
            <PlaylistTab
              settings={settings}
              onAddBatchDownloads={handleAddBatchDownloads}
              showToast={showToast}
            />
          )}

          {activeTab === 'bulk' && (
            <BulkTab
              settings={settings}
              onAddBatchDownloads={handleAddBatchDownloads}
              showToast={showToast}
            />
          )}

          {activeTab === 'queue' && (
            <QueueTab
              queue={queue}
              onCancelTask={handleCancelTask}
              onCancelAll={handleCancelAll}
              onClearFinished={handleClearFinished}
              onRetryTask={handleRetryTask}
              onRetryAllFailed={handleRetryAllFailed}
              onOpenFolder={handleOpenFolder}
              onRevealFile={handleRevealFile}
            />
          )}

          {activeTab === 'library' && (
            <LibraryTab
              history={history}
              onClearHistory={handleClearHistory}
              onDeleteHistoryItem={handleDeleteHistoryItem}
              onPlayInApp={setPreviewMedia}
              onOpenDefaultPlayer={handleOpenDefaultPlayer}
              onRevealFile={handleRevealFile}
              showToast={showToast}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsTab
              settings={settings}
              systemStatus={systemStatus}
              onSaveSettings={handleSaveSettings}
              onSelectFolder={handleSelectFolder}
              showToast={showToast}
            />
          )}
        </main>
      </div>

      {/* In-App Media Player Modal */}
      {previewMedia && (
        <MediaPlayerModal
          media={previewMedia}
          onClose={() => setPreviewMedia(null)}
        />
      )}

      {/* Toast Notification */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
}
