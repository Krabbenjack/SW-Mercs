"""SW-Mercs main menu and editor command center."""
import sys
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QStackedWidget, QVBoxLayout, QWidget)
from app.shared.theme import apply_theme


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.map_window = None
        self.setWindowTitle("SW-Mercs")
        self.resize(850, 570)
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.home, home = self._page(90, 65)
        home.addStretch()
        title = QLabel("SW-MERCS")
        title.setObjectName("brand")
        title.setAlignment(Qt.AlignCenter)
        home.addWidget(title)
        subtitle = QLabel("GALACTIC ECONOMY & OPERATIONS")
        subtitle.setAlignment(Qt.AlignCenter)
        home.addWidget(subtitle)
        self.play_button = self._button(home, "PLAY\nComing later", enabled=False)
        self.editor_button = self._button(home, "EDITOR\nOpen development tools", self.show_editors)
        self.editor_button.setObjectName("primary")
        self._button(home, "Exit", self.close, height=35)
        home.addStretch()

        self.center, center = self._page(45, 35)
        title = QLabel("EDITOR COMMAND CENTER")
        title.setObjectName("heading")
        center.addWidget(title)
        center.addWidget(QLabel("Development & Data Management"))
        self.map_button = self._button(center, "STAR MAP EDITOR\nSystems · Routes · Zones · Infrastructure", self.open_map, height=95)
        self.ship_button = self._button(center, "STARSHIP EDITOR\nShip Database · Fleet Manager · Maintenance (planned)", enabled=False, height=95)
        self.industry_button = self._button(center, "INDUSTRY EDITOR\nGoods · Production · Economic Simulation (planned)", enabled=False, height=95)
        for button in (self.map_button, self.ship_button, self.industry_button):
            button.setObjectName("module")
        center.addStretch()
        self.back_button = self._button(center, "← Back to Main Menu", self.show_home, height=35)
        self.show_home()
        apply_theme(self, "launcher")

    def _page(self, x, y):
        widget = QWidget()
        widget.setObjectName("central")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(x, y, x, y)
        layout.setSpacing(16)
        self.pages.addWidget(widget)
        return widget, layout

    @staticmethod
    def _button(layout, title, callback=None, enabled=True, height=78):
        button = QPushButton(title)
        button.setEnabled(enabled)
        button.setMinimumHeight(height)
        if callback is not None:
            button.clicked.connect(callback)
        layout.addWidget(button)
        return button

    def show_home(self):
        self.pages.setCurrentWidget(self.home)

    def show_editors(self):
        self.pages.setCurrentWidget(self.center)

    def open_map(self):
        try:
            from app.editors.starmap.gui import StarMapEditor
            if self.map_window is None:
                self.map_window = StarMapEditor()
            self.map_window.show()
            self.map_window.raise_()
            self.map_window.activateWindow()
        except Exception as exc:
            traceback.print_exc()
            QMessageBox.critical(self, "Star Map Editor", f"Could not start editor:\n{exc}")

    def closeEvent(self, event):
        if self.map_window is not None and self.map_window.isVisible():
            if not self.map_window.close():
                event.ignore()
                return
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SW-Mercs")
    window = Launcher()
    window.show()
    return app.exec()
