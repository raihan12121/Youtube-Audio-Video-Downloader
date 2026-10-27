"""
Application Settings & Environment Configuration tab.
"""

from tkinter import filedialog
from typing import Callable, Optional
import customtkinter as ctk

from src.config import config
from src.core.utils import check_ffmpeg, check_nodejs, open_folder


class SettingsTab(ctk.CTkFrame):
    """Settings tab for setting preferences, themes, FFmpeg status, and cookies."""

    def __init__(self, master, on_theme_change: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_theme_change = on_theme_change

        self._setup_ui()

    def _setup_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)
        self.scroll.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        title_lbl = ctk.CTkLabel(
            header,
            text="Application Settings & Tools",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            header,
            text="Configure download defaults, environment tools, playlists organization, and theme appearance.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65")
        )
        sub_lbl.pack(anchor="w")

        # 2. System Status Card
        sys_card = ctk.CTkFrame(self.scroll, corner_radius=10, fg_color=("gray92", "#1E222B"))
        sys_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        sys_card.grid_columnconfigure(1, weight=1)

        s_title = ctk.CTkLabel(
            sys_card,
            text="System Engine Status",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        s_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))

        # FFmpeg status
        has_ffmpeg, ffmpeg_info = check_ffmpeg()
        ff_icon = "🟢" if has_ffmpeg else "🔴"
        ff_text = f"FFmpeg: {ffmpeg_info}" if has_ffmpeg else "FFmpeg: Not Found (Required for 1080p+ merging and MP3 conversion)"

        ff_lbl = ctk.CTkLabel(
            sys_card,
            text=f"{ff_icon}  {ff_text}",
            font=ctk.CTkFont(size=12),
            text_color=("#38A169" if has_ffmpeg else "#E53E3E")
        )
        ff_lbl.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=4)

        # Node.js status
        has_node, node_info = check_nodejs()
        node_icon = "🟢" if has_node else "🟡"
        node_text = f"Node.js: {node_info}" if has_node else "Node.js: Not detected (Recommended for YouTube signature solving)"

        node_lbl = ctk.CTkLabel(
            sys_card,
            text=f"{node_icon}  {node_text}",
            font=ctk.CTkFont(size=12),
            text_color=("#38A169" if has_node else "#DD6B20")
        )
        node_lbl.grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(4, 14))

        # 3. Download Preferences Card
        pref_card = ctk.CTkFrame(self.scroll, corner_radius=10, fg_color=("gray92", "#1E222B"))
        pref_card.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        pref_card.grid_columnconfigure(1, weight=1)

        p_title = ctk.CTkLabel(
            pref_card,
            text="Default Download Paths & Concurrency",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        p_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))

        # Path
        path_lbl = ctk.CTkLabel(pref_card, text="Default Download Folder:", font=ctk.CTkFont(size=12))
        path_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=6)

        path_row = ctk.CTkFrame(pref_card, fg_color="transparent")
        path_row.grid(row=1, column=1, sticky="ew", padx=16, pady=6)
        path_row.grid_columnconfigure(0, weight=1)

        self.path_entry = ctk.CTkEntry(path_row, height=32)
        self.path_entry.insert(0, config.download_dir)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        browse_btn = ctk.CTkButton(
            path_row,
            text="Browse...",
            width=80,
            height=32,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            command=self._handle_browse
        )
        browse_btn.grid(row=0, column=1)

        # Concurrency
        conc_lbl = ctk.CTkLabel(pref_card, text="Max Concurrent Downloads:", font=ctk.CTkFont(size=12))
        conc_lbl.grid(row=2, column=0, sticky="w", padx=16, pady=8)

        conc_row = ctk.CTkFrame(pref_card, fg_color="transparent")
        conc_row.grid(row=2, column=1, sticky="w", padx=16, pady=8)

        self.conc_slider = ctk.CTkSlider(
            conc_row,
            from_=1,
            to=6,
            number_of_steps=5,
            width=160,
            command=self._on_slider_change
        )
        current_conc = config.get("max_concurrent_downloads", 3)
        self.conc_slider.set(current_conc)
        self.conc_slider.pack(side="left", padx=(0, 10))

        self.conc_val_lbl = ctk.CTkLabel(
            conc_row,
            text=f"{int(current_conc)} threads",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.conc_val_lbl.pack(side="left")

        # 4. Defaults & Metadata Card
        meta_card = ctk.CTkFrame(self.scroll, corner_radius=10, fg_color=("gray92", "#1E222B"))
        meta_card.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        meta_card.grid_columnconfigure(1, weight=1)

        m_title = ctk.CTkLabel(
            meta_card,
            text="Media & Organization Defaults",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        m_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))

        # Video resolution
        vres_lbl = ctk.CTkLabel(meta_card, text="Preferred Video Resolution:", font=ctk.CTkFont(size=12))
        vres_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=6)

        self.vres_menu = ctk.CTkOptionMenu(
            meta_card,
            values=["Best Available", "2160p (4K)", "1440p (2K)", "1080p (Full HD)", "720p (HD)", "480p"],
            width=200
        )
        self.vres_menu.set(config.get("default_video_resolution", "Best Available"))
        self.vres_menu.grid(row=1, column=1, sticky="w", padx=16, pady=6)

        # Video container
        vcont_lbl = ctk.CTkLabel(meta_card, text="Default Video Format:", font=ctk.CTkFont(size=12))
        vcont_lbl.grid(row=2, column=0, sticky="w", padx=16, pady=6)

        self.vcont_menu = ctk.CTkOptionMenu(
            meta_card,
            values=["mp4", "mkv", "webm"],
            width=200
        )
        self.vcont_menu.set(config.get("default_video_container", "mp4"))
        self.vcont_menu.grid(row=2, column=1, sticky="w", padx=16, pady=6)

        # Audio format
        afmt_lbl = ctk.CTkLabel(meta_card, text="Default Audio Format:", font=ctk.CTkFont(size=12))
        afmt_lbl.grid(row=3, column=0, sticky="w", padx=16, pady=6)

        self.afmt_menu = ctk.CTkOptionMenu(
            meta_card,
            values=["mp3", "m4a", "wav", "flac", "opus"],
            width=200
        )
        self.afmt_menu.set(config.get("default_audio_format", "mp3"))
        self.afmt_menu.grid(row=3, column=1, sticky="w", padx=16, pady=6)

        # Checkboxes
        self.embed_thumb_var = ctk.BooleanVar(value=config.get("embed_thumbnail", True))
        self.embed_thumb_chk = ctk.CTkCheckBox(
            meta_card,
            text="Embed Album Art / Thumbnail into file",
            variable=self.embed_thumb_var
        )
        self.embed_thumb_chk.grid(row=4, column=0, columnspan=2, sticky="w", padx=16, pady=6)

        self.embed_meta_var = ctk.BooleanVar(value=config.get("embed_metadata", True))
        self.embed_meta_chk = ctk.CTkCheckBox(
            meta_card,
            text="Embed Metadata (Artist, Title, Album, Date)",
            variable=self.embed_meta_var
        )
        self.embed_meta_chk.grid(row=5, column=0, columnspan=2, sticky="w", padx=16, pady=6)

        self.subfolder_var = ctk.BooleanVar(value=config.get("organize_playlists_in_subfolders", True))
        self.subfolder_chk = ctk.CTkCheckBox(
            meta_card,
            text="Automatically place Playlist and Channel downloads into named subfolders",
            variable=self.subfolder_var
        )
        self.subfolder_chk.grid(row=6, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 14))

        # 5. Advanced / YouTube Cookies Card
        adv_card = ctk.CTkFrame(self.scroll, corner_radius=10, fg_color=("gray92", "#1E222B"))
        adv_card.grid(row=4, column=0, sticky="ew", pady=(0, 16))
        adv_card.grid_columnconfigure(1, weight=1)

        a_title = ctk.CTkLabel(
            adv_card,
            text="YouTube Authentication & Cookies (Optional)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        a_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 6))

        a_sub = ctk.CTkLabel(
            adv_card,
            text="Required only for age-restricted videos, private playlists, or member-only videos.",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60")
        )
        a_sub.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 10))

        cookie_lbl = ctk.CTkLabel(adv_card, text="Browser Cookies Source:", font=ctk.CTkFont(size=12))
        cookie_lbl.grid(row=2, column=0, sticky="w", padx=16, pady=6)

        self.cookie_menu = ctk.CTkOptionMenu(
            adv_card,
            values=["none", "chrome", "firefox", "edge", "brave"],
            width=200
        )
        self.cookie_menu.set(config.get("browser_cookies", "none"))
        self.cookie_menu.grid(row=2, column=1, sticky="w", padx=16, pady=6)

        # 6. Appearance & Theme Card
        app_card = ctk.CTkFrame(self.scroll, corner_radius=10, fg_color=("gray92", "#1E222B"))
        app_card.grid(row=5, column=0, sticky="ew", pady=(0, 20))
        app_card.grid_columnconfigure(1, weight=1)

        ap_title = ctk.CTkLabel(
            app_card,
            text="Appearance & Theme",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        ap_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))

        mode_lbl = ctk.CTkLabel(app_card, text="Color Mode:", font=ctk.CTkFont(size=12))
        mode_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=6)

        self.theme_menu = ctk.CTkOptionMenu(
            app_card,
            values=["Dark", "Light", "System"],
            width=200,
            command=self._on_theme_select
        )
        self.theme_menu.set(config.get("appearance_mode", "Dark"))
        self.theme_menu.grid(row=1, column=1, sticky="w", padx=16, pady=6)

        # 7. Save Confirmation Button
        save_btn = ctk.CTkButton(
            self.scroll,
            text="💾 Save Preferences",
            height=46,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#3182CE", "#2B6CB0"),
            hover_color=("#2B6CB0", "#2C5282"),
            command=self._handle_save
        )
        save_btn.grid(row=6, column=0, sticky="ew", pady=(0, 25))

        self.save_feedback = ctk.CTkLabel(
            self.scroll,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#38A169", "#68D391")
        )
        self.save_feedback.grid(row=7, column=0, pady=(0, 20))

    def _on_slider_change(self, val):
        self.conc_val_lbl.configure(text=f"{int(val)} threads")

    def _handle_browse(self):
        folder = filedialog.askdirectory(initialdir=self.path_entry.get())
        if folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

    def _on_theme_select(self, mode: str):
        ctk.set_appearance_mode(mode)
        config.set("appearance_mode", mode)
        if self.on_theme_change:
            self.on_theme_change()

    def _handle_save(self):
        config.set("download_dir", self.path_entry.get().strip())
        config.set("max_concurrent_downloads", int(self.conc_slider.get()))
        config.set("default_video_resolution", self.vres_menu.get())
        config.set("default_video_container", self.vcont_menu.get())
        config.set("default_audio_format", self.afmt_menu.get())
        config.set("embed_thumbnail", self.embed_thumb_var.get())
        config.set("embed_metadata", self.embed_meta_var.get())
        config.set("organize_playlists_in_subfolders", self.subfolder_var.get())
        config.set("browser_cookies", self.cookie_menu.get())
        config.set("appearance_mode", self.theme_menu.get())
        config.save()

        self.save_feedback.configure(text="✓ Settings successfully saved!")
        self.after(3000, lambda: self.save_feedback.configure(text=""))
