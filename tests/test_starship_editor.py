"""Exercise real Qt forms, catalog switching, persistence and guarded imports."""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt, QMimeData, QPoint, QPointF, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QMessageBox
from app.editors.starships.fields import WEAPON_MIME, WeaponLoadoutDialog
from app.editors.starships.window import StarshipEditor
from app.editors.starships.store import json_bytes
from test_starship_store import temporary_catalog


def main():
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        store = temporary_catalog(root)
        editor = StarshipEditor(store)
        editor.show()
        app.processEvents()
        ships = editor.ship_panel
        assert len(ships.items) == 96 and ships.current_id == 1001
        assert ships.form.tabs.count() == 8
        assert not ships.form.tabs.isTabVisible(ships.form.tabs.indexOf(ships.form.pages["hangar"]))
        assert ships.form.forms["crew"].isRowVisible(ships.form.inputs[("crew", "passenger_capacity")])
        assert not ships.form.forms["crew"].isRowVisible(ships.form.inputs[("crew", "officers")])
        assert not ships.form.forms["cargo"].isRowVisible(ships.form.inputs[("cargo", "container_slots")])
        assert not ships.save_button.isEnabled()
        ships.search.setText("6002")
        assert not ships.items[6002].isHidden() and ships.items[1001].isHidden()
        ships.search.clear()
        editor.tabs.setCurrentIndex(1)
        weapons = editor.weapon_panel
        assert weapons.form is None
        with patch("PySide6.QtWidgets.QInputDialog.getText", return_value=("Medium laser", True)):
            weapons.new_button.click()
        assert weapons.dirty and weapons.current_id == 1
        weapons.form.inputs[("weapon", "damage")].input.setText("15")
        weapons.save_button.click()
        assert store.read(1, True)["weapon"]["damage"] == 15
        editor.tabs.setCurrentIndex(0)
        form = ships.form
        form.inputs[("technical", "length_m")].input.setText("12.5")
        assert ships.dirty and ships.save_button.isEnabled()
        factions = form.inputs[("general", "factions")].input
        factions.known.setChecked(True)
        factions.select.setCurrentText("Rebel Alliance")
        factions.add_button.click()
        factions.select.setCurrentText("Civilian")
        factions.add_button.click()
        loadout = form.inputs[("combat", "weapons")].input
        failures = []
        def populate_popup(apply):
            dialog = QApplication.activeModalWidget()
            try:
                assert isinstance(dialog, WeaponLoadoutDialog)
                assert dialog.catalog.count() == 1
                dialog.search.setText("medium")
                assert not dialog.catalog.item(0).isHidden()
                mime = QMimeData()
                mime.setData(WEAPON_MIME, b"1")
                table = dialog.mounts.table
                enter = QDragEnterEvent(QPoint(15, 15), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
                QApplication.sendEvent(table.viewport(), enter)
                assert enter.isAccepted()
                drop = QDropEvent(QPointF(15, 15), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
                QApplication.sendEvent(table.viewport(), drop)
                assert drop.isAccepted() and table.rowCount() == 1
                table.cellWidget(0, 1).setText("4")
                table.cellWidget(0, 2).setCurrentText("Starboard")
                table.cellWidget(0, 3).setText("0")
                if apply:
                    dialog._apply()
                else:
                    dialog.reject()
            except BaseException as exc:
                failures.append(exc)
                dialog.reject()
        QTimer.singleShot(0, lambda: populate_popup(False))
        loadout.equipment_button.click()
        assert not failures and loadout.value() is None
        QTimer.singleShot(0, lambda: populate_popup(True))
        loadout.equipment_button.click()
        if failures:
            raise failures[0]
        form.group_checks["hangar"].setChecked(True)
        assert form.tabs.isTabVisible(form.tabs.indexOf(form.pages["hangar"]))
        form.inputs[("hangar", "starfighter_capacity")].input.setText("2")
        form.group_checks["hangar"].setChecked(False)
        assert not form.tabs.isTabVisible(form.tabs.indexOf(form.pages["hangar"]))
        assert ships.dirty
        with patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.Cancel):
            ships.tree.setCurrentItem(ships.items[1002])
        assert ships.current_id == 1001 and ships.dirty
        ships.save_button.click()
        record = store.read(1001)
        assert record["technical"]["length_m"] == 12.5
        assert len(record["general"]["factions"]) == 2
        assert record["combat"]["weapons"] == [
            {"weapon_id": 1, "quantity": 4, "direction": "Starboard", "ammunition_capacity": 0}]
        assert record["field_visibility"]["hangar"] is False
        assert record["hangar"]["starfighter_capacity"] == 2
        assert not ships.form.tabs.isTabVisible(ships.form.tabs.indexOf(ships.form.pages["hangar"]))
        assert not ships.dirty
        ships.form.inputs[("technical", "atmospheric_capability")].input.setCurrentIndex(2)
        assert ships.dirty
        ships.save_button.click()
        assert store.read(1001)["technical"]["atmospheric_capability"] is False
        path = root / "import.json"
        path.write_bytes(json_bytes({"id": 1001, "general": {"manufacturer": "Test"}}))
        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileNames", return_value=([str(path)], "")), \
                patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.No):
            ships.import_button.click()
        assert store.read(1001)["general"]["manufacturer"] is None
        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileNames", return_value=([str(path)], "")), \
                patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.Yes):
            ships.import_button.click()
        assert store.read(1001)["general"]["manufacturer"] == "Test"
        assert store.read(1001)["combat"]["weapons"] == record["combat"]["weapons"]
        export_path = root / "filtered.json"
        ships.search.setText("Starfighters")
        with patch("app.editors.starships.window.EXPORTS_DIR", root), \
                patch("PySide6.QtWidgets.QInputDialog.getItem", return_value=("Filtered records", True)), \
                patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(export_path), "")):
            ships.export_button.click()
        assert len(store.import_files([export_path])) == 23
        ships.search.clear()
        ships.tree.setCurrentItem(ships.items[10001])
        assert ships.form.tabs.count() == 9 and ("station", "special_function") in ships.form.inputs
        ships.tree.setCurrentItem(ships.items[6002])
        assert ships.form.forms["cargo"].isRowVisible(ships.form.inputs[("cargo", "container_slots")])
        assert not ships.form.tabs.isTabVisible(ships.form.tabs.indexOf(ships.form.pages["hangar"]))
        ships.tree.setCurrentItem(ships.items[11001])
        assert ships.form.tabs.count() == 4 and ("container", "cargo_capacity_cu") in ships.form.inputs
        with patch("PySide6.QtWidgets.QInputDialog.getItem", return_value=("Starships / Starfighters", True)), \
                patch("PySide6.QtWidgets.QInputDialog.getText", return_value=("New craft", True)):
            ships.new_button.click()
        new_id = ships.current_id
        ships.save_button.click()
        assert store.read(new_id)["name"] == "New craft"
        assert len(ships.items) == 97
        ships.form.name.setText("Unsaved")
        with patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.Cancel):
            assert not editor.close()
        with patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.Discard):
            assert editor.close()
        assert store.read(new_id)["name"] == "New craft"
    print("Starship and weapon Qt editor workflows passed.")


if __name__ == "__main__":
    main()
