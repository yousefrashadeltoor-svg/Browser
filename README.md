# JO Browser

A premium Python desktop browser built with **PyQt6 + QtWebEngine**.  
Fast, elegant, highly customizable — more feature-rich than most default browsers.

---

## ✨ Features

| Category | Features |
|---|---|
| **Core** | Multi-tab browsing, back/forward/reload, smart URL bar / omnibox, local HTML + folder support |
| **Tabs** | Unlimited tabs, pin, mute, drag & reorder, close others/right, restore closed, incognito |
| **Interface** | Dark, Light, Neon, Soft, Minimal, Gaming, Work themes + custom theme editor |
| **Customization** | Accent color, font, tab style, compact/spacious mode, bookmarks bar, background |
| **Productivity** | Bookmarks + folders, reading list, history, quick notes, command palette (Ctrl+K) |
| **Downloads** | Download manager with pause/resume/cancel, progress, speed, file reveal |
| **Privacy** | Incognito tabs, Do Not Track, HTTPS-only mode, cookie control, phishing warnings |
| **Developer** | Open local projects/HTML, localhost quick-connect, view source, JS console, DevTools hook |
| **AI / Assistant** | Plugin-ready sidebar — connect Gemini, OpenAI, or any provider via `ai_registry.register()` |
| **Keyboard** | 30+ shortcuts, command palette for everything |
| **Settings** | 13-section settings center (General, Appearance, Privacy, Downloads, Developer, …) |
| **Session** | Auto-save & restore session every 30 s, crash recovery, recently closed tabs |
| **Profiles** | Multi-profile architecture (independent settings, bookmarks, history per profile) |

---

## 🚀 Quick Start (Windows)

```batch
# 1. Install (run once)
install.bat

# 2. Launch
run.bat
```

Or manually:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
python main.py
```

---

## 📦 Package to .exe (Windows)

```bash
pip install pyinstaller
pyinstaller build.spec
# Output: dist/JOBrowser.exe
```

Or one-liner:

```bash
pyinstaller --onefile --windowed --icon=assets/icons/jo.ico main.py
```

Compatible with: **Windows 7 / 8 / 8.1 / 10 / 11** (32-bit and 64-bit via Python packaging).

---

## 📁 Project Structure

```
jo_browser/
├── main.py                   # Entry point
├── requirements.txt          # Python dependencies
├── build.spec                # PyInstaller build config
├── install.bat               # Windows one-click setup
├── run.bat                   # Windows one-click launch
│
├── browser/                  # Core logic modules
│   ├── core.py               # Main window (JOBrowser)
│   ├── settings.py           # Settings manager (JSON persistence)
│   ├── themes.py             # Theme engine + stylesheet builder
│   ├── history.py            # History manager (SQLite)
│   ├── bookmarks.py          # Bookmarks manager (SQLite, folders, reading list)
│   ├── downloads.py          # Downloads manager (PyQt6 download API)
│   ├── session.py            # Session save/restore + closed-tab stack
│   ├── notes.py              # Notes manager (SQLite)
│   ├── privacy.py            # Privacy + incognito + phishing check
│   ├── ai_sidebar.py         # AI assistant sidebar (plugin-ready)
│   ├── developer.py          # Developer sidebar + JS console
│   ├── splash.py             # Animated splash screen (pure Qt)
│   └── utils.py              # Logging, paths, data-dir bootstrap
│
├── ui/                       # UI widgets
│   ├── toolbar.py            # Navigation toolbar + smart URL bar
│   ├── sidebar.py            # Animated sidebar container
│   ├── panels.py             # BookmarksPanel, HistoryPanel, NotesPanel, DownloadsPanel
│   ├── new_tab_page.py       # Rich HTML new-tab dashboard
│   ├── command_palette.py    # Ctrl+K command palette
│   └── settings_dialog.py   # Full 13-section settings dialog
│
├── assets/
│   ├── icons/                # App icons (.png, .ico)
│   └── themes/               # Exported custom theme JSON files
│
└── data/                     # Auto-created at runtime
    ├── profiles/
    │   └── default/
    │       ├── settings.json
    │       ├── session.json
    │       ├── history.db
    │       ├── bookmarks.db
    │       └── notes.db
    └── downloads.db
```

---

## ⌨️ Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New Tab | `Ctrl+T` |
| Close Tab | `Ctrl+W` |
| Restore Closed Tab | `Ctrl+Shift+T` |
| Focus URL Bar | `Ctrl+L` |
| Command Palette | `Ctrl+K` |
| Settings | `Ctrl+,` |
| Reload | `F5` |
| Hard Reload | `Ctrl+Shift+R` |
| Full Screen | `F11` |
| Bookmark Page | `Ctrl+D` |
| History | `Ctrl+H` |
| Downloads | `Ctrl+J` |
| Find in Page | `Ctrl+F` |
| Zoom In / Out / Reset | `Ctrl++` / `Ctrl+-` / `Ctrl+0` |
| Back / Forward | `Alt+Left` / `Alt+Right` |
| Switch Tab | `Ctrl+1…5` |
| Next / Prev Tab | `Ctrl+Tab` / `Ctrl+Shift+Tab` |
| Incognito Tab | `Ctrl+Shift+N` |

---

## 🤖 AI Integration (Plugin-ready)

Connect any LLM provider to the AI sidebar in 3 lines:

```python
from browser.ai_sidebar import ai_registry

def my_gemini(task: str, context: str) -> str:
    # call your Gemini / OpenAI / local LLM here
    return "AI response..."

ai_registry.register("gemini", my_gemini)
```

Features ready to wire up: page summarization, translation, key points, ask-anything, voice input, text-to-speech.

---

## 🎨 Custom Themes

Themes are dicts of color keys — save/load/export as JSON:

```python
from browser.themes import ThemeManager, build_stylesheet
tm = ThemeManager(settings)

# Create a custom theme
my_theme = dict(tm.get_preset("dark"))
my_theme["accent"] = "#ff6b6b"
tm.save_custom("Coral", my_theme)
```

Built-in presets: `dark`, `light`, `neon`, `soft`, `minimal`, `gaming`, `work`.

---

## 📋 Requirements

```
PyQt6 >= 6.4.0
PyQt6-WebEngine >= 6.4.0
requests >= 2.28.0
aiohttp >= 3.8.0
cryptography >= 38.0.0
Pillow >= 9.0.0
```

---

## 🛣️ Roadmap (Future Versions)

- [ ] Password manager with local encryption
- [ ] Full multi-window support
- [ ] Extension/plugin system
- [ ] Picture-in-picture video
- [ ] Google Workspace integration panel
- [ ] Per-site permissions manager
- [ ] Tab groups with labels & colors
- [ ] Sync across devices (optional, encrypted)
- [ ] Built-in ad/tracker blocker (filter lists)
- [ ] Custom startup page editor

---

*JO Browser — Built with ❤️ in Python*
