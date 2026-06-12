"""
JO Browser — Command Palette (Ctrl+K / Ctrl+Space)
Quick search for commands, history, bookmarks, and settings.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeyEvent

log = logging.getLogger(__name__)

BUILT_IN_COMMANDS = [
    ("New Tab",              "new_tab",        "Ctrl+T"),
    ("New Incognito Window", "incognito",      "Ctrl+Shift+N"),
    ("Open Settings",        "settings",       "Ctrl+,"),
    ("Toggle Bookmarks",     "bookmarks",      ""),
    ("Toggle History",       "history",        ""),
    ("Toggle Notes",         "notes",          ""),
    ("Toggle AI Sidebar",    "ai",             ""),
    ("Toggle Dev Tools",     "dev",            ""),
    ("Open Downloads",       "downloads",      ""),
    ("Reload Page",          "reload",         "F5"),
    ("Hard Reload",          "hard_reload",    "Ctrl+Shift+R"),
    ("Zoom In",              "zoom_in",        "Ctrl++"),
    ("Zoom Out",             "zoom_out",       "Ctrl+-"),
    ("Reset Zoom",           "zoom_reset",     "Ctrl+0"),
    ("Go Back",              "back",           "Alt+Left"),
    ("Go Forward",           "forward",        "Alt+Right"),
    ("Find in Page",         "find",           "Ctrl+F"),
    ("View Source",          "view_source",    ""),
    ("Clear History",        "clear_history",  ""),
    ("Clear Cache",          "clear_cache",    ""),
    ("Close Tab",            "close_tab",      "Ctrl+W"),
    ("Restore Closed Tab",   "restore_tab",    "Ctrl+Shift+T"),
    ("Switch to Dark Theme", "theme_dark",     ""),
    ("Switch to Light Theme","theme_light",    ""),
    ("Switch to Neon Theme", "theme_neon",     ""),
    ("Switch to Work Theme", "theme_work",     ""),
    ("Full Screen",          "fullscreen",     "F11"),
    ("Focus URL Bar",        "focus_url",      "Ctrl+L"),
    ("Bookmark This Page",   "bookmark",       "Ctrl+D"),
    ("Save Page As",         "save_page",      "Ctrl+S"),
    ("Print Page",           "print",          "Ctrl+P"),
]


class CommandPalette(QDialog):
    command_selected = pyqtSignal(str)  # emits command id
    navigate_to     = pyqtSignal(str)  # emits URL

    def __init__(self, history_mgr=None, bookmarks_mgr=None, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self._hist = history_mgr
        self._bm   = bookmarks_mgr
        self._all_items: list[tuple[str, str, str]] = []  # label, id, hint
        self._setup_ui()
        self._build_items()
        self.setMinimumWidth(560)
        self.setMaximumHeight(480)
        self.setStyleSheet("""
            QDialog { background: #1e1e2e; border: 1px solid #2a2a40; border-radius: 14px; }
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Type a command or URL...")
        self._search.setStyleSheet("""
            QLineEdit {
                background: #252535; border: none; border-radius: 8px;
                padding: 10px 14px; font-size: 15px; color: #e8e8f0;
            }
        """)
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { padding: 10px 12px; border-radius: 6px; color: #e8e8f0; }
            QListWidget::item:selected { background: #6C63FF; color: #fff; }
        """)
        self._list.itemActivated.connect(self._on_activate)
        layout.addWidget(self._list)

        hint = QLabel("↑↓ navigate  ↵ select  Esc close")
        hint.setStyleSheet("color: #606078; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

    def _build_items(self):
        self._all_items = []
        for label, cmd_id, shortcut in BUILT_IN_COMMANDS:
            hint = f"  {shortcut}" if shortcut else ""
            self._all_items.append((f"{label}{hint}", cmd_id, "command"))
        # Recent history
        if self._hist:
            for row in self._hist.recent(30):
                title = row["title"] or row["url"]
                self._all_items.append((f"🕐 {title}", row["url"], "url"))
        # Bookmarks
        if self._bm:
            for row in self._bm.search("", limit=30):
                title = row["title"] or row["url"]
                self._all_items.append((f"★ {title}", row["url"], "url"))

    def _filter(self, text: str):
        self._list.clear()
        q = text.lower()
        for label, id_, kind in self._all_items:
            if not q or q in label.lower() or q in id_.lower():
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, (id_, kind))
                self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _on_activate(self, item: QListWidgetItem):
        id_, kind = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
        if kind == "url":
            self.navigate_to.emit(id_)
        else:
            self.command_selected.emit(id_)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key.Key_Escape:
            self.reject()
        elif e.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            count = self._list.count()
            if count == 0:
                return
            row = self._list.currentRow()
            if e.key() == Qt.Key.Key_Down:
                self._list.setCurrentRow((row + 1) % count)
            else:
                self._list.setCurrentRow((row - 1) % count)
        elif e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            item = self._list.currentItem()
            if item:
                self._on_activate(item)
        else:
            super().keyPressEvent(e)

    def show_centered(self, parent_rect):
        self._filter("")
        self._search.clear()
        self._search.setFocus()
        # Position at top-center of parent
        x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
        y = parent_rect.y() + 100
        self.move(x, y)
        self.exec()
