"""
Single Video / Audio Downloader tab with instant preview and format picker.
"""

import threading
from tkinter import filedialog
from typing import Callable, Optional
import customtkinter as ctk

from src.config import config
from src.core.downloader import DownloadTask, downloader
from src.core.extractor import extract_single_info
from src.core.utils import format_bytes, format_duration
from src.utils.thumbnail_cache import thumbnail_cache


class SingleTab(ctk.CTkFrame):
    """Tab for downloading individual videos or audio tracks with live metadata preview."""

    def __init__(self, master, on_queue_jump: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_queue_jump = on_queue_jump
        self.current_info = None

        self._setup_ui()

    def _setup_ui(self):
        # Scrollable container for smaller screens
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=15)
        self.container.grid_columnconfigure(0, weight=1)

        # 1. Header
        header_lbl = ctk.CTkLabel(
            self.container,
            text="Single Video & Audio Downloader",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header_lbl.grid(row=0, column=0, sticky="w", pady=(0, 4))

        sub_lbl = ctk.CTkLabel(
            self.container,
            text="Paste any YouTube video or short URL to inspect and download in ultra-high quality.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65")
        )
        sub_lbl.grid(row=1, column=0, sticky="w", pady=(0, 16))

        # 2. URL Input Card
        input_card = ctk.CTkFrame(self.container, corner_radius=10, fg_color=("gray92", "#1E222B"))
        input_card.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        input_card.grid_columnconfigure(0, weight=1)

        input_row = ctk.CTkFrame(input_card, fg_color="transparent")
        input_row.pack(fill="x", padx=16, pady=16)
        input_row.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Paste YouTube URL here (e.g. https://www.youtube.com/watch?v=...)",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.url_entry.bind("<Return>", lambda e: self._start_fetch())

        paste_btn = ctk.CTkButton(
            input_row,
            text="📋 Paste",
            width=80,
            height=40,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            command=self._handle_paste
        )
        paste_btn.grid(row=0, column=1, padx=(0, 8))

        self.fetch_btn = ctk.CTkButton(
            input_row,
            text="🔍 Inspect Video",
            width=120,
            height=40,
            fg_color=("#3182CE", "#2B6CB0"),
            hover_color=("#2B6CB0", "#2C5282"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._start_fetch
        )
        self.fetch_btn.grid(row=0, column=2)

        self.status_lbl = ctk.CTkLabel(
            input_card,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60")
        )
        self.status_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # 3. Preview Card (hidden until fetched)
        self.preview_card = ctk.CTkFrame(self.container, corner_radius=10, fg_color=("gray92", "#1E222B"))
        self.preview_card.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        self.preview_card.grid_columnconfigure(1, weight=1)

        # Thumbnail
        self.thumb_preview = ctk.CTkLabel(self.preview_card, text="", width=240, height=135)
        self.thumb_preview.grid(row=0, column=0, rowspan=4, padx=16, pady=16)

        # Details
        self.prev_title = ctk.CTkLabel(
            self.preview_card,
            text="Video Title",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=480
        )
        self.prev_title.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=(16, 4))

        self.prev_channel = ctk.CTkLabel(
            self.preview_card,
            text="👤 Channel Name",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65"),
            anchor="w"
        )
        self.prev_channel.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=(0, 4))

        self.prev_meta = ctk.CTkLabel(
            self.preview_card,
            text="⏱ Duration: 00:00  •  👁 Views: 0",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.prev_meta.grid(row=2, column=1, sticky="w", padx=(0, 16), pady=(0, 8))

        # Initially hide preview card
        self.preview_card.grid_remove()

        # 4. Format & Options Card
        self.options_card = ctk.CTkFrame(self.container, corner_radius=10, fg_color=("gray92", "#1E222B"))
        self.options_card.grid(row=4, column=0, sticky="ew", pady=(0, 16))
        self.options_card.grid_columnconfigure(1, weight=1)

        opt_title = ctk.CTkLabel(
            self.options_card,
            text="Download Settings & Format Preset",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        opt_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))

        # Mode selector
        mode_lbl = ctk.CTkLabel(self.options_card, text="Download Mode:", font=ctk.CTkFont(size=12))
        mode_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=8)

        self.mode_var = ctk.StringVar(value="video")
        self.mode_selector = ctk.CTkSegmentedButton(
            self.options_card,
            values=["Video + Audio", "Audio Only"],
            command=self._on_mode_change
        )
        self.mode_selector.set("Video + Audio")
        self.mode_selector.grid(row=1, column=1, sticky="w", padx=16, pady=8)

        # Video resolution row
        self.res_lbl = ctk.CTkLabel(self.options_card, text="Video Quality:", font=ctk.CTkFont(size=12))
        self.res_lbl.grid(row=2, column=0, sticky="w", padx=16, pady=8)

        self.res_var = ctk.StringVar(value="Best Available")
        self.res_dropdown = ctk.CTkOptionMenu(
            self.options_card,
            variable=self.res_var,
            values=["Best Available", "2160p (4K)", "1440p (2K)", "1080p (Full HD)", "720p (HD)", "480p", "360p"],
            width=200
        )
        self.res_dropdown.grid(row=2, column=1, sticky="w", padx=16, pady=8)

        # Video format row
        self.format_lbl = ctk.CTkLabel(self.options_card, text="File Container:", font=ctk.CTkFont(size=12))
        self.format_lbl.grid(row=3, column=0, sticky="w", padx=16, pady=8)

        self.format_var = ctk.StringVar(value="mp4")
        self.format_dropdown = ctk.CTkOptionMenu(
            self.options_card,
            variable=self.format_var,
            values=["mp4", "mkv", "webm"],
            width=200
        )
        self.format_dropdown.grid(row=3, column=1, sticky="w", padx=16, pady=8)

        # Audio quality row (hidden for video)
        self.audio_bitrate_lbl = ctk.CTkLabel(self.options_card, text="Audio Bitrate:", font=ctk.CTkFont(size=12))
        self.audio_bitrate_var = ctk.StringVar(value="320 kbps")
        self.audio_bitrate_dropdown = ctk.CTkOptionMenu(
            self.options_card,
            variable=self.audio_bitrate_var,
            values=["320 kbps", "256 kbps", "192 kbps", "128 kbps"],
            width=200
        )

        # Audio format row (hidden for video)
        self.audio_fmt_lbl = ctk.CTkLabel(self.options_card, text="Audio Format:", font=ctk.CTkFont(size=12))
        self.audio_fmt_var = ctk.StringVar(value="mp3")
        self.audio_fmt_dropdown = ctk.CTkOptionMenu(
            self.options_card,
            variable=self.audio_fmt_var,
            values=["mp3", "m4a", "wav", "flac", "opus"],
            width=200
        )

        # Checkboxes
        self.subtitles_var = ctk.BooleanVar(value=config.get("download_subtitles", False))
        self.subtitles_chk = ctk.CTkCheckBox(
            self.options_card,
            text="Download subtitles (.srt / embedded)",
            variable=self.subtitles_var
        )
        self.subtitles_chk.grid(row=4, column=1, sticky="w", padx=16, pady=(8, 14))

        # 5. Output Directory Row
        dir_card = ctk.CTkFrame(self.container, corner_radius=10, fg_color=("gray92", "#1E222B"))
        dir_card.grid(row=5, column=0, sticky="ew", pady=(0, 20))
        dir_card.grid_columnconfigure(1, weight=1)

        dir_lbl = ctk.CTkLabel(dir_card, text="Save To:", font=ctk.CTkFont(size=12, weight="bold"))
        dir_lbl.grid(row=0, column=0, padx=(16, 10), pady=14)

        self.dir_entry = ctk.CTkEntry(dir_card, height=36)
        self.dir_entry.insert(0, config.download_dir)
        self.dir_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=14)

        browse_btn = ctk.CTkButton(
            dir_card,
            text="Browse...",
            width=90,
            height=36,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            command=self._handle_browse
        )
        browse_btn.grid(row=0, column=2, padx=(0, 16), pady=14)

        # 6. Big Download Button
        self.download_btn = ctk.CTkButton(
            self.container,
            text="⬇  Add to Queue & Download",
            height=50,
            corner_radius=10,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#38A169", "#2F855A"),
            hover_color=("#2F855A", "#276749"),
            command=self._handle_download
        )
        self.download_btn.grid(row=6, column=0, sticky="ew", pady=(0, 25))

    def _handle_paste(self):
        try:
            clipboard = self.clipboard_get().strip()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clipboard)
            self._start_fetch()
        except Exception:
            pass

    def _handle_browse(self):
        folder = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)
            config.download_dir = folder

    def _on_mode_change(self, choice: str):
        if choice == "Audio Only":
            self.mode_var.set("audio")
            # Hide video options
            self.res_lbl.grid_remove()
            self.res_dropdown.grid_remove()
            self.format_lbl.grid_remove()
            self.format_dropdown.grid_remove()
            self.subtitles_chk.grid_remove()

            # Show audio options
            self.audio_bitrate_lbl.grid(row=2, column=0, sticky="w", padx=16, pady=8)
            self.audio_bitrate_dropdown.grid(row=2, column=1, sticky="w", padx=16, pady=8)
            self.audio_fmt_lbl.grid(row=3, column=0, sticky="w", padx=16, pady=8)
            self.audio_fmt_dropdown.grid(row=3, column=1, sticky="w", padx=16, pady=8)
        else:
            self.mode_var.set("video")
            # Hide audio options
            self.audio_bitrate_lbl.grid_remove()
            self.audio_bitrate_dropdown.grid_remove()
            self.audio_fmt_lbl.grid_remove()
            self.audio_fmt_dropdown.grid_remove()

            # Show video options
            self.res_lbl.grid(row=2, column=0, sticky="w", padx=16, pady=8)
            self.res_dropdown.grid(row=2, column=1, sticky="w", padx=16, pady=8)
            self.format_lbl.grid(row=3, column=0, sticky="w", padx=16, pady=8)
            self.format_dropdown.grid(row=3, column=1, sticky="w", padx=16, pady=8)
            self.subtitles_chk.grid(row=4, column=1, sticky="w", padx=16, pady=(8, 14))

    def _start_fetch(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_lbl.configure(text="⚠ Please enter or paste a valid YouTube URL", text_color="#E53E3E")
            return

        self.status_lbl.configure(text="🔍 Connecting and fetching video details...", text_color=("#3182CE", "#63B3ED"))
        self.fetch_btn.configure(state="disabled")

        threading.Thread(target=self._fetch_worker, args=(url,), daemon=True).start()

    def _fetch_worker(self, url: str):
        try:
            info = extract_single_info(url)
            self.current_info = info
            self.after(0, self._on_fetch_success, info)
        except Exception as e:
            self.after(0, self._on_fetch_error, str(e))

    def _on_fetch_success(self, info: dict):
        self.fetch_btn.configure(state="normal")
        self.status_lbl.configure(text="✓ Video details loaded successfully", text_color=("#38A169", "#68D391"))

        # Update preview card
        self.preview_card.grid()
        self.prev_title.configure(text=info.get("title", ""))
        self.prev_channel.configure(text=f"👤 {info.get('uploader', 'YouTube')}")

        dur_str = format_duration(info.get("duration", 0))
        views = f"{info.get('view_count', 0):,}"
        self.prev_meta.configure(text=f"⏱ Duration: {dur_str}  •  👁 Views: {views}")

        # Load high quality preview thumbnail
        img = thumbnail_cache.get_ctk_image(
            info.get("thumbnail"),
            size=(240, 135),
            on_loaded=lambda c_img: self.thumb_preview.configure(image=c_img)
        )
        self.thumb_preview.configure(image=img)

        # Update available resolutions dropdown
        resolutions = info.get("resolutions", [])
        if resolutions:
            self.res_dropdown.configure(values=resolutions)
            self.res_dropdown.set(resolutions[0])

    def _on_fetch_error(self, err_msg: str):
        self.fetch_btn.configure(state="normal")
        self.status_lbl.configure(
            text=f"⚠ Error: {err_msg[:80]}...",
            text_color="#E53E3E"
        )

    def _handle_download(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_lbl.configure(text="⚠ Please enter a URL first", text_color="#E53E3E")
            return

        mode = self.mode_var.get()
        out_dir = self.dir_entry.get().strip() or config.download_dir

        if mode == "audio":
            task = DownloadTask(
                url=url,
                title=self.current_info.get("title", "YouTube Audio") if self.current_info else "YouTube Audio",
                channel=self.current_info.get("uploader", "") if self.current_info else "",
                thumbnail=self.current_info.get("thumbnail", "") if self.current_info else "",
                duration=self.current_info.get("duration", 0) if self.current_info else 0,
                mode="audio",
                quality=self.audio_bitrate_var.get(),
                container=self.audio_fmt_var.get(),
                output_dir=out_dir
            )
        else:
            task = DownloadTask(
                url=url,
                title=self.current_info.get("title", "YouTube Video") if self.current_info else "YouTube Video",
                channel=self.current_info.get("uploader", "") if self.current_info else "",
                thumbnail=self.current_info.get("thumbnail", "") if self.current_info else "",
                duration=self.current_info.get("duration", 0) if self.current_info else 0,
                mode="video",
                quality=self.res_var.get(),
                container=self.format_var.get(),
                output_dir=out_dir
            )

        downloader.add_task(task)

        # Visual feedback
        self.status_lbl.configure(
            text="✓ Added to download queue! Check Active Downloads tab.",
            text_color=("#38A169", "#68D391")
        )

        # Switch to Queue tab if callback supplied
        if self.on_queue_jump:
            self.after(400, self.on_queue_jump)
