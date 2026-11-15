"""Main entry point for the Star Map Editor application."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.gui import StarMapEditor


def load_application_theme(app: QApplication) -> None:
    """Apply the shared SW-Mercs stylesheet if the resource is available."""
    stylesheet = Path(__file__).resolve().parent / "resources" / "styles" / "swmercs.qss"
    if stylesheet.is_file():
        app.setStyleSheet(stylesheet.read_text(encoding="utf-8"))


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    load_application_theme(app)
    window = StarMapEditor()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
