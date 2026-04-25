from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy
from PyQt6.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt6.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values
import sys
import os

# Load environment variables
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname", "Swayam")

def TempDirectoryPath(Filename):
    path = os.path.join("Frontend", "Files", Filename)
    return path

def SetMicrophoneStatus(Command):
    with open(TempDirectoryPath('Mic.data'), "w", encoding='utf-8') as file:
        file.write(Command)

def GetMicrophoneStatus():
    path = TempDirectoryPath('Mic.data')
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as file:
            return file.read()
    return "False"

def SetAssistantStatus(Status):
    with open(TempDirectoryPath('Status.data'), "w", encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    path = TempDirectoryPath('Status.data')
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as file:
            return file.read()
    return "Available..."

def ShowTextToScreen(Text):
    with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
        file.write(Text)

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.Shape.NoFrame)
        layout.addWidget(self.chat_text_edit)
        self.setStyleSheet("background-color: black;")
        layout.setSpacing(0)
        self.chat_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: black; 
                color: white; 
                font-family: Consolas, 'Courier New', monospace; 
                font-size: 14px; 
                border: none;
                padding: 10px;
            }
        """)

class InitialScreen(QWidget):
    def __init__(self):
        super(InitialScreen, self).__init__()
        layout = QVBoxLayout(self)
        self.setStyleSheet("background-color: black;")
        label = QLabel(f"INITIALIZING {Assistantname.upper()}...", self)
        label.setStyleSheet("color: cyan; font-size: 20px; font-weight: bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

class MessageScreen(QWidget):
    def __init__(self):
        super(MessageScreen, self).__init__()
        layout = QVBoxLayout(self)
        self.chat_section = ChatSection()
        layout.addWidget(self.chat_section)

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super(CustomTopBar, self).__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stacked_widget = stacked_widget
        self.dragPos = None

    def initUI(self):
        self.setFixedHeight(50)
        self.setStyleSheet("background-color: black; border-bottom: 1px solid cyan;")
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        home_button = QPushButton("Monitor")
        home_button.setStyleSheet("""
            QPushButton { border: 2px solid cyan; border-radius: 10px; color: cyan; background-color: black; padding: 5px 10px; font-weight: bold;}
            QPushButton:hover { background-color: cyan; color: black; }
        """)
        message_button = QPushButton("Chat")
        message_button.setStyleSheet("""
            QPushButton { border: 2px solid cyan; border-radius: 10px; color: cyan; background-color: black; padding: 5px 10px; font-weight: bold;}
            QPushButton:hover { background-color: cyan; color: black; }
        """)
        minimize_button = QPushButton("_")
        minimize_button.setStyleSheet("border: none; color: white; font-size: 20px; background: transparent; padding: 0 10px;")
        close_button = QPushButton("X")
        close_button.setStyleSheet("border: none; color: white; font-size: 20px; background: transparent; padding: 0 10px;")

        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        # Safe minimization and closing access via window()
        minimize_button.clicked.connect(lambda: self.window().showMinimized())
        close_button.clicked.connect(lambda: self.window().close())

        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addWidget(minimize_button)
        layout.addWidget(close_button)

    # Enable dragging the window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.dragPos:
            self.window().move(self.window().pos() + event.globalPosition().toPoint() - self.dragPos)
            self.dragPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.dragPos = None

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(100, 100, 800, 600)
        
        # 1. Create a Central Widget to hold Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 2. Main Vertical Layout (TopBar + Content)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Remove white borders
        self.main_layout.setSpacing(0)
        
        # 3. Create Screens
        self.stacked_widget = QStackedWidget()
        self.initial_screen = InitialScreen()
        self.message_screen = MessageScreen()
        self.stacked_widget.addWidget(self.initial_screen)
        self.stacked_widget.addWidget(self.message_screen)
        
        # 4. Create Top Bar
        self.top_bar = CustomTopBar(self, self.stacked_widget)

        # 5. Add Widgets to Layout (Bar at top, Stack at bottom)
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.stacked_widget)

        # Timer to check for new messages
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_messages)
        self.timer.start(500)

    def check_messages(self):
        path = TempDirectoryPath('Responses.data')
        if os.path.exists(path):
            with open(path, "r", encoding='utf-8') as file:
                text = file.read()
                if text:
                    self.message_screen.chat_section.chat_text_edit.setPlainText(text)
                    self.stacked_widget.setCurrentIndex(1)

def GraphicalUserInterface():
    os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    SetMicrophoneStatus("True")
    sys.exit(app.exec())

if __name__ == "__main__":
    GraphicalUserInterface()