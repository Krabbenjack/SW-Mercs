"""Repository-relative paths independent of working directory."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RESOURCES_DIR = ROOT / "resources"
SAVES_DIR = ROOT / "saves"
STARMAPS_DIR = SAVES_DIR / "starmaps"
SHIPSETS_DIR = SAVES_DIR / "shipsets"
EXPORTS_DIR = ROOT / "exports"

def ensure_save_directories():
    """Create the standard save directories without touching existing files."""
    for directory in (STARMAPS_DIR, SHIPSETS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

def open_project_directory():
    """Keep legacy user saves discoverable without moving them."""
    ensure_save_directories()
    for directory in (STARMAPS_DIR, SAVES_DIR, ROOT / "star-map-editor" / "core" / "Saves",
                      ROOT / "star-map-editor" / "Saves"):
        if directory.is_dir() and any(directory.glob("*.swmproj")):
            return directory
    return STARMAPS_DIR
