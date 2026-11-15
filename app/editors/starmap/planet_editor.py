"""Planet and moon management for the system statistics sidebar."""
from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QInputDialog, QMessageBox, QComboBox,
)

from .systems import MoonData, PlanetData, PLANET_TYPES


class PlanetEditor(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.system = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for title, attr, callbacks in (
            ("Planets", "planet", (self.add_planet, self.rename_planet, self.delete_planet)),
            ("Moons of selected planet", "moon", (self.add_moon, self.rename_moon, self.delete_moon)),
        ):
            label = QLabel(title)
            label.setProperty("role", "section")
            layout.addWidget(label)
            items = QListWidget()
            items.setMaximumHeight(96)
            items.setMinimumWidth(0)
            setattr(self, f"{attr}_list", items)
            layout.addWidget(items)
            row = QHBoxLayout()
            for name, callback in zip(("Add", "Rename", "Delete"), callbacks):
                button = QPushButton(name)
                button.setAccessibleName(f"{name} {attr}")
                button.clicked.connect(callback)
                setattr(self, f"{attr}_{name.lower()}_button", button)
                row.addWidget(button)
            layout.addLayout(row)
            if attr == "planet":
                layout.addWidget(QLabel("Planet type:"))
                self.type_combo = QComboBox()
                self.type_combo.addItem("Unknown / unspecified", None)
                for key, name in PLANET_TYPES.items():
                    self.type_combo.addItem(name, key)
                layout.addWidget(self.type_combo)
        self.planet_list.currentItemChanged.connect(lambda *_: self.refresh_moons())
        self.moon_list.currentItemChanged.connect(lambda *_: self._update_buttons())
        self.type_combo.currentIndexChanged.connect(self.change_type)
        self.set_system(None)

    @staticmethod
    def _selected_id(widget):
        item = widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    @staticmethod
    def _fill(widget, records, selected_id=None):
        with QSignalBlocker(widget):
            widget.clear()
            for record in records:
                item = QListWidgetItem(record.name)
                item.setData(Qt.UserRole, record.id)
                widget.addItem(item)
                if record.id == selected_id:
                    widget.setCurrentItem(item)
            if widget.currentItem() is None and widget.count():
                widget.setCurrentRow(0)

    def selected_planet(self):
        selected_id = self._selected_id(self.planet_list)
        return next((p for p in self.system.planets if p.id == selected_id), None) if self.system else None

    def selected_moon(self):
        planet = self.selected_planet()
        selected_id = self._selected_id(self.moon_list)
        return next((m for m in planet.moons if m.id == selected_id), None) if planet else None

    def set_system(self, system):
        selected = self._selected_id(self.planet_list) if system is self.system else None
        self.system = system
        self.refresh_planets(selected)

    def refresh_planets(self, selected_id=None):
        self._fill(self.planet_list, self.system.planets if self.system else [], selected_id)
        self.refresh_moons()

    def refresh_moons(self, selected_id=None):
        planet = self.selected_planet()
        self._fill(self.moon_list, planet.moons if planet else [], selected_id)
        with QSignalBlocker(self.type_combo):
            self.type_combo.setCurrentIndex(max(0, self.type_combo.findData(planet.planet_type if planet else None)))
        self._update_buttons()

    def _update_buttons(self):
        has_planet = self.selected_planet() is not None
        has_moon = self.selected_moon() is not None
        self.planet_add_button.setEnabled(self.system is not None)
        self.planet_rename_button.setEnabled(has_planet)
        self.planet_delete_button.setEnabled(has_planet)
        self.type_combo.setEnabled(has_planet)
        self.moon_add_button.setEnabled(has_planet)
        self.moon_rename_button.setEnabled(has_moon)
        self.moon_delete_button.setEnabled(has_moon)

    def _ask_name(self, title, value=""):
        name, ok = QInputDialog.getText(self, title, "Name:", text=value)
        return name.strip() if ok and name.strip() else None

    def add_planet(self):
        if self.system is None:
            return
        name = self._ask_name("Add planet")
        if name:
            planet = PlanetData.create_new(name)
            self.system.planets.append(planet)
            self.refresh_planets(planet.id)
            self.changed.emit()

    def rename_planet(self):
        planet = self.selected_planet()
        if planet:
            name = self._ask_name("Rename planet", planet.name)
            if name and name != planet.name:
                planet.name = name
                self.refresh_planets(planet.id)
                self.changed.emit()

    def delete_planet(self):
        planet = self.selected_planet()
        if planet and QMessageBox.question(
                self, "Delete planet", f"Delete {planet.name} and its {len(planet.moons)} moon(s)?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.system.planets.remove(planet)
            self.refresh_planets()
            self.changed.emit()

    def change_type(self, _index):
        planet = self.selected_planet()
        if planet:
            value = self.type_combo.currentData()
            if planet.planet_type != value:
                planet.planet_type = value
                self.changed.emit()

    def add_moon(self):
        planet = self.selected_planet()
        if planet:
            name = self._ask_name("Add moon")
            if name:
                moon = MoonData.create_new(name)
                planet.moons.append(moon)
                self.refresh_moons(moon.id)
                self.changed.emit()

    def rename_moon(self):
        moon = self.selected_moon()
        if moon:
            name = self._ask_name("Rename moon", moon.name)
            if name and name != moon.name:
                moon.name = name
                self.refresh_moons(moon.id)
                self.changed.emit()

    def delete_moon(self):
        planet, moon = self.selected_planet(), self.selected_moon()
        if planet and moon and QMessageBox.question(
                self, "Delete moon", f"Delete {moon.name}?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            planet.moons.remove(moon)
            self.refresh_moons()
            self.changed.emit()
