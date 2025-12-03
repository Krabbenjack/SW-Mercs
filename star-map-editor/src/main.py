import sys
from PyQt5.QtWidgets import QApplication

# Handle both direct execution and module execution
try:
    from gui import StarMapEditor
except ModuleNotFoundError:
    from src.gui import StarMapEditor


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    window = StarMapEditor()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
