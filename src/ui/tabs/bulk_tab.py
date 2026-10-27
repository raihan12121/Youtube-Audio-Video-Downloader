"""
Multi-URL Bulk Downloader tab.
Allows pasting multiple YouTube links at once and queueing them in batch.
"""

from typing import Callable, Optional
import customtkinter as ctk

from src.config import config
from src.core.downloader import DownloadTask, downloader
from src.core.utils import sanitize_filename


class BulkTab(ctk.CTkFrame):
    """Tab for pasting a list of arbitrary YouTube URLs and batch downloading."""

    def __init__(self, master, on_queue_jump: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_queue_jump = on_queue_jump

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 6))

        title_lbl = ctk.CTkLabel(
            header,
            text="Multi-URL Bulk Downloader",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            header,
            text="Paste multiple YouTube links (one per line) to queue all of them simultaneously.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65")
        )
        sub_lbl.pack(anchor="w")

        # 2. Options card
        opt_card = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray92", "#1E222B"))
        opt_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        opt_card.grid_columnconfigure(1, weight=1)

        opt_row = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_row.pack(fill="x", padx=16, pady=12)

        # Mode
        self.mode_var = ctk.StringVar(value="video")
        self.mode_btn = ctk.CTkSegmentedButton(
            opt_row,
            values=["Video + Audio", "Audio Only (MP3)"],
            command=self._on_mode_change
        )
        self.mode_btn.set("Video + Audio")
        self.mode_btn.pack(side="left", padx=(0, 12))

        # Quality
        self.quality_var = ctk.StringVar(value="Best Available")
        self.quality_menu = ctk.CTkOptionMenu(
            opt_row,
            variable=self.quality_var,
            values=["Best Available", "1080p (Full HD)", "720p (HD)", "480p", "360p"],
            width=150,
            height=30
        )
        self.quality_menu.pack(side="left", padx=(0, 12))

        # Subfolder option
        self.subfolder_entry = ctk.CTkEntry(
            opt_row,
            placeholder_text="Optional Subfolder Name...",
            width=200,
            height=30
        )
        self.subfolder_entry.pack(side="left")

        # 3. Multiline URL Textbox
        text_card = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray92", "#1E222B"))
        text_card.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        text_card.grid_columnconfigure(0, weight=1)
        text_card.grid_rowconfigure(1, weight=1)

        t_header = ctk.CTkFrame(text_card, fg_color="transparent")
        t_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        t_lbl = ctk.CTkLabel(
            t_header,
            text="Paste YouTube URLs below (one per line):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        t_lbl.pack(side="left")

        clear_btn = ctk.CTkButton(
            t_header,
            text="✕ Clear",
            width=65,
            height=26,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            command=self._clear_text
        )
        clear_btn.pack(side="right", padx=(6, 0))

        paste_btn = ctk.CTkButton(
            t_header,
            text="📋 Paste Clipboard",
            width=110,
            height=26,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            command=self._paste_clipboard
        )
        paste_btn.pack(side="right")

        self.url_box = ctk.CTkTextbox(
            text_card,
            font=ctk.CTkFont(size=12),
            wrap="none"
        )
        self.url_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self.url_box.bind("<KeyRelease>", lambda e: self._update_count())

        # 4. Bottom action
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))

        self.queue_btn = ctk.CTkButton(
            bottom_frame,
            text="⬇  Add All URLs to Queue (0)",
            height=46,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#38A169", "#2F855A"),
            hover_color=("#2F855A", "#276749"),
            state="disabled",
            command=self._handle_queue_all
        )
        self.queue_btn.pack(fill="x")

    def _on_mode_change(self, choice: str):
        if choice == "Audio Only (MP3)":
            self.mode_var.set("audio")
            self.quality_menu.configure(values=["320 kbps (High Quality)", "256 kbps", "192 kbps", "128 kbps"])
            self.quality_var.set("320 kbps (High Quality)")
        else:
            self.mode_var.set("video")
            self.quality_menu.configure(values=["Best Available", "1080p (Full HD)", "720p (HD)", "480p", "360p"])
            self.quality_var.set("Best Available")

    def _clear_text(self):
        self.url_box.delete("1.0", "end")
        self._update_count()

    def _paste_clipboard(self):
        try:
            cb = self.clipboard_get()
            self.url_box.insert("insert", cb)
            self._update_count()
        except Exception:
            pass

    def _get_urls(self):
        content = self.url_box.get("1.0", "end").strip()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        valid_urls = [u for u in lines if "youtube.com" in u or "youtu.be" in u or "http" in u]
        return valid_urls

    def _update_count(self):
        urls = self._get_urls()
        count = len(urls)
        if count > 0:
            self.queue_btn.configure(
                state="normal",
                text=f"⬇  Add All URLs to Queue ({count})"
            )
        else:
            self.queue_btn.configure(
                state="disabled",
                text="⬇  Add All URLs to Queue (0)"
            )

    def _handle_queue_all(self):
        urls = self._get_urls()
        if not urls:
            return

        mode = self.mode_var.get()
        quality = self.quality_var.get()
        container = "mp3" if mode == "audio" else "mp4"
        subfolder = sanitize_filename(self.subfolder_entry.get().strip())

        tasks = []
        for idx, u in enumerate(urls, 1):
            task = DownloadTask(
                url=u,
                title=f"Bulk Item #{idx}",
                mode=mode,
                quality=quality,
                container=container,
                subfolder=subfolder
            )
            tasks.append(task)

        downloader.add_batch(tasks)

        self.url_box.delete("1.0", "end")
        self._update_count()

        if self.on_queue_jump:
            self.after(300, self.on_queue_jump)
