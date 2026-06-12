"""
JO Browser — Navigation Toolbar
Contains: back, forward, reload, stop, home, URL bar, bookmarks toggle,
sidebar toggles, menu button, and download indicator.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QCompleter, QSizePolicy
)
from PyQt6.QtCore import Qt, QStringListModel, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut

log = logging.getLogger(__name__)


class SmartUrlBar(QLineEdit):
    """
    Smart URL / omnibox: detects URLs vs search queries,
    shows autocomplete from history, and has a security indicator.
    """
    navigate = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("urlbar")
        self.setPlaceholderText("Search or enter URL...")
        self.setClearButtonEnabled(True)
        self.setMinimumWidth(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.returnPressed.connect(self._on_return)
        self._completer_model = QStringListModel()
        self._completer = QCompleter(self._completer_model, self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self._completer)

    def set_suggestions(self, urls: list[str]):
        self._completer_model.setStringList(urls)

    def set_url(self, url: str):
        if not self.hasFocus():
            self.setText(url)
            self._update_security_style(url)

    def _update_security_style(self, url: str):
        if url.startswith("https://"):
            self.setStyleSheet(self.styleSheet() + "QLineEdit { color: #50fa7b; }")
        elif url.startswith("http://"):
            self.setStyleSheet(self.styleSheet() + "QLineEdit { color: #ffb86c; }")
        else:
            self.setStyleSheet("")

    def _on_return(self):
        text = self.text().strip()
        if not text:
            return
        self.navigate.emit(self._resolve(text))

    def _resolve(self, text: str) -> str:
        if text.startswith(("http://", "https://", "file:///", "jo://", "view-source:")):
            return text
        if "." in text and " " not in text and not text.startswith(" "):
            return "https://" + text
        # Treat as search
        return f"https://www.google.com/search?q={text}"

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()


class NavigationToolbar(QWidget):
    """Full browser toolbar."""
    navigate_to = pyqtSignal(str)
    go_back = pyqtSignal()
    go_forward = pyqtSignal()
    reload_page = pyqtSignal()
    stop_page = pyqtSignal()
    go_home = pyqtSignal()
    new_tab_requested = pyqtSignal()
    toggle_sidebar = pyqtSignal(str)   # sidebar name: 'bookmarks','history','notes','ai','dev'
    toggle_menu = pyqtSignal()
    bookmark_toggle = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setObjectName("toolbar")
        self._setup_ui()
        self._setup_shortcuts()

    def _icon_btn(self, icon: str, tip: str) -> QPushButton:
        btn = QPushButton(icon)
        btn.setObjectName("icon_btn")
        btn.setToolTip(tip)
        btn.setFixedSize(34, 34)
        return btn

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Navigation
        self.btn_back = self._icon_btn("◀", "Back (Alt+Left)")
        self.btn_forward = self._icon_btn("▶", "Forward (Alt+Right)")
        self.btn_reload = self._icon_btn("↻", "Reload (F5)")
        self.btn_stop = self._icon_btn("✕", "Stop")
        self.btn_home = self._icon_btn("⌂", "Home")

        self.btn_back.clicked.connect(self.go_back)
        self.btn_forward.clicked.connect(self.go_forward)
        self.btn_reload.clicked.connect(self.reload_page)
        self.btn_stop.clicked.connect(self.stop_page)
        self.btn_home.clicked.connect(self.go_home)

        for btn in [self.btn_back, self.btn_forward, self.btn_reload, self.btn_stop, self.btn_home]:
            layout.addWidget(btn)

        layout.addSpacing(4)

        # URL bar
        self.url_bar = SmartUrlBar()
        self.url_bar.navigate.connect(self.navigate_to)
        layout.addWidget(self.url_bar)

        layout.addSpacing(4)

        # Bookmark toggle
        self.btn_bookmark = self._icon_btn("☆", "Bookmark this page (Ctrl+D)")
        self.btn_bookmark.clicked.connect(self.bookmark_toggle)
        layout.addWidget(self.btn_bookmark)

        # Sidebar toggles
        for icon, name, tip in [
            ("📚", "bookmarks", "Bookmarks"),
            ("⏱", "history", "History"),
            ("📝", "notes", "Notes"),
            ("🤖", "ai", "AI Assistant"),
            ("🛠", "dev", "Developer Tools"),
        ]:
            btn = self._icon_btn(icon, tip)
            btn.clicked.connect(lambda checked, n=name: self.toggle_sidebar.emit(n))
            layout.addWidget(btn)

        # Downloads
        self.btn_downloads = self._icon_btn("⬇", "Downloads")
        self.btn_downloads.clicked.connect(lambda: self.toggle_sidebar.emit("downloads"))
        layout.addWidget(self.btn_downloads)

        # New tab
        btn_new = self._icon_btn("+", "New Tab (Ctrl+T)")
        btn_new.clicked.connect(self.new_tab_requested)
        layout.addWidget(btn_new)

        # Menu
        btn_menu = self._icon_btn("☰", "Menu")
        btn_menu.clicked.connect(self.toggle_menu)
        layout.addWidget(btn_menu)

    def _setup_shortcuts(self):
        pass  # Shortcuts are registered in the main window

    def update_url(self, url: str):
        self.url_bar.set_url(url)

    def update_suggestions(self, urls: list[str]):
        self.url_bar.set_suggestions(urls)

    def set_loading(self, loading: bool):
        self.btn_reload.setVisible(not loading)
        self.btn_stop.setVisible(loading)

    def set_bookmark_state(self, bookmarked: bool):
        self.btn_bookmark.setText("★" if bookmarked else "☆")
        self.btn_bookmark.setStyleSheet(
            "color: #6C63FF;" if bookmarked else ""
        )

    def set_nav_state(self, can_back: bool, can_forward: bool):
        self.btn_back.setEnabled(can_back)
        self.btn_forward.setEnabled(can_forward)
