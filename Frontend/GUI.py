# ============================================================
#  Frontend/GUI.py  —  Swayam AI  (Full Jarvis UI)
# ============================================================

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QLabel, QSizePolicy, QScrollArea,
    QSystemTrayIcon, QMenu, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import (
    QIcon, QMovie, QColor, QFont, QPixmap,
    QPainter, QPen, QBrush, QLinearGradient, QPainterPath
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QThread, pyqtSignal,
    QPropertyAnimation, QEasingCurve, QRect, QPoint
)
from dotenv import dotenv_values
import sys
import os

# ── Load config ──────────────────────────────────────────────
env_vars      = dotenv_values(".env")
AssistantName = env_vars.get("Assistantname", "Swayam")
UserName      = env_vars.get("Username",      "User")

# ── File helpers ─────────────────────────────────────────────
def TempDirectoryPath(Filename):
    return os.path.join("Frontend", "Files", Filename)

def SetMicrophoneStatus(Command):
    os.makedirs(TempDirectoryPath("").rstrip(os.sep), exist_ok=True)
    with open(TempDirectoryPath("Mic.data"), "w", encoding="utf-8") as f:
        f.write(Command)

def GetMicrophoneStatus():
    p = TempDirectoryPath("Mic.data")
    return open(p, "r", encoding="utf-8").read().strip() if os.path.exists(p) else "False"

def SetAssistantStatus(Status):
    with open(TempDirectoryPath("Status.data"), "w", encoding="utf-8") as f:
        f.write(Status)

def GetAssistantStatus():
    p = TempDirectoryPath("Status.data")
    return open(p, "r", encoding="utf-8").read().strip() if os.path.exists(p) else "Available..."

def ShowTextToScreen(Text):
    with open(TempDirectoryPath("Responses.data"), "w", encoding="utf-8") as f:
        f.write(Text)

def AnswerModifier(Answer):
    return "\n".join(l for l in Answer.split("\n") if l.strip())

def QueryModifier(Query):
    q = Query.lower().strip()
    qw = ["how","what","who","where","when","why","which","whose","whom"]
    if any(q.startswith(w) for w in qw):
        return q.rstrip(".?!") + "?"
    return q.rstrip(".?!") + "."

# ── Colour palette ────────────────────────────────────────────
BG         = "#05080f"
SURFACE    = "#0b1120"
SURFACE2   = "#101828"
BORDER     = "#1a2a40"
BORDER2    = "#243650"
CYAN       = "#00e5ff"
CYAN2      = "#33eeff"
CYAN_DIM   = "rgba(0,229,255,0.10)"
TEXT       = "#c8d8f0"
DIM        = "#4a6080"
RED        = "#ff4d6d"
GREEN      = "#00ff88"
ORANGE     = "#ff8c42"


# ═══════════════════════════════════════════════════════════
#  CHAT BUBBLE
# ═══════════════════════════════════════════════════════════
class ChatBubble(QFrame):
    def __init__(self, speaker, message, is_user=False):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 3, 8, 3)

        # avatar
        avatar = QLabel()
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background: {'rgba(0,229,255,0.15)' if is_user else SURFACE2};
                border: 1px solid {'rgba(0,229,255,0.4)' if is_user else BORDER};
                border-radius: 16px;
                color: {CYAN if is_user else TEXT};
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        avatar.setText("👤" if is_user else "◈")

        # bubble
        bubble = QLabel()
        bubble.setWordWrap(True)
        bubble.setTextFormat(Qt.TextFormat.PlainText)
        bubble.setText(message)
        bubble.setMaximumWidth(560)
        bubble.setMinimumWidth(40)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        if is_user:
            bubble.setStyleSheet(f"""
                QLabel {{
                    background: rgba(0,229,255,0.10);
                    color: {CYAN2};
                    border: 1px solid rgba(0,229,255,0.30);
                    border-radius: 14px 14px 2px 14px;
                    padding: 10px 16px;
                    font-size: 13px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    line-height: 1.5;
                }}
            """)
            outer.setAlignment(Qt.AlignmentFlag.AlignRight)
            outer.addStretch()
            outer.addWidget(bubble)
            outer.addWidget(avatar)
        else:
            bubble.setStyleSheet(f"""
                QLabel {{
                    background: {SURFACE2};
                    color: {TEXT};
                    border: 1px solid {BORDER};
                    border-radius: 14px 14px 14px 2px;
                    padding: 10px 16px;
                    font-size: 13px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    line-height: 1.5;
                }}
            """)
            outer.setAlignment(Qt.AlignmentFlag.AlignLeft)
            outer.addWidget(avatar)
            outer.addWidget(bubble)
            outer.addStretch()

        # name label
        self.setStyleSheet("background: transparent;")


# ═══════════════════════════════════════════════════════════
#  TYPING INDICATOR
# ═══════════════════════════════════════════════════════════
class TypingIndicator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        avatar = QLabel("◈")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background: {SURFACE2}; border: 1px solid {BORDER};
                border-radius: 16px; color: {CYAN}; font-size: 14px; font-weight: bold;
            }}
        """)

        self.dots_label = QLabel("● ● ●")
        self.dots_label.setStyleSheet(f"""
            QLabel {{
                background: {SURFACE2}; color: {DIM};
                border: 1px solid {BORDER}; border-radius: 14px 14px 14px 2px;
                padding: 10px 16px; font-size: 16px; font-family: monospace;
            }}
        """)

        layout.addWidget(avatar)
        layout.addWidget(self.dots_label)
        layout.addStretch()

        # animate dots
        self._frame = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(400)

    def _animate(self):
        frames = ["●  ○  ○", "●  ●  ○", "●  ●  ●", "○  ●  ●", "○  ○  ●"]
        self.dots_label.setText(frames[self._frame % len(frames)])
        self._frame += 1


# ═══════════════════════════════════════════════════════════
#  CHAT PANEL
# ═══════════════════════════════════════════════════════════
class ChatPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {BG};")
        self._typing_widget = None
        self._last_messages = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── scroll area ──────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: {BG}; border: none; }}
            QScrollBar:vertical {{
                width: 4px; background: transparent; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER2}; border-radius: 2px; min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet(f"background: {BG};")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setContentsMargins(12, 16, 12, 16)
        self.chat_layout.setSpacing(6)
        self.scroll.setWidget(self.chat_container)

        # ── status bar ──────────────────────────────────
        self.status_bar = QLabel(f"  ◉  {AssistantName}  ·  Available")
        self.status_bar.setFixedHeight(30)
        self.status_bar.setStyleSheet(f"""
            QLabel {{
                color: {DIM}; font-size: 11px;
                font-family: 'Consolas', monospace; letter-spacing: 1px;
                padding-left: 16px; border-top: 1px solid {BORDER};
                background: {SURFACE};
            }}
        """)

        # ── input bar ───────────────────────────────────
        input_frame = QWidget()
        input_frame.setFixedHeight(72)
        input_frame.setStyleSheet(f"""
            QWidget {{
                background: {SURFACE};
                border-top: 1px solid {BORDER};
            }}
        """)
        il = QHBoxLayout(input_frame)
        il.setContentsMargins(16, 14, 16, 14)
        il.setSpacing(10)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("  Type a message or use voice ...")
        self.text_input.setFixedHeight(42)
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background: {BG};
                border: 1px solid {BORDER};
                border-radius: 21px;
                color: {TEXT};
                font-size: 13px;
                font-family: 'Consolas', 'Courier New', monospace;
                padding: 0 20px;
            }}
            QLineEdit:focus {{
                border: 1px solid {CYAN};
                background: rgba(0,229,255,0.03);
            }}
            QLineEdit::placeholder {{ color: {DIM}; }}
        """)
        self.text_input.returnPressed.connect(self._send_text)

        def icon_btn(glyph, tooltip, size=42, accent=CYAN, bg="rgba(0,229,255,0.08)"):
            b = QPushButton(glyph)
            b.setFixedSize(size, size)
            b.setToolTip(tooltip)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {bg}; border: 1px solid {accent};
                    border-radius: {size//2}px; font-size: 17px; color: {accent};
                }}
                QPushButton:hover {{ background: rgba(0,229,255,0.20); }}
                QPushButton:checked {{ background: {accent}; color: #000; }}
            """)
            return b

        self.mic_btn = icon_btn("🎙", "Toggle Microphone")
        self.mic_btn.setCheckable(True)
        self.mic_btn.setChecked(True)
        self.mic_btn.toggled.connect(self._toggle_mic)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(42, 42)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYAN}; border: none; border-radius: 21px;
                font-size: 16px; color: #000; font-weight: bold;
            }}
            QPushButton:hover {{ background: {CYAN2}; }}
            QPushButton:pressed {{ background: #00c8e0; }}
        """)
        self.send_btn.clicked.connect(self._send_text)

        self.clear_btn = icon_btn("🗑", "Clear Chat", accent=RED,
                                   bg="rgba(255,77,109,0.08)")
        self.clear_btn.clicked.connect(self.clear_chat)

        il.addWidget(self.text_input)
        il.addWidget(self.mic_btn)
        il.addWidget(self.send_btn)
        il.addWidget(self.clear_btn)

        outer.addWidget(self.scroll)
        outer.addWidget(self.status_bar)
        outer.addWidget(input_frame)

    # ── slots ────────────────────────────────────────────
    def _send_text(self):
        txt = self.text_input.text().strip()
        if txt:
            # Write to special file; Main.py listens for this
            with open(TempDirectoryPath("TextInput.data"), "w", encoding="utf-8") as f:
                f.write(txt)
            self.text_input.clear()
            self.add_message(UserName, txt, is_user=True)
            self.show_typing()

    def _toggle_mic(self, checked):
        SetMicrophoneStatus("True" if checked else "False")
        self.mic_btn.setText("🎙" if checked else "🔇")

    # ── public methods ───────────────────────────────────
    def add_message(self, speaker, text, is_user=False):
        self.hide_typing()
        bubble = ChatBubble(speaker, text, is_user)
        self.chat_layout.addWidget(bubble)
        QTimer.singleShot(60, self._scroll_bottom)

    def show_typing(self):
        if self._typing_widget is None:
            self._typing_widget = TypingIndicator()
            self.chat_layout.addWidget(self._typing_widget)
            QTimer.singleShot(60, self._scroll_bottom)

    def hide_typing(self):
        if self._typing_widget is not None:
            self._typing_widget.deleteLater()
            self._typing_widget = None

    def set_status(self, txt):
        colours = {
            "Listening":  f"color: {GREEN};",
            "Thinking":   f"color: {ORANGE};",
            "Searching":  f"color: {ORANGE};",
            "Answering":  f"color: {CYAN};",
            "Available":  f"color: {DIM};",
        }
        style_extra = ""
        for k, v in colours.items():
            if k.lower() in txt.lower():
                style_extra = v
                break
        self.status_bar.setText(f"  ◉  {AssistantName}  ·  {txt}")
        self.status_bar.setStyleSheet(f"""
            QLabel {{
                font-size: 11px; font-family: 'Consolas', monospace; letter-spacing: 1px;
                padding-left: 16px; border-top: 1px solid {BORDER};
                background: {SURFACE}; {style_extra}
            }}
        """)

    def clear_chat(self):
        for i in reversed(range(self.chat_layout.count())):
            w = self.chat_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._typing_widget = None
        import json
        chat_log = os.path.join("Data", "ChatLog.json")
        os.makedirs("Data", exist_ok=True)
        with open(chat_log, "w", encoding="utf-8") as f:
            json.dump([], f)
        # clear Responses.data too
        open(TempDirectoryPath("Responses.data"), "w").write("")

    def _scroll_bottom(self):
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )


# ═══════════════════════════════════════════════════════════
#  HOME / MONITOR SCREEN
# ═══════════════════════════════════════════════════════════
class HomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {BG};")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)

        # animated GIF orb
        gif_path = os.path.join("Frontend", "Graphics", "Jarvis.gif")
        if os.path.exists(gif_path):
            gif_label = QLabel()
            gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            movie = QMovie(gif_path)
            movie.setScaledSize(QSize(300, 300))
            gif_label.setMovie(movie)
            movie.start()
            layout.addWidget(gif_label)

        # Name
        name_lbl = QLabel(AssistantName.upper())
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(f"""
            QLabel {{
                color: {CYAN};
                font-size: 36px;
                font-weight: 800;
                letter-spacing: 14px;
                font-family: 'Consolas', monospace;
                margin-top: 8px;
            }}
        """)

        # Sub-title
        sub_lbl = QLabel("AI DESKTOP ASSISTANT  ·  POWERED BY GROQ")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet(f"""
            QLabel {{
                color: {DIM};
                font-size: 11px;
                letter-spacing: 4px;
                font-family: 'Consolas', monospace;
                margin-top: 6px;
            }}
        """)

        # Live status display on home screen
        self.live_status = QLabel("●  AVAILABLE")
        self.live_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.live_status.setStyleSheet(f"""
            QLabel {{
                color: {GREEN};
                font-size: 12px;
                letter-spacing: 3px;
                font-family: 'Consolas', monospace;
                margin-top: 20px;
            }}
        """)

        layout.addWidget(name_lbl)
        layout.addWidget(sub_lbl)
        layout.addWidget(self.live_status)

    def update_status(self, txt):
        self.live_status.setText(f"●  {txt.upper()}")


# ═══════════════════════════════════════════════════════════
#  TOP BAR
# ═══════════════════════════════════════════════════════════
class TopBar(QWidget):
    def __init__(self, parent, stack):
        super().__init__(parent)
        self.stack = stack
        self.dragPos = None
        self.setFixedHeight(54)
        self.setStyleSheet(f"""
            QWidget {{
                background: {SURFACE};
                border-bottom: 1px solid {BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 12, 0)
        layout.setSpacing(8)

        # Brand
        brand = QLabel(f"◈  {AssistantName.upper()}")
        brand.setStyleSheet(f"""
            QLabel {{
                color: {CYAN}; font-size: 14px;
                font-family: 'Consolas', monospace; letter-spacing: 5px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(brand)
        layout.addStretch()

        def nav(text, idx):
            b = QPushButton(text)
            b.setFixedHeight(30)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    border: 1px solid {BORDER}; border-radius: 6px;
                    color: {DIM}; background: transparent;
                    padding: 0 16px; font-size: 12px;
                    font-family: 'Consolas', monospace;
                }}
                QPushButton:hover {{
                    border-color: {CYAN}; color: {CYAN};
                    background: rgba(0,229,255,0.06);
                }}
            """)
            b.clicked.connect(lambda: stack.setCurrentIndex(idx))
            return b

        def ctrl(glyph, action, danger=False):
            b = QPushButton(glyph)
            b.setFixedSize(32, 32)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    border: none; color: {RED if danger else DIM};
                    font-size: 15px; background: transparent; border-radius: 4px;
                }}
                QPushButton:hover {{
                    background: {'rgba(255,77,109,0.15)' if danger else SURFACE2};
                    color: {RED if danger else TEXT};
                }}
            """)
            b.clicked.connect(action)
            return b

        layout.addWidget(nav("⌂  Monitor", 0))
        layout.addWidget(nav("💬  Chat",    1))
        layout.addSpacing(8)
        layout.addWidget(ctrl("─", lambda: self.window().showMinimized()))
        layout.addWidget(ctrl("✕", lambda: self.window().close(), danger=True))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.dragPos:
            self.window().move(
                self.window().pos() + event.globalPosition().toPoint() - self.dragPos
            )
            self.dragPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.dragPos = None


# ═══════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(AssistantName)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(60, 60, 1060, 680)
        self.setMinimumSize(720, 500)

        self._last_response = ""
        self._last_status   = ""

        # central
        central = QWidget()
        self.setCentralWidget(central)
        ml = QVBoxLayout(central)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        # screens
        self.stack        = QStackedWidget()
        self.home_screen  = HomeScreen()
        self.chat_panel   = ChatPanel()
        self.stack.addWidget(self.home_screen)   # index 0
        self.stack.addWidget(self.chat_panel)    # index 1

        # top bar
        self.top_bar = TopBar(self, self.stack)

        ml.addWidget(self.top_bar)
        ml.addWidget(self.stack)

        # system tray
        self._setup_tray()

        # poll timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        self.timer.start(350)

    # ── system tray ─────────────────────────────────────
    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon_path = os.path.join("Frontend", "Graphics", "Home.png")
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        self.tray.setToolTip(AssistantName)
        menu = QMenu()
        menu.addAction("Show",  self.show)
        menu.addAction("Hide",  self.hide)
        menu.addSeparator()
        menu.addAction("Quit",  lambda: QApplication.quit())
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.show() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )
        self.tray.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage(
            AssistantName, "Running in background. Double-click tray icon to restore.",
            QSystemTrayIcon.MessageIcon.Information, 2500
        )

    # ── poll for backend updates ─────────────────────────
    def _poll(self):
        # 1. check status
        sp = TempDirectoryPath("Status.data")
        if os.path.exists(sp):
            status = open(sp, encoding="utf-8").read().strip()
            if status != self._last_status:
                self._last_status = status
                self.chat_panel.set_status(status)
                self.home_screen.update_status(status)
                if "thinking" in status.lower() or "searching" in status.lower():
                    self.chat_panel.show_typing()
                else:
                    self.chat_panel.hide_typing()

        # 2. check responses
        rp = TempDirectoryPath("Responses.data")
        if not os.path.exists(rp):
            return
        text = open(rp, encoding="utf-8").read().strip()
        if not text or text == self._last_response:
            return
        self._last_response = text
        self.stack.setCurrentIndex(1)

        # parse lines into bubbles
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                speaker, msg = line.split(":", 1)
                speaker = speaker.strip()
                msg     = msg.strip()
                if not msg:
                    continue
                is_user = (speaker.lower() == UserName.lower())
                self.chat_panel.add_message(speaker, msg, is_user=is_user)
            else:
                self.chat_panel.add_message(AssistantName, line, is_user=False)


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════
def GraphicalUserInterface():
    os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette for native widgets
    from PyQt6.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base,            QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(SURFACE2))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(SURFACE2))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Text,            QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button,          QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(CYAN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    SetMicrophoneStatus("True")
    sys.exit(app.exec())


if __name__ == "__main__":
    GraphicalUserInterface()