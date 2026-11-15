"""Main entry point for the Star Map Editor application."""

import sys
from PySide6.QtWidgets import QApplication

from core.gui import StarMapEditor


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    window = StarMapEditor()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
