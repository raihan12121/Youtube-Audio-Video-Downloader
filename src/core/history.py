"""
History database manager using SQLite.
Keeps record of all completed downloads with search and management capabilities.
"""

import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional


DB_FILE = Path(__file__).resolve().parent.parent.parent / "downloads_history.db"


class HistoryManager:
    def __init__(self, db_path: Path = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates the history table if it does not exist."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT,
                    file_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    mode TEXT DEFAULT 'video',
                    format TEXT,
                    resolution TEXT,
                    duration INTEGER DEFAULT 0,
                    channel TEXT,
                    completed_at REAL
                )
                """
            )
            conn.commit()

    def add_record(
        self,
        title: str,
        url: str,
        file_path: str,
        file_size: int = 0,
        mode: str = "video",
        format_name: str = "mp4",
        resolution: str = "",
        duration: int = 0,
        channel: str = ""
    ) -> int:
        """Adds a completed download record to history."""
        completed_at = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO history (title, url, file_path, file_size, mode, format, resolution, duration, channel, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, url, file_path, file_size, mode, format_name, resolution, duration, channel, completed_at),
            )
            conn.commit()
            return cursor.lastrowid

    def get_records(
        self,
        limit: int = 200,
        query: Optional[str] = None,
        mode: Optional[str] = None
    ) -> List[Dict]:
        """Fetch history records with optional search and mode filtering."""
        sql = "SELECT * FROM history WHERE 1=1"
        params = []

        if query:
            sql += " AND (title LIKE ? OR channel LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])

        if mode and mode.lower() != "all":
            sql += " AND LOWER(mode) = LOWER(?)"
            params.append(mode)

        sql += " ORDER BY completed_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_record(self, record_id: int):
        """Remove a record by its ID."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
            conn.commit()

    def clear_all(self):
        """Clear all history entries."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM history")
            conn.commit()


# Global singleton
history = HistoryManager()
