"""
JO Browser — Notes Manager
Quick notes panel: multiple notes stored in SQLite.
"""

import sqlite3
import logging
from datetime import datetime
from browser.utils import data_path

log = logging.getLogger(__name__)


class NotesManager:
    def __init__(self, profile: str = "default"):
        db_path = data_path("profiles", profile, "notes.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created_at TEXT,
                updated_at TEXT,
                color TEXT DEFAULT '#6C63FF'
            )
        """)
        self._conn.commit()

    def add(self, title: str = "Untitled", content: str = "", color: str = "#6C63FF") -> int:
        now = datetime.now().isoformat()
        cur = self._conn.execute(
            "INSERT INTO notes (title,content,created_at,updated_at,color) VALUES (?,?,?,?,?)",
            (title, content, now, now, color),
        )
        self._conn.commit()
        return cur.lastrowid

    def update(self, id_: int, title: str = None, content: str = None, color: str = None):
        updates = {}
        if title is not None:
            updates["title"] = title
        if content is not None:
            updates["content"] = content
        if color is not None:
            updates["color"] = color
        if not updates:
            return
        updates["updated_at"] = datetime.now().isoformat()
        parts = ", ".join(f"{k}=?" for k in updates)
        self._conn.execute(f"UPDATE notes SET {parts} WHERE id=?", (*updates.values(), id_))
        self._conn.commit()

    def delete(self, id_: int):
        self._conn.execute("DELETE FROM notes WHERE id=?", (id_,))
        self._conn.commit()

    def all(self) -> list[sqlite3.Row]:
        return self._conn.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()

    def get(self, id_: int) -> sqlite3.Row | None:
        return self._conn.execute("SELECT * FROM notes WHERE id=?", (id_,)).fetchone()

    def search(self, query: str) -> list[sqlite3.Row]:
        q = f"%{query}%"
        return self._conn.execute(
            "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC",
            (q, q),
        ).fetchall()
