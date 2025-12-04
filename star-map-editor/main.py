"""Main entry point for the Star Map Editor application."""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from gui import StarMapEditor


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    window = StarMapEditor()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
