# YouTube Video, Audio & Bulk Downloader Pro 🎬

[![GitHub Release](https://img.shields.io/github/v/release/raihan12121/Youtube-Audio-Video-Downloader?style=for-the-badge&color=blue)](https://github.com/raihan12121/Youtube-Audio-Video-Downloader/releases/latest)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows)](https://github.com/raihan12121/Youtube-Audio-Video-Downloader/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Built with Electron](https://img.shields.io/badge/Built_with-Electron-47848F?style=for-the-badge&logo=electron)](https://www.electronjs.org/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind-CSS_v4-38B2AC?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)

A modern, high-performance Windows desktop application designed to download YouTube videos, audios, and bulk collections across **individual videos, shorts, entire playlists, and complete channel uploads**.

Built with **Electron**, **React 19**, **Tailwind CSS**, **Lucide Icons**, **yt-dlp**, and **FFmpeg**.

---

## 📥 Downloads (Latest Version v2.0.0)

Grab the ready-to-run Windows desktop app from the [Releases Page](https://github.com/raihan12121/Youtube-Audio-Video-Downloader/releases/latest):

| Download Package | Type | Description |
| :--- | :--- | :--- |
| [**YouTube Downloader Pro Setup 2.0.0.exe**](https://github.com/raihan12121/Youtube-Audio-Video-Downloader/releases/latest/download/YouTube.Downloader.Pro.Setup.2.0.0.exe) | **Windows Installer (NSIS)** | Full installer. Automatically creates Desktop and Start Menu shortcuts. |
| [**YouTube Downloader Pro 2.0.0.exe**](https://github.com/raihan12121/Youtube-Audio-Video-Downloader/releases/latest/download/YouTube.Downloader.Pro.2.0.0.exe) | **Portable (.exe)** | Standalone portable executable. Runs instantly without installation. |

---

## ✨ Features & Capabilities

### 1. 🎬 Single Video & Audio Downloader
- **Instant Video Inspection**: Real-time thumbnail preview, video title, author, views count, duration, and available format resolutions.
- **Ultra-High Definition Video**: Download in **4K (2160p)**, **2K (1440p)**, **1080p (Full HD)**, **720p (HD)**, **480p**, or **360p** in **MP4**, **MKV**, or **WebM**.
- **High-Fidelity Audio Extraction**: Convert to **MP3**, **M4A (AAC)**, **WAV**, **FLAC**, or **OPUS** up to **320 kbps**.
- **Cover Art & ID3 Tagging**: Automatically embeds high-resolution album art and artist/title metadata into the output file.
- **Subtitles**: Option to download and embed English or auto-generated subtitles (.srt).

### 2. 📑 Playlist & Channel Bulk Downloader
- **Universal Extraction**: Supports playlist URLs (`playlist?list=...`) and full channel handles (`/@ChannelName` or `/@ChannelName/videos`).
- **Interactive Checklist**: Select all, deselect all, or pick specific videos from a playlist.
- **Live Search Filter**: Filter large playlists with hundreds of videos by title in real-time.
- **Preset Limits**: Scan all videos, or limit to the first 25, 50, 100, or 200 items.
- **Smart Organization**: Automatically puts downloads into a subfolder named after the playlist or channel.
- **Sequential Track Numbering**: Adds `01 - `, `02 - ` prefixes to preserve chronological or album playback order.

### 3. 📋 Multi-URL Bulk Batch
- Paste 10, 50, or 100+ arbitrary YouTube links (one per line) and queue them with chosen presets in one click.

### 4. ⏳ Active Download Queue & Bandwidth Monitor
- **Multi-Threaded Scheduler**: Download 1 to 6 files simultaneously without freezing.
- **Live Metrics**: Per-task progress bar, download speed (`MB/s`), downloaded / total bytes, and ETA timer.
- **Task Controls**: Pause, Cancel, Retry individual failed items, or click **"Retry All Failed"** with one click.
- **Windows Toast Notifications**: Native desktop notification popup whenever a download finishes.

### 5. ▶ Built-In Media Player & Library
- **In-App Media Player**: Preview and listen to downloaded videos and audio tracks directly inside the app without opening an external player.
- **Explorer Integration**: 1-click **"Reveal in File Explorer"** highlights the file on your disk.
- **Library History**: SQLite-backed persistent record of past downloads with search and filtering.

### 6. ⚙️ Settings & System Engine Diagnostics
- **Core Engine Health**: Live status indicator for **FFmpeg 9.0.1**, **Node.js v24**, and **yt-dlp**.
- **Custom Download Location**: Change your default download directory with a native Windows folder picker.
- **YouTube Cookies Support**: Import cookies from Chrome, Firefox, Edge, or Brave to unlock age-restricted, private, or member-only videos.

---

## 🛠️ Tech Stack

- **Desktop Framework**: Electron 35
- **Frontend**: React 19, Tailwind CSS v4, Lucide React Icons
- **Bundler**: Vite 6
- **Download Engines**: yt-dlp, FFmpeg (Essentials Build), Node.js JavaScript challenge solver

---

## 🚀 Running from Source

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- [Python 3.10+](https://www.python.org/) with `yt-dlp` installed:
  ```bash
  pip install yt-dlp
  ```
- [FFmpeg](https://ffmpeg.org/) (on system PATH)

### Installation & Development
```bash
# Clone the repository
git clone https://github.com/raihan12121/Youtube-Audio-Video-Downloader.git
cd Youtube-Audio-Video-Downloader

# Install dependencies
npm install

# Start Vite + Electron in development mode
npm run dev
```

### Packaging Windows Executables
```bash
# Build frontend assets and create Windows NSIS installer + Portable exe
npm run build
```
Binaries will be placed in the `release/` directory.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
