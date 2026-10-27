/**
 * Robust yt-dlp & FFmpeg execution engine in Node.js
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Active spawned download child processes by task ID
const activeProcesses = new Map();

/**
 * Locate FFmpeg executable path
 */
function findFfmpegPath() {
  // 1. Check system path
  try {
    const res = execSync('where ffmpeg', { encoding: 'utf-8', timeout: 3000 }).trim();
    if (res) {
      return res.split(/\r?\n/)[0];
    }
  } catch (e) {}

  // 2. Check WinGet links
  const localAppData = process.env.LOCALAPPDATA;
  if (localAppData) {
    const wingetPath = path.join(localAppData, 'Microsoft', 'WinGet', 'Links', 'ffmpeg.exe');
    if (fs.existsSync(wingetPath)) return wingetPath;
  }

  // 3. Local app bin
  const localBin = path.join(__dirname, '..', 'bin', 'ffmpeg.exe');
  if (fs.existsSync(localBin)) return localBin;

  return 'ffmpeg';
}

/**
 * Locate Node.js executable
 */
function findNodePath() {
  try {
    const res = execSync('where node', { encoding: 'utf-8', timeout: 3000 }).trim();
    if (res) return res.split(/\r?\n/)[0];
  } catch (e) {}
  return 'node';
}

/**
 * Determine command to run yt-dlp
 */
function getYtDlpCommand() {
  // Check if standalone yt-dlp executable exists
  try {
    execSync('yt-dlp --version', { encoding: 'utf-8', timeout: 3000 });
    return { cmd: 'yt-dlp', args: [] };
  } catch (e) {}

  // Fallback to python -m yt_dlp
  try {
    execSync('python -m yt_dlp --version', { encoding: 'utf-8', timeout: 3000 });
    return { cmd: 'python', args: ['-m', 'yt_dlp'] };
  } catch (e) {}

  return { cmd: 'yt-dlp', args: [] };
}

/**
 * Check engine versions and health
 */
function getSystemStatus() {
  const ffmpegPath = findFfmpegPath();
  let ffmpegVersion = null;
  try {
    const out = execSync(`"${ffmpegPath}" -version`, { encoding: 'utf-8', timeout: 3000 });
    ffmpegVersion = out.split(/\r?\n/)[0] || 'Available';
  } catch (e) {}

  let nodeVersion = null;
  try {
    nodeVersion = execSync('node --version', { encoding: 'utf-8', timeout: 3000 }).trim();
  } catch (e) {}

  let ytdlpVersion = null;
  try {
    const y = getYtDlpCommand();
    ytdlpVersion = execSync(`${y.cmd} ${y.args.join(' ')} --version`, { encoding: 'utf-8', timeout: 3000 }).trim();
  } catch (e) {}

  return {
    ffmpeg: {
      available: !!ffmpegVersion,
      version: ffmpegVersion,
      path: ffmpegPath
    },
    nodejs: {
      available: !!nodeVersion,
      version: nodeVersion
    },
    ytdlp: {
      available: !!ytdlpVersion,
      version: ytdlpVersion
    }
  };
}

/**
 * Extract single video/audio info
 */
function extractSingleInfo(url, cookies = 'none', customCookies = '') {
  return new Promise((resolve, reject) => {
    const yt = getYtDlpCommand();
    const args = [
      ...yt.args,
      '--dump-single-json',
      '--no-warnings',
      '--no-playlist',
      '--skip-download',
      '--remote-components', 'ejs:github'
    ];

    if (cookies && cookies !== 'none') {
      args.push('--cookies-from-browser', cookies);
    }
    if (customCookies && fs.existsSync(customCookies)) {
      args.push('--cookies', customCookies);
    }

    args.push(url);

    let stdout = '';
    let stderr = '';

    const proc = spawn(yt.cmd, args);

    proc.stdout.on('data', (d) => {
      stdout += d.toString();
    });

    proc.stderr.on('data', (d) => {
      stderr += d.toString();
    });

    proc.on('close', (code) => {
      if (code === 0 && stdout) {
        try {
          const info = JSON.parse(stdout);
          const formats = info.formats || [];

          // Parse unique video resolutions
          const resSet = new Set();
          for (const f of formats) {
            if (f.height && f.vcodec && f.vcodec !== 'none') {
              if (f.height >= 2160) resSet.add('2160p (4K)');
              else if (f.height >= 1440) resSet.add('1440p (2K)');
              else if (f.height >= 1080) resSet.add('1080p (Full HD)');
              else if (f.height >= 720) resSet.add('720p (HD)');
              else if (f.height >= 480) resSet.add('480p');
              else if (f.height >= 360) resSet.add('360p');
            }
          }

          const order = ['2160p (4K)', '1440p (2K)', '1080p (Full HD)', '720p (HD)', '480p', '360p'];
          const resolutions = order.filter(r => resSet.has(r));
          if (!resolutions.includes('Best Available')) {
            resolutions.unshift('Best Available');
          }

          resolve({
            id: info.id,
            title: info.title || 'Unknown Title',
            uploader: info.uploader || info.channel || 'YouTube',
            duration: info.duration || 0,
            thumbnail: info.thumbnail || (info.thumbnails && info.thumbnails.length ? info.thumbnails[info.thumbnails.length - 1].url : ''),
            view_count: info.view_count || 0,
            resolutions,
            webpage_url: info.webpage_url || url,
            filesize_approx: info.filesize_approx || info.filesize || 0,
          });
        } catch (e) {
          reject(new Error(`Failed to parse video info: ${e.message}`));
        }
      } else {
        reject(new Error(stderr || `yt-dlp exited with code ${code}`));
      }
    });

    proc.on('error', (err) => {
      reject(err);
    });
  });
}

/**
 * Extract playlist or channel videos list
 */
function extractPlaylistOrChannel(url, maxItems = null, cookies = 'none') {
  return new Promise((resolve, reject) => {
    const yt = getYtDlpCommand();
    const args = [
      ...yt.args,
      '--dump-single-json',
      '--flat-playlist',
      '--no-warnings',
      '--skip-download',
      '--remote-components', 'ejs:github'
    ];

    if (maxItems && maxItems > 0) {
      args.push('--playlist-items', `1:${maxItems}`);
    }

    if (cookies && cookies !== 'none') {
      args.push('--cookies-from-browser', cookies);
    }

    args.push(url);

    let stdout = '';
    let stderr = '';

    const proc = spawn(yt.cmd, args);

    proc.stdout.on('data', (d) => {
      stdout += d.toString();
    });

    proc.stderr.on('data', (d) => {
      stderr += d.toString();
    });

    proc.on('close', (code) => {
      if (code === 0 && stdout) {
        try {
          const info = JSON.parse(stdout);
          const rawEntries = info.entries || [];
          const entries = [];

          rawEntries.forEach((e, idx) => {
            if (!e) return;
            const vid = e.id;
            const videoUrl = e.url || (vid ? `https://www.youtube.com/watch?v=${vid}` : null);
            if (!videoUrl) return;

            let thumb = e.thumbnail;
            if (!thumb && e.thumbnails && e.thumbnails.length) {
              thumb = e.thumbnails[e.thumbnails.length - 1].url;
            }

            entries.push({
              index: idx + 1,
              id: vid,
              title: e.title || `Video ${idx + 1}`,
              url: videoUrl,
              duration: e.duration || 0,
              uploader: e.uploader || info.uploader || info.channel || '',
              thumbnail: thumb || '',
              selected: true
            });
          });

          const isChannel = url.includes('/@') || url.includes('/channel/') || url.includes('/c/') || url.includes('/user/');
          const title = info.title || (isChannel ? 'Channel Videos' : 'YouTube Playlist');

          resolve({
            type: isChannel ? 'channel' : 'playlist',
            title,
            uploader: info.uploader || info.channel || '',
            url,
            total: entries.length,
            entries
          });
        } catch (e) {
          reject(new Error(`Failed to parse playlist: ${e.message}`));
        }
      } else {
        reject(new Error(stderr || `yt-dlp exited with code ${code}`));
      }
    });

    proc.on('error', (err) => {
      reject(err);
    });
  });
}

/**
 * Start a download task with live progress reporting
 */
function startDownload(task, onProgress, onStatus) {
  return new Promise((resolve, reject) => {
    const yt = getYtDlpCommand();
    const ffmpegPath = findFfmpegPath();

    const targetDir = task.subfolder
      ? path.join(task.outputDir, task.subfolder)
      : task.outputDir;

    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    const prefix = task.filenamePrefix ? `${task.filenamePrefix} - ` : '';
    const outtmpl = path.join(targetDir, `${prefix}%(title)s.%(ext)s`);

    const args = [
      ...yt.args,
      '--newline',
      '--no-playlist',
      '--js-runtimes', 'node',
      '--remote-components', 'ejs:github',
      '-o', outtmpl,
    ];

    if (ffmpegPath && fs.existsSync(ffmpegPath)) {
      args.push('--ffmpeg-location', ffmpegPath);
    }

    if (task.browserCookies && task.browserCookies !== 'none') {
      args.push('--cookies-from-browser', task.browserCookies);
    }
    if (task.customCookiesPath && fs.existsSync(task.customCookiesPath)) {
      args.push('--cookies', task.customCookiesPath);
    }

    if (task.mode === 'audio') {
      args.push('-x');
      const audioFmt = ['mp3', 'm4a', 'wav', 'flac', 'opus'].includes(task.container) ? task.container : 'mp3';
      args.push('--audio-format', audioFmt);

      let qualityNum = '0';
      if (task.quality && task.quality.includes('320')) qualityNum = '320K';
      else if (task.quality && task.quality.includes('256')) qualityNum = '256K';
      else if (task.quality && task.quality.includes('192')) qualityNum = '192K';
      else if (task.quality && task.quality.includes('128')) qualityNum = '128K';
      args.push('--audio-quality', qualityNum);

      if (task.embedThumbnail) {
        args.push('--embed-thumbnail');
      }
      if (task.embedMetadata) {
        args.push('--add-metadata');
      }
    } else {
      // Video
      let maxH = 0;
      if (task.quality && (task.quality.includes('2160p') || task.quality.includes('4K'))) maxH = 2160;
      else if (task.quality && (task.quality.includes('1440p') || task.quality.includes('2K'))) maxH = 1440;
      else if (task.quality && task.quality.includes('1080p')) maxH = 1080;
      else if (task.quality && task.quality.includes('720p')) maxH = 720;
      else if (task.quality && task.quality.includes('480p')) maxH = 480;
      else if (task.quality && task.quality.includes('360p')) maxH = 360;

      if (maxH > 0) {
        args.push('-f', `bestvideo[height<=${maxH}]+bestaudio/best[height<=${maxH}]/bestvideo+bestaudio/best`);
      } else {
        args.push('-f', 'bestvideo+bestaudio/best');
      }

      const container = ['mp4', 'mkv', 'webm'].includes(task.container) ? task.container : 'mp4';
      args.push('--merge-output-format', container);

      if (task.downloadSubtitles) {
        args.push('--write-subs', '--write-auto-subs', '--sub-langs', 'en.*,en', '--embed-subs');
      }
      if (task.embedThumbnail && ['mp4', 'mkv'].includes(container)) {
        args.push('--embed-thumbnail');
      }
      if (task.embedMetadata) {
        args.push('--add-metadata');
      }
    }

    args.push(task.url);

    const proc = spawn(yt.cmd, args);
    activeProcesses.set(task.id, proc);

    let finalFile = '';
    let lastError = '';

    proc.stdout.on('data', (chunk) => {
      const lines = chunk.toString().split(/\r?\n/);
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // Parse filename
        if (trimmed.startsWith('[download] Destination:') || trimmed.startsWith('[ExtractAudio] Destination:') || trimmed.startsWith('[Merger] Merging formats into')) {
          const match = trimmed.match(/(?:Destination:\s+|Merging formats into\s+)(.+)$/);
          if (match && match[1]) {
            finalFile = match[1].replace(/["']/g, '').trim();
          }
        }

        // Parse progress line: [download] 42.5% of 10.23MiB at 2.45MiB/s ETA 00:03
        if (trimmed.startsWith('[download]') && trimmed.includes('%')) {
          const pctMatch = trimmed.match(/(\d+(?:\.\d+)?)%/);
          const sizeMatch = trimmed.match(/of\s+~?(\d+(?:\.\d+)?[A-Za-z]+)/);
          const speedMatch = trimmed.match(/at\s+~?(\d+(?:\.\d+)?[A-Za-z]+\/s)/);
          const etaMatch = trimmed.match(/ETA\s+([0-9:]+)/);

          const pct = pctMatch ? parseFloat(pctMatch[1]) : 0;
          const totalStr = sizeMatch ? sizeMatch[1] : '';
          const speedStr = speedMatch ? speedMatch[1] : '-- KB/s';
          const etaStr = etaMatch ? etaMatch[1] : '--:--';

          onProgress({
            taskId: task.id,
            progress: pct,
            totalStr,
            speedStr,
            etaStr,
            status: 'DOWNLOADING'
          });
        } else if (trimmed.startsWith('[ExtractAudio]') || trimmed.startsWith('[Merger]') || trimmed.startsWith('[EmbedThumbnail]')) {
          onStatus({
            taskId: task.id,
            status: 'PROCESSING',
            message: trimmed.slice(1, trimmed.indexOf(']')) + '...'
          });
        }
      }
    });

    proc.stderr.on('data', (chunk) => {
      lastError += chunk.toString();
    });

    proc.on('close', (code) => {
      activeProcesses.delete(task.id);

      if (code === 0) {
        // Find generated file if not explicitly matched
        if (!finalFile || !fs.existsSync(finalFile)) {
          try {
            const files = fs.readdirSync(targetDir);
            const ext = task.container || (task.mode === 'audio' ? 'mp3' : 'mp4');
            const matching = files.find(f => f.endsWith(`.${ext}`));
            if (matching) {
              finalFile = path.join(targetDir, matching);
            }
          } catch (e) {}
        }

        let fileSize = 0;
        if (finalFile && fs.existsSync(finalFile)) {
          fileSize = fs.statSync(finalFile).size;
        }

        resolve({
          finalPath: finalFile || targetDir,
          fileSize
        });
      } else {
        reject(new Error(lastError || `Process exited with code ${code}`));
      }
    });

    proc.on('error', (err) => {
      activeProcesses.delete(task.id);
      reject(err);
    });
  });
}

/**
 * Cancel an active download task
 */
function cancelDownload(taskId) {
  const proc = activeProcesses.get(taskId);
  if (proc) {
    try {
      proc.kill('SIGTERM');
      activeProcesses.delete(taskId);
      return true;
    } catch (e) {
      return false;
    }
  }
  return false;
}

module.exports = {
  getSystemStatus,
  extractSingleInfo,
  extractPlaylistOrChannel,
  startDownload,
  cancelDownload,
};
