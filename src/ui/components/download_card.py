"""
UI component for rendering an active download task in the Queue tab.
"""

from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk

from src.core.downloader import DownloadTask, downloader
from src.core.utils import format_bytes, format_duration, open_file, open_folder
from src.utils.thumbnail_cache import thumbnail_cache


class DownloadCard(ctk.CTkFrame):
    """Card widget representing a single item in the download queue."""

    STATUS_COLORS = {
        "QUEUED": ("#718096", "#4A5568"),
        "DOWNLOADING": ("#3182CE", "#2B6CB0"),
        "PROCESSING": ("#805AD5", "#6B46C1"),
        "COMPLETED": ("#38A169", "#2F855A"),
        "CANCELLED": ("#E53E3E", "#C53030"),
        "FAILED": ("#E53E3E", "#9B2C2C"),
        "PAUSED": ("#DD6B20", "#C05621"),
    }

    def __init__(
        self,
        master,
        task: DownloadTask,
        on_cancel: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, corner_radius=10, fg_color=("gray88", "#1E222B"), **kwargs)
        self.task = task
        self.on_cancel = on_cancel

        self._setup_ui()
        self.update_task_data()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)

        # 1. Left Thumbnail
        self.thumb_label = ctk.CTkLabel(self, text="", width=110, height=62)
        self.thumb_label.grid(row=0, column=0, rowspan=2, padx=(10, 12), pady=10)

        # Load thumbnail async
        initial_img = thumbnail_cache.get_ctk_image(
            self.task.thumbnail,
            size=(110, 62),
            on_loaded=self._on_thumbnail_ready
        )
        self.thumb_label.configure(image=initial_img)

        # 2. Middle Content Frame
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=(8, 2))
        self.info_frame.grid_columnconfigure(0, weight=1)

        # Title row
        title_text = self.task.title if len(self.task.title) <= 65 else self.task.title[:62] + "..."
        self.title_lbl = ctk.CTkLabel(
            self.info_frame,
            text=title_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            justify="left"
        )
        self.title_lbl.grid(row=0, column=0, sticky="w", pady=(0, 2))

        # Channel & preset tag
        tag_text = f"👤 {self.task.channel or 'YouTube'}  •  🎯 {self.task.quality.upper()} ({self.task.container.upper()})"
        self.tag_lbl = ctk.CTkLabel(
            self.info_frame,
            text=tag_text,
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray65"),
            anchor="w"
        )
        self.tag_lbl.grid(row=1, column=0, sticky="w", pady=(0, 4))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.info_frame, height=8, corner_radius=4)
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=(2, 4))
        self.progress_bar.set(0.0)

        # Stats row (Speed, Downloaded/Total, ETA, Status)
        self.stats_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.stats_frame.grid(row=3, column=0, sticky="ew")

        self.stats_lbl = ctk.CTkLabel(
            self.stats_frame,
            text="Waiting in queue...",
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70")
        )
        self.stats_lbl.pack(side="left")

        # 3. Right Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=0, column=2, rowspan=2, padx=(10, 12), pady=10)

        # Status badge
        self.status_badge = ctk.CTkButton(
            self.action_frame,
            text=self.task.status,
            width=80,
            height=24,
            corner_radius=12,
            font=ctk.CTkFont(size=10, weight="bold"),
            state="disabled"
        )
        self.status_badge.pack(pady=(0, 6))

        # Cancel / Action button
        self.cancel_btn = ctk.CTkButton(
            self.action_frame,
            text="✕ Cancel",
            width=75,
            height=26,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray60", "#4A5568"),
            font=ctk.CTkFont(size=11),
            command=self._handle_cancel
        )
        self.cancel_btn.pack(pady=2)

        # Open folder button (initially hidden)
        self.open_btn = ctk.CTkButton(
            self.action_frame,
            text="📁 Folder",
            width=75,
            height=26,
            fg_color=("#3182CE", "#2B6CB0"),
            hover_color=("#2B6CB0", "#2C5282"),
            font=ctk.CTkFont(size=11),
            command=self._handle_open_folder
        )

    def _on_thumbnail_ready(self, img: ctk.CTkImage):
        try:
            self.thumb_label.configure(image=img)
        except Exception:
            pass

    def update_task_data(self):
        """Refreshes UI elements based on current task object values."""
        # Update title if it changed from "Fetching info..."
        if self.task.title:
            title_text = self.task.title if len(self.task.title) <= 65 else self.task.title[:62] + "..."
            self.title_lbl.configure(text=title_text)

        # Update progress bar
        p_val = max(0.0, min(1.0, self.task.progress / 100.0))
        self.progress_bar.set(p_val)

        # Update badge
        status = self.task.status
        self.status_badge.configure(text=status)
        colors = self.STATUS_COLORS.get(status, ("#718096", "#4A5568"))
        self.status_badge.configure(fg_color=colors[1])

        # Stats text
        if status == "DOWNLOADING":
            dl_str = format_bytes(self.task.downloaded_bytes)
            tot_str = format_bytes(self.task.total_bytes) if self.task.total_bytes > 0 else "..."
            self.stats_lbl.configure(
                text=f"{self.task.progress:.1f}%  •  {dl_str} / {tot_str}  •  ⚡ {self.task.speed_str}  •  ⏳ ETA: {self.task.eta_str}"
            )
            self.cancel_btn.configure(state="normal", text="✕ Cancel")
        elif status == "PROCESSING":
            self.stats_lbl.configure(text=f"🔄 Processing: {self.task.speed_str}")
        elif status == "COMPLETED":
            tot_str = format_bytes(self.task.total_bytes)
            self.stats_lbl.configure(text=f"✓ Download complete ({tot_str})")
            self.cancel_btn.pack_forget()
            self.open_btn.pack(pady=2)
        elif status == "FAILED":
            err = self.task.error_message
            err_short = err[:50] + "..." if len(err) > 50 else err
            self.stats_lbl.configure(text=f"⚠ Failed: {err_short}")
            self.cancel_btn.configure(text="Retry", command=self._handle_retry)
        elif status == "CANCELLED":
            self.stats_lbl.configure(text="Download was cancelled")
            self.cancel_btn.configure(state="disabled")

    def _handle_cancel(self):
        downloader.cancel_task(self.task.id)
        if self.on_cancel:
            self.on_cancel(self.task.id)

    def _handle_open_folder(self):
        target = self.task.final_filepath or self.task.output_dir
        open_folder(target)

    def _handle_retry(self):
        self.task.status = "QUEUED"
        self.task.progress = 0.0
        self.task.cancel_event.clear()
        downloader.add_task(self.task)
        self.update_task_data()
