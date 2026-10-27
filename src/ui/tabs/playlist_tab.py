"""
Batch Playlist and Channel Downloader tab.
Fetches all videos from playlists or full channels with interactive selection.
"""

import threading
from tkinter import filedialog
from typing import Callable, Dict, List, Optional
import customtkinter as ctk

from src.config import config
from src.core.downloader import DownloadTask, downloader
from src.core.extractor import extract_playlist_or_channel
from src.core.utils import is_playlist_or_channel, sanitize_filename
from src.ui.components.video_card import VideoCard


class PlaylistTab(ctk.CTkFrame):
    """Tab for downloading playlists and channels in bulk with per-video selection."""

    def __init__(self, master, on_queue_jump: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_queue_jump = on_queue_jump

        self.playlist_data: Optional[Dict] = None
        self.video_cards: List[VideoCard] = []
        self.entries: List[Dict] = []

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # 1. Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 6))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Playlist & Channel Bulk Downloader",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="Download entire playlists or complete channel uploads with smart batch options and sequential naming.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65")
        )
        sub_lbl.pack(anchor="w")

        # 2. Input Card
        input_card = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray92", "#1E222B"))
        input_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        input_card.grid_columnconfigure(0, weight=1)

        row1 = ctk.CTkFrame(input_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(14, 8))
        row1.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            row1,
            placeholder_text="Paste Playlist URL or Channel URL (e.g. https://www.youtube.com/@channel or playlist?list=...)",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.url_entry.bind("<Return>", lambda e: self._start_scan())

        paste_btn = ctk.CTkButton(
            row1,
            text="📋 Paste",
            width=80,
            height=40,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            command=self._handle_paste
        )
        paste_btn.grid(row=0, column=1, padx=(0, 8))

        self.scan_btn = ctk.CTkButton(
            row1,
            text="⚡ Fetch Playlist/Channel",
            width=180,
            height=40,
            fg_color=("#3182CE", "#2B6CB0"),
            hover_color=("#2B6CB0", "#2C5282"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._start_scan
        )
        self.scan_btn.grid(row=0, column=2)

        # Limit row
        row2 = ctk.CTkFrame(input_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 12))

        limit_lbl = ctk.CTkLabel(row2, text="Max Items:", font=ctk.CTkFont(size=11))
        limit_lbl.pack(side="left", padx=(0, 6))

        self.limit_var = ctk.StringVar(value="All Videos")
        self.limit_dropdown = ctk.CTkOptionMenu(
            row2,
            variable=self.limit_var,
            values=["All Videos", "First 25", "First 50", "First 100", "First 200"],
            width=120,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        self.limit_dropdown.pack(side="left", padx=(0, 16))

        self.status_lbl = ctk.CTkLabel(
            row2,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60")
        )
        self.status_lbl.pack(side="left")

        # 3. Batch Options Toolbar (Format, Subfolder, Numbering)
        self.toolbar_card = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray92", "#1E222B"))
        self.toolbar_card.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.toolbar_card.grid_columnconfigure(1, weight=1)

        t_row1 = ctk.CTkFrame(self.toolbar_card, fg_color="transparent")
        t_row1.pack(fill="x", padx=16, pady=10)

        # Mode
        self.batch_mode_var = ctk.StringVar(value="video")
        self.batch_mode_btn = ctk.CTkSegmentedButton(
            t_row1,
            values=["Video + Audio", "Audio Only (MP3)"],
            command=self._on_batch_mode_change
        )
        self.batch_mode_btn.set("Video + Audio")
        self.batch_mode_btn.pack(side="left", padx=(0, 12))

        # Quality
        self.batch_quality_var = ctk.StringVar(value="Best Available")
        self.batch_quality_menu = ctk.CTkOptionMenu(
            t_row1,
            variable=self.batch_quality_var,
            values=["Best Available", "1080p (Full HD)", "720p (HD)", "480p", "360p"],
            width=150,
            height=30
        )
        self.batch_quality_menu.pack(side="left", padx=(0, 12))

        # Subfolder & Numbering switches
        self.subfolder_var = ctk.BooleanVar(value=config.get("organize_playlists_in_subfolders", True))
        self.subfolder_chk = ctk.CTkCheckBox(
            t_row1,
            text="Create Named Subfolder",
            variable=self.subfolder_var
        )
        self.subfolder_chk.pack(side="left", padx=(0, 12))

        self.numbering_var = ctk.BooleanVar(value=config.get("number_playlist_items", True))
        self.numbering_chk = ctk.CTkCheckBox(
            t_row1,
            text="Number sequentially (01 -, 02 -)",
            variable=self.numbering_var
        )
        self.numbering_chk.pack(side="left")

        # Selection action bar
        t_row2 = ctk.CTkFrame(self.toolbar_card, fg_color="transparent")
        t_row2.pack(fill="x", padx=16, pady=(0, 10))

        sel_all_btn = ctk.CTkButton(
            t_row2,
            text="✓ Select All",
            width=90,
            height=28,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            font=ctk.CTkFont(size=11),
            command=self._select_all
        )
        sel_all_btn.pack(side="left", padx=(0, 6))

        desel_all_btn = ctk.CTkButton(
            t_row2,
            text="✕ Deselect All",
            width=90,
            height=28,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            font=ctk.CTkFont(size=11),
            command=self._deselect_all
        )
        desel_all_btn.pack(side="left", padx=(0, 12))

        # Search filter
        self.filter_entry = ctk.CTkEntry(
            t_row2,
            placeholder_text="Filter videos in playlist...",
            height=28,
            width=220,
            font=ctk.CTkFont(size=11)
        )
        self.filter_entry.pack(side="left", padx=(0, 12))
        self.filter_entry.bind("<KeyRelease>", lambda e: self._filter_cards())

        self.count_lbl = ctk.CTkLabel(
            t_row2,
            text="No playlist scanned yet",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray40", "gray65")
        )
        self.count_lbl.pack(side="right")

        # 4. Scrollable Video Checklist Table
        self.table_scroll = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray92", "#1E222B"))
        self.table_scroll.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.table_scroll.grid_columnconfigure(0, weight=1)

        # Placeholder message inside table
        self.empty_lbl = ctk.CTkLabel(
            self.table_scroll,
            text="Paste a Playlist or Channel link above and click 'Fetch Playlist/Channel'\nto load all videos for bulk download.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60")
        )
        self.empty_lbl.pack(pady=60)

        # 5. Bottom Action Bar
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 15))
        bottom_frame.grid_columnconfigure(1, weight=1)

        self.batch_download_btn = ctk.CTkButton(
            bottom_frame,
            text="⬇  Download Selected Videos (0)",
            height=46,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#38A169", "#2F855A"),
            hover_color=("#2F855A", "#276749"),
            state="disabled",
            command=self._handle_batch_download
        )
        self.batch_download_btn.pack(fill="x")

    def _handle_paste(self):
        try:
            clipboard = self.clipboard_get().strip()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clipboard)
            self._start_scan()
        except Exception:
            pass

    def _on_batch_mode_change(self, val: str):
        if val == "Audio Only (MP3)":
            self.batch_mode_var.set("audio")
            self.batch_quality_menu.configure(values=["320 kbps (High Quality)", "256 kbps", "192 kbps", "128 kbps"])
            self.batch_quality_var.set("320 kbps (High Quality)")
        else:
            self.batch_mode_var.set("video")
            self.batch_quality_menu.configure(values=["Best Available", "1080p (Full HD)", "720p (HD)", "480p", "360p"])
            self.batch_quality_var.set("Best Available")

    def _start_scan(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_lbl.configure(text="⚠ Please enter a valid URL", text_color="#E53E3E")
            return

        self.scan_btn.configure(state="disabled")
        self.status_lbl.configure(text="🔍 Scanning playlist/channel...", text_color=("#3182CE", "#63B3ED"))

        # Determine limit
        limit_text = self.limit_var.get()
        max_items = None
        if "25" in limit_text:
            max_items = 25
        elif "50" in limit_text:
            max_items = 50
        elif "100" in limit_text:
            max_items = 100
        elif "200" in limit_text:
            max_items = 200

        threading.Thread(
            target=self._scan_worker,
            args=(url, max_items),
            daemon=True
        ).start()

    def _scan_worker(self, url: str, max_items: Optional[int]):
        try:
            data = extract_playlist_or_channel(url, max_items=max_items)
            self.playlist_data = data
            self.entries = data.get("entries", [])
            self.after(0, self._render_entries)
        except Exception as e:
            self.after(0, self._on_scan_error, str(e))

    def _render_entries(self):
        self.scan_btn.configure(state="normal")
        self.empty_lbl.pack_forget()

        # Clear existing cards
        for card in self.video_cards:
            card.destroy()
        self.video_cards.clear()

        # Update info header
        title = self.playlist_data.get("title", "Playlist")
        total = len(self.entries)
        self.status_lbl.configure(
            text=f"✓ Found {total} videos in '{title[:35]}...'",
            text_color=("#38A169", "#68D391")
        )

        # Create cards
        for entry in self.entries:
            card = VideoCard(
                self.table_scroll,
                entry=entry,
                on_toggle=self._on_item_toggled
            )
            card.pack(fill="x", pady=2)
            self.video_cards.append(card)

        self._update_selection_counter()

    def _on_scan_error(self, err_msg: str):
        self.scan_btn.configure(state="normal")
        self.status_lbl.configure(
            text=f"⚠ Scan Error: {err_msg[:70]}",
            text_color="#E53E3E"
        )

    def _on_item_toggled(self, entry: Dict, selected: bool):
        self._update_selection_counter()

    def _select_all(self):
        for card in self.video_cards:
            card.set_selected(True)
        self._update_selection_counter()

    def _deselect_all(self):
        for card in self.video_cards:
            card.set_selected(False)
        self._update_selection_counter()

    def _filter_cards(self):
        query = self.filter_entry.get().strip().lower()
        for card in self.video_cards:
            title = card.entry.get("title", "").lower()
            if not query or query in title:
                card.pack(fill="x", pady=2)
            else:
                card.pack_forget()

    def _update_selection_counter(self):
        sel_count = sum(1 for e in self.entries if e.get("selected", True))
        tot_count = len(self.entries)
        self.count_lbl.configure(text=f"Selected: {sel_count} / {tot_count}")

        if sel_count > 0:
            self.batch_download_btn.configure(
                state="normal",
                text=f"⬇  Download Selected Videos ({sel_count})"
            )
        else:
            self.batch_download_btn.configure(
                state="disabled",
                text="⬇  Download Selected Videos (0)"
            )

    def _handle_batch_download(self):
        selected_entries = [e for e in self.entries if e.get("selected", True)]
        if not selected_entries:
            return

        mode = self.batch_mode_var.get()
        quality = self.batch_quality_var.get()

        # Subfolder setup
        subfolder = None
        if self.subfolder_var.get() and self.playlist_data:
            subfolder = sanitize_filename(self.playlist_data.get("title", "Playlist"))

        tasks = []
        for e in selected_entries:
            prefix = f"{e['index']:02d}" if self.numbering_var.get() else ""
            container = "mp3" if mode == "audio" else "mp4"

            task = DownloadTask(
                url=e["url"],
                title=e.get("title", "YouTube Video"),
                channel=e.get("uploader", ""),
                thumbnail=e.get("thumbnail", ""),
                duration=e.get("duration", 0),
                mode=mode,
                quality=quality,
                container=container,
                subfolder=subfolder,
                filename_prefix=prefix
            )
            tasks.append(task)

        downloader.add_batch(tasks)

        self.status_lbl.configure(
            text=f"✓ Queued {len(tasks)} videos for download!",
            text_color=("#38A169", "#68D391")
        )

        if self.on_queue_jump:
            self.after(400, self.on_queue_jump)
