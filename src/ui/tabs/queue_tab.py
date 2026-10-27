"""
Active Downloads Queue tab.
Displays live progress cards, download speed, ETA, and cancellation controls.
"""

from typing import Dict
import customtkinter as ctk

from src.config import config
from src.core.downloader import DownloadTask, downloader
from src.core.utils import format_speed, open_folder
from src.ui.components.download_card import DownloadCard


class QueueTab(ctk.CTkFrame):
    """Tab displaying all queued, downloading, and recently finished tasks."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.cards: Dict[str, DownloadCard] = {}

        self._setup_ui()
        self._bind_downloader_events()
        self._start_refresh_loop()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 6))

        title_lbl = ctk.CTkLabel(
            header,
            text="Active Download Queue",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.pack(side="left")

        self.summary_lbl = ctk.CTkLabel(
            header,
            text="0 Active • 0 Queued",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65")
        )
        self.summary_lbl.pack(side="right")

        # 2. Control bar
        ctrl_bar = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray92", "#1E222B"))
        ctrl_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Speed indicator
        self.speed_indicator = ctk.CTkLabel(
            ctrl_bar,
            text="⚡ Total Speed: 0.0 MB/s",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#3182CE", "#63B3ED")
        )
        self.speed_indicator.pack(side="left", padx=16, pady=10)

        # Action buttons
        open_dir_btn = ctk.CTkButton(
            ctrl_bar,
            text="📁 Open Folder",
            width=100,
            height=28,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            font=ctk.CTkFont(size=11),
            command=self._handle_open_dir
        )
        open_dir_btn.pack(side="right", padx=(6, 16), pady=10)

        clear_btn = ctk.CTkButton(
            ctrl_bar,
            text="🧹 Clear Finished",
            width=110,
            height=28,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            font=ctk.CTkFont(size=11),
            command=self._handle_clear_finished
        )
        clear_btn.pack(side="right", padx=6, pady=10)

        cancel_all_btn = ctk.CTkButton(
            ctrl_bar,
            text="✕ Cancel All",
            width=90,
            height=28,
            fg_color=("#E53E3E", "#C53030"),
            hover_color=("#C53030", "#9B2C2C"),
            font=ctk.CTkFont(size=11),
            command=self._handle_cancel_all
        )
        cancel_all_btn.pack(side="right", padx=6, pady=10)

        # 3. Scrollable List of Cards
        self.card_scroll = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray92", "#1E222B"))
        self.card_scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 15))
        self.card_scroll.grid_columnconfigure(0, weight=1)

        self.empty_lbl = ctk.CTkLabel(
            self.card_scroll,
            text="No active downloads in queue.\nAdd a single video, playlist, or channel to start downloading.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60")
        )
        self.empty_lbl.pack(pady=70)

    def _bind_downloader_events(self):
        downloader.on_task_added = self._on_task_added_event
        downloader.on_task_updated = self._on_task_updated_event

    def _on_task_added_event(self, task: DownloadTask):
        self.after(0, self._add_card, task)

    def _on_task_updated_event(self, task: DownloadTask):
        # Queued for periodic UI update
        pass

    def _add_card(self, task: DownloadTask):
        if self.empty_lbl.winfo_ismapped():
            self.empty_lbl.pack_forget()

        if task.id not in self.cards:
            card = DownloadCard(
                self.card_scroll,
                task=task,
                on_cancel=self._handle_task_cancel
            )
            card.pack(fill="x", pady=4)
            self.cards[task.id] = card

    def _handle_task_cancel(self, task_id: str):
        downloader.cancel_task(task_id)

    def _handle_cancel_all(self):
        downloader.cancel_all()

    def _handle_clear_finished(self):
        downloader.clear_completed()
        to_del = []
        for tid, card in self.cards.items():
            if card.task.status in ["COMPLETED", "CANCELLED", "FAILED"]:
                card.destroy()
                to_del.append(tid)

        for tid in to_del:
            del self.cards[tid]

        if not self.cards:
            self.empty_lbl.pack(pady=70)

    def _handle_open_dir(self):
        open_folder(config.download_dir)

    def _start_refresh_loop(self):
        """Periodic 400ms tick to smoothly refresh card progress bars and speeds."""
        self._refresh_ui()
        self.after(400, self._start_refresh_loop)

    def _refresh_ui(self):
        tasks = downloader.get_all_tasks()

        # Add missing cards if any
        for task in tasks:
            if task.id not in self.cards:
                self._add_card(task)

        # Update card data
        active_count = 0
        queued_count = 0
        total_speed = 0.0

        for task in tasks:
            if task.status in ["DOWNLOADING", "PROCESSING"]:
                active_count += 1
                total_speed += task.speed
            elif task.status == "QUEUED":
                queued_count += 1

            if task.id in self.cards:
                self.cards[task.id].update_task_data()

        self.summary_lbl.configure(text=f"{active_count} Active • {queued_count} Queued")
        self.speed_indicator.configure(text=f"⚡ Total Speed: {format_speed(total_speed)}")
