"""
JO Browser — Main Entry Point
A premium Python desktop browser built with PyQt6 + QtWebEngine.
Package with: pyinstaller build.spec
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from browser.utils import setup_logging, ensure_data_dirs
from browser.settings import Settings
from browser.session import SessionManager


def main():
    setup_logging()
    ensure_data_dirs()

    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("JO Browser")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("JO")
    app.setOrganizationDomain("jobrowser.app")

    icon_path = ROOT / "assets" / "icons" / "jo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    settings = Settings()

    # ── Splash screen ────────────────────────────────────────────────────────
    splash = None
    if settings.get("startup.show_splash", True):
        from browser.splash import show_splash
        splash = show_splash()
        app.processEvents()

    # ── Main window ──────────────────────────────────────────────────────────
    session = SessionManager()

    from browser.core import JOBrowser
    window = JOBrowser(settings=settings, session=session)

    def _launch():
        if splash:
            splash.finish(window)
        window.show()
        # Restore previous session if enabled
        if settings.get("startup.restore_session", True):
            session.restore(window)
        else:
            window.open_new_tab()

    if splash:
        # Show splash for 1.8 seconds before the window appears
        QTimer.singleShot(1800, _launch)
    else:
        _launch()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
