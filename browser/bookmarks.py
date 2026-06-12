"""
JO Browser — Bookmarks Manager
Tree-based bookmarks stored in SQLite: folders + entries.
Supports search, import/export (Netscape HTML format), and CRUD.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from browser.utils import data_path

log = logging.getLogger(__name__)


class BookmarksManager:
    def __init__(self, profile: str = "default"):
        db_path = data_path("profiles", profile, "bookmarks.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                created_at TEXT,
                sort_order INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                description TEXT,
                folder_id INTEGER,
                created_at TEXT,
                favicon_url TEXT,
                sort_order INTEGER DEFAULT 0,
                in_reading_list INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_bm_folder ON bookmarks(folder_id);
            CREATE INDEX IF NOT EXISTS idx_bm_url ON bookmarks(url);
        """)
        # Ensure root folder exists
        if not self._conn.execute("SELECT 1 FROM folders WHERE id=1").fetchone():
            self._conn.execute(
                "INSERT INTO folders (id, name, parent_id, created_at) VALUES (1,'Bookmarks',NULL,?)",
                (datetime.now().isoformat(),),
            )
        self._conn.commit()

    # ---------- Folders ----------

    def add_folder(self, name: str, parent_id: int = 1) -> int:
        cur = self._conn.execute(
            "INSERT INTO folders (name, parent_id, created_at) VALUES (?,?,?)",
            (name, parent_id, datetime.now().isoformat()),
        )
        self._conn.commit()
        return cur.lastrowid

    def rename_folder(self, id_: int, name: str):
        self._conn.execute("UPDATE folders SET name=? WHERE id=?", (name, id_))
        self._conn.commit()

    def delete_folder(self, id_: int):
        self._conn.execute("DELETE FROM bookmarks WHERE folder_id=?", (id_,))
        self._conn.execute("DELETE FROM folders WHERE id=?", (id_,))
        self._conn.commit()

    def get_folders(self, parent_id: Optional[int] = 1) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM folders WHERE parent_id=? ORDER BY sort_order, name",
            (parent_id,),
        ).fetchall()

    # ---------- Bookmarks ----------

    def add(self, url: str, title: str = "", folder_id: int = 1,
            description: str = "", favicon_url: str = "") -> int:
        cur = self._conn.execute(
            "INSERT INTO bookmarks (url,title,description,folder_id,created_at,favicon_url) "
            "VALUES (?,?,?,?,?,?)",
            (url, title, description, folder_id, datetime.now().isoformat(), favicon_url),
        )
        self._conn.commit()
        return cur.lastrowid

    def update(self, id_: int, **kwargs):
        allowed = {"url", "title", "description", "folder_id", "favicon_url", "sort_order"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        parts = ", ".join(f"{k}=?" for k in fields)
        self._conn.execute(
            f"UPDATE bookmarks SET {parts} WHERE id=?",
            (*fields.values(), id_),
        )
        self._conn.commit()

    def delete(self, id_: int):
        self._conn.execute("DELETE FROM bookmarks WHERE id=?", (id_,))
        self._conn.commit()

    def exists(self, url: str) -> bool:
        return bool(self._conn.execute("SELECT 1 FROM bookmarks WHERE url=?", (url,)).fetchone())

    def get_by_folder(self, folder_id: int = 1) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM bookmarks WHERE folder_id=? AND in_reading_list=0 "
            "ORDER BY sort_order, created_at DESC",
            (folder_id,),
        ).fetchall()

    def search(self, query: str, limit: int = 50) -> list[sqlite3.Row]:
        q = f"%{query}%"
        return self._conn.execute(
            "SELECT * FROM bookmarks WHERE (url LIKE ? OR title LIKE ? OR description LIKE ?) "
            "ORDER BY created_at DESC LIMIT ?",
            (q, q, q, limit),
        ).fetchall()

    def get_bar_bookmarks(self, limit: int = 20) -> list[sqlite3.Row]:
        """Return top-level bookmarks for the bookmark bar."""
        return self.get_by_folder(1)[:limit]

    # ---------- Reading List ----------

    def add_to_reading_list(self, url: str, title: str = ""):
        if not self._conn.execute("SELECT 1 FROM bookmarks WHERE url=? AND in_reading_list=1", (url,)).fetchone():
            self._conn.execute(
                "INSERT INTO bookmarks (url,title,folder_id,created_at,in_reading_list) VALUES (?,?,1,?,1)",
                (url, title, datetime.now().isoformat()),
            )
            self._conn.commit()

    def get_reading_list(self) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM bookmarks WHERE in_reading_list=1 ORDER BY created_at DESC"
        ).fetchall()

    def remove_from_reading_list(self, url: str):
        self._conn.execute("DELETE FROM bookmarks WHERE url=? AND in_reading_list=1", (url,))
        self._conn.commit()

    # ---------- Import / Export ----------

    def export_json(self, path: str):
        rows = self._conn.execute("SELECT * FROM bookmarks").fetchall()
        data = [dict(r) for r in rows]
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def import_json(self, path: str):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for bm in data:
            if not self.exists(bm.get("url", "")):
                self.add(
                    url=bm.get("url", ""),
                    title=bm.get("title", ""),
                    folder_id=bm.get("folder_id", 1),
                    description=bm.get("description", ""),
                )

    def export_netscape_html(self, path: str):
        """Export in browser-compatible Netscape HTML format."""
        rows = self._conn.execute("SELECT * FROM bookmarks").fetchall()
        lines = [
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
            "<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">",
            "<TITLE>Bookmarks</TITLE>",
            "<H1>Bookmarks</H1>",
            "<DL><p>",
        ]
        for r in rows:
            lines.append(
                f'    <DT><A HREF="{r["url"]}" ADD_DATE="{r["created_at"]}">{r["title"] or r["url"]}</A>'
            )
        lines.append("</DL><p>")
        Path(path).write_text("\n".join(lines), encoding="utf-8")
