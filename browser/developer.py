"""
JO Browser — Developer Sidebar
Dev tools panel: DevTools hook, console log viewer,
local project opener, localhost quick-connect.
"""

import logging
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFileDialog, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineCore import QWebEnginePage

log = logging.getLogger(__name__)

COMMON_PORTS = [3000, 3001, 4000, 4200, 5000, 5173, 8000, 8080, 8888, 9000]


class DeveloperSidebarWidget(QWidget):
    def __init__(self, browser_window, parent=None):
        super().__init__(parent)
        self._browser = browser_window
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel("🛠 Developer Tools")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        # ---------- Local Project ----------
        proj_box = QGroupBox("Local Project")
        proj_layout = QVBoxLayout(proj_box)
        open_folder_btn = QPushButton("📂 Open Folder")
        open_folder_btn.clicked.connect(self._open_folder)
        proj_layout.addWidget(open_folder_btn)
        open_html_btn = QPushButton("📄 Open HTML File")
        open_html_btn.clicked.connect(self._open_html)
        proj_layout.addWidget(open_html_btn)
        layout.addWidget(proj_box)

        # ---------- Localhost Quick-Connect ----------
        local_box = QGroupBox("Localhost Quick-Connect")
        local_layout = QHBoxLayout(local_box)
        self._port_combo = QComboBox()
        for p in COMMON_PORTS:
            self._port_combo.addItem(str(p))
        self._port_combo.setEditable(True)
        local_layout.addWidget(QLabel("Port:"))
        local_layout.addWidget(self._port_combo)
        go_btn = QPushButton("Go")
        go_btn.clicked.connect(self._goto_localhost)
        local_layout.addWidget(go_btn)
        layout.addWidget(local_box)

        # ---------- DevTools ----------
        devtools_box = QGroupBox("DevTools")
        devtools_layout = QVBoxLayout(devtools_box)
        open_devtools_btn = QPushButton("🔍 Open DevTools")
        open_devtools_btn.clicked.connect(self._open_devtools)
        devtools_layout.addWidget(open_devtools_btn)
        view_source_btn = QPushButton("📜 View Page Source")
        view_source_btn.clicked.connect(self._view_source)
        devtools_layout.addWidget(view_source_btn)
        layout.addWidget(devtools_box)

        # ---------- Console ----------
        console_box = QGroupBox("Console")
        console_layout = QVBoxLayout(console_box)
        self._console_output = QTextEdit()
        self._console_output.setReadOnly(True)
        self._console_output.setMaximumHeight(200)
        self._console_output.setPlaceholderText("JavaScript console output...")
        console_layout.addWidget(self._console_output)

        run_row = QHBoxLayout()
        self._js_input = QLineEdit()
        self._js_input.setPlaceholderText("Run JavaScript...")
        self._js_input.returnPressed.connect(self._run_js)
        run_row.addWidget(self._js_input)
        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self._run_js)
        run_row.addWidget(run_btn)
        console_layout.addLayout(run_row)
        layout.addWidget(console_box)

        # ---------- Page Info ----------
        info_box = QGroupBox("Page Info")
        info_layout = QVBoxLayout(info_box)
        self._info_lbl = QLabel("Load a page to see details.")
        self._info_lbl.setWordWrap(True)
        self._info_lbl.setStyleSheet("font-size: 12px; color: #9898b0;")
        info_layout.addWidget(self._info_lbl)
        refresh_info_btn = QPushButton("Refresh Info")
        refresh_info_btn.clicked.connect(self._refresh_info)
        info_layout.addWidget(refresh_info_btn)
        layout.addWidget(info_box)

        layout.addStretch()

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Local Project Folder")
        if folder:
            index_path = Path(folder) / "index.html"
            if index_path.exists():
                self._browser.open_url(f"file:///{index_path}")
            else:
                self._browser.open_url(f"file:///{folder}")

    def _open_html(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open HTML File", "", "HTML Files (*.html *.htm);;All Files (*)"
        )
        if path:
            self._browser.open_url(f"file:///{path}")

    def _goto_localhost(self):
        port = self._port_combo.currentText().strip()
        if port.isdigit():
            self._browser.open_url(f"http://localhost:{port}")

    def _open_devtools(self):
        tab = self._browser.current_tab()
        if tab:
            tab.page().setDevToolsPage(QWebEnginePage(tab.page().profile(), tab))
            log.info("DevTools opened")

    def _view_source(self):
        tab = self._browser.current_tab()
        if tab:
            url = tab.url().toString()
            self._browser.open_new_tab(url=f"view-source:{url}")

    def _run_js(self):
        tab = self._browser.current_tab()
        js = self._js_input.text().strip()
        if tab and js:
            def cb(result):
                self._console_output.append(f">> {js}\n<< {result}\n")
            tab.page().runJavaScript(js, cb)
            self._js_input.clear()

    def _refresh_info(self):
        tab = self._browser.current_tab()
        if not tab:
            return
        url = tab.url().toString()
        title = tab.title()
        self._info_lbl.setText(
            f"<b>URL:</b> {url}<br>"
            f"<b>Title:</b> {title}<br>"
            f"<b>Security:</b> {'HTTPS ✓' if url.startswith('https') else 'HTTP (not secure)'}"
        )

    def log_js(self, message: str):
        self._console_output.append(message)
