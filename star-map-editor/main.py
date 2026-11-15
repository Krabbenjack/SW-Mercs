"""Compatibility entry point for opening the map editor directly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from app.editors.starmap.gui import StarMapEditor

def main():
    app = QApplication(sys.argv)
    window = StarMapEditor()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())

