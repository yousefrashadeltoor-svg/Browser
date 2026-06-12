"""
JO Browser — Splash Screen
Shown briefly on startup (when startup.show_splash is True).
Pure Qt — no external image required.
"""

from PyQt6.QtWidgets import QSplashScreen, QLabel, QProgressBar, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QGradient


def _make_splash_pixmap(w: int = 480, h: int = 280) -> QPixmap:
    px = QPixmap(w, h)
    px.fill(Qt.GlobalColor.transparent)

    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background gradient
    grad = QLinearGradient(0, 0, w, h)
    grad.setColorAt(0.0, QColor("#0d0d1a"))
    grad.setColorAt(1.0, QColor("#1a1a2e"))
    painter.fillRect(0, 0, w, h, grad)

    # Accent glow (ellipse)
    glow = QLinearGradient(0, 0, w, h)
    glow.setColorAt(0.0, QColor(108, 99, 255, 60))
    glow.setColorAt(1.0, QColor(99, 179, 255, 30))
    painter.setBrush(glow)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(int(w * 0.1), int(h * 0.1), int(w * 0.6), int(h * 0.6))

    # Logo box
    box_x, box_y, box_s = w // 2 - 44, 60, 88
    logo_grad = QLinearGradient(box_x, box_y, box_x + box_s, box_y + box_s)
    logo_grad.setColorAt(0.0, QColor("#6C63FF"))
    logo_grad.setColorAt(1.0, QColor("#a855f7"))
    painter.setBrush(logo_grad)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(box_x, box_y, box_s, box_s, 22, 22)

    # "JO" text in box
    painter.setPen(QColor("#ffffff"))
    f = QFont("Segoe UI", 30, QFont.Weight.Black)
    painter.setFont(f)
    painter.drawText(box_x, box_y, box_s, box_s, Qt.AlignmentFlag.AlignCenter, "JO")

    # Browser name
    painter.setPen(QColor("#e8e8f0"))
    name_font = QFont("Segoe UI", 22, QFont.Weight.Bold)
    painter.setFont(name_font)
    painter.drawText(0, 162, w, 36, Qt.AlignmentFlag.AlignCenter, "JO Browser")

    # Tagline
    painter.setPen(QColor("#9898b0"))
    tag_font = QFont("Segoe UI", 11)
    painter.setFont(tag_font)
    painter.drawText(0, 198, w, 24, Qt.AlignmentFlag.AlignCenter, "Premium · Fast · Elegant")

    # Version
    painter.setPen(QColor("#606078"))
    ver_font = QFont("Segoe UI", 9)
    painter.setFont(ver_font)
    painter.drawText(0, h - 20, w, 16, Qt.AlignmentFlag.AlignCenter, "Version 1.0.0")

    painter.end()
    return px


def show_splash(duration_ms: int = 2200):
    """Show the splash screen for duration_ms, return the QSplashScreen object."""
    px = _make_splash_pixmap()
    splash = QSplashScreen(px, Qt.WindowType.WindowStaysOnTopHint)
    splash.setMask(px.mask())
    splash.show()
    return splash
