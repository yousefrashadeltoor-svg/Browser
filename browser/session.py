"""
JO Browser — Session Manager
Saves / restores open tabs so the browser can pick up where it left off.
Data stored in data/profiles/<profile>/session.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from browser.utils import data_path

log = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, profile: str = "default"):
        self._path = data_path("profiles", profile, "session.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Closed-tabs stack (for "reopen closed tab")
        self._closed: list[dict] = []

    # ---------- Save ----------

    def save(self, browser_window):
        """Call with the main JOBrowser window to persist its open tabs."""
        tabs = []
        tw = browser_window.tab_widget
        for i in range(tw.count()):
            tab = tw.widget(i)
            if tab and hasattr(tab, "url"):
                url = tab.url().toString()
                title = tw.tabText(i)
                tabs.append({"url": url, "title": title, "pinned": getattr(tab, "_pinned", False)})
        data = {
            "saved_at": datetime.now().isoformat(),
            "active_index": tw.currentIndex(),
            "tabs": tabs,
        }
        try:
            self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            log.info("Session saved: %d tabs", len(tabs))
        except Exception as e:
            log.error("Could not save session: %s", e)

    # ---------- Restore ----------

    def restore(self, browser_window):
        """Re-open tabs from the last saved session."""
        if not self._path.exists():
            browser_window.open_new_tab()
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            tabs = data.get("tabs", [])
            active = data.get("active_index", 0)
            if not tabs:
                browser_window.open_new_tab()
                return
            for tab_data in tabs:
                browser_window.open_new_tab(url=tab_data.get("url", "jo://newtab"),
                                             pinned=tab_data.get("pinned", False))
            browser_window.tab_widget.setCurrentIndex(min(active, browser_window.tab_widget.count() - 1))
            log.info("Session restored: %d tabs", len(tabs))
        except Exception as e:
            log.error("Could not restore session: %s", e)
            browser_window.open_new_tab()

    # ---------- Crash recovery ----------

    def has_recovery(self) -> bool:
        return self._path.exists()

    def tab_count(self) -> int:
        if not self._path.exists():
            return 0
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return len(data.get("tabs", []))
        except Exception:
            return 0

    # ---------- Closed-tab stack ----------

    def push_closed(self, url: str, title: str):
        self._closed.append({"url": url, "title": title})
        if len(self._closed) > 50:
            self._closed.pop(0)

    def pop_closed(self) -> dict | None:
        return self._closed.pop() if self._closed else None

    def closed_tabs(self) -> list[dict]:
        return list(reversed(self._closed))
