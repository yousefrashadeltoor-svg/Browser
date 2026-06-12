"""
JO Browser — History Manager
Stores visited URLs in SQLite. Supports search, delete, and clear.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from browser.utils import data_path

log = logging.getLogger(__name__)


class HistoryManager:
    def __init__(self, profile: str = "default"):
        db_path = data_path("profiles", profile, "history.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                visited_at TEXT NOT NULL,
                visit_count INTEGER DEFAULT 1
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_url ON history(url)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_visited ON history(visited_at)")
        self._conn.commit()

    def add(self, url: str, title: str = ""):
        now = datetime.now().isoformat()
        existing = self._conn.execute(
            "SELECT id, visit_count FROM history WHERE url=?", (url,)
        ).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE history SET visited_at=?, visit_count=?, title=? WHERE id=?",
                (now, existing["visit_count"] + 1, title or "", existing["id"]),
            )
        else:
            self._conn.execute(
                "INSERT INTO history (url, title, visited_at) VALUES (?,?,?)",
                (url, title or "", now),
            )
        self._conn.commit()

    def search(self, query: str, limit: int = 50) -> list[sqlite3.Row]:
        q = f"%{query}%"
        return self._conn.execute(
            "SELECT * FROM history WHERE url LIKE ? OR title LIKE ? "
            "ORDER BY visited_at DESC LIMIT ?",
            (q, q, limit),
        ).fetchall()

    def recent(self, limit: int = 100) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM history ORDER BY visited_at DESC LIMIT ?", (limit,)
        ).fetchall()

    def delete(self, id_: int):
        self._conn.execute("DELETE FROM history WHERE id=?", (id_,))
        self._conn.commit()

    def delete_url(self, url: str):
        self._conn.execute("DELETE FROM history WHERE url=?", (url,))
        self._conn.commit()

    def clear(self):
        self._conn.execute("DELETE FROM history")
        self._conn.commit()

    def most_visited(self, limit: int = 10) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT url, title, visit_count FROM history "
            "ORDER BY visit_count DESC LIMIT ?",
            (limit,),
        ).fetchall()

    def suggestions(self, prefix: str, limit: int = 8) -> list[str]:
        q = f"{prefix}%"
        rows = self._conn.execute(
            "SELECT DISTINCT url FROM history WHERE url LIKE ? "
            "ORDER BY visit_count DESC LIMIT ?",
            (q, limit),
        ).fetchall()
        return [r["url"] for r in rows]
