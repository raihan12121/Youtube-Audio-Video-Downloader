"""
Multithreaded download queue engine powered by yt-dlp.
Manages concurrent downloads, progress reporting, pause/cancel, and format conversion.
"""

import os
import queue
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import yt_dlp

from src.config import config
from src.core.history import history
from src.core.utils import format_bytes, format_eta, format_speed, sanitize_filename


class CancelledException(Exception):
    """Exception raised when download is cancelled by user."""
    pass


class DownloadTask:
    """Represents a single download job in the queue."""

    def __init__(
        self,
        url: str,
        title: str = "Fetching info...",
        channel: str = "",
        thumbnail: str = "",
        duration: int = 0,
        mode: str = "video",            # "video" or "audio"
        quality: str = "Best Available",# "1080p", "720p", "320 kbps", etc.
        container: str = "mp4",         # "mp4", "mp3", "m4a", etc.
        output_dir: Optional[str] = None,
        subfolder: Optional[str] = None,
        filename_prefix: str = "",
        task_id: Optional[str] = None,
    ):
        self.id = task_id or str(uuid.uuid4())
        self.url = url
        self.title = title
        self.channel = channel
        self.thumbnail = thumbnail
        self.duration = duration
        self.mode = mode.lower()
        self.quality = quality
        self.container = container.lower()
        self.output_dir = output_dir or config.download_dir
        self.subfolder = sanitize_filename(subfolder) if subfolder else ""
        self.filename_prefix = filename_prefix

        # Progress and state
        self.status = "QUEUED"          # QUEUED, DOWNLOADING, PROCESSING, COMPLETED, CANCELLED, FAILED, PAUSED
        self.progress = 0.0             # 0.0 to 100.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.speed = 0.0
        self.speed_str = "-- KB/s"
        self.eta_seconds = 0
        self.eta_str = "--:--"
        self.error_message = ""
        self.final_filepath = ""
        self.created_at = time.time()
        self.completed_at: Optional[float] = None

        # Control flags
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()
        self.status = "CANCELLED"

    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()


class DownloadEngine:
    """Queue manager and thread pool executor for download tasks."""

    def __init__(self):
        self.tasks: Dict[str, DownloadTask] = {}
        self.task_order: List[str] = []
        self._work_queue = queue.Queue()
        self._workers: List[threading.Thread] = []
        self._lock = threading.RLock()
        self._running = True

        # Callbacks
        self.on_task_added: Optional[Callable[[DownloadTask], None]] = None
        self.on_task_updated: Optional[Callable[[DownloadTask], None]] = None
        self.on_task_completed: Optional[Callable[[DownloadTask], None]] = None
        self.on_task_failed: Optional[Callable[[DownloadTask, str], None]] = None

        self._start_workers()

    def _start_workers(self):
        max_workers = config.get("max_concurrent_downloads", 3)
        for i in range(max_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True, name=f"DownloadWorker-{i+1}")
            t.start()
            self._workers.append(t)

    def _worker_loop(self):
        while self._running:
            try:
                task: DownloadTask = self._work_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if not task or task.is_cancelled():
                self._work_queue.task_done()
                continue

            try:
                self._execute_download(task)
            except Exception as e:
                task.status = "FAILED"
                task.error_message = str(e)
                if self.on_task_failed:
                    self.on_task_failed(task, str(e))
                if self.on_task_updated:
                    self.on_task_updated(task)
            finally:
                self._work_queue.task_done()

    def add_task(self, task: DownloadTask):
        with self._lock:
            self.tasks[task.id] = task
            self.task_order.append(task.id)
            self._work_queue.put(task)
            if self.on_task_added:
                self.on_task_added(task)

    def add_batch(self, tasks: List[DownloadTask]):
        for t in tasks:
            self.add_task(t)

    def cancel_task(self, task_id: str):
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.cancel()
                if self.on_task_updated:
                    self.on_task_updated(task)

    def cancel_all(self):
        with self._lock:
            for task in self.tasks.values():
                if task.status in ["QUEUED", "DOWNLOADING", "PROCESSING"]:
                    task.cancel()
                    if self.on_task_updated:
                        self.on_task_updated(task)

    def clear_completed(self):
        with self._lock:
            to_remove = [
                tid for tid, t in self.tasks.items()
                if t.status in ["COMPLETED", "CANCELLED", "FAILED"]
            ]
            for tid in to_remove:
                del self.tasks[tid]
                if tid in self.task_order:
                    self.task_order.remove(tid)

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[DownloadTask]:
        with self._lock:
            return [self.tasks[tid] for tid in self.task_order if tid in self.tasks]

    def _execute_download(self, task: DownloadTask):
        if task.is_cancelled():
            return

        task.status = "DOWNLOADING"
        if self.on_task_updated:
            self.on_task_updated(task)

        target_dir = Path(task.output_dir)
        if task.subfolder:
            target_dir = target_dir / task.subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        # Output template
        prefix = f"{task.filename_prefix} - " if task.filename_prefix else ""
        outtmpl = str(target_dir / f"{prefix}%(title)s.%(ext)s")

        # Progress hook for yt-dlp
        def progress_hook(d: Dict[str, Any]):
            if task.is_cancelled():
                raise CancelledException("Download cancelled by user.")

            status = d.get("status")
            if status == "downloading":
                task.status = "DOWNLOADING"
                downloaded = d.get("downloaded_bytes") or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                speed = d.get("speed") or 0.0
                eta = d.get("eta") or 0

                task.downloaded_bytes = downloaded
                task.total_bytes = total
                task.speed = speed
                task.speed_str = format_speed(speed)
                task.eta_seconds = eta
                task.eta_str = format_eta(eta)

                if total > 0:
                    task.progress = min(99.0, (downloaded / total) * 100.0)
                else:
                    task.progress = 50.0

                if self.on_task_updated:
                    self.on_task_updated(task)

            elif status == "finished":
                task.status = "PROCESSING"
                task.progress = 99.0
                task.speed_str = "Merging / Converting..."
                task.eta_str = "--:--"
                if self.on_task_updated:
                    self.on_task_updated(task)

        # Post-processor hook
        def postprocessor_hook(d: Dict[str, Any]):
            if task.is_cancelled():
                raise CancelledException("Download cancelled by user.")
            if d.get("status") == "processing":
                task.status = "PROCESSING"
                pp_name = d.get("postprocessor", "Processing")
                task.speed_str = f"{pp_name}..."
                if self.on_task_updated:
                    self.on_task_updated(task)

        # Build yt-dlp options
        ydl_opts = self._build_ydl_options(task, outtmpl, progress_hook, postprocessor_hook)

        final_path = ""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(task.url, download=True)
                if info:
                    task.title = info.get("title", task.title)
                    task.channel = info.get("uploader") or info.get("channel") or task.channel
                    task.duration = info.get("duration") or task.duration
                    if not task.thumbnail and info.get("thumbnail"):
                        task.thumbnail = info["thumbnail"]

                    # Determine final file path
                    if "_filename" in info:
                        final_path = info["_filename"]
                    elif "requested_downloads" in info and info["requested_downloads"]:
                        final_path = info["requested_downloads"][0].get("filepath", "")

            # If final_path has extension changed by postprocessor
            if not final_path or not Path(final_path).exists():
                # Scan directory for matching title
                safe_t = sanitize_filename(task.title)
                for f in target_dir.glob(f"*{task.container}*"):
                    if safe_t.lower() in f.name.lower() or task.id in f.name:
                        final_path = str(f)
                        break

            task.final_filepath = final_path or str(target_dir)
            task.status = "COMPLETED"
            task.progress = 100.0
            task.speed_str = "Completed"
            task.eta_str = "00:00"
            task.completed_at = time.time()

            file_size = 0
            if final_path and Path(final_path).exists():
                file_size = Path(final_path).stat().st_size
                task.total_bytes = file_size

            # Save to SQLite history
            history.add_record(
                title=task.title,
                url=task.url,
                file_path=task.final_filepath,
                file_size=file_size,
                mode=task.mode,
                format_name=task.container,
                resolution=task.quality,
                duration=task.duration,
                channel=task.channel,
            )

            if self.on_task_completed:
                self.on_task_completed(task)
            if self.on_task_updated:
                self.on_task_updated(task)

        except CancelledException:
            task.status = "CANCELLED"
            task.speed_str = "Cancelled"
            if self.on_task_updated:
                self.on_task_updated(task)

        except Exception as e:
            task.status = "FAILED"
            task.error_message = str(e)
            task.speed_str = "Failed"
            if self.on_task_failed:
                self.on_task_failed(task, str(e))
            if self.on_task_updated:
                self.on_task_updated(task)

    def _build_ydl_options(
        self,
        task: DownloadTask,
        outtmpl: str,
        progress_hook: Callable,
        postprocessor_hook: Callable
    ) -> Dict[str, Any]:
        """Constructs yt-dlp arguments dictionary based on format and preferences."""
        opts: Dict[str, Any] = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "progress_hooks": [progress_hook],
            "postprocessor_hooks": [postprocessor_hook],
            "noplaylist": True,  # Download the single video inside this task
        }

        # Enable node.js runtime for YouTube challenges
        if shutil.which("node"):
            opts["js_runtimes"] = {"node": {}}
            opts["remote_components"] = ["ejs:github"]

        # Browser cookies
        browser = config.get("browser_cookies", "none")
        if browser and browser != "none":
            opts["cookiesfrombrowser"] = (browser,)

        custom_cookies = config.get("custom_cookies_path", "")
        if custom_cookies:
            opts["cookiefile"] = custom_cookies

        # Rate limit
        rate_limit_mb = config.get("rate_limit_mb", 0)
        if rate_limit_mb and rate_limit_mb > 0:
            opts["ratelimit"] = rate_limit_mb * 1024 * 1024

        postprocessors = []

        if task.mode == "audio":
            # Audio-only extraction
            opts["format"] = "bestaudio/best"
            target_codec = task.container if task.container in ["mp3", "m4a", "wav", "flac", "opus"] else "mp3"

            # Parse audio quality (e.g. "320 kbps" -> "320")
            quality_num = "320"
            for q in ["320", "256", "192", "128"]:
                if q in task.quality:
                    quality_num = q
                    break

            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": target_codec,
                "preferredquality": quality_num,
            })

            # Embed thumbnail as album art
            if config.get("embed_thumbnail", True):
                opts["writethumbnail"] = True
                postprocessors.append({"key": "FFmpegThumbnailsConvertor", "format": "jpg"})
                postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})

            # Embed metadata (Artist, Title, Year)
            if config.get("embed_metadata", True):
                postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})

        else:
            # Video + Audio download & merge
            quality_str = task.quality
            max_height = 0
            if "2160p" in quality_str or "4K" in quality_str:
                max_height = 2160
            elif "1440p" in quality_str or "2K" in quality_str:
                max_height = 1440
            elif "1080p" in quality_str:
                max_height = 1080
            elif "720p" in quality_str:
                max_height = 720
            elif "480p" in quality_str:
                max_height = 480
            elif "360p" in quality_str:
                max_height = 360

            if max_height > 0:
                opts["format"] = (
                    f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best"
                )
            else:
                opts["format"] = "bestvideo+bestaudio/best"

            container = task.container if task.container in ["mp4", "mkv", "webm"] else "mp4"
            opts["merge_output_format"] = container

            # Embed subtitles
            if config.get("download_subtitles", False):
                opts["writesubtitles"] = True
                opts["writeautomaticsub"] = True
                opts["subtitleslangs"] = [config.get("subtitles_lang", "en")]
                postprocessors.append({"key": "FFmpegEmbedSubtitle"})

            # Embed thumbnail into video container
            if config.get("embed_thumbnail", True) and container in ["mp4", "mkv"]:
                opts["writethumbnail"] = True
                postprocessors.append({"key": "FFmpegThumbnailsConvertor", "format": "jpg"})
                postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})

            # Embed metadata
            if config.get("embed_metadata", True):
                postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})

        if postprocessors:
            opts["postprocessors"] = postprocessors

        return opts


# Global downloader engine
downloader = DownloadEngine()
