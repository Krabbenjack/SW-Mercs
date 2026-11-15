"""Nullable Qt input controls and reference editors used by the catalog."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QTableWidget,
    QVBoxLayout, QWidget,
)

from .schema import DIRECTIONS
from .store import CatalogError


def choice(options, blank=True, show_id=False):
    combo = QComboBox()
    if blank:
        combo.addItem("— Unknown —", None)
    for key, name in options.items():
        combo.addItem(f"{key} · {name}" if show_id else name, key)
    return combo


def number(text, integer=False):
    if not text.strip():
        return None
    try:
        return int(text) if integer else float(text)
    except ValueError as exc:
        raise CatalogError(f"Invalid number: {text}") from exc


class ListField(QWidget):
    changed = Signal()

    def __init__(self, options, free_text=False):
        super().__init__()
        self.options = options
        self.free_text = free_text
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.known = QCheckBox("Known / specified")
        layout.addWidget(self.known)
        self.items = QListWidget()
        self.items.setMaximumHeight(105)
        layout.addWidget(self.items)
        controls = QHBoxLayout()
        self.select = choice(options, blank=not free_text, show_id=not free_text)
        self.select.setEditable(free_text)
        if free_text:
            self.select.setCurrentText("")
        self.add_button = QPushButton("Add")
        self.remove_button = QPushButton("Remove")
        controls.addWidget(self.select, 1)
        controls.addWidget(self.add_button)
        controls.addWidget(self.remove_button)
        layout.addLayout(controls)
        self.known.toggled.connect(self._toggle)
        self.add_button.clicked.connect(self._add)
        self.remove_button.clicked.connect(self._remove)

    def _toggle(self, checked):
        for widget in (self.items, self.select, self.add_button, self.remove_button):
            widget.setEnabled(checked)
        self.changed.emit()

    def _append(self, value):
        item = QListWidgetItem(self.options.get(value, str(value)))
        item.setData(Qt.UserRole, value)
        self.items.addItem(item)

    def _add(self):
        value = self.select.currentText().strip() if self.free_text else self.select.currentData()
        if value not in (None, "") and value not in (self.value() or []):
            self._append(value)
            self.changed.emit()

    def _remove(self):
        row = self.items.currentRow()
        if row >= 0:
            self.items.takeItem(row)
            self.changed.emit()

    def set_value(self, values):
        self.items.clear()
        for value in values or []:
            self._append(value)
        self.known.setChecked(values is not None)
        self._toggle(values is not None)

    def value(self):
        if not self.known.isChecked():
            return None
        return [self.items.item(row).data(Qt.UserRole) for row in range(self.items.count())]


class TableField(QWidget):
    changed = Signal()

    def __init__(self, options, weapons):
        super().__init__()
        self.options, self.weapons = options, weapons
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.known = QCheckBox("Known / specified")
        layout.addWidget(self.known)
        headers = ["Weapon", "Count", "Direction", "Ammo capacity"] if weapons else ["Good", "Quantity"]
        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setMinimumHeight(160)
        self.table.setMaximumHeight(260)
        layout.addWidget(self.table)
        controls = QHBoxLayout()
        self.add_button = QPushButton("Add weapon" if weapons else "Add material")
        self.remove_button = QPushButton("Remove row")
        controls.addWidget(self.add_button)
        controls.addWidget(self.remove_button)
        controls.addStretch()
        layout.addLayout(controls)
        if weapons and not options:
            hint = QLabel("Create a weapon in Component Database first.")
            hint.setProperty("role", "hint")
            layout.addWidget(hint)
        self.known.toggled.connect(self._toggle)
        self.add_button.clicked.connect(lambda: self._append({}))
        self.remove_button.clicked.connect(self._remove)

    def _toggle(self, checked):
        self.table.setEnabled(checked)
        self.add_button.setEnabled(checked and bool(self.options))
        self.remove_button.setEnabled(checked)
        self.changed.emit()

    def _append(self, value):
        row = self.table.rowCount()
        self.table.insertRow(row)
        ref = choice(self.options, blank=False, show_id=self.weapons)
        ref.setCurrentIndex(max(0, ref.findData(value.get("weapon_id" if self.weapons else "goods_id"))))
        self.table.setCellWidget(row, 0, ref)
        ref.currentIndexChanged.connect(lambda *_: self.changed.emit())
        count = QLineEdit(str(value.get("quantity", 1)))
        self.table.setCellWidget(row, 1, count)
        count.textChanged.connect(lambda *_: self.changed.emit())
        if self.weapons:
            direction = choice({key: key for key in DIRECTIONS}, blank=False)
            direction.setCurrentIndex(max(0, direction.findData(value.get("direction", "Front"))))
            self.table.setCellWidget(row, 2, direction)
            direction.currentIndexChanged.connect(lambda *_: self.changed.emit())
            ammo = QLineEdit("" if value.get("ammunition_capacity") is None else str(value["ammunition_capacity"]))
            ammo.setPlaceholderText("Unknown")
            self.table.setCellWidget(row, 3, ammo)
            ammo.textChanged.connect(lambda *_: self.changed.emit())
        self.changed.emit()

    def _remove(self):
        row = self.table.currentRow()
        if row < 0:
            row = self.table.rowCount() - 1
        if row >= 0:
            self.table.removeRow(row)
            self.changed.emit()

    def set_value(self, values):
        self.table.setRowCount(0)
        for value in values or []:
            self._append(value)
        self.known.setChecked(values is not None)
        self._toggle(values is not None)

    def value(self):
        if not self.known.isChecked():
            return None
        rows = []
        for row in range(self.table.rowCount()):
            cell = lambda column: self.table.cellWidget(row, column)
            value = {"quantity": number(cell(1).text(), self.weapons)}
            if self.weapons:
                value.update(weapon_id=cell(0).currentData(), direction=cell(2).currentData(),
                             ammunition_capacity=number(cell(3).text(), True))
            else:
                value["goods_id"] = cell(0).currentData()
            rows.append(value)
        return rows


FACTIONS = {text: text for text in ("Galactic Empire", "Rebel Alliance", "Corporate Sector Authority",
                                   "Corporations", "Planetary Militias", "Civilian", "Pirates", "Independent")}


class FieldInput(QWidget):
    changed = Signal()

    def __init__(self, field, store):
        super().__init__()
        self.field = field
        kind = field.kind
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if kind == "long":
            self.input = QPlainTextEdit()
            self.input.setPlaceholderText("Unknown")
            self.input.setMaximumHeight(115)
            self.input.textChanged.connect(lambda *_: self.changed.emit())
        elif kind == "bool":
            self.input = choice({True: "Yes", False: "No"})
            self.input.currentIndexChanged.connect(lambda *_: self.changed.emit())
        elif kind in ("goods", "facility"):
            self.input = choice(store.references(kind))
            self.input.currentIndexChanged.connect(lambda *_: self.changed.emit())
        elif kind in ("strings", "containers", "goods_list"):
            options = FACTIONS if field.key == "factions" else store.references(kind)
            self.input = ListField(options, free_text=kind == "strings")
            self.input.changed.connect(lambda *_: self.changed.emit())
        elif kind in ("weapons", "materials"):
            self.input = TableField(store.references(kind), kind == "weapons")
            self.input.changed.connect(lambda *_: self.changed.emit())
        else:
            self.input = QLineEdit()
            self.input.setPlaceholderText("Unknown")
            self.input.textChanged.connect(lambda *_: self.changed.emit())
        layout.addWidget(self.input)

    def set_value(self, value):
        if isinstance(self.input, (ListField, TableField)):
            self.input.set_value(value)
        elif isinstance(self.input, QComboBox):
            self.input.setCurrentIndex(max(0, self.input.findData(value)))
        elif isinstance(self.input, QPlainTextEdit):
            self.input.setPlainText(value or "")
        else:
            self.input.setText("" if value is None else str(value))

    def value(self):
        if isinstance(self.input, (ListField, TableField)):
            return self.input.value()
        if isinstance(self.input, QComboBox):
            return self.input.currentData()
        if isinstance(self.input, QPlainTextEdit):
            return self.input.toPlainText().strip() or None
        text = self.input.text().strip()
        if self.field.kind in ("int", "number"):
            return number(text, self.field.kind == "int")
        return text or None
