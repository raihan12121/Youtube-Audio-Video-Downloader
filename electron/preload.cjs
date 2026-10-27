/**
 * Electron Preload script exposing window.electronAPI securely via contextBridge
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Window controls
  minimize: () => ipcRenderer.invoke('window:minimize'),
  maximize: () => ipcRenderer.invoke('window:maximize'),
  close: () => ipcRenderer.invoke('window:close'),
  isMaximized: () => ipcRenderer.invoke('window:isMaximized'),

  // Environment & Diagnostics
  getSystemStatus: () => ipcRenderer.invoke('engine:getSystemStatus'),
  getDefaultDownloadDir: () => ipcRenderer.invoke('system:getDefaultDownloadDir'),

  // Extraction
  extractInfo: (url, cookies, customCookies) =>
    ipcRenderer.invoke('engine:extractInfo', { url, cookies, customCookies }),
  extractPlaylist: (url, maxItems, cookies) =>
    ipcRenderer.invoke('engine:extractPlaylist', { url, maxItems, cookies }),

  // Downloads
  startDownload: (task) => ipcRenderer.invoke('download:start', task),
  cancelDownload: (taskId) => ipcRenderer.invoke('download:cancel', taskId),

  // Download Event Listeners
  onDownloadProgress: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('download:progress', handler);
    return () => ipcRenderer.removeListener('download:progress', handler);
  },
  onDownloadStatus: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('download:status', handler);
    return () => ipcRenderer.removeListener('download:status', handler);
  },
  onDownloadComplete: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('download:complete', handler);
    return () => ipcRenderer.removeListener('download:complete', handler);
  },
  onDownloadError: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('download:error', handler);
    return () => ipcRenderer.removeListener('download:error', handler);
  },

  // Shell & Filesystem
  selectDirectory: (defaultPath) => ipcRenderer.invoke('dialog:selectDirectory', defaultPath),
  openPath: (filePath) => ipcRenderer.invoke('shell:openPath', filePath),
  showItemInFolder: (filePath) => ipcRenderer.invoke('shell:showItemInFolder', filePath),

  // Storage (Settings & History)
  getSettings: () => ipcRenderer.invoke('store:getSettings'),
  saveSettings: (settings) => ipcRenderer.invoke('store:saveSettings', settings),
  getHistory: () => ipcRenderer.invoke('store:getHistory'),
  addHistory: (record) => ipcRenderer.invoke('store:addHistory', record),
  deleteHistory: (id) => ipcRenderer.invoke('store:deleteHistory', id),
  clearHistory: () => ipcRenderer.invoke('store:clearHistory'),

  // Notifications
  showNotification: (options) => ipcRenderer.invoke('notification:show', options),
});
