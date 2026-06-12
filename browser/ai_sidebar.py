"""
JO Browser — AI / Assistant Sidebar
Plugin-ready architecture for future AI integrations (Gemini, OpenAI, etc.).
The sidebar provides hooks for: page summary, translation, voice input, TTS,
and search assistance. No external API keys are hardcoded.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QLineEdit, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

log = logging.getLogger(__name__)


class AIWorker(QThread):
    """Generic worker thread that calls an AI provider hook."""
    result_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, task: str, context: str, provider_fn):
        super().__init__()
        self._task = task
        self._context = context
        self._fn = provider_fn

    def run(self):
        try:
            result = self._fn(self._task, self._context)
            self.result_ready.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AIProviderRegistry:
    """
    Register AI providers by name.
    Example usage once Gemini key is available:
        registry.register("gemini", my_gemini_fn)
    Each fn must accept (task: str, context: str) -> str.
    """
    def __init__(self):
        self._providers: dict[str, callable] = {}
        self._register_placeholder()

    def _register_placeholder(self):
        def placeholder(task: str, context: str) -> str:
            return (
                f"[AI provider not configured]\n\n"
                f"Task: {task}\n\n"
                f"To enable AI features, register a provider:\n"
                f"  registry.register('gemini', your_gemini_fn)\n\n"
                f"Context preview: {context[:200]}..."
            )
        self._providers["placeholder"] = placeholder

    def register(self, name: str, fn: callable):
        self._providers[name] = fn
        log.info("Registered AI provider: %s", name)

    def get(self, name: str = None) -> callable:
        if name and name in self._providers:
            return self._providers[name]
        # Return first non-placeholder provider, or placeholder
        for k, v in self._providers.items():
            if k != "placeholder":
                return v
        return self._providers["placeholder"]

    def list_providers(self) -> list[str]:
        return [k for k in self._providers if k != "placeholder"]


# Global registry — plug in your providers here
ai_registry = AIProviderRegistry()


class AISidebarWidget(QWidget):
    """The AI assistant sidebar panel."""

    def __init__(self, browser_window, parent=None):
        super().__init__(parent)
        self._browser = browser_window
        self._worker: AIWorker | None = None
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header
        header = QLabel("🤖 JO Assistant")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #e8e8f0;")
        layout.addWidget(header)

        sub = QLabel("AI-powered page tools")
        sub.setStyleSheet("font-size: 12px; color: #9898b0;")
        layout.addWidget(sub)

        # Action buttons
        btn_row = QHBoxLayout()
        for label, task in [("Summarize", "summarize"), ("Translate", "translate"),
                              ("Explain", "explain"), ("Key Points", "keypoints")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, t=task: self._run_task(t))
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        # Chat input
        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask anything about this page...")
        self._input.returnPressed.connect(lambda: self._run_task("ask", self._input.text()))
        layout.addWidget(self._input)

        ask_btn = QPushButton("Ask")
        ask_btn.setObjectName("accent")
        ask_btn.clicked.connect(lambda: self._run_task("ask", self._input.text()))
        layout.addWidget(ask_btn)

        # Output area
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("AI response will appear here...")
        self._output.setMinimumHeight(200)
        layout.addWidget(self._output)

        # Voice / TTS placeholders
        media_row = QHBoxLayout()
        voice_btn = QPushButton("🎙 Voice Input")
        voice_btn.setToolTip("Voice input — connect a speech-to-text provider to enable")
        voice_btn.clicked.connect(self._voice_placeholder)
        tts_btn = QPushButton("🔊 Read Aloud")
        tts_btn.setToolTip("Text-to-speech — connect a TTS provider to enable")
        tts_btn.clicked.connect(self._tts_placeholder)
        media_row.addWidget(voice_btn)
        media_row.addWidget(tts_btn)
        layout.addLayout(media_row)

        # Provider label
        self._provider_lbl = QLabel("Provider: none configured")
        self._provider_lbl.setStyleSheet("font-size: 11px; color: #606078;")
        layout.addWidget(self._provider_lbl)

        layout.addStretch()

    def _get_page_content(self) -> str:
        """Extract plain text from current web page."""
        tab = self._browser.current_tab()
        if not tab:
            return ""
        result = []
        tab.page().toPlainText(lambda text: result.append(text))
        return result[0] if result else ""

    def _run_task(self, task: str, extra: str = ""):
        current_url = ""
        tab = self._browser.current_tab()
        if tab:
            current_url = tab.url().toString()

        context = f"URL: {current_url}\n\nExtra: {extra}" if extra else f"URL: {current_url}"
        provider_fn = ai_registry.get()

        self._output.setPlainText("Thinking...")
        self._worker = AIWorker(task, context, provider_fn)
        self._worker.result_ready.connect(self._output.setPlainText)
        self._worker.error.connect(lambda e: self._output.setPlainText(f"Error: {e}"))
        self._worker.start()

    def _voice_placeholder(self):
        self._output.setPlainText(
            "Voice input: Register a speech-to-text provider via ai_registry.register() "
            "to enable this feature."
        )

    def _tts_placeholder(self):
        self._output.setPlainText(
            "Text-to-speech: Register a TTS provider via ai_registry.register() "
            "to enable this feature."
        )
