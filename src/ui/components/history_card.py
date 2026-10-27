"""
Card widget representing a completed download in the History tab.
"""

from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional
import customtkinter as ctk

from src.core.history import history
from src.core.utils import format_bytes, format_duration, open_file, open_folder


class HistoryCard(ctk.CTkFrame):
    """Row item in the download history tab."""

    def __init__(
        self,
        master,
        record: Dict,
        on_delete: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(master, corner_radius=8, fg_color=("gray88", "#1E222B"), **kwargs)
        self.record = record
        self.on_delete = on_delete

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)

        # 1. Mode icon
        mode = self.record.get("mode", "video")
        icon_text = "🎬" if mode == "video" else "🎵"
        self.icon_lbl = ctk.CTkLabel(
            self,
            text=icon_text,
            font=ctk.CTkFont(size=22),
            width=40
        )
        self.icon_lbl.grid(row=0, column=0, rowspan=2, padx=(12, 6), pady=8)

        # 2. Main title & metadata
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="w", padx=0, pady=8)

        title = self.record.get("title", "Untitled")
        title_disp = title if len(title) <= 65 else title[:62] + "..."
        self.title_lbl = ctk.CTkLabel(
            info_frame,
            text=title_disp,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            justify="left"
        )
        self.title_lbl.pack(anchor="w")

        # Details row
        f_size = format_bytes(self.record.get("file_size", 0))
        fmt = self.record.get("format", "").upper()
        res = self.record.get("resolution", "")
        completed_at = self.record.get("completed_at", 0)
        time_str = datetime.fromtimestamp(completed_at).strftime("%Y-%m-%d %H:%M") if completed_at else ""

        details = f"{fmt} • {res} • {f_size} • {time_str}"
        self.details_lbl = ctk.CTkLabel(
            info_frame,
            text=details,
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray65"),
            anchor="w"
        )
        self.details_lbl.pack(anchor="w")

        # 3. Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=(8, 12), pady=8)

        file_exists = Path(self.record.get("file_path", "")).exists()

        if file_exists:
            self.play_btn = ctk.CTkButton(
                btn_frame,
                text="▶ Play",
                width=65,
                height=26,
                fg_color=("#3182CE", "#2B6CB0"),
                hover_color=("#2B6CB0", "#2C5282"),
                font=ctk.CTkFont(size=11),
                command=self._handle_play
            )
            self.play_btn.pack(side="left", padx=3)

            self.folder_btn = ctk.CTkButton(
                btn_frame,
                text="📁 Reveal",
                width=65,
                height=26,
                fg_color=("gray75", "#2D3748"),
                hover_color=("gray60", "#4A5568"),
                font=ctk.CTkFont(size=11),
                command=self._handle_open_folder
            )
            self.folder_btn.pack(side="left", padx=3)
        else:
            self.missing_lbl = ctk.CTkLabel(
                btn_frame,
                text="(File moved/deleted)",
                font=ctk.CTkFont(size=10, slant="italic"),
                text_color=("gray50", "gray50")
            )
            self.missing_lbl.pack(side="left", padx=5)

        self.del_btn = ctk.CTkButton(
            btn_frame,
            text="✕",
            width=28,
            height=26,
            fg_color="transparent",
            hover_color=("gray70", "#4A5568"),
            text_color=("gray40", "gray60"),
            command=self._handle_delete
        )
        self.del_btn.pack(side="left", padx=(3, 0))

    def _handle_play(self):
        fp = self.record.get("file_path", "")
        if fp:
            open_file(fp)

    def _handle_open_folder(self):
        fp = self.record.get("file_path", "")
        if fp:
            open_folder(fp)

    def _handle_delete(self):
        rec_id = self.record.get("id")
        if rec_id:
            history.delete_record(rec_id)
            if self.on_delete:
                self.on_delete(rec_id)
            self.destroy()
