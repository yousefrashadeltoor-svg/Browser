"""
JO Browser — Sidebar Container
Hosts multiple panels (bookmarks, history, notes, AI, dev tools, downloads)
and switches between them. Panels are lazy-loaded on first open.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

log = logging.getLogger(__name__)

PANEL_ICONS = {
    "bookmarks": "📚",
    "history":   "⏱",
    "notes":     "📝",
    "ai":        "🤖",
    "dev":       "🛠",
    "downloads": "⬇",
}


class SidebarContainer(QWidget):
    """Animated sidebar that hosts named panels."""
    close_requested = pyqtSignal()

    COLLAPSED_W = 0
    EXPANDED_W  = 320

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)
        self._panels: dict[str, QWidget] = {}
        self._current: str | None = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setObjectName("panel")
        header.setFixedHeight(44)
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(12, 0, 8, 0)
        self._title_lbl = QLabel("Panel")
        self._title_lbl.setStyleSheet("font-weight: 700; font-size: 14px;")
        hlay.addWidget(self._title_lbl)
        hlay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("icon_btn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.collapse)
        hlay.addWidget(close_btn)
        root.addWidget(header)

        # Stack
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

    def register_panel(self, name: str, widget: QWidget):
        self._panels[name] = widget
        self._stack.addWidget(widget)

    def toggle(self, name: str):
        if self._current == name and self.maximumWidth() > 0:
            self.collapse()
        else:
            self.expand(name)

    def expand(self, name: str):
        if name not in self._panels:
            log.warning("Panel not registered: %s", name)
            return
        self._current = name
        self._title_lbl.setText(f"{PANEL_ICONS.get(name, '')} {name.title()}")
        self._stack.setCurrentWidget(self._panels[name])
        self._animate(self.EXPANDED_W)

    def collapse(self):
        self._current = None
        self._animate(self.COLLAPSED_W)
        self.close_requested.emit()

    def _animate(self, target_w: int):
        anim = QPropertyAnimation(self, b"maximumWidth", self)
        anim.setDuration(220)
        anim.setStartValue(self.maximumWidth())
        anim.setEndValue(target_w)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # Also animate minimum so widget collapses fully
        anim2 = QPropertyAnimation(self, b"minimumWidth", self)
        anim2.setDuration(220)
        anim2.setStartValue(self.minimumWidth())
        anim2.setEndValue(target_w)
        anim2.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        anim2.start()
        self._anim = anim   # keep reference
        self._anim2 = anim2
