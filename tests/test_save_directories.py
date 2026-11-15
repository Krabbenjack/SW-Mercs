"""Standard save paths, startup creation and backwards-compatible discovery."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.shared import paths


class SaveDirectoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.saves = self.root / "saves"
        self.maps = self.saves / "starmaps"
        self.shipsets = self.saves / "shipsets"
        patcher = patch.multiple(paths, ROOT=self.root, SAVES_DIR=self.saves,
                                 STARMAPS_DIR=self.maps, SHIPSETS_DIR=self.shipsets)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_startup_creates_both_without_overwriting_files(self):
        self.assertFalse(self.saves.exists())
        paths.ensure_save_directories()
        self.assertTrue(self.maps.is_dir())
        self.assertTrue(self.shipsets.is_dir())
        existing = self.maps / "existing.swmproj"
        existing.write_text("keep")
        paths.ensure_save_directories()
        self.assertEqual(existing.read_text(), "keep")
        self.assertEqual(paths.open_project_directory(), self.maps)

    def test_legacy_directories_remain_discoverable(self):
        self.assertEqual(paths.open_project_directory(), self.maps)
        for directory in (self.root / "star-map-editor" / "Saves",
                          self.root / "star-map-editor" / "core" / "Saves",
                          self.saves, self.maps):
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "older.swmproj").write_text("keep")
            self.assertEqual(paths.open_project_directory(), directory)
        self.assertTrue((self.saves / "older.swmproj").exists())


if __name__ == "__main__":
    unittest.main()
