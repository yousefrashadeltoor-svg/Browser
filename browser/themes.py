"""
JO Browser — Theme Engine
Generates Qt stylesheets from a theme descriptor dict.
Themes: dark (default), light, neon, soft, minimal, gaming, work, custom.
"""

import json
import logging
from pathlib import Path
from typing import Any

from browser.utils import data_path

log = logging.getLogger(__name__)

# Built-in theme presets
PRESETS: dict[str, dict[str, str]] = {
    "dark": {
        "name": "Dark",
        "bg": "#0d0d1a",
        "bg2": "#13131f",
        "bg3": "#1a1a2e",
        "surface": "#1e1e2e",
        "surface2": "#252535",
        "border": "#2a2a40",
        "accent": "#6C63FF",
        "accent_hover": "#7c74ff",
        "text": "#e8e8f0",
        "text2": "#9898b0",
        "text3": "#6060778",
        "error": "#ff5555",
        "success": "#50fa7b",
        "warn": "#ffb86c",
        "tab_active": "#1e1e2e",
        "tab_inactive": "#13131f",
        "toolbar_bg": "#0d0d1a",
    },
    "light": {
        "name": "Light",
        "bg": "#f4f4f8",
        "bg2": "#ececf2",
        "bg3": "#e4e4ee",
        "surface": "#ffffff",
        "surface2": "#f0f0f8",
        "border": "#d0d0e0",
        "accent": "#5851db",
        "accent_hover": "#6862eb",
        "text": "#1a1a2e",
        "text2": "#4a4a6a",
        "text3": "#8080a0",
        "error": "#e03030",
        "success": "#22aa55",
        "warn": "#dd8800",
        "tab_active": "#ffffff",
        "tab_inactive": "#e8e8f0",
        "toolbar_bg": "#f4f4f8",
    },
    "neon": {
        "name": "Neon",
        "bg": "#050510",
        "bg2": "#080818",
        "bg3": "#0a0a20",
        "surface": "#0d0d22",
        "surface2": "#111130",
        "border": "#1a1a44",
        "accent": "#00ffcc",
        "accent_hover": "#33ffdd",
        "text": "#e0ffe8",
        "text2": "#80ccaa",
        "text3": "#4488664",
        "error": "#ff2266",
        "success": "#00ff88",
        "warn": "#ffdd00",
        "tab_active": "#0d0d22",
        "tab_inactive": "#080818",
        "toolbar_bg": "#050510",
    },
    "soft": {
        "name": "Soft",
        "bg": "#faf7f4",
        "bg2": "#f2ede8",
        "bg3": "#ece4dc",
        "surface": "#ffffff",
        "surface2": "#faf5f0",
        "border": "#e0d4c8",
        "accent": "#d4845a",
        "accent_hover": "#e0906a",
        "text": "#3a2e28",
        "text2": "#6a5a50",
        "text3": "#9a8a80",
        "error": "#cc4444",
        "success": "#559944",
        "warn": "#cc8800",
        "tab_active": "#ffffff",
        "tab_inactive": "#f0e8e0",
        "toolbar_bg": "#faf7f4",
    },
    "minimal": {
        "name": "Minimal",
        "bg": "#111111",
        "bg2": "#181818",
        "bg3": "#202020",
        "surface": "#1c1c1c",
        "surface2": "#242424",
        "border": "#333333",
        "accent": "#ffffff",
        "accent_hover": "#cccccc",
        "text": "#f0f0f0",
        "text2": "#aaaaaa",
        "text3": "#666666",
        "error": "#ff4444",
        "success": "#44ff88",
        "warn": "#ffcc00",
        "tab_active": "#1c1c1c",
        "tab_inactive": "#181818",
        "toolbar_bg": "#111111",
    },
    "gaming": {
        "name": "Gaming",
        "bg": "#080e14",
        "bg2": "#0c1420",
        "bg3": "#101c2c",
        "surface": "#0e1a28",
        "surface2": "#142030",
        "border": "#1e3040",
        "accent": "#00ccff",
        "accent_hover": "#33ddff",
        "text": "#d0eeff",
        "text2": "#7aafcc",
        "text3": "#448899",
        "error": "#ff3344",
        "success": "#00ff88",
        "warn": "#ffaa00",
        "tab_active": "#0e1a28",
        "tab_inactive": "#0c1420",
        "toolbar_bg": "#080e14",
    },
    "work": {
        "name": "Work",
        "bg": "#1e2028",
        "bg2": "#252830",
        "bg3": "#2c3040",
        "surface": "#272b35",
        "surface2": "#2e3240",
        "border": "#383c4a",
        "accent": "#4a9eff",
        "accent_hover": "#60aaff",
        "text": "#dde4f0",
        "text2": "#8899bb",
        "text3": "#556688",
        "error": "#ff6666",
        "success": "#66dd99",
        "warn": "#ffcc66",
        "tab_active": "#272b35",
        "tab_inactive": "#252830",
        "toolbar_bg": "#1e2028",
    },
}


def build_stylesheet(t: dict[str, str]) -> str:
    """Return a complete Qt stylesheet for the given theme descriptor."""
    return f"""
/* ===== JO Browser Global Stylesheet ===== */

QMainWindow, QDialog, QWidget {{
    background: {t['bg']};
    color: {t['text']};
    font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
    border: none;
}}

/* --- Toolbar / Navigation bar --- */
#toolbar {{
    background: {t['toolbar_bg']};
    border-bottom: 1px solid {t['border']};
    padding: 6px 8px;
    min-height: 48px;
}}

/* --- URL bar --- */
#urlbar {{
    background: {t['surface']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 24px;
    padding: 6px 16px;
    font-size: 14px;
    selection-background-color: {t['accent']};
}}
#urlbar:focus {{
    border-color: {t['accent']};
    background: {t['surface2']};
}}

/* --- Tab bar --- */
QTabBar {{
    background: {t['bg2']};
    border: none;
}}
QTabBar::tab {{
    background: {t['tab_inactive']};
    color: {t['text2']};
    border: none;
    border-radius: 8px 8px 0 0;
    padding: 8px 16px;
    margin-right: 2px;
    min-width: 120px;
    max-width: 220px;
}}
QTabBar::tab:selected {{
    background: {t['tab_active']};
    color: {t['text']};
}}
QTabBar::tab:hover:!selected {{
    background: {t['surface2']};
    color: {t['text']};
}}
QTabBar::close-button {{
    image: none;
    subcontrol-position: right;
}}

/* --- Buttons --- */
QPushButton {{
    background: {t['surface']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
}}
QPushButton:hover {{
    background: {t['surface2']};
    border-color: {t['accent']};
}}
QPushButton:pressed {{
    background: {t['bg3']};
}}
QPushButton#accent {{
    background: {t['accent']};
    color: #ffffff;
    border: none;
}}
QPushButton#accent:hover {{
    background: {t['accent_hover']};
}}
QPushButton#icon_btn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 6px;
    color: {t['text2']};
}}
QPushButton#icon_btn:hover {{
    background: {t['surface']};
    color: {t['text']};
}}

/* --- Sidebar / Panels --- */
#sidebar {{
    background: {t['bg2']};
    border-right: 1px solid {t['border']};
    min-width: 280px;
    max-width: 380px;
}}
#panel {{
    background: {t['surface']};
    border-radius: 12px;
    padding: 12px;
}}

/* --- Lists --- */
QListWidget, QTreeWidget, QTableWidget {{
    background: {t['surface']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    alternate-background-color: {t['surface2']};
    outline: none;
}}
QListWidget::item, QTreeWidget::item {{
    padding: 8px 12px;
    border-radius: 6px;
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background: {t['accent']};
    color: #ffffff;
}}
QListWidget::item:hover, QTreeWidget::item:hover {{
    background: {t['surface2']};
}}

/* --- Scrollbars --- */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {t['border']};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t['accent']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {t['border']};
    border-radius: 3px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {t['accent']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* --- Inputs --- */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {t['surface']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 10px;
    selection-background-color: {t['accent']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {t['accent']};
}}

/* --- ComboBox --- */
QComboBox {{
    background: {t['surface']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 10px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {t['surface']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    selection-background-color: {t['accent']};
}}

/* --- Checkboxes & Radio --- */
QCheckBox, QRadioButton {{
    color: {t['text']};
    spacing: 8px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {t['border']};
    border-radius: 4px;
    background: {t['surface']};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {t['accent']};
    border-color: {t['accent']};
}}

/* --- Sliders --- */
QSlider::groove:horizontal {{
    background: {t['border']};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {t['accent']};
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}}
QSlider::sub-page:horizontal {{
    background: {t['accent']};
    border-radius: 2px;
}}

/* --- Menus --- */
QMenu {{
    background: {t['surface']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 10px;
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 24px 8px 16px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: {t['accent']};
    color: #ffffff;
}}
QMenu::separator {{
    height: 1px;
    background: {t['border']};
    margin: 4px 8px;
}}

/* --- Status bar --- */
QStatusBar {{
    background: {t['bg2']};
    color: {t['text2']};
    border-top: 1px solid {t['border']};
    font-size: 12px;
    padding: 2px 8px;
}}

/* --- Tooltip --- */
QToolTip {{
    background: {t['surface2']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* --- Progress bar --- */
QProgressBar {{
    background: {t['surface']};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {t['accent']};
    border-radius: 4px;
}}

/* --- Splitter --- */
QSplitter::handle {{
    background: {t['border']};
    width: 2px;
    height: 2px;
}}

/* --- Group box --- */
QGroupBox {{
    border: 1px solid {t['border']};
    border-radius: 10px;
    margin-top: 16px;
    padding: 12px;
    color: {t['text2']};
    font-size: 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {t['text2']};
}}
"""


class ThemeManager:
    """Load, save, and apply themes."""

    def __init__(self, settings):
        self._settings = settings
        self._custom_dir = data_path("themes")
        self._current: dict[str, str] = {}

    def get_preset(self, name: str) -> dict[str, str]:
        return PRESETS.get(name, PRESETS["dark"])

    def list_presets(self) -> list[str]:
        return list(PRESETS.keys())

    def list_custom(self) -> list[str]:
        return [p.stem for p in self._custom_dir.glob("*.json")]

    def load(self, name: str) -> dict[str, str]:
        if name in PRESETS:
            self._current = dict(PRESETS[name])
            return self._current
        custom_path = self._custom_dir / f"{name}.json"
        if custom_path.exists():
            try:
                self._current = json.loads(custom_path.read_text(encoding="utf-8"))
                return self._current
            except Exception as e:
                log.warning("Could not load custom theme %s: %s", name, e)
        return dict(PRESETS["dark"])

    def save_custom(self, name: str, theme: dict[str, str]):
        path = self._custom_dir / f"{name}.json"
        path.write_text(json.dumps(theme, indent=2), encoding="utf-8")
        log.info("Saved custom theme: %s", name)

    def delete_custom(self, name: str):
        path = self._custom_dir / f"{name}.json"
        if path.exists():
            path.unlink()

    def export_theme(self, name: str, dest: str):
        theme = self.load(name)
        Path(dest).write_text(json.dumps(theme, indent=2), encoding="utf-8")

    def import_theme(self, path: str) -> str:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        name = data.get("name", Path(path).stem)
        self.save_custom(name, data)
        return name

    def stylesheet(self, name: str = None) -> str:
        name = name or self._settings.get("appearance.theme", "dark")
        theme = self.load(name)
        return build_stylesheet(theme)

    @property
    def current(self) -> dict[str, str]:
        return self._current
