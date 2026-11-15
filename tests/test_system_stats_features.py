"""Test the ported system details in the current map editor and file formats."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QMessageBox
from app.editors.starmap import MapProject, SystemData, PlanetData, MoonData
from app.editors.starmap.systems import PLANET_TYPES, MAX_FLUFF_LENGTH
from app.editors.starmap.data_loader import get_data_loader, format_population
from app.editors.starmap.gui import StarMapEditor
from app.editors.starmap.project_io import save_project, load_project, export_map_data


class SystemStatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_population_values(self):
        loader = get_data_loader()
        self.assertEqual(loader.get_population_value("galactic_capital"), 1_500_000_000_000)
        self.assertEqual(loader.get_population_value("uninhabited"), 0)
        self.assertIsNone(loader.get_population_value(None))
        self.assertIsNone(loader.get_population_value("missing"))
        for value, label in ((None, ""), (0, "0"), (500, "500"), (50_000, "50K"),
                             (500_000_000, "500M"), (1_500_000_000_000, "1.5T")):
            self.assertEqual(format_population(value), label)

    def test_roundtrip_export_and_old_files(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "map.swmproj"
            export = Path(dirname) / "map.json"
            old = {"systems": [{"id": "a", "name": "A", "x": 0, "y": 1,
                                "population_id": "micro", "facilities": ["mining"]},
                               {"id": "b", "name": "B", "x": 1, "y": 2,
                                "planets": [{"id": "p", "name": "Old planet",
                                             "moons": [{"id": "m", "name": "Old moon"}]}],
                                "fluff_text": "Old description"}]}
            path.write_text(json.dumps(old))
            project = load_project(path)
            a, b = project.systems["a"], project.systems["b"]
            self.assertEqual((a.planets, a.fluff_text), ([], ""))
            self.assertIsNone(b.planets[0].planet_type)
            self.assertEqual(b.planets[0].moons[0].id, "m")
            self.assertEqual(b.fluff_text, "Old description")
            a.planets = [PlanetData.create_new(name, key) for key, name in PLANET_TYPES.items()]
            a.planets[0].moons.append(MoonData.create_new("Moon"))
            a.fluff_text = "Test ö — description"
            self.assertTrue(save_project(project, path))
            restored = load_project(path)
            self.assertEqual(restored.systems["a"], a)
            self.assertEqual(restored.systems["b"], b)
            self.assertTrue(export_map_data(restored, export))
            raw = json.loads(export.read_text())["systems"]
            self.assertEqual([p["planet_type"] for p in raw[0]["planets"]], list(PLANET_TYPES))
            self.assertEqual(raw[0]["planets"][0]["moons"][0]["id"], a.planets[0].moons[0].id)
            self.assertEqual(raw[0]["fluff_text"], a.fluff_text)
            self.assertNotIn("planet_type", raw[1]["planets"][0])

    def test_real_qt_sidebar(self):
        editor = StarMapEditor()
        editor.show()
        try:
            a = SystemData.create_new("Coruscant", QPointF(0, 0))
            a.population_id = "galactic_capital"
            b = SystemData.create_new("Other", QPointF(100, 0))
            b.fluff_text = "Other text"
            for system in (a, b):
                editor.project.systems[system.id] = system
                editor.add_system_to_scene(system)
            editor.set_mode("stats")
            editor.unsaved_changes = False
            editor.system_items[a.id].setSelected(True)
            self.app.processEvents()
            widget = editor.stats_inspector.system_stats_widget
            planets = widget.planet_editor
            self.assertIs(widget.current_system, a)
            self.assertFalse(editor.unsaved_changes)
            self.assertIn("1.5T", widget.population_value_label.text())
            self.assertFalse(planets.moon_add_button.isEnabled())
            with patch("PySide6.QtWidgets.QInputDialog.getText", return_value=(" First ", True)):
                planets.planet_add_button.click()
            self.assertEqual(a.planets[0].name, "First")
            self.assertTrue(editor.unsaved_changes)
            editor.unsaved_changes = False
            planets.type_combo.setCurrentIndex(planets.type_combo.findData("temperate"))
            self.assertEqual(a.planets[0].planet_type, "temperate")
            self.assertTrue(editor.unsaved_changes)
            with patch("PySide6.QtWidgets.QInputDialog.getText", return_value=("Moon 1", True)):
                planets.moon_add_button.click()
            moon_id = a.planets[0].moons[0].id
            with patch("PySide6.QtWidgets.QInputDialog.getText", return_value=("Centax", True)):
                planets.moon_rename_button.click()
            self.assertEqual(a.planets[0].moons[0].id, moon_id)
            self.assertEqual(a.planets[0].moons[0].name, "Centax")
            with patch("PySide6.QtWidgets.QInputDialog.getText", return_value=("Second", True)):
                planets.planet_add_button.click()
            planets.type_combo.setCurrentIndex(planets.type_combo.findData("gas_giant"))
            self.assertEqual(planets.moon_list.count(), 0)
            planets.planet_list.setCurrentRow(0)
            self.assertEqual(planets.type_combo.currentData(), "temperate")
            self.assertEqual(planets.moon_list.count(), 1)
            self.assertEqual(a.planets[1].planet_type, "gas_giant")
            planet_id = a.planets[0].id
            with patch("PySide6.QtWidgets.QInputDialog.getText", return_value=("Prime", True)):
                planets.planet_rename_button.click()
            self.assertEqual(a.planets[0].id, planet_id)
            self.assertEqual(a.planets[0].name, "Prime")
            with patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.No):
                planets.planet_delete_button.click()
            self.assertEqual(len(a.planets), 2)
            with patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.Yes):
                planets.moon_delete_button.click()
            self.assertEqual(a.planets[0].moons, [])
            planets.planet_list.setCurrentRow(1)
            with patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.Yes):
                planets.planet_delete_button.click()
            self.assertEqual(len(a.planets), 1)
            widget.fluff_text_edit.setPlainText("x" * 550)
            self.assertEqual(len(a.fluff_text), MAX_FLUFF_LENGTH)
            self.assertEqual(widget.fluff_counter.text(), "500 / 500")
            widget.population_combo.setCurrentIndex(widget.population_combo.findData("uninhabited"))
            self.assertEqual(widget.population_value_label.text(), "0 inhabitants")
            self.assertEqual(a.population_id, "uninhabited")
            editor.unsaved_changes = False
            editor.scene.clearSelection()
            editor.system_items[b.id].setSelected(True)
            self.app.processEvents()
            self.assertIs(widget.current_system, b)
            self.assertEqual(widget.fluff_text_edit.toPlainText(), "Other text")
            self.assertEqual(planets.planet_list.count(), 0)
            self.assertEqual(widget.population_value_label.text(), "Population unknown")
            self.assertFalse(editor.unsaved_changes)
            editor.scene.clearSelection()
            editor.system_items[a.id].setSelected(True)
            self.app.processEvents()
            self.assertEqual(planets.planet_list.count(), 1)
            self.assertEqual(widget.fluff_text_edit.toPlainText(), "x" * 500)
            self.assertEqual(planets.type_combo.currentData(), "temperate")
            self.assertFalse(editor.unsaved_changes)
        finally:
            editor.scene.clearSelection()
            editor.unsaved_changes = False
            editor.close()


if __name__ == "__main__":
    unittest.main()
