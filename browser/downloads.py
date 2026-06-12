"""
JO Browser — Downloads Manager
Wraps QWebEngineDownloadRequest; tracks progress, pause, resume, cancel.
Stores metadata in SQLite for persistent download history.
"""

import sqlite3
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest

from browser.utils import data_path

log = logging.getLogger(__name__)

CATEGORIES = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico"],
    "video": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"],
    "audio": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"],
    "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".csv"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "installer": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"],
}


def categorize(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            return cat
    return "other"


class DownloadItem(QObject):
    progress_changed = pyqtSignal(int, int)   # received, total
    state_changed = pyqtSignal(str)           # 'downloading','paused','completed','cancelled','error'
    speed_updated = pyqtSignal(float)         # bytes/sec

    def __init__(self, download: QWebEngineDownloadRequest, save_path: str):
        super().__init__()
        self._dl = download
        self._save_path = save_path
        self._last_bytes = 0
        self._last_time = datetime.now().timestamp()
        self.db_id: Optional[int] = None

        download.receivedBytesChanged.connect(self._on_progress)
        download.stateChanged.connect(self._on_state)
        download.setDownloadDirectory(str(Path(save_path).parent))
        download.setDownloadFileName(Path(save_path).name)
        download.accept()

    @property
    def filename(self) -> str:
        return Path(self._save_path).name

    @property
    def url(self) -> str:
        return self._dl.url().toString()

    @property
    def total_bytes(self) -> int:
        return self._dl.totalBytes()

    @property
    def received_bytes(self) -> int:
        return self._dl.receivedBytes()

    @property
    def state(self) -> str:
        s = self._dl.state()
        mapping = {
            QWebEngineDownloadRequest.DownloadState.DownloadInProgress: "downloading",
            QWebEngineDownloadRequest.DownloadState.DownloadCompleted: "completed",
            QWebEngineDownloadRequest.DownloadState.DownloadCancelled: "cancelled",
            QWebEngineDownloadRequest.DownloadState.DownloadInterrupted: "error",
        }
        return mapping.get(s, "unknown")

    def pause(self):
        self._dl.pause()
        self.state_changed.emit("paused")

    def resume(self):
        self._dl.resume()
        self.state_changed.emit("downloading")

    def cancel(self):
        self._dl.cancel()
        self.state_changed.emit("cancelled")

    def open_file(self):
        os.startfile(self._save_path)

    def reveal_in_folder(self):
        os.startfile(str(Path(self._save_path).parent))

    def _on_progress(self):
        received = self._dl.receivedBytes()
        total = self._dl.totalBytes()
        now = datetime.now().timestamp()
        elapsed = now - self._last_time
        if elapsed > 0.5:
            speed = (received - self._last_bytes) / elapsed
            self.speed_updated.emit(speed)
            self._last_bytes = received
            self._last_time = now
        self.progress_changed.emit(received, total)

    def _on_state(self):
        self.state_changed.emit(self.state)


class DownloadsManager(QObject):
    download_added = pyqtSignal(object)

    def __init__(self, settings):
        super().__init__()
        self._settings = settings
        self._items: list[DownloadItem] = []
        db_path = data_path("downloads.db")
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._setup_db()

    def _setup_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                filename TEXT,
                save_path TEXT,
                total_bytes INTEGER,
                state TEXT,
                category TEXT,
                started_at TEXT,
                completed_at TEXT
            )
        """)
        self._conn.commit()

    def handle(self, download: QWebEngineDownloadRequest):
        default_dir = self._settings.get("downloads.default_path",
                                         str(Path.home() / "Downloads"))
        filename = download.downloadFileName() or "download"
        save_path = str(Path(default_dir) / filename)

        item = DownloadItem(download, save_path)
        self._items.append(item)

        # Persist metadata
        cur = self._conn.execute(
            "INSERT INTO downloads (url,filename,save_path,total_bytes,state,category,started_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (item.url, item.filename, save_path, item.total_bytes,
             "downloading", categorize(filename), datetime.now().isoformat()),
        )
        self._conn.commit()
        item.db_id = cur.lastrowid

        item.state_changed.connect(lambda s, i=item: self._on_state(i, s))
        self.download_added.emit(item)
        log.info("Download started: %s", filename)

    def _on_state(self, item: DownloadItem, state: str):
        if item.db_id:
            self._conn.execute(
                "UPDATE downloads SET state=?, completed_at=? WHERE id=?",
                (state, datetime.now().isoformat() if state == "completed" else None, item.db_id),
            )
            self._conn.commit()

    def active(self) -> list[DownloadItem]:
        return [i for i in self._items if i.state == "downloading"]

    def all_items(self) -> list[DownloadItem]:
        return list(self._items)

    def history(self, category: str = None, limit: int = 200) -> list[sqlite3.Row]:
        if category:
            return self._conn.execute(
                "SELECT * FROM downloads WHERE category=? ORDER BY started_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        return self._conn.execute(
            "SELECT * FROM downloads ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()

    def clear_history(self):
        self._conn.execute("DELETE FROM downloads WHERE state != 'downloading'")
        self._conn.commit()


def format_size(b: int) -> str:
    if b < 0:
        return "Unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def format_speed(bps: float) -> str:
    return format_size(int(bps)) + "/s"
