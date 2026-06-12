"""
JO Browser — Core Window (JOBrowser)
The main application window. Manages: tabs, toolbar, sidebars, shortcuts,
menus, zoom, find-in-page, profiles, and event wiring.
"""

import logging
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTabBar, QMenu, QMenuBar, QStatusBar, QMessageBox, QInputDialog,
    QApplication, QToolBar, QSplitter, QLabel, QFileDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineSettings,
    QWebEngineDownloadRequest
)
from PyQt6.QtCore import (
    Qt, QUrl, QTimer, pyqtSignal, QSize, QRect
)
from PyQt6.QtGui import (
    QKeySequence, QShortcut, QAction, QIcon, QFont, QFontDatabase
)

from browser.settings import Settings
from browser.themes import ThemeManager
from browser.history import HistoryManager
from browser.bookmarks import BookmarksManager
from browser.downloads import DownloadsManager
from browser.session import SessionManager
from browser.notes import NotesManager
from browser.privacy import PrivacyManager
from browser.ai_sidebar import AISidebarWidget
from browser.developer import DeveloperSidebarWidget

from ui.toolbar import NavigationToolbar
from ui.sidebar import SidebarContainer
from ui.panels import BookmarksPanel, HistoryPanel, NotesPanel, DownloadsPanel
from ui.new_tab_page import get_new_tab_html
from ui.command_palette import CommandPalette
from ui.settings_dialog import SettingsDialog

log = logging.getLogger(__name__)

# Internal URL scheme
JO_SCHEME = "jo://"
JO_NEWTAB = "jo://newtab"


class BrowserTab(QWebEngineView):
    """Single browser tab: wraps QWebEngineView with extra state."""
    title_changed_signal = pyqtSignal(str, object)  # title, tab_ref
    icon_changed_signal  = pyqtSignal(object)        # tab_ref
    url_changed_signal   = pyqtSignal(str, object)   # url, tab_ref
    loading_signal       = pyqtSignal(bool, object)  # loading, tab_ref

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        self._page = QWebEnginePage(profile, self)
        self.setPage(self._page)
        self._pinned = False
        self._muted = False
        self._zoom_factor = 1.0
        self._configure_settings()

        self.titleChanged.connect(lambda t: self.title_changed_signal.emit(t, self))
        self.iconChanged.connect(lambda: self.icon_changed_signal.emit(self))
        self.urlChanged.connect(lambda u: self.url_changed_signal.emit(u.toString(), self))
        self.loadStarted.connect(lambda: self.loading_signal.emit(True, self))
        self.loadFinished.connect(lambda _: self.loading_signal.emit(False, self))

    def _configure_settings(self):
        s = self._page.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        s.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

    def navigate(self, url: str):
        self.load(QUrl(url))

    def zoom_in(self):
        self._zoom_factor = min(self._zoom_factor + 0.1, 3.0)
        self.setZoomFactor(self._zoom_factor)

    def zoom_out(self):
        self._zoom_factor = max(self._zoom_factor - 0.1, 0.25)
        self.setZoomFactor(self._zoom_factor)

    def zoom_reset(self):
        self._zoom_factor = 1.0
        self.setZoomFactor(1.0)

    def toggle_mute(self):
        self._muted = not self._muted
        self._page.setAudioMuted(self._muted)

    @property
    def is_pinned(self):
        return self._pinned

    def pin(self, value: bool):
        self._pinned = value


class JOBrowser(QMainWindow):
    """Main browser window."""

    def __init__(self, settings: Settings, session: SessionManager, profile_name: str = "default"):
        super().__init__()
        self._settings = settings
        self._session = session
        self._profile_name = profile_name
        self._incognito = False

        # Managers
        self._theme_mgr    = ThemeManager(settings)
        self._history_mgr  = HistoryManager(profile_name)
        self._bookmarks_mgr = BookmarksManager(profile_name)
        self._downloads_mgr = DownloadsManager(settings)
        self._notes_mgr    = NotesManager(profile_name)
        self._privacy_mgr  = PrivacyManager(settings)

        # WebEngine profile
        self._web_profile = self._privacy_mgr.get_normal_profile(profile_name)
        self._web_profile.downloadRequested.connect(self._downloads_mgr.handle)

        # Command palette (lazy)
        self._palette: CommandPalette | None = None

        self._setup_window()
        self._setup_ui()
        self._apply_theme()
        self._setup_shortcuts()
        self._setup_session_autosave()

        log.info("JOBrowser initialized — profile: %s", profile_name)

    # ─── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("JO Browser")
        self.setMinimumSize(900, 600)
        self.resize(1280, 820)
        # Restore window geometry
        x = self._settings.get("window.x", 100)
        y = self._settings.get("window.y", 100)
        w = self._settings.get("window.width", 1280)
        h = self._settings.get("window.height", 820)
        self.setGeometry(x, y, w, h)
        if self._settings.get("advanced.always_on_top", False):
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

    # ─── UI construction ──────────────────────────────────────────────────────

    def _setup_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ──
        self._toolbar = NavigationToolbar(self._settings)
        self._toolbar.navigate_to.connect(self._navigate_to)
        self._toolbar.go_back.connect(self._go_back)
        self._toolbar.go_forward.connect(self._go_forward)
        self._toolbar.reload_page.connect(self._reload)
        self._toolbar.stop_page.connect(self._stop)
        self._toolbar.go_home.connect(self._go_home)
        self._toolbar.new_tab_requested.connect(self.open_new_tab)
        self._toolbar.toggle_sidebar.connect(self._toggle_sidebar)
        self._toolbar.toggle_menu.connect(self._show_app_menu)
        self._toolbar.bookmark_toggle.connect(self._toggle_bookmark)
        root.addWidget(self._toolbar)

        # ── Bookmark bar ──
        self._bookmarks_bar = self._build_bookmarks_bar()
        root.addWidget(self._bookmarks_bar)
        self._bookmarks_bar.setVisible(self._settings.get("general.show_bookmarks_bar", True))

        # ── Content area (sidebar + tabs) ──
        content_split = QSplitter(Qt.Orientation.Horizontal)
        content_split.setChildrenCollapsible(True)

        # Sidebar
        self._sidebar = SidebarContainer()
        self._setup_sidebar_panels()
        content_split.addWidget(self._sidebar)

        # Tab widget
        self.tab_widget = self._build_tab_widget()
        content_split.addWidget(self.tab_widget)
        content_split.setStretchFactor(1, 1)

        root.addWidget(content_split)

        # ── Status bar ──
        self._status = QStatusBar()
        self.setStatusBar(self._status)

        # ── Menu bar ──
        self._setup_menu_bar()

    def _build_tab_widget(self) -> QTabWidget:
        tw = QTabWidget()
        tw.setTabsClosable(True)
        tw.setMovable(True)
        tw.setDocumentMode(True)
        tw.tabCloseRequested.connect(self.close_tab)
        tw.currentChanged.connect(self._on_tab_changed)
        tw.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tw.tabBar().customContextMenuRequested.connect(self._tab_context_menu)
        return tw

    def _build_bookmarks_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("bookmarks_bar")
        bar.setFixedHeight(32)
        bar.setStyleSheet("""
            QWidget#bookmarks_bar {
                background: #13131f;
                border-bottom: 1px solid #2a2a40;
            }
            QPushButton {
                background: transparent;
                color: #9898b0;
                border: none;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 12px;
            }
            QPushButton:hover { background: #1e1e2e; color: #e8e8f0; }
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 0, 8, 0)
        lay.setSpacing(2)
        for bm in self._bookmarks_mgr.get_bar_bookmarks():
            btn = self._make_bm_btn(bm["title"] or bm["url"][:20], bm["url"])
            lay.addWidget(btn)
        lay.addStretch()
        return bar

    def _make_bm_btn(self, label: str, url: str):
        from PyQt6.QtWidgets import QPushButton
        btn = QPushButton(label[:24])
        btn.setToolTip(url)
        btn.clicked.connect(lambda: self._navigate_to(url))
        return btn

    def _setup_sidebar_panels(self):
        bm_panel  = BookmarksPanel(self._bookmarks_mgr)
        bm_panel.navigate.connect(self._navigate_to)
        hist_panel = HistoryPanel(self._history_mgr)
        hist_panel.navigate.connect(self._navigate_to)
        notes_panel = NotesPanel(self._notes_mgr)
        dl_panel   = DownloadsPanel(self._downloads_mgr)
        ai_panel   = AISidebarWidget(self)
        dev_panel  = DeveloperSidebarWidget(self)

        self._sidebar.register_panel("bookmarks", bm_panel)
        self._sidebar.register_panel("history",   hist_panel)
        self._sidebar.register_panel("notes",     notes_panel)
        self._sidebar.register_panel("downloads", dl_panel)
        self._sidebar.register_panel("ai",        ai_panel)
        self._sidebar.register_panel("dev",       dev_panel)

        self._bm_panel   = bm_panel
        self._hist_panel = hist_panel

    def _setup_menu_bar(self):
        mb = self.menuBar()

        # File
        file_m = mb.addMenu("File")
        file_m.addAction("New Tab",          self.open_new_tab,               QKeySequence("Ctrl+T"))
        file_m.addAction("New Incognito Tab", self.open_incognito_tab,         QKeySequence("Ctrl+Shift+N"))
        file_m.addAction("Open File...",      self._open_file,                 QKeySequence("Ctrl+O"))
        file_m.addAction("Open Folder...",    self._open_folder)
        file_m.addSeparator()
        file_m.addAction("Save Page As...",   self._save_page,                 QKeySequence("Ctrl+S"))
        file_m.addAction("Print...",          self._print_page,                QKeySequence("Ctrl+P"))
        file_m.addSeparator()
        file_m.addAction("Close Tab",         lambda: self.close_tab(self.tab_widget.currentIndex()), QKeySequence("Ctrl+W"))
        file_m.addAction("Quit",              self.close,                      QKeySequence("Ctrl+Q"))

        # Edit
        edit_m = mb.addMenu("Edit")
        edit_m.addAction("Find in Page...",   self._find_in_page,              QKeySequence("Ctrl+F"))
        edit_m.addAction("Command Palette",   self._show_command_palette,      QKeySequence("Ctrl+K"))
        edit_m.addSeparator()
        edit_m.addAction("Settings",          self._open_settings,             QKeySequence("Ctrl+,"))

        # View
        view_m = mb.addMenu("View")
        view_m.addAction("Zoom In",           self._zoom_in,                   QKeySequence("Ctrl++"))
        view_m.addAction("Zoom Out",          self._zoom_out,                  QKeySequence("Ctrl+-"))
        view_m.addAction("Reset Zoom",        self._zoom_reset,                QKeySequence("Ctrl+0"))
        view_m.addSeparator()
        view_m.addAction("Full Screen",       self._toggle_fullscreen,         QKeySequence("F11"))
        view_m.addAction("Toggle Bookmarks Bar", self._toggle_bm_bar)
        view_m.addSeparator()
        view_m.addAction("Reload",            self._reload,                    QKeySequence("F5"))
        view_m.addAction("Hard Reload",       self._hard_reload,               QKeySequence("Ctrl+Shift+R"))
        view_m.addAction("View Source",       self._view_source)

        # Themes submenu
        theme_m = view_m.addMenu("Theme")
        for name in self._theme_mgr.list_presets():
            n = name
            theme_m.addAction(n.title(), lambda checked=False, t=n: self._apply_theme(t))

        # History
        hist_m = mb.addMenu("History")
        hist_m.addAction("History",           lambda: self._toggle_sidebar("history"), QKeySequence("Ctrl+H"))
        hist_m.addAction("Recently Closed",   self._show_recently_closed)
        hist_m.addSeparator()
        hist_m.addAction("Clear History",     self._clear_history)

        # Bookmarks
        bm_m = mb.addMenu("Bookmarks")
        bm_m.addAction("Bookmark This Page", self._toggle_bookmark,           QKeySequence("Ctrl+D"))
        bm_m.addAction("Add to Reading List", self._add_reading_list)
        bm_m.addSeparator()
        bm_m.addAction("Manage Bookmarks",    lambda: self._toggle_sidebar("bookmarks"))

        # Tools
        tools_m = mb.addMenu("Tools")
        tools_m.addAction("Downloads",        lambda: self._toggle_sidebar("downloads"), QKeySequence("Ctrl+J"))
        tools_m.addAction("Notes",            lambda: self._toggle_sidebar("notes"))
        tools_m.addAction("AI Assistant",     lambda: self._toggle_sidebar("ai"))
        tools_m.addSeparator()
        tools_m.addAction("Developer Tools",  lambda: self._toggle_sidebar("dev"))
        tools_m.addAction("Task Manager",     self._show_task_manager)

        # Help
        help_m = mb.addMenu("Help")
        help_m.addAction("About JO Browser",  self._show_about)

    # ─── Shortcuts ────────────────────────────────────────────────────────────

    def _setup_shortcuts(self):
        shortcuts = {
            "Ctrl+T":       self.open_new_tab,
            "Ctrl+W":       lambda: self.close_tab(self.tab_widget.currentIndex()),
            "Ctrl+Shift+T": self._restore_closed_tab,
            "Ctrl+L":       self._focus_url_bar,
            "Ctrl+K":       self._show_command_palette,
            "Ctrl+,":       self._open_settings,
            "F5":           self._reload,
            "Ctrl+R":       self._reload,
            "Ctrl+Shift+R": self._hard_reload,
            "F11":          self._toggle_fullscreen,
            "Ctrl+D":       self._toggle_bookmark,
            "Ctrl+H":       lambda: self._toggle_sidebar("history"),
            "Ctrl+J":       lambda: self._toggle_sidebar("downloads"),
            "Ctrl+F":       self._find_in_page,
            "Ctrl++":       self._zoom_in,
            "Ctrl+=":       self._zoom_in,
            "Ctrl+-":       self._zoom_out,
            "Ctrl+0":       self._zoom_reset,
            "Alt+Left":     self._go_back,
            "Alt+Right":    self._go_forward,
            "Ctrl+1":       lambda: self._switch_to_tab(0),
            "Ctrl+2":       lambda: self._switch_to_tab(1),
            "Ctrl+3":       lambda: self._switch_to_tab(2),
            "Ctrl+4":       lambda: self._switch_to_tab(3),
            "Ctrl+5":       lambda: self._switch_to_tab(4),
            "Ctrl+Tab":     self._next_tab,
            "Ctrl+Shift+Tab": self._prev_tab,
            "Escape":       self._on_escape,
        }
        for seq, fn in shortcuts.items():
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(fn)

    # ─── Tab management ───────────────────────────────────────────────────────

    def open_new_tab(self, url: str = None, pinned: bool = False) -> BrowserTab:
        tab = BrowserTab(self._web_profile)
        tab.title_changed_signal.connect(self._on_title_changed)
        tab.url_changed_signal.connect(self._on_url_changed)
        tab.loading_signal.connect(self._on_loading)

        idx = self.tab_widget.addTab(tab, "New Tab")
        self.tab_widget.setCurrentIndex(idx)

        if pinned:
            tab.pin(True)

        target = url or self._settings.get("general.home_url", JO_NEWTAB)
        if target == JO_NEWTAB or target == "jo://newtab":
            self._load_new_tab_page(tab)
        else:
            tab.navigate(target)

        log.debug("Opened new tab: %s", target)
        return tab

    def open_incognito_tab(self):
        profile = self._privacy_mgr.get_incognito_profile()
        tab = BrowserTab(profile)
        tab.title_changed_signal.connect(self._on_title_changed)
        tab.url_changed_signal.connect(self._on_url_changed)
        tab.loading_signal.connect(self._on_loading)
        idx = self.tab_widget.addTab(tab, "🕵 Incognito")
        self.tab_widget.setCurrentIndex(idx)
        self._load_new_tab_page(tab)

    def close_tab(self, idx: int):
        tab = self.tab_widget.widget(idx)
        if tab:
            url = tab.url().toString()
            title = self.tab_widget.tabText(idx)
            self._session.push_closed(url, title)
        if self.tab_widget.count() == 1:
            # Don't close last tab — open new tab instead
            self.open_new_tab()
        self.tab_widget.removeTab(idx)

    def current_tab(self) -> BrowserTab | None:
        return self.tab_widget.currentWidget()

    def _switch_to_tab(self, idx: int):
        if idx < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(idx)

    def _next_tab(self):
        n = self.tab_widget.count()
        self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex() + 1) % n)

    def _prev_tab(self):
        n = self.tab_widget.count()
        self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex() - 1) % n)

    def _tab_context_menu(self, pos):
        bar = self.tab_widget.tabBar()
        idx = bar.tabAt(pos)
        if idx < 0:
            return
        tab = self.tab_widget.widget(idx)
        menu = QMenu(self)
        menu.addAction("New Tab",   self.open_new_tab)
        menu.addSeparator()
        menu.addAction("Reload",    lambda: tab.reload() if tab else None)
        menu.addAction("Mute",      lambda: tab.toggle_mute() if isinstance(tab, BrowserTab) else None)
        menu.addSeparator()

        pinned = isinstance(tab, BrowserTab) and tab.is_pinned
        menu.addAction("Unpin Tab" if pinned else "Pin Tab",
                       lambda: self._toggle_pin(idx))
        menu.addSeparator()
        menu.addAction("Close Tab",              lambda: self.close_tab(idx))
        menu.addAction("Close Other Tabs",       lambda: self._close_others(idx))
        menu.addAction("Close Tabs to the Right",lambda: self._close_right(idx))
        menu.addAction("Restore Last Closed Tab",self._restore_closed_tab)
        menu.exec(bar.mapToGlobal(pos))

    def _toggle_pin(self, idx: int):
        tab = self.tab_widget.widget(idx)
        if isinstance(tab, BrowserTab):
            tab.pin(not tab.is_pinned)

    def _close_others(self, keep_idx: int):
        for i in reversed(range(self.tab_widget.count())):
            if i != keep_idx:
                self.tab_widget.removeTab(i)

    def _close_right(self, from_idx: int):
        for i in reversed(range(from_idx + 1, self.tab_widget.count())):
            self.tab_widget.removeTab(i)

    def _restore_closed_tab(self):
        data = self._session.pop_closed()
        if data:
            self.open_new_tab(url=data["url"])

    # ─── Navigation ───────────────────────────────────────────────────────────

    def _navigate_to(self, url: str):
        url = self._privacy_mgr.force_https(url)
        if self._privacy_mgr.phishing_warning(url):
            ans = QMessageBox.warning(
                self, "Suspicious Page",
                f"This URL may be a phishing attempt:\n{url}\n\nContinue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ans != QMessageBox.StandardButton.Yes:
                return
        tab = self.current_tab()
        if not tab:
            tab = self.open_new_tab(url=url)
        else:
            if url in (JO_NEWTAB, "jo://newtab"):
                self._load_new_tab_page(tab)
            else:
                tab.navigate(url)

    def open_url(self, url: str):
        """Public API used by developer panel and external callers."""
        self._navigate_to(url)

    def _load_new_tab_page(self, tab: BrowserTab):
        recent = [dict(r) for r in self._history_mgr.recent(6)]
        html = get_new_tab_html(recent)
        tab.setHtml(html, QUrl("jo://newtab"))

    def _go_back(self):
        tab = self.current_tab()
        if tab:
            tab.back()

    def _go_forward(self):
        tab = self.current_tab()
        if tab:
            tab.forward()

    def _reload(self):
        tab = self.current_tab()
        if tab:
            tab.reload()

    def _hard_reload(self):
        tab = self.current_tab()
        if tab:
            tab.page().triggerAction(QWebEnginePage.WebAction.ReloadAndBypassCache)

    def _stop(self):
        tab = self.current_tab()
        if tab:
            tab.stop()

    def _go_home(self):
        home = self._settings.get("general.home_url", JO_NEWTAB)
        self._navigate_to(home)

    # ─── Tab event handlers ───────────────────────────────────────────────────

    def _on_tab_changed(self, idx: int):
        tab = self.tab_widget.widget(idx)
        if not isinstance(tab, BrowserTab):
            return
        url = tab.url().toString()
        self._toolbar.update_url(url)
        self._toolbar.set_nav_state(tab.history().canGoBack(), tab.history().canGoForward())
        bookmarked = self._bookmarks_mgr.exists(url)
        self._toolbar.set_bookmark_state(bookmarked)
        suggestions = self._history_mgr.suggestions(url[:10])
        self._toolbar.update_suggestions(suggestions)

    def _on_title_changed(self, title: str, tab):
        idx = self.tab_widget.indexOf(tab)
        if idx >= 0:
            display = title[:28] + ("…" if len(title) > 28 else "")
            self.tab_widget.setTabText(idx, display)
            if tab == self.current_tab():
                self.setWindowTitle(f"{title} — JO Browser")

    def _on_url_changed(self, url: str, tab):
        if tab != self.current_tab():
            return
        self._toolbar.update_url(url)
        self._toolbar.set_nav_state(tab.history().canGoBack(), tab.history().canGoForward())
        # Record history (skip internal pages)
        if not url.startswith("jo://"):
            title = tab.title() or ""
            self._history_mgr.add(url, title)
            self._toolbar.update_suggestions(self._history_mgr.suggestions(url[:20]))
        # Update bookmark star
        self._toolbar.set_bookmark_state(self._bookmarks_mgr.exists(url))
        # Status bar
        self._status.showMessage(url, 3000)

    def _on_loading(self, loading: bool, tab):
        if tab == self.current_tab():
            self._toolbar.set_loading(loading)

    # ─── Bookmarks ────────────────────────────────────────────────────────────

    def _toggle_bookmark(self):
        tab = self.current_tab()
        if not tab:
            return
        url = tab.url().toString()
        if url.startswith("jo://"):
            return
        if self._bookmarks_mgr.exists(url):
            # Remove bookmark
            rows = self._bookmarks_mgr.search(url, limit=1)
            if rows:
                self._bookmarks_mgr.delete(rows[0]["id"])
            self._toolbar.set_bookmark_state(False)
            self._status.showMessage("Bookmark removed", 2000)
        else:
            title = tab.title() or url
            self._bookmarks_mgr.add(url, title)
            self._toolbar.set_bookmark_state(True)
            self._status.showMessage("Bookmarked!", 2000)
        self._bm_panel.refresh()
        self._rebuild_bookmarks_bar()

    def _add_reading_list(self):
        tab = self.current_tab()
        if tab:
            self._bookmarks_mgr.add_to_reading_list(tab.url().toString(), tab.title())
            self._status.showMessage("Added to reading list", 2000)

    def _rebuild_bookmarks_bar(self):
        lay = self._bookmarks_bar.layout()
        while lay.count() > 0:
            item = lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for bm in self._bookmarks_mgr.get_bar_bookmarks():
            btn = self._make_bm_btn(bm["title"] or bm["url"][:20], bm["url"])
            lay.addWidget(btn)
        lay.addStretch()

    # ─── Sidebar ──────────────────────────────────────────────────────────────

    def _toggle_sidebar(self, name: str):
        self._sidebar.toggle(name)

    # ─── App menu ─────────────────────────────────────────────────────────────

    def _show_app_menu(self):
        menu = QMenu(self)
        menu.addAction("New Tab",               self.open_new_tab)
        menu.addAction("New Incognito Tab",      self.open_incognito_tab)
        menu.addSeparator()
        menu.addAction("Settings",              self._open_settings)
        menu.addAction("Downloads",             lambda: self._toggle_sidebar("downloads"))
        menu.addAction("History",               lambda: self._toggle_sidebar("history"))
        menu.addAction("Bookmarks",             lambda: self._toggle_sidebar("bookmarks"))
        menu.addAction("Notes",                 lambda: self._toggle_sidebar("notes"))
        menu.addSeparator()
        theme_m = menu.addMenu("Theme")
        for name in self._theme_mgr.list_presets():
            n = name
            theme_m.addAction(n.title(), lambda checked=False, t=n: self._apply_theme(t))
        menu.addSeparator()
        menu.addAction("About JO Browser",      self._show_about)
        menu.addAction("Quit",                  self.close)
        # Show below toolbar
        btn = self._toolbar.findChild(type(self._toolbar.btn_back))
        pos = self._toolbar.mapToGlobal(self._toolbar.rect().bottomRight())
        menu.exec(pos)

    # ─── Command Palette ──────────────────────────────────────────────────────

    def _show_command_palette(self):
        if not self._palette:
            self._palette = CommandPalette(self._history_mgr, self._bookmarks_mgr, self)
            self._palette.command_selected.connect(self._handle_command)
            self._palette.navigate_to.connect(self._navigate_to)
        self._palette.show_centered(self.geometry())

    def _handle_command(self, cmd: str):
        mapping = {
            "new_tab":       self.open_new_tab,
            "incognito":     self.open_incognito_tab,
            "settings":      self._open_settings,
            "reload":        self._reload,
            "hard_reload":   self._hard_reload,
            "zoom_in":       self._zoom_in,
            "zoom_out":      self._zoom_out,
            "zoom_reset":    self._zoom_reset,
            "back":          self._go_back,
            "forward":       self._go_forward,
            "find":          self._find_in_page,
            "view_source":   self._view_source,
            "clear_history": self._clear_history,
            "clear_cache":   self._clear_cache,
            "close_tab":     lambda: self.close_tab(self.tab_widget.currentIndex()),
            "restore_tab":   self._restore_closed_tab,
            "fullscreen":    self._toggle_fullscreen,
            "focus_url":     self._focus_url_bar,
            "bookmark":      self._toggle_bookmark,
            "print":         self._print_page,
            "bookmarks":     lambda: self._toggle_sidebar("bookmarks"),
            "history":       lambda: self._toggle_sidebar("history"),
            "notes":         lambda: self._toggle_sidebar("notes"),
            "ai":            lambda: self._toggle_sidebar("ai"),
            "dev":           lambda: self._toggle_sidebar("dev"),
            "downloads":     lambda: self._toggle_sidebar("downloads"),
            "theme_dark":    lambda: self._apply_theme("dark"),
            "theme_light":   lambda: self._apply_theme("light"),
            "theme_neon":    lambda: self._apply_theme("neon"),
            "theme_work":    lambda: self._apply_theme("work"),
        }
        fn = mapping.get(cmd)
        if fn:
            fn()
        else:
            log.warning("Unknown command: %s", cmd)

    # ─── View actions ─────────────────────────────────────────────────────────

    def _zoom_in(self):
        tab = self.current_tab()
        if isinstance(tab, BrowserTab):
            tab.zoom_in()

    def _zoom_out(self):
        tab = self.current_tab()
        if isinstance(tab, BrowserTab):
            tab.zoom_out()

    def _zoom_reset(self):
        tab = self.current_tab()
        if isinstance(tab, BrowserTab):
            tab.zoom_reset()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _find_in_page(self):
        text, ok = QInputDialog.getText(self, "Find in Page", "Search:")
        if ok and text:
            tab = self.current_tab()
            if tab:
                tab.findText(text)

    def _view_source(self):
        tab = self.current_tab()
        if tab:
            self.open_new_tab(url=f"view-source:{tab.url().toString()}")

    def _toggle_bm_bar(self):
        visible = not self._bookmarks_bar.isVisible()
        self._bookmarks_bar.setVisible(visible)
        self._settings.set("general.show_bookmarks_bar", visible)

    def _focus_url_bar(self):
        self._toolbar.url_bar.setFocus()
        self._toolbar.url_bar.selectAll()

    def _on_escape(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self._stop()

    # ─── File actions ─────────────────────────────────────────────────────────

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "",
            "Web Files (*.html *.htm *.xml *.svg);;All Files (*)"
        )
        if path:
            self._navigate_to(f"file:///{path}")

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Project Folder")
        if folder:
            index_path = Path(folder) / "index.html"
            url = f"file:///{index_path}" if index_path.exists() else f"file:///{folder}"
            self._navigate_to(url)

    def _save_page(self):
        tab = self.current_tab()
        if not tab:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Page", "", "HTML Files (*.html);;All Files (*)"
        )
        if path:
            tab.page().save(path)

    def _print_page(self):
        tab = self.current_tab()
        if tab:
            tab.page().printToPdf(str(Path.home() / "Desktop" / "page.pdf"))
            self._status.showMessage("Saved PDF to Desktop", 3000)

    # ─── History / Privacy ────────────────────────────────────────────────────

    def _show_recently_closed(self):
        closed = self._session.closed_tabs()
        if not closed:
            QMessageBox.information(self, "Recently Closed", "No recently closed tabs.")
            return
        items = [f"{t['title'] or t['url']}" for t in closed]
        item, ok = QInputDialog.getItem(self, "Recently Closed Tabs", "Select tab to reopen:", items, 0, False)
        if ok:
            idx = items.index(item)
            self.open_new_tab(url=closed[idx]["url"])

    def _clear_history(self):
        ans = QMessageBox.question(self, "Clear History", "Clear all browsing history?")
        if ans == QMessageBox.StandardButton.Yes:
            self._history_mgr.clear()
            self._status.showMessage("History cleared", 2000)
            self._hist_panel.refresh()

    def _clear_cache(self):
        self._privacy_mgr.clear_cache(self._web_profile)
        self._status.showMessage("Cache cleared", 2000)

    def _show_task_manager(self):
        QMessageBox.information(
            self, "Task Manager",
            "Process-level tab isolation and task manager coming in a future version."
        )

    # ─── Theme ────────────────────────────────────────────────────────────────

    def _apply_theme(self, name: str = None):
        if name is None:
            name = self._settings.get("appearance.theme", "dark")
        else:
            self._settings.set("appearance.theme", name)
        stylesheet = self._theme_mgr.stylesheet(name)
        QApplication.instance().setStyleSheet(stylesheet)
        log.info("Applied theme: %s", name)

    # ─── Settings ─────────────────────────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self._settings, self._theme_mgr, self)
        dlg.theme_changed.connect(self._apply_theme)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec()

    def _on_settings_saved(self):
        self._apply_theme()
        self._bookmarks_bar.setVisible(self._settings.get("general.show_bookmarks_bar", True))
        if self._settings.get("advanced.always_on_top", False):
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()

    # ─── About ────────────────────────────────────────────────────────────────

    def _show_about(self):
        QMessageBox.about(
            self, "About JO Browser",
            "<h2 style='color:#6C63FF;'>JO Browser</h2>"
            "<p><b>Version:</b> 1.0.0</p>"
            "<p>A premium Python desktop browser built with PyQt6 and QtWebEngine.</p>"
            "<p>Designed to be fast, elegant, and highly customizable.</p>"
            "<p style='color:#666;'>© 2025 JO Browser</p>"
        )

    # ─── Session autosave ─────────────────────────────────────────────────────

    def _setup_session_autosave(self):
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(30_000)   # every 30 seconds
        self._autosave_timer.timeout.connect(lambda: self._session.save(self))
        self._autosave_timer.start()

    # ─── Window events ────────────────────────────────────────────────────────

    def closeEvent(self, event):
        # Save session & window geometry
        self._session.save(self)
        geo = self.geometry()
        self._settings.set("window.x",      geo.x())
        self._settings.set("window.y",      geo.y())
        self._settings.set("window.width",  geo.width())
        self._settings.set("window.height", geo.height())
        log.info("Browser closing — session saved")
        event.accept()
