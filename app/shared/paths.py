"""Repository-relative paths independent of working directory."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RESOURCES_DIR = ROOT / "resources"
SAVES_DIR = ROOT / "saves"
EXPORTS_DIR = ROOT / "exports"

def open_project_directory():
    """Keep legacy user saves discoverable without moving them."""
    for directory in (SAVES_DIR, ROOT / "star-map-editor" / "core" / "Saves",
                      ROOT / "star-map-editor" / "Saves"):
        if directory.is_dir() and any(directory.glob("*.swmproj")):
            return directory
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    return SAVES_DIR
