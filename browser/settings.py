"""
JO Browser — Settings
Persists all user preferences to data/settings.json.
Access via settings.get(key, default) / settings.set(key, value).
Keys use dot-notation: "appearance.theme", "startup.restore_session", etc.
"""

import json
import logging
from pathlib import Path
from typing import Any

from browser.utils import data_path

log = logging.getLogger(__name__)

DEFAULTS: dict[str, Any] = {
    # General
    "general.home_url": "jo://newtab",
    "general.search_engine": "https://www.google.com/search?q={}",
    "general.search_engine_name": "Google",
    "general.show_bookmarks_bar": True,
    "general.smooth_scrolling": True,
    "general.hardware_acceleration": True,
    # Startup
    "startup.restore_session": True,
    "startup.show_splash": True,
    "startup.startup_page": "new_tab",  # new_tab | home | last
    # Appearance
    "appearance.theme": "dark",  # dark | light | custom
    "appearance.accent_color": "#6C63FF",
    "appearance.font_family": "Inter",
    "appearance.font_size": 14,
    "appearance.toolbar_transparent": False,
    "appearance.compact_mode": False,
    "appearance.tab_style": "rounded",  # rounded | flat | pill
    "appearance.background_type": "gradient",  # gradient | image | solid
    "appearance.background_gradient": ["#0f0f1a", "#1a1a2e"],
    "appearance.background_image": "",
    "appearance.background_blur": 0,
    "appearance.animations": True,
    # Tabs
    "tabs.pin_on_startup": [],
    "tabs.show_preview": True,
    "tabs.max_tab_width": 220,
    "tabs.close_confirms": False,
    # Privacy
    "privacy.incognito_on_start": False,
    "privacy.do_not_track": True,
    "privacy.block_third_party_cookies": False,
    "privacy.safe_browsing": True,
    "privacy.https_only": False,
    # Downloads
    "downloads.default_path": str(Path.home() / "Downloads"),
    "downloads.ask_every_time": False,
    "downloads.open_after": False,
    # Developer
    "developer.devtools_enabled": True,
    "developer.show_console": False,
    # Advanced
    "advanced.cache_size_mb": 256,
    "advanced.low_resource_mode": False,
    "advanced.always_on_top": False,
}


class Settings:
    _path: Path
    _data: dict[str, Any]

    def __init__(self, profile: str = "default"):
        self._path = data_path("profiles", profile, "settings.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data = {}
        self._load()

    # ---------- public API ----------

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._data:
            return self._data[key]
        if key in DEFAULTS:
            return DEFAULTS[key]
        return default

    def set(self, key: str, value: Any):
        self._data[key] = value
        self._save()

    def all(self) -> dict[str, Any]:
        merged = {**DEFAULTS, **self._data}
        return merged

    def reset(self, key: str = None):
        if key:
            self._data.pop(key, None)
        else:
            self._data = {}
        self._save()

    # ---------- persistence ----------

    def _load(self):
        try:
            if self._path.exists():
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning("Could not load settings: %s", e)
            self._data = {}

    def _save(self):
        try:
            self._path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            log.error("Could not save settings: %s", e)
