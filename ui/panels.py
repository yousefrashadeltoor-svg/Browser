"""
JO Browser — Sidebar Panels
BookmarksPanel, HistoryPanel, NotesPanel, DownloadsPanel
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox,
    QFileDialog, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction

from browser.downloads import format_size, format_speed

log = logging.getLogger(__name__)


# ─── Bookmarks Panel ────────────────────────────────────────────────────────

class BookmarksPanel(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, bookmarks_mgr, parent=None):
        super().__init__(parent)
        self._bm = bookmarks_mgr
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search bookmarks...")
        self._search.textChanged.connect(self._search_changed)
        layout.addWidget(self._search)

        # Tree
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._tree)

        # Actions
        btn_row = QHBoxLayout()
        btn_new_folder = QPushButton("New Folder")
        btn_new_folder.clicked.connect(self._new_folder)
        btn_export = QPushButton("Export")
        btn_export.clicked.connect(self._export)
        btn_import = QPushButton("Import")
        btn_import.clicked.connect(self._import)
        btn_row.addWidget(btn_new_folder)
        btn_row.addWidget(btn_export)
        btn_row.addWidget(btn_import)
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self, query: str = ""):
        self._tree.clear()
        if query:
            results = self._bm.search(query)
            for row in results:
                item = QTreeWidgetItem([row["title"] or row["url"]])
                item.setData(0, Qt.ItemDataRole.UserRole, row["url"])
                item.setToolTip(0, row["url"])
                self._tree.addTopLevelItem(item)
        else:
            self._build_tree(None, self._bm.get_folders(parent_id=1), 1)

    def _build_tree(self, parent_item, folders, folder_id):
        bookmarks = self._bm.get_by_folder(folder_id)
        for row in bookmarks:
            item = QTreeWidgetItem([row["title"] or row["url"]])
            item.setData(0, Qt.ItemDataRole.UserRole, row["url"])
            item.setToolTip(0, row["url"])
            item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
            if parent_item:
                parent_item.addChild(item)
            else:
                self._tree.addTopLevelItem(item)
        for folder in folders:
            fid = folder["id"]
            fi = QTreeWidgetItem([f"📁 {folder['name']}"])
            fi.setData(0, Qt.ItemDataRole.UserRole, None)
            if parent_item:
                parent_item.addChild(fi)
            else:
                self._tree.addTopLevelItem(fi)
            sub_folders = self._bm.get_folders(parent_id=fid)
            self._build_tree(fi, sub_folders, fid)
        if parent_item:
            parent_item.setExpanded(True)

    def _search_changed(self, text: str):
        self._refresh(text)

    def _on_double_click(self, item: QTreeWidgetItem, _):
        url = item.data(0, Qt.ItemDataRole.UserRole)
        if url:
            self.navigate.emit(url)

    def _show_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return
        url = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        if url:
            menu.addAction("Open", lambda: self.navigate.emit(url))
            menu.addAction("Open in New Tab", lambda: self.navigate.emit(url))
            menu.addSeparator()
            menu.addAction("Delete", lambda: self._delete_item(item, url))
        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _delete_item(self, item, url: str):
        self._bm.delete_url_bookmark(url) if hasattr(self._bm, "delete_url_bookmark") else None
        self._refresh()

    def _new_folder(self):
        self._bm.add_folder("New Folder")
        self._refresh()

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Bookmarks", "bookmarks.html", "HTML (*.html)")
        if path:
            self._bm.export_netscape_html(path)

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Bookmarks", "", "JSON (*.json)")
        if path:
            self._bm.import_json(path)
            self._refresh()

    def refresh(self):
        self._refresh()


# ─── History Panel ───────────────────────────────────────────────────────────

class HistoryPanel(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, history_mgr, parent=None):
        super().__init__(parent)
        self._hist = history_mgr
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search history...")
        self._search.textChanged.connect(self._search_changed)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(lambda item: self.navigate.emit(item.data(Qt.ItemDataRole.UserRole)))
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._ctx_menu)
        layout.addWidget(self._list)

        btn_clear = QPushButton("Clear All History")
        btn_clear.clicked.connect(self._clear_all)
        layout.addWidget(btn_clear)

        self._refresh()

    def _refresh(self, query: str = ""):
        self._list.clear()
        rows = self._hist.search(query) if query else self._hist.recent(100)
        for row in rows:
            item = QListWidgetItem(f"{row['title'] or row['url']}")
            item.setData(Qt.ItemDataRole.UserRole, row["url"])
            item.setToolTip(f"{row['url']}\n{row['visited_at']}")
            self._list.addItem(item)

    def _search_changed(self, text: str):
        self._refresh(text)

    def _ctx_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return
        url = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.addAction("Open", lambda: self.navigate.emit(url))
        menu.addAction("Delete", lambda: self._delete(item, url))
        menu.exec(self._list.viewport().mapToGlobal(pos))

    def _delete(self, item, url: str):
        self._hist.delete_url(url)
        self._list.takeItem(self._list.row(item))

    def _clear_all(self):
        if QMessageBox.question(self, "Clear History", "Clear all browsing history?") == QMessageBox.StandardButton.Yes:
            self._hist.clear()
            self._list.clear()

    def refresh(self):
        self._refresh()


# ─── Notes Panel ─────────────────────────────────────────────────────────────

class NotesPanel(QWidget):
    def __init__(self, notes_mgr, parent=None):
        super().__init__(parent)
        self._notes = notes_mgr
        self._current_id = None
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._auto_save)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # List of notes
        top_row = QHBoxLayout()
        self._note_list = QListWidget()
        self._note_list.setMaximumHeight(120)
        self._note_list.currentRowChanged.connect(self._on_note_selected)
        top_row.addWidget(self._note_list)
        note_btns = QVBoxLayout()
        btn_new = QPushButton("+ New")
        btn_new.clicked.connect(self._new_note)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._delete_note)
        note_btns.addWidget(btn_new)
        note_btns.addWidget(btn_del)
        note_btns.addStretch()
        top_row.addLayout(note_btns)
        layout.addLayout(top_row)

        # Title
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Note title...")
        self._title_edit.textChanged.connect(lambda: self._save_timer.start(800))
        layout.addWidget(self._title_edit)

        # Content
        self._content_edit = QTextEdit()
        self._content_edit.setPlaceholderText("Start writing...")
        self._content_edit.textChanged.connect(lambda: self._save_timer.start(800))
        layout.addWidget(self._content_edit)

        self._refresh_list()

    def _refresh_list(self):
        self._note_list.clear()
        for note in self._notes.all():
            item = QListWidgetItem(note["title"] or "Untitled")
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            self._note_list.addItem(item)

    def _on_note_selected(self, idx):
        if idx < 0:
            return
        item = self._note_list.item(idx)
        if not item:
            return
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = self._notes.get(note_id)
        if note:
            self._current_id = note_id
            self._title_edit.blockSignals(True)
            self._content_edit.blockSignals(True)
            self._title_edit.setText(note["title"] or "")
            self._content_edit.setPlainText(note["content"] or "")
            self._title_edit.blockSignals(False)
            self._content_edit.blockSignals(False)

    def _new_note(self):
        note_id = self._notes.add("Untitled", "")
        self._refresh_list()
        # Select the new note
        for i in range(self._note_list.count()):
            if self._note_list.item(i).data(Qt.ItemDataRole.UserRole) == note_id:
                self._note_list.setCurrentRow(i)
                break

    def _delete_note(self):
        if self._current_id:
            self._notes.delete(self._current_id)
            self._current_id = None
            self._title_edit.clear()
            self._content_edit.clear()
            self._refresh_list()

    def _auto_save(self):
        if self._current_id:
            self._notes.update(
                self._current_id,
                title=self._title_edit.text(),
                content=self._content_edit.toPlainText(),
            )


# ─── Downloads Panel ─────────────────────────────────────────────────────────

class DownloadItemWidget(QWidget):
    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._item = item
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        row = QHBoxLayout()
        self._name_lbl = QLabel(item.filename[:40])
        self._name_lbl.setStyleSheet("font-weight: 600; font-size: 13px;")
        row.addWidget(self._name_lbl)
        row.addStretch()
        self._state_lbl = QLabel(item.state)
        self._state_lbl.setStyleSheet("font-size: 11px; color: #9898b0;")
        row.addWidget(self._state_lbl)
        layout.addLayout(row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setMaximumHeight(6)
        self._progress.setTextVisible(False)
        layout.addWidget(self._progress)

        btn_row = QHBoxLayout()
        self._speed_lbl = QLabel("")
        self._speed_lbl.setStyleSheet("font-size: 11px; color: #9898b0;")
        btn_row.addWidget(self._speed_lbl)
        btn_row.addStretch()
        pause_btn = QPushButton("Pause")
        pause_btn.setFixedWidth(55)
        pause_btn.clicked.connect(item.pause)
        resume_btn = QPushButton("Resume")
        resume_btn.setFixedWidth(65)
        resume_btn.clicked.connect(item.resume)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(60)
        cancel_btn.clicked.connect(item.cancel)
        btn_row.addWidget(pause_btn)
        btn_row.addWidget(resume_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        item.progress_changed.connect(self._on_progress)
        item.state_changed.connect(self._on_state)
        item.speed_updated.connect(self._on_speed)

    def _on_progress(self, received, total):
        if total > 0:
            self._progress.setValue(int(received / total * 100))
        size_str = f"{format_size(received)} / {format_size(total)}"
        self._state_lbl.setText(size_str)

    def _on_state(self, state: str):
        self._state_lbl.setText(state)

    def _on_speed(self, bps: float):
        self._speed_lbl.setText(format_speed(bps))


class DownloadsPanel(QWidget):
    def __init__(self, downloads_mgr, parent=None):
        super().__init__(parent)
        self._dm = downloads_mgr
        self._setup_ui()
        self._dm.download_added.connect(self._on_new_download)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        label = QLabel("Downloads")
        label.setStyleSheet("font-weight: 700; font-size: 14px;")
        layout.addWidget(label)

        self._items_layout = QVBoxLayout()
        self._items_layout.setSpacing(4)
        layout.addLayout(self._items_layout)

        btn_clear = QPushButton("Clear Completed")
        btn_clear.clicked.connect(self._clear_done)
        layout.addWidget(btn_clear)

        layout.addStretch()

    def _on_new_download(self, item):
        widget = DownloadItemWidget(item)
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: #1e1e2e; border-radius: 8px; border: 1px solid #2a2a40; }")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addWidget(widget)
        self._items_layout.insertWidget(0, frame)

    def _clear_done(self):
        self._dm.clear_history()
        # Remove completed widgets
        while self._items_layout.count() > 0:
            item = self._items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
