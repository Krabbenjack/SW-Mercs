"""SW-Mercs application entry point.

Run from the repository root with: python swmercs.py
The existing Star Map Editor remains in its legacy directory until its
imports and resource paths can be migrated with regression coverage.
"""
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QVBoxLayout, QWidget,
)

ROOT = Path(__file__).resolve().parent
LEGACY_EDITOR = ROOT / "star-map-editor"


class EditorCenter(QMainWindow):
    def __init__(self, home):
        super().__init__(home)
        self.home = home
        self.map_window = None
        self.setWindowTitle("SW-Mercs | Editor Command Center")
        self.resize(850, 570)
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(45, 35, 45, 35)
        layout.setSpacing(16)
        title = QLabel("EDITOR COMMAND CENTER")
        title.setObjectName("heading")
        layout.addWidget(title)
        layout.addWidget(QLabel("Development & Data Management"))
        for name, detail, enabled, callback in (
            ("STAR MAP EDITOR", "Systems · Routes · Zones · Infrastructure", True, self.open_map),
            ("STARSHIP EDITOR", "Ship Database · Fleet Manager · Maintenance (planned)", False, None),
            ("INDUSTRY EDITOR", "Goods · Production · Economic Simulation (planned)", False, None),
        ):
            button = QPushButton(f"{name}\n{detail}")
            button.setObjectName("module")
            button.setEnabled(enabled)
            button.setMinimumHeight(95)
            if callback:
                button.clicked.connect(callback)
            layout.addWidget(button)
        layout.addStretch()
        back = QPushButton("← Back to Main Menu")
        back.clicked.connect(self.go_back)
        layout.addWidget(back)

    def open_map(self):
        # The legacy module imports core.* directly. Keep its directory on
        # sys.path until the module can be migrated without breaking imports.
        path = str(LEGACY_EDITOR)
        if path not in sys.path:
            sys.path.insert(0, path)
        from core.gui import StarMapEditor
        if self.map_window is None:
            self.map_window = StarMapEditor()
            self.map_window.destroyed.connect(self._map_destroyed)
        self.map_window.show()
        self.map_window.raise_()
        self.map_window.activateWindow()

    def _map_destroyed(self):
        self.map_window = None

    def go_back(self):
        self.home.show()
        self.hide()


class Home(QMainWindow):
    def __init__(self):
        super().__init__()
        self.center = None
        self.setWindowTitle("SW-Mercs")
        self.resize(720, 520)
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(90, 65, 90, 65)
        layout.setSpacing(20)
        layout.addStretch()
        heading = QLabel("SW-MERCS")
        heading.setObjectName("brand")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)
        subtitle = QLabel("GALACTIC ECONOMY & OPERATIONS")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(25)
        play = QPushButton("PLAY\nComing later")
        play.setMinimumHeight(78)
        play.setEnabled(False)
        layout.addWidget(play)
        editor = QPushButton("EDITOR\nOpen development tools")
        editor.setObjectName("primary")
        editor.setMinimumHeight(78)
        editor.clicked.connect(self.open_editor)
        layout.addWidget(editor)
        quit_button = QPushButton("Exit")
        quit_button.clicked.connect(QApplication.instance().quit)
        layout.addWidget(quit_button)
        layout.addStretch()

    def open_editor(self):
        if self.center is None:
            self.center = EditorCenter(self)
        self.center.show()
        self.hide()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SW-Mercs")
    theme = ROOT / "resources" / "styles" / "launcher.qss"
    if theme.is_file():
        app.setStyleSheet(theme.read_text(encoding="utf-8"))
    home = Home()
    home.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
