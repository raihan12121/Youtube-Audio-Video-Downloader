"""
Completed Downloads History & Library tab.
"""

from typing import List
import customtkinter as ctk

from src.config import config
from src.core.history import history
from src.core.utils import open_folder
from src.ui.components.history_card import HistoryCard


class HistoryTab(ctk.CTkFrame):
    """Tab displaying historical completed downloads from SQLite."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.cards: List[HistoryCard] = []

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 6))

        title_lbl = ctk.CTkLabel(
            header,
            text="Completed Downloads Library",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            header,
            text="0 items",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65")
        )
        self.count_lbl.pack(side="right")

        # 2. Filter & Search Bar
        bar = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray92", "#1E222B"))
        bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Mode filter
        self.filter_mode_var = ctk.StringVar(value="all")
        self.filter_btn = ctk.CTkSegmentedButton(
            bar,
            values=["All", "Videos", "Audios"],
            command=self._on_filter_change
        )
        self.filter_btn.set("All")
        self.filter_btn.pack(side="left", padx=16, pady=10)

        # Search entry
        self.search_entry = ctk.CTkEntry(
            bar,
            placeholder_text="Search downloads...",
            width=220,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        self.search_entry.pack(side="left", padx=(0, 12), pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        # Clear All button
        clear_btn = ctk.CTkButton(
            bar,
            text="🗑 Clear History",
            width=100,
            height=28,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            font=ctk.CTkFont(size=11),
            command=self._handle_clear_all
        )
        clear_btn.pack(side="right", padx=(6, 16), pady=10)

        open_dir_btn = ctk.CTkButton(
            bar,
            text="📁 Downloads Folder",
            width=120,
            height=28,
            fg_color=("gray75", "#2D3748"),
            hover_color=("gray65", "#4A5568"),
            font=ctk.CTkFont(size=11),
            command=lambda: open_folder(config.download_dir)
        )
        open_dir_btn.pack(side="right", padx=6, pady=10)

        # 3. Scrollable List of History Cards
        self.list_scroll = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray92", "#1E222B"))
        self.list_scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 15))
        self.list_scroll.grid_columnconfigure(0, weight=1)

        self.empty_lbl = ctk.CTkLabel(
            self.list_scroll,
            text="No download history found.\nDownloaded files will appear here with instant play and reveal shortcuts.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60")
        )

    def _on_filter_change(self, choice: str):
        if choice == "Videos":
            self.filter_mode_var.set("video")
        elif choice == "Audios":
            self.filter_mode_var.set("audio")
        else:
            self.filter_mode_var.set("all")
        self.refresh()

    def refresh(self):
        """Fetch records and render cards."""
        query = self.search_entry.get().strip()
        mode = self.filter_mode_var.get()

        records = history.get_records(query=query if query else None, mode=mode)

        # Clear existing
        for c in self.cards:
            c.destroy()
        self.cards.clear()

        self.count_lbl.configure(text=f"{len(records)} items")

        if not records:
            self.empty_lbl.pack(pady=70)
        else:
            self.empty_lbl.pack_forget()
            for r in records:
                card = HistoryCard(
                    self.list_scroll,
                    record=r,
                    on_delete=lambda rid: self.refresh()
                )
                card.pack(fill="x", pady=3)
                self.cards.append(card)

    def _handle_clear_all(self):
        history.clear_all()
        self.refresh()
