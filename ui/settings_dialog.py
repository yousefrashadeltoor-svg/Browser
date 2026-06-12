"""
JO Browser — Settings Dialog
Full settings UI with sections: General, Appearance, Startup, Tabs, Privacy,
Downloads, Security, Shortcuts, Profiles, Developer, Advanced, About.
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, QListWidgetItem,
    QStackedWidget, QWidget, QLabel, QLineEdit, QCheckBox, QPushButton,
    QComboBox, QSlider, QFileDialog, QGroupBox, QFormLayout, QSpinBox,
    QColorDialog, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

log = logging.getLogger(__name__)

SECTIONS = [
    ("⚙ General",     "general"),
    ("🎨 Appearance",  "appearance"),
    ("🚀 Startup",     "startup"),
    ("📑 Tabs",        "tabs"),
    ("🔒 Privacy",     "privacy"),
    ("⬇ Downloads",   "downloads"),
    ("🛡 Security",    "security"),
    ("⌨ Shortcuts",   "shortcuts"),
    ("👤 Profiles",    "profiles"),
    ("🛠 Developer",   "developer"),
    ("⚡ Advanced",    "advanced"),
    ("💾 Backup",      "backup"),
    ("ℹ About",       "about"),
]


def section_widget(title: str) -> tuple[QWidget, QFormLayout]:
    w = QScrollArea()
    w.setWidgetResizable(True)
    inner = QWidget()
    lay = QFormLayout(inner)
    lay.setContentsMargins(24, 20, 24, 20)
    lay.setSpacing(14)
    lay.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    hdr = QLabel(title)
    hdr.setStyleSheet("font-size: 20px; font-weight: 700; margin-bottom: 8px;")
    lay.addRow(hdr)
    w.setWidget(inner)
    return w, lay


class SettingsDialog(QDialog):
    theme_changed = pyqtSignal(str)
    settings_saved = pyqtSignal()

    def __init__(self, settings, theme_mgr, parent=None):
        super().__init__(parent)
        self._s = settings
        self._tm = theme_mgr
        self.setWindowTitle("JO Browser — Settings")
        self.resize(860, 600)
        self._widgets: dict[str, QWidget] = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left nav ──
        nav = QListWidget()
        nav.setFixedWidth(190)
        nav.setStyleSheet("""
            QListWidget { background: #13131f; border: none; padding: 8px 0; }
            QListWidget::item { padding: 12px 20px; border-radius: 0; color: #9898b0; font-size: 13px; }
            QListWidget::item:selected { background: #1e1e2e; color: #e8e8f0; border-left: 3px solid #6C63FF; }
        """)
        nav.currentRowChanged.connect(self._switch_section)
        for label, _ in SECTIONS:
            nav.addItem(QListWidgetItem(label))
        root.addWidget(nav)

        # ── Right stack ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QStackedWidget { background: #0d0d1a; }")
        root.addWidget(self._stack)

        self._build_sections()
        nav.setCurrentRow(0)

    def _switch_section(self, idx: int):
        self._stack.setCurrentIndex(idx)

    def _build_sections(self):
        self._build_general()
        self._build_appearance()
        self._build_startup()
        self._build_tabs()
        self._build_privacy()
        self._build_downloads()
        self._build_security()
        self._build_shortcuts()
        self._build_profiles()
        self._build_developer()
        self._build_advanced()
        self._build_backup()
        self._build_about()

    # ── General ──────────────────────────────────────────────────────────────
    def _build_general(self):
        w, lay = section_widget("General")
        home = QLineEdit(self._s.get("general.home_url", "jo://newtab"))
        lay.addRow("Home URL:", home)
        self._widgets["general.home_url"] = home

        engine = QComboBox()
        engines = ["Google", "DuckDuckGo", "Bing", "Yahoo", "Brave Search", "Startpage"]
        engine.addItems(engines)
        cur = self._s.get("general.search_engine_name", "Google")
        engine.setCurrentText(cur)
        lay.addRow("Search Engine:", engine)
        self._widgets["general.search_engine_name"] = engine

        smooth = QCheckBox("Smooth scrolling")
        smooth.setChecked(self._s.get("general.smooth_scrolling", True))
        lay.addRow(smooth)
        self._widgets["general.smooth_scrolling"] = smooth

        show_bm = QCheckBox("Show bookmarks bar")
        show_bm.setChecked(self._s.get("general.show_bookmarks_bar", True))
        lay.addRow(show_bm)
        self._widgets["general.show_bookmarks_bar"] = show_bm

        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        lay.addRow(save_btn)
        self._stack.addWidget(w)

    # ── Appearance ───────────────────────────────────────────────────────────
    def _build_appearance(self):
        w, lay = section_widget("Appearance")

        theme_combo = QComboBox()
        theme_combo.addItems(self._tm.list_presets() + self._tm.list_custom())
        theme_combo.setCurrentText(self._s.get("appearance.theme", "dark"))
        theme_combo.currentTextChanged.connect(lambda t: self.theme_changed.emit(t))
        lay.addRow("Theme:", theme_combo)
        self._widgets["appearance.theme"] = theme_combo

        accent_btn = QPushButton("Choose Accent Color")
        accent_btn.clicked.connect(self._pick_accent)
        self._accent_lbl = QLabel(self._s.get("appearance.accent_color", "#6C63FF"))
        lay.addRow("Accent Color:", accent_btn)
        lay.addRow("", self._accent_lbl)

        font_combo = QComboBox()
        font_combo.addItems(["Inter", "Segoe UI", "Roboto", "SF Pro", "JetBrains Mono", "Fira Code"])
        font_combo.setCurrentText(self._s.get("appearance.font_family", "Inter"))
        lay.addRow("Font:", font_combo)
        self._widgets["appearance.font_family"] = font_combo

        font_size = QSpinBox()
        font_size.setRange(10, 22)
        font_size.setValue(self._s.get("appearance.font_size", 14))
        lay.addRow("Font Size:", font_size)
        self._widgets["appearance.font_size"] = font_size

        tab_style = QComboBox()
        tab_style.addItems(["rounded", "flat", "pill"])
        tab_style.setCurrentText(self._s.get("appearance.tab_style", "rounded"))
        lay.addRow("Tab Style:", tab_style)
        self._widgets["appearance.tab_style"] = tab_style

        compact = QCheckBox("Compact mode")
        compact.setChecked(self._s.get("appearance.compact_mode", False))
        lay.addRow(compact)
        self._widgets["appearance.compact_mode"] = compact

        animations = QCheckBox("Enable animations")
        animations.setChecked(self._s.get("appearance.animations", True))
        lay.addRow(animations)
        self._widgets["appearance.animations"] = animations

        save_btn = QPushButton("Apply")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        lay.addRow(save_btn)
        self._stack.addWidget(w)

    def _pick_accent(self):
        color = QColorDialog.getColor(QColor(self._s.get("appearance.accent_color", "#6C63FF")), self)
        if color.isValid():
            self._accent_lbl.setText(color.name())
            self._s.set("appearance.accent_color", color.name())

    # ── Startup ───────────────────────────────────────────────────────────────
    def _build_startup(self):
        w, lay = section_widget("Startup")

        restore = QCheckBox("Restore previous session on startup")
        restore.setChecked(self._s.get("startup.restore_session", True))
        lay.addRow(restore)
        self._widgets["startup.restore_session"] = restore

        splash = QCheckBox("Show splash screen")
        splash.setChecked(self._s.get("startup.show_splash", True))
        lay.addRow(splash)
        self._widgets["startup.show_splash"] = splash

        startup_page = QComboBox()
        startup_page.addItems(["new_tab", "home", "last"])
        startup_page.setCurrentText(self._s.get("startup.startup_page", "new_tab"))
        lay.addRow("Startup page:", startup_page)
        self._widgets["startup.startup_page"] = startup_page

        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        lay.addRow(save_btn)
        self._stack.addWidget(w)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    def _build_tabs(self):
        w, lay = section_widget("Tabs")

        preview = QCheckBox("Show tab preview on hover")
        preview.setChecked(self._s.get("tabs.show_preview", True))
        lay.addRow(preview)
        self._widgets["tabs.show_preview"] = preview

        max_width = QSpinBox()
        max_width.setRange(80, 400)
        max_width.setValue(self._s.get("tabs.max_tab_width", 220))
        lay.addRow("Max tab width (px):", max_width)
        self._widgets["tabs.max_tab_width"] = max_width

        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        lay.addRow(save_btn)
        self._stack.addWidget(w)

    # ── Privacy ───────────────────────────────────────────────────────────────
    def _build_privacy(self):
        w, lay = section_widget("Privacy")

        dnt = QCheckBox("Send Do Not Track")
        dnt.setChecked(self._s.get("privacy.do_not_track", True))
        lay.addRow(dnt)
        self._widgets["privacy.do_not_track"] = dnt

        block3p = QCheckBox("Block third-party cookies")
        block3p.setChecked(self._s.get("privacy.block_third_party_cookies", False))
        lay.addRow(block3p)
        self._widgets["privacy.block_third_party_cookies"] = block3p

        https_only = QCheckBox("HTTPS-only mode")
        https_only.setChecked(self._s.get("privacy.https_only", False))
        lay.addRow(https_only)
        self._widgets["privacy.https_only"] = https_only

        clear_btn = QPushButton("Clear All Browsing Data")
        clear_btn.setStyleSheet("color: #ff5555;")
        lay.addRow(clear_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        lay.addRow(save_btn)
        self._stack.addWidget(w)

    # ── Downloads ─────────────────────────────────────────────────────────────
    def _build_downloads(self):
        w, lay = section_widget("Downloads")

        dl_path = QLineEdit(self._s.get("downloads.default_path", str(Path.home() / "Downloads")))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: self._browse_dl_path(dl_path))
        row_w = QWidget()
        row_l = QHBoxLayout(row_w)
        row_l.setContentsMargins(0,0,0,0)
        row_l.addWidget(dl_path)
        row_l.addWidget(browse_btn)
        lay.addRow("Download folder:", row_w)
        self._widgets["downloads.default_path"] = dl_path

        ask = QCheckBox("Ask where to save each download")
        ask.setChecked(self._s.get("downloads.ask_every_time", False))
        lay.addRow(ask)
        self._widgets["downloads.ask_every_time"] = ask

        open_after = QCheckBox("Open file after download")
        open_after.setChecked(self._s.get("downloads.open_after", False))
        lay.addRow(open_after)
        self._widgets["downloads.open_after"] = open_after

        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        lay.addRow(save_btn)
        self._stack.addWidget(w)

    def _browse_dl_path(self, edit: QLineEdit):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            edit.setText(folder)

    # ── Security ──────────────────────────────────────────────────────────────
    def _build_security(self):
        w, lay = section_widget("Security")
        sb = QCheckBox("Safe browsing (warn on suspicious links)")
        sb.setChecked(self._s.get("privacy.safe_browsing", True))
        lay.addRow(sb)
        self._widgets["privacy.safe_browsing"] = sb
        info = QLabel("Password manager and advanced permissions management\ncoming in a future version.")
        info.setStyleSheet("color: #9898b0; font-size: 12px;")
        lay.addRow(info)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        lay.addRow(save_btn)
        self._stack.addWidget(w)

    # ── Shortcuts ─────────────────────────────────────────────────────────────
    def _build_shortcuts(self):
        w, lay = section_widget("Keyboard Shortcuts")
        shortcuts = [
            ("New Tab", "Ctrl+T"), ("Close Tab", "Ctrl+W"), ("Reload", "F5"),
            ("Address Bar", "Ctrl+L"), ("Find in Page", "Ctrl+F"),
            ("Full Screen", "F11"), ("Command Palette", "Ctrl+K"),
            ("Bookmark Page", "Ctrl+D"), ("Zoom In", "Ctrl++"),
            ("Zoom Out", "Ctrl+-"), ("Back", "Alt+Left"), ("Forward", "Alt+Right"),
            ("History", "Ctrl+H"), ("Downloads", "Ctrl+J"), ("Settings", "Ctrl+,"),
        ]
        for action, shortcut in shortcuts:
            lbl = QLabel(shortcut)
            lbl.setStyleSheet("font-family: monospace; color: #6C63FF; background: #1e1e2e; padding: 2px 8px; border-radius: 4px;")
            lay.addRow(f"{action}:", lbl)
        note = QLabel("Customizable shortcuts coming in a future version.")
        note.setStyleSheet("color: #9898b0; font-size: 12px;")
        lay.addRow(note)
        self._stack.addWidget(w)

    # ── Profiles ──────────────────────────────────────────────────────────────
    def _build_profiles(self):
        w, lay = section_widget("Profiles")
        info = QLabel("Multi-profile support: create separate browser profiles with\nindependent settings, themes, bookmarks, and history.")
        info.setStyleSheet("color: #9898b0;")
        lay.addRow(info)
        cur_lbl = QLabel("Current profile: Default")
        cur_lbl.setStyleSheet("font-weight: 600;")
        lay.addRow(cur_lbl)
        btn_new = QPushButton("+ New Profile")
        lay.addRow(btn_new)
        self._stack.addWidget(w)

    # ── Developer ─────────────────────────────────────────────────────────────
    def _build_developer(self):
        w, lay = section_widget("Developer")
        devtools = QCheckBox("Enable developer tools")
        devtools.setChecked(self._s.get("developer.devtools_enabled", True))
        lay.addRow(devtools)
        self._widgets["developer.devtools_enabled"] = devtools
        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        lay.addRow(save_btn)
        self._stack.addWidget(w)

    # ── Advanced ──────────────────────────────────────────────────────────────
    def _build_advanced(self):
        w, lay = section_widget("Advanced")
        cache = QSpinBox()
        cache.setRange(32, 2048)
        cache.setValue(self._s.get("advanced.cache_size_mb", 256))
        cache.setSuffix(" MB")
        lay.addRow("HTTP cache size:", cache)
        self._widgets["advanced.cache_size_mb"] = cache

        hw_accel = QCheckBox("Hardware acceleration")
        hw_accel.setChecked(self._s.get("general.hardware_acceleration", True))
        lay.addRow(hw_accel)
        self._widgets["general.hardware_acceleration"] = hw_accel

        low_res = QCheckBox("Low-resource mode (disable animations)")
        low_res.setChecked(self._s.get("advanced.low_resource_mode", False))
        lay.addRow(low_res)
        self._widgets["advanced.low_resource_mode"] = low_res

        aot = QCheckBox("Always on top")
        aot.setChecked(self._s.get("advanced.always_on_top", False))
        lay.addRow(aot)
        self._widgets["advanced.always_on_top"] = aot

        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        lay.addRow(save_btn)
        self._stack.addWidget(w)

    # ── Backup ────────────────────────────────────────────────────────────────
    def _build_backup(self):
        w, lay = section_widget("Backup & Restore")
        exp_bm = QPushButton("Export Bookmarks (HTML)")
        lay.addRow(exp_bm)
        imp_bm = QPushButton("Import Bookmarks (JSON)")
        lay.addRow(imp_bm)
        info = QLabel("Full backup/restore (settings, history, notes) coming soon.")
        info.setStyleSheet("color: #9898b0; font-size: 12px;")
        lay.addRow(info)
        self._stack.addWidget(w)

    # ── About ─────────────────────────────────────────────────────────────────
    def _build_about(self):
        w, lay = section_widget("About JO Browser")
        logo = QLabel("JO Browser")
        logo.setStyleSheet("font-size: 28px; font-weight: 900; color: #6C63FF;")
        lay.addRow(logo)
        lay.addRow(QLabel("Version: 1.0.0"))
        lay.addRow(QLabel("Built with PyQt6 + QtWebEngine"))
        lay.addRow(QLabel("Python-native premium browser"))
        copy = QLabel("© 2025 JO Browser. All rights reserved.")
        copy.setStyleSheet("color: #9898b0; font-size: 12px;")
        lay.addRow(copy)
        self._stack.addWidget(w)

    # ── Save ──────────────────────────────────────────────────────────────────
    def _save(self):
        for key, widget in self._widgets.items():
            if isinstance(widget, QCheckBox):
                self._s.set(key, widget.isChecked())
            elif isinstance(widget, QLineEdit):
                self._s.set(key, widget.text())
            elif isinstance(widget, QComboBox):
                self._s.set(key, widget.currentText())
            elif isinstance(widget, (QSpinBox,)):
                self._s.set(key, widget.value())
        self.settings_saved.emit()
        log.info("Settings saved")
