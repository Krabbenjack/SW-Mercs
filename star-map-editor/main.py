"""Compatibility entry point for opening the map editor directly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from app.editors.starmap.gui import StarMapEditor
from app.shared.paths import ensure_save_directories

def main():
    app = QApplication(sys.argv)
    ensure_save_directories()
    window = StarMapEditor()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())

