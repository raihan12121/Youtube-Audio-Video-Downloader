/**
 * Formatting helpers for bytes, speed, duration, and numbers
 */

export function formatBytes(bytes) {
  if (bytes === undefined || bytes === null || isNaN(bytes) || bytes < 0) return '0 B';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i] || 'TB'}`;
}

export function formatSpeed(bytesPerSec) {
  if (!bytesPerSec || bytesPerSec <= 0) return '-- KB/s';
  return `${formatBytes(bytesPerSec)}/s`;
}

export function formatDuration(seconds) {
  if (!seconds || seconds <= 0 || isNaN(seconds)) return '--:--';
  const sec = Math.floor(seconds);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  const h = Math.floor(m / 60);
  const remainingM = m % 60;

  if (h > 0) {
    return `${h.toString().padStart(2, '0')}:${remainingM.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
  return `${remainingM.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

export function formatEta(seconds) {
  if (!seconds || seconds <= 0 || isNaN(seconds)) return '--:--';
  if (seconds > 86400) return '> 1 day';
  const sec = Math.floor(seconds);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  const h = Math.floor(m / 60);
  const remainingM = m % 60;

  if (h > 0) {
    return `${h}h ${remainingM}m`;
  }
  return `${remainingM}:${s.toString().padStart(2, '0')}`;
}

export function formatNumber(num) {
  if (!num && num !== 0) return '0';
  return new Intl.NumberFormat().format(num);
}

export function sanitizeFilename(name) {
  if (!name) return 'download';
  return name.replace(/[\\/*?:"<>|]/g, '').trim().slice(0, 150);
}
