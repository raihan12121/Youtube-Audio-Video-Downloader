"""
Item row component for Playlist and Channel video checklist.
"""

from typing import Callable, Dict, Optional
import customtkinter as ctk

from src.core.utils import format_duration
from src.utils.thumbnail_cache import thumbnail_cache


class VideoCard(ctk.CTkFrame):
    """Row item in the playlist/channel checklist table."""

    def __init__(
        self,
        master,
        entry: Dict,
        on_toggle: Optional[Callable[[Dict, bool], None]] = None,
        **kwargs
    ):
        super().__init__(master, corner_radius=6, fg_color=("gray92", "#1A202C"), **kwargs)
        self.entry = entry
        self.on_toggle = on_toggle
        self.is_selected = entry.get("selected", True)

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(3, weight=1)

        # 1. Checkbox
        self.check_var = ctk.BooleanVar(value=self.is_selected)
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.check_var,
            width=24,
            command=self._on_check_change
        )
        self.checkbox.grid(row=0, column=0, padx=(10, 5), pady=8)

        # 2. Index badge
        idx_text = f"#{self.entry.get('index', 1)}"
        self.idx_lbl = ctk.CTkLabel(
            self,
            text=idx_text,
            width=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray40", "gray50")
        )
        self.idx_lbl.grid(row=0, column=1, padx=(0, 6), pady=8)

        # 3. Small thumbnail
        self.thumb_lbl = ctk.CTkLabel(self, text="", width=76, height=42)
        self.thumb_lbl.grid(row=0, column=2, padx=(0, 10), pady=6)

        thumb_img = thumbnail_cache.get_ctk_image(
            self.entry.get("thumbnail"),
            size=(76, 42),
            on_loaded=self._on_thumb_loaded
        )
        self.thumb_lbl.configure(image=thumb_img)

        # 4. Title and duration
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=3, sticky="w", padx=0, pady=4)

        title = self.entry.get("title", "Untitled")
        title_disp = title if len(title) <= 70 else title[:67] + "..."
        self.title_lbl = ctk.CTkLabel(
            info_frame,
            text=title_disp,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            justify="left"
        )
        self.title_lbl.pack(anchor="w")

        duration_sec = self.entry.get("duration", 0)
        dur_str = format_duration(duration_sec)
        uploader = self.entry.get("uploader", "")
        meta_str = f"⏱ {dur_str}" + (f"  •  {uploader}" if uploader else "")

        self.meta_lbl = ctk.CTkLabel(
            info_frame,
            text=meta_str,
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.meta_lbl.pack(anchor="w")

    def _on_thumb_loaded(self, img: ctk.CTkImage):
        try:
            self.thumb_lbl.configure(image=img)
        except Exception:
            pass

    def _on_check_change(self):
        self.is_selected = self.check_var.get()
        self.entry["selected"] = self.is_selected
        if self.on_toggle:
            self.on_toggle(self.entry, self.is_selected)

    def set_selected(self, val: bool):
        self.check_var.set(val)
        self.is_selected = val
        self.entry["selected"] = val
