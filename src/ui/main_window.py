"""
Main Application Window with modern sidebar navigation and dynamic tab switching.
"""

from typing import Dict
import customtkinter as ctk

from src.config import config
from src.core.downloader import downloader
from src.core.utils import check_ffmpeg
from src.ui.tabs.bulk_tab import BulkTab
from src.ui.tabs.history_tab import HistoryTab
from src.ui.tabs.playlist_tab import PlaylistTab
from src.ui.tabs.queue_tab import QueueTab
from src.ui.tabs.settings_tab import SettingsTab
from src.ui.tabs.single_tab import SingleTab


class MainWindow(ctk.CTk):
    """The root window for the YouTube Downloader desktop application."""

    def __init__(self):
        super().__init__()

        # Appearance configuration
        app_mode = config.get("appearance_mode", "Dark")
        ctk.set_appearance_mode(app_mode)
        ctk.set_default_color_theme("blue")

        # Window settings
        self.title("YouTube Video & Bulk Downloader Pro")
        self.geometry("1100x720")
        self.minsize(960, 600)

        # Main layout: 2 columns (Sidebar + Content area)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_tab_name = ""
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.tab_frames: Dict[str, ctk.CTkFrame] = {}

        self._build_sidebar()
        self._build_content_area()

        # Default tab
        self.select_tab("single")

        # Periodically update badge counts on sidebar
        self._start_sidebar_badge_loop()

    def _build_sidebar(self):
        """Creates the left navigation sidebar."""
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("gray95", "#14171E"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)  # Spacer push down

        # App Logo & Branding
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(24, 20), sticky="ew")

        brand_row = ctk.CTkFrame(logo_frame, fg_color="transparent")
        brand_row.pack(anchor="w")

        icon_lbl = ctk.CTkLabel(
            brand_row,
            text="▶",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FF0000"
        )
        icon_lbl.pack(side="left", padx=(0, 8))

        app_title = ctk.CTkLabel(
            brand_row,
            text="YT Downloader",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        app_title.pack(side="left")

        ver_lbl = ctk.CTkLabel(
            logo_frame,
            text="Desktop Pro Edition • v2.0",
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray50")
        )
        ver_lbl.pack(anchor="w", padx=(2, 0))

        # Nav Buttons Definition
        nav_items = [
            ("single", "🎬  Single Media", lambda: self.select_tab("single")),
            ("playlist", "📑  Playlist & Channel", lambda: self.select_tab("playlist")),
            ("bulk", "📋  Bulk URLs", lambda: self.select_tab("bulk")),
            ("queue", "⏳  Active Downloads", lambda: self.select_tab("queue")),
            ("history", "📚  Library / History", lambda: self.select_tab("history")),
            ("settings", "⚙️  Settings & Tools", lambda: self.select_tab("settings")),
        ]

        for idx, (tab_id, label, cmd) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                height=42,
                corner_radius=8,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="transparent",
                text_color=("gray20", "gray90"),
                hover_color=("gray85", "#1E222B"),
                command=cmd
            )
            btn.grid(row=idx, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[tab_id] = btn

        # Bottom System Indicator
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.grid(row=8, column=0, padx=16, pady=16, sticky="ew")

        has_ffmpeg, _ = check_ffmpeg()
        ff_text = "🟢 FFmpeg Ready" if has_ffmpeg else "🔴 FFmpeg Missing"
        self.ff_badge = ctk.CTkLabel(
            bottom_frame,
            text=ff_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#38A169" if has_ffmpeg else "#E53E3E")
        )
        self.ff_badge.pack(anchor="w")

    def _build_content_area(self):
        """Builds all tab views inside the main container."""
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Initialize all tab widgets
        self.tab_frames["single"] = SingleTab(
            self.content_area,
            on_queue_jump=lambda: self.select_tab("queue")
        )
        self.tab_frames["playlist"] = PlaylistTab(
            self.content_area,
            on_queue_jump=lambda: self.select_tab("queue")
        )
        self.tab_frames["bulk"] = BulkTab(
            self.content_area,
            on_queue_jump=lambda: self.select_tab("queue")
        )
        self.tab_frames["queue"] = QueueTab(self.content_area)
        self.tab_frames["history"] = HistoryTab(self.content_area)
        self.tab_frames["settings"] = SettingsTab(
            self.content_area,
            on_theme_change=self._refresh_theme
        )

        # Place them all in the same grid spot (hidden by default)
        for frame in self.tab_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()

    def select_tab(self, tab_id: str):
        """Switches active view and updates sidebar highlight."""
        if tab_id not in self.tab_frames:
            return

        self.current_tab_name = tab_id

        # Update sidebar button colors
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color=("#3182CE", "#2B6CB0"),
                    text_color="#FFFFFF"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray20", "gray90")
                )

        # Show target frame
        for tid, frame in self.tab_frames.items():
            if tid == tab_id:
                frame.grid()
                # If history tab, trigger refresh
                if tid == "history" and hasattr(frame, "refresh"):
                    frame.refresh()
            else:
                frame.grid_remove()

    def _start_sidebar_badge_loop(self):
        """Update Queue button text with active/pending count."""
        active_cnt = sum(
            1 for t in downloader.get_all_tasks()
            if t.status in ["DOWNLOADING", "QUEUED", "PROCESSING"]
        )
        q_btn = self.nav_buttons.get("queue")
        if q_btn:
            if active_cnt > 0:
                q_btn.configure(text=f"⏳  Active Queue ({active_cnt})")
            else:
                q_btn.configure(text="⏳  Active Downloads")

        self.after(1000, self._start_sidebar_badge_loop)

    def _refresh_theme(self):
        has_ffmpeg, _ = check_ffmpeg()
        ff_text = "🟢 FFmpeg Ready" if has_ffmpeg else "🔴 FFmpeg Missing"
        self.ff_badge.configure(
            text=ff_text,
            text_color=("#38A169" if has_ffmpeg else "#E53E3E")
        )
