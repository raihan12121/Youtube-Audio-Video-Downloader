"""
Utility helpers for system detection, formatting, file handling, and URL parsing.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def get_default_download_dir() -> str:
    """Returns the default Downloads folder on the system."""
    home = Path.home()
    downloads = home / "Downloads" / "YouTube Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    return str(downloads)


def check_ffmpeg() -> Tuple[bool, Optional[str]]:
    """
    Checks if ffmpeg is available on system PATH or local app bin folder.
    Returns (is_available, executable_path_or_version).
    """
    # 1. Check PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            res = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True, timeout=5)
            first_line = res.stdout.splitlines()[0] if res.stdout else "Available"
            return True, f"{ffmpeg_path} ({first_line.split(' ')[2] if len(first_line.split(' ')) > 2 else 'OK'})"
        except Exception:
            return True, ffmpeg_path

    # 2. Check local application bin/
    local_bin = Path(__file__).resolve().parent.parent.parent / "bin" / "ffmpeg.exe"
    if local_bin.exists():
        return True, str(local_bin)

    # 3. Check AppData local / winget links
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        winget_path = Path(local_app_data) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
        if winget_path.exists():
            return True, str(winget_path)

    return False, None


def check_nodejs() -> Tuple[bool, Optional[str]]:
    """Checks if Node.js is available for yt-dlp JS challenge solving."""
    node_path = shutil.which("node")
    if node_path:
        try:
            res = subprocess.run([node_path, "--version"], capture_output=True, text=True, timeout=5)
            ver = res.stdout.strip() if res.stdout else "Available"
            return True, f"{node_path} ({ver})"
        except Exception:
            return True, node_path
    return False, None


def format_bytes(bytes_num: Optional[float]) -> str:
    """Format bytes into readable string (e.g. 14.5 MB)."""
    if bytes_num is None or bytes_num < 0:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}" if unit != 'B' else f"{int(bytes_num)} B"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"


def format_speed(speed_bytes_sec: Optional[float]) -> str:
    """Format download speed into readable string."""
    if speed_bytes_sec is None or speed_bytes_sec <= 0:
        return "-- KB/s"
    return f"{format_bytes(speed_bytes_sec)}/s"


def format_duration(seconds: Optional[int]) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds is None or seconds < 0:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_eta(seconds: Optional[int]) -> str:
    """Format ETA seconds."""
    if seconds is None or seconds < 0:
        return "--:--"
    if seconds > 86400:
        return "> 1 day"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m:02d}:{s:02d}"


def sanitize_filename(name: str) -> str:
    """Remove illegal characters for file names."""
    if not name:
        return "youtube_download"
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    cleaned = cleaned.strip()
    return cleaned[:200] if len(cleaned) > 200 else cleaned


def is_playlist_or_channel(url: str) -> bool:
    """Detect if URL is likely a playlist or channel URL."""
    url_lower = url.lower()
    return (
        "list=" in url_lower or
        "/playlist" in url_lower or
        "/@" in url_lower or
        "/channel/" in url_lower or
        "/c/" in url_lower or
        "/user/" in url_lower or
        "/videos" in url_lower or
        "/featured" in url_lower or
        "/shorts" in url_lower and "list=" in url_lower
    )


def open_folder(path_str: str):
    """Opens folder in Explorer, selecting the file if path is a file."""
    p = Path(path_str).resolve()
    if p.is_file():
        if sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{str(p)}"])
        else:
            subprocess.run(["xdg-open", str(p.parent)])
    elif p.is_dir():
        if sys.platform == "win32":
            os.startfile(str(p))
        else:
            subprocess.run(["xdg-open", str(p)])
    else:
        # Parent may exist
        if p.parent.exists():
            if sys.platform == "win32":
                os.startfile(str(p.parent))
            else:
                subprocess.run(["xdg-open", str(p.parent)])


def open_file(path_str: str):
    """Opens the file in the default system media player."""
    p = Path(path_str).resolve()
    if p.exists() and p.is_file():
        if sys.platform == "win32":
            os.startfile(str(p))
        else:
            subprocess.run(["xdg-open", str(p)])
