/**
 * Main Electron Process
 */

const { app, BrowserWindow, ipcMain, dialog, shell, Notification } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const ytdlpEngine = require('./ytdlp-engine.cjs');

let mainWindow = null;

// Paths for JSON storage
const userDataPath = app.getPath('userData');
const settingsFile = path.join(userDataPath, 'settings.json');
const historyFile = path.join(userDataPath, 'history.json');

// Default downloads dir: ~/Downloads/YouTube Downloads
const defaultDownloadDir = path.join(app.getPath('downloads'), 'YouTube Downloads');
if (!fs.existsSync(defaultDownloadDir)) {
  fs.mkdirSync(defaultDownloadDir, { recursive: true });
}

// Load / Save Settings
function loadSettings() {
  const defaults = {
    downloadDir: defaultDownloadDir,
    maxConcurrentDownloads: 3,
    defaultMode: 'video',
    defaultVideoResolution: 'Best Available',
    defaultVideoContainer: 'mp4',
    defaultAudioFormat: 'mp3',
    defaultAudioQuality: '320 kbps',
    embedThumbnail: true,
    embedMetadata: true,
    downloadSubtitles: false,
    organizePlaylistsInSubfolders: true,
    numberPlaylistItems: true,
    browserCookies: 'none',
    customCookiesPath: '',
  };

  try {
    if (fs.existsSync(settingsFile)) {
      const data = JSON.parse(fs.readFileSync(settingsFile, 'utf-8'));
      return { ...defaults, ...data };
    }
  } catch (e) {}

  return defaults;
}

function saveSettings(settings) {
  try {
    fs.writeFileSync(settingsFile, JSON.stringify(settings, null, 2), 'utf-8');
    return true;
  } catch (e) {
    return false;
  }
}

// Load / Save History
function loadHistory() {
  try {
    if (fs.existsSync(historyFile)) {
      return JSON.parse(fs.readFileSync(historyFile, 'utf-8'));
    }
  } catch (e) {}
  return [];
}

function saveHistory(history) {
  try {
    fs.writeFileSync(historyFile, JSON.stringify(history, null, 2), 'utf-8');
    return true;
  } catch (e) {
    return false;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1240,
    height: 820,
    minWidth: 1000,
    minHeight: 650,
    frame: false, // Frameless for custom Windows 11 Fluent titlebar
    backgroundColor: '#0b0f17',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
      webSecurity: false, // Allows local file playback for in-app media player
    },
  });

  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  const devUrl = 'http://localhost:5173';

  if (isDev) {
    mainWindow.loadURL(devUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// IPC: Window Controls
ipcMain.handle('window:minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.handle('window:maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.handle('window:close', () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.handle('window:isMaximized', () => {
  return mainWindow ? mainWindow.isMaximized() : false;
});

// IPC: System & Diagnostics
ipcMain.handle('engine:getSystemStatus', () => {
  return ytdlpEngine.getSystemStatus();
});

ipcMain.handle('system:getDefaultDownloadDir', () => {
  return defaultDownloadDir;
});

// IPC: Extraction
ipcMain.handle('engine:extractInfo', async (event, { url, cookies, customCookies }) => {
  return await ytdlpEngine.extractSingleInfo(url, cookies, customCookies);
});

ipcMain.handle('engine:extractPlaylist', async (event, { url, maxItems, cookies }) => {
  return await ytdlpEngine.extractPlaylistOrChannel(url, maxItems, cookies);
});

// IPC: Download Execution
ipcMain.handle('download:start', async (event, task) => {
  try {
    const settings = loadSettings();
    const taskWithSettings = {
      ...task,
      outputDir: task.outputDir || settings.downloadDir || defaultDownloadDir,
      browserCookies: task.browserCookies || settings.browserCookies,
      customCookiesPath: task.customCookiesPath || settings.customCookiesPath,
    };

    const result = await ytdlpEngine.startDownload(
      taskWithSettings,
      (progressData) => {
        if (mainWindow) mainWindow.webContents.send('download:progress', progressData);
      },
      (statusData) => {
        if (mainWindow) mainWindow.webContents.send('download:status', statusData);
      }
    );

    // Save to history
    const history = loadHistory();
    const historyItem = {
      id: task.id || Date.now().toString(),
      title: task.title,
      url: task.url,
      filePath: result.finalPath,
      fileSize: result.fileSize,
      mode: task.mode,
      format: task.container,
      quality: task.quality,
      duration: task.duration || 0,
      channel: task.channel || '',
      thumbnail: task.thumbnail || '',
      completedAt: Date.now(),
    };
    history.unshift(historyItem);
    saveHistory(history);

    if (mainWindow) {
      mainWindow.webContents.send('download:complete', {
        taskId: task.id,
        finalPath: result.finalPath,
        fileSize: result.fileSize,
      });
    }

    // Windows Toast Notification
    if (Notification.isSupported()) {
      new Notification({
        title: 'Download Complete! 🎉',
        body: task.title || 'Your file is ready.',
        silent: false,
      }).show();
    }

    return { success: true, result };
  } catch (err) {
    if (mainWindow) {
      mainWindow.webContents.send('download:error', {
        taskId: task.id,
        error: err.message,
      });
    }
    return { success: false, error: err.message };
  }
});

ipcMain.handle('download:cancel', (event, taskId) => {
  return ytdlpEngine.cancelDownload(taskId);
});

// IPC: Native Dialogs & Shell
ipcMain.handle('dialog:selectDirectory', async (event, defaultPath) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    defaultPath: defaultPath || defaultDownloadDir,
    properties: ['openDirectory', 'createDirectory'],
  });
  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

ipcMain.handle('shell:openPath', async (event, filePath) => {
  if (filePath && fs.existsSync(filePath)) {
    return await shell.openPath(filePath);
  }
  return 'File not found';
});

ipcMain.handle('shell:showItemInFolder', (event, filePath) => {
  if (filePath && fs.existsSync(filePath)) {
    shell.showItemInFolder(filePath);
    return true;
  }
  return false;
});

// IPC: Settings & History Persistence
ipcMain.handle('store:getSettings', () => {
  return loadSettings();
});

ipcMain.handle('store:saveSettings', (event, settings) => {
  return saveSettings(settings);
});

ipcMain.handle('store:getHistory', () => {
  return loadHistory();
});

ipcMain.handle('store:addHistory', (event, record) => {
  const history = loadHistory();
  history.unshift(record);
  return saveHistory(history);
});

ipcMain.handle('store:deleteHistory', (event, id) => {
  const history = loadHistory();
  const updated = history.filter((item) => item.id !== id);
  return saveHistory(updated);
});

ipcMain.handle('store:clearHistory', () => {
  return saveHistory([]);
});

ipcMain.handle('notification:show', (event, { title, body }) => {
  if (Notification.isSupported()) {
    new Notification({ title, body }).show();
    return true;
  }
  return false;
});
