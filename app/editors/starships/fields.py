"""Nullable Qt input controls and reference editors used by the catalog."""
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QTableWidget,
    QVBoxLayout, QWidget, QDialog, QDialogButtonBox, QTableWidgetItem,
    QAbstractItemView, QSplitter, QMessageBox,
)

from .schema import (DIRECTIONS, WEAPON_SIZE_CLASSES, SILHOUETTE_CLASSES, MIN_SHIP_SILHOUETTE,
                     size_label, RANGE_BANDS, MIN_RATING, MAX_RATING)
from .store import CatalogError


def choice(options, blank=True, show_id=False):
    combo = QComboBox()
    if blank:
        combo.addItem("— Unknown —", None)
    for key, name in options.items():
        combo.addItem(f"{key} · {name}" if show_id else name, key)
    return combo


def size_help_button(parent):
    button = QPushButton("?")
    button.setFixedWidth(32)
    button.setToolTip("Explain weapon size classes")
    button.setAccessibleName("Weapon size class help")
    button.clicked.connect(lambda: show_size_help(parent))
    return button


def show_size_help(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Weapon size classes")
    dialog.resize(840, 370)
    layout = QVBoxLayout(dialog)
    hint = QLabel("Size measures the required weapon mount, not damage or quantity. "
                  "A ship can equip weapons up to and including its maximum class. "
                  "Automatic limits are editable game-design defaults; unclassified weapons cannot be newly assigned.")
    hint.setWordWrap(True)
    layout.addWidget(hint)
    table = QTableWidget(len(WEAPON_SIZE_CLASSES), 3)
    table.setHorizontalHeaderLabels(["Class", "Example weapons", "Typical carriers"])
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.verticalHeader().hide()
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
    for row, (size, (_, weapons, carriers)) in enumerate(WEAPON_SIZE_CLASSES.items()):
        for column, value in enumerate((size_label(size), weapons, carriers)):
            table.setItem(row, column, QTableWidgetItem(value))
    table.resizeRowsToContents()
    layout.addWidget(table)
    buttons = QDialogButtonBox(QDialogButtonBox.Close)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.exec()


def show_silhouette_help(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Ship silhouette · FFG")
    dialog.resize(680, 490)
    layout = QVBoxLayout(dialog)
    hint = QLabel("Silhouette describes relative size and mass, not a fixed length. "
                  "The classes are approximate; 10 and higher are for exceptional ships and stations. "
                  "SW-Mercs ships and stations require silhouette 3 or higher; 0–2 are reference only. "
                  "Weapon size limits are separate.")
    hint.setWordWrap(True)
    layout.addWidget(hint)
    table = QTableWidget(len(SILHOUETTE_CLASSES) + 1, 2)
    table.setHorizontalHeaderLabels(["Silhouette", "Typical examples"])
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.verticalHeader().hide()
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
    for row, (size, (name, examples)) in enumerate(SILHOUETTE_CLASSES.items()):
        table.setItem(row, 0, QTableWidgetItem(f"{size} · {name}"))
        table.setItem(row, 1, QTableWidgetItem(examples + (" (reference only)" if size < MIN_SHIP_SILHOUETTE else "")))
    table.setItem(11, 0, QTableWidgetItem("11+ · Custom"))
    table.setItem(11, 1, QTableWidgetItem("Exceptional megastructures / vessels"))
    table.resizeRowsToContents()
    layout.addWidget(table)
    source = QLabel("Reference: Age of Rebellion Core Rulebook, pp. 236, 266–284; labels are editor shorthand.")
    source.setWordWrap(True)
    source.setProperty("role", "muted")
    layout.addWidget(source)
    buttons = QDialogButtonBox(QDialogButtonBox.Close)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.exec()


def show_range_help(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Sensor and weapon range · FFG")
    dialog.resize(500, 340)
    layout = QVBoxLayout(dialog)
    hint = QLabel("Select the maximum effective range band. Sensors and weapons use the same "
                  "ordered scale. Physical distances and combat rules will be defined later.")
    hint.setWordWrap(True)
    layout.addWidget(hint)
    table = QTableWidget(len(RANGE_BANDS), 2)
    table.setHorizontalHeaderLabels(["ID", "Range band"])
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.verticalHeader().hide()
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    for row, (key, label) in enumerate(RANGE_BANDS.items()):
        table.setItem(row, 0, QTableWidgetItem(str(key)))
        table.setItem(row, 1, QTableWidgetItem(label))
    layout.addWidget(table)
    buttons = QDialogButtonBox(QDialogButtonBox.Close)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.exec()


def show_rating_help(parent, key):
    tracking = key == "tracking"
    dialog = QDialog(parent)
    dialog.setWindowTitle("Tracking" if tracking else "Maneuverability")
    dialog.resize(520, 230)
    layout = QVBoxLayout(dialog)
    hint = QLabel(
        "Tracking measures how well a weapon can follow an agile target. "
        "0 = minimal tracking; 10 = excellent tracking." if tracking else
        "Maneuverability measures how well a vessel can change direction and evade fire. "
        "0 = stationary or effectively immobile; 10 = exceptionally agile.")
    hint.setWordWrap(True)
    layout.addWidget(hint)
    scale = QLabel("0–10 · Higher is better. Unknown is distinct from 0. "
                   "Tracking will be compared against target maneuverability in a future combat system; "
                   "no hit chance is calculated yet.")
    scale.setWordWrap(True)
    layout.addWidget(scale)
    buttons = QDialogButtonBox(QDialogButtonBox.Close)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.exec()


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


WEAPON_MIME = "application/x-swmercs-weapon-id"


class WeaponCatalogList(QListWidget):
    def __init__(self, options, eligible, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        for weapon_id, name in options.items():
            item = QListWidgetItem(f"{weapon_id} · {name}")
            item.setData(Qt.UserRole, weapon_id)
            if weapon_id not in eligible:
                item.setFlags(item.flags() & ~(Qt.ItemIsEnabled | Qt.ItemIsDragEnabled))
            self.addItem(item)

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item is None or not item.flags() & Qt.ItemIsEnabled:
            return
        mime = QMimeData()
        mime.setData(WEAPON_MIME, str(item.data(Qt.UserRole)).encode("ascii"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)


class WeaponDropTable(QTableWidget):
    weapon_dropped = Signal(int)

    def __init__(self, options, columns):
        super().__init__(0, columns)
        self.options = options
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.setDefaultDropAction(Qt.CopyAction)
        self.setDropIndicatorShown(True)

    def _weapon_id(self, event):
        if event.mimeData().hasFormat(WEAPON_MIME):
            try:
                weapon_id = int(bytes(event.mimeData().data(WEAPON_MIME)))
                if weapon_id in self.options:
                    return weapon_id
            except (ValueError, TypeError):
                pass
        return None

    def dragEnterEvent(self, event):
        if self._weapon_id(event) is not None:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        weapon_id = self._weapon_id(event)
        if weapon_id is None:
            event.ignore()
            return
        self.weapon_dropped.emit(weapon_id)
        event.setDropAction(Qt.CopyAction)
        event.accept()


class TableField(QWidget):
    changed = Signal()

    def __init__(self, options, weapons, eligible=None):
        super().__init__()
        self.options, self.weapons = options, weapons
        self.eligible = options if eligible is None else eligible
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.known = QCheckBox("Known / specified")
        layout.addWidget(self.known)
        headers = ["Weapon", "Count", "Direction", "Ammo capacity"] if weapons else ["Good", "Quantity"]
        self.table = WeaponDropTable(self.eligible, len(headers)) if weapons else QTableWidget(0, len(headers))
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
        if weapons:
            self.add_button.hide()
            self.table.weapon_dropped.connect(self.add_weapon)

    def _toggle(self, checked):
        self.table.setEnabled(checked or self.weapons)
        self.add_button.setEnabled(checked and bool(self.options))
        self.remove_button.setEnabled(checked)
        self.changed.emit()

    def add_weapon(self, weapon_id):
        if weapon_id in self.eligible:
            self.known.setChecked(True)
            self._append({"weapon_id": weapon_id})

    def _append(self, value):
        row = self.table.rowCount()
        self.table.insertRow(row)
        options = self.options
        if self.weapons:
            options = dict(self.eligible)
            current_id = value.get("weapon_id")
            if current_id in self.options and current_id not in options:
                options[current_id] = self.options[current_id] + " (existing; incompatible)"
        ref = choice(options, blank=False, show_id=self.weapons)
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


class WeaponLoadoutDialog(QDialog):
    """Searchable drag source next to the editable ship equipment drop target."""
    def __init__(self, store, values, parent=None, limit=2):
        super().__init__(parent)
        self.setWindowTitle("Ship equipment · Weapon catalog")
        self.resize(1040, 540)
        self.setMinimumSize(820, 440)
        self.store, self.previous, self.limit = store, values, limit
        self.sizes = store.weapon_sizes()
        options = {key: f"{name} [{size_label(self.sizes[key])}]" for key, name in store.references("weapons").items()}
        eligible = {key: name for key, name in options.items()
                    if self.sizes[key] is not None and self.sizes[key] <= limit}
        layout = QVBoxLayout(self)
        hint = QLabel("Drag a weapon from the catalog onto the ship's equipment. "
                      "Set count, firing direction and ammunition for each mount.")
        hint.setWordWrap(True)
        hint.setProperty("role", "hint")
        layout.addWidget(hint)
        limit_row = QHBoxLayout()
        limit_row.addWidget(QLabel(f"Maximum weapon size: {size_label(limit)} · incompatible weapons are disabled"))
        limit_row.addWidget(size_help_button(self))
        limit_row.addStretch()
        layout.addLayout(limit_row)
        splitter = QSplitter(Qt.Horizontal)
        source = QWidget()
        source_layout = QVBoxLayout(source)
        source_layout.addWidget(QLabel("WEAPON CATALOG"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search weapon name or ID…")
        source_layout.addWidget(self.search)
        self.catalog = WeaponCatalogList(options, eligible)
        for row in range(self.catalog.count()):
            item = self.catalog.item(row)
            stats = store.read(item.data(Qt.UserRole), weapons=True)["weapon"]
            size = self.sizes[item.data(Qt.UserRole)]
            reason = ("Unclassified: assign a size in Component Database first." if size is None
                      else "Too large for this ship." if size > limit else "Compatible size.")
            item.setToolTip(reason + "\n" + ("\n".join(f"{pretty}: {value}" for pretty, value in (
                ("Type", stats["weapon_type"]), ("Damage", stats["damage"]),
                ("Range", RANGE_BANDS.get(stats["range"])), ("Tracking", stats["tracking"]),
                ("Rate of fire", stats["rate_of_fire"]))
                if value is not None) or "No weapon statistics yet"))
        source_layout.addWidget(self.catalog, 1)
        add = QPushButton("Add selected weapon")
        add.setEnabled(bool(eligible))
        source_layout.addWidget(add)
        splitter.addWidget(source)
        target = QWidget()
        target_layout = QVBoxLayout(target)
        target_layout.addWidget(QLabel("SHIP EQUIPMENT · DROP WEAPONS HERE"))
        self.mounts = TableField(options, weapons=True, eligible=eligible)
        self.mounts.table.setMaximumHeight(16777215)
        header = self.mounts.table.horizontalHeader()
        for column, width in ((1, 72), (2, 138), (3, 118)):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width)
        self.mounts.set_value(values)
        target_layout.addWidget(self.mounts, 1)
        splitter.addWidget(target)
        splitter.setSizes([310, 730])
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Apply loadout")
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.result_value = values
        self.search.textChanged.connect(self._filter)
        self.catalog.itemDoubleClicked.connect(lambda item: self.mounts.add_weapon(item.data(Qt.UserRole)))
        add.clicked.connect(self._add_selected)

    def _filter(self, text):
        for row in range(self.catalog.count()):
            item = self.catalog.item(row)
            item.setHidden(text.casefold() not in item.text().casefold())

    def _add_selected(self):
        item = self.catalog.currentItem()
        if item is not None and not item.isHidden():
            self.mounts.add_weapon(item.data(Qt.UserRole))

    def _apply(self):
        try:
            values = self.mounts.value()
            self.store.validate_loadout_sizes(values, self.limit, self.previous, self.sizes)
            for mount in values or []:
                if mount["quantity"] is None or mount["quantity"] <= 0:
                    raise CatalogError("Weapon count must be a positive integer.")
                ammo = mount["ammunition_capacity"]
                if ammo is not None and ammo < 0:
                    raise CatalogError("Ammunition capacity cannot be negative.")
            self.result_value = values
            self.accept()
        except (CatalogError, ValueError) as exc:
            QMessageBox.warning(self, "Invalid equipment", str(exc))


class WeaponField(QWidget):
    changed = Signal()

    def __init__(self, store):
        super().__init__()
        self.store = store
        self.weapon_limit = lambda: 2
        self._values = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.equipment_button = QPushButton("Equipment · Open weapon catalog")
        layout.addWidget(self.equipment_button)
        self.summary = QLabel()
        self.summary.setProperty("role", "muted")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.equipment_button.clicked.connect(self.open_catalog)

    def open_catalog(self):
        dialog = WeaponLoadoutDialog(self.store, self._values, self, limit=self.weapon_limit())
        if dialog.exec() == QDialog.Accepted:
            if dialog.result_value != self._values:
                self.set_value(dialog.result_value)
                self.changed.emit()

    def set_value(self, values):
        self._values = values
        names = self.store.references("weapons")
        if values is None:
            self.summary.setText("Unknown weapon loadout")
        elif not values:
            self.summary.setText("No weapons installed")
        else:
            self.summary.setText("\n".join(
                f"{mount['quantity']} × {names.get(mount['weapon_id'], mount['weapon_id'])} · {mount['direction']}"
                for mount in values))

    def value(self):
        return self._values


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
        elif kind in ("range_band", "rating"):
            self.input = (choice(RANGE_BANDS, show_id=True) if kind == "range_band"
                          else choice({value: str(value) for value in range(MIN_RATING, MAX_RATING + 1)}))
            self.input.currentIndexChanged.connect(lambda *_: self.changed.emit())
            row = QHBoxLayout()
            row.addWidget(self.input, 1)
            self.help_button = QPushButton("?")
            self.help_button.setFixedWidth(32)
            self.help_button.setToolTip(f"Explain {field.label.lower()}")
            self.help_button.setAccessibleName(f"{field.label} help")
            if kind == "range_band":
                self.help_button.clicked.connect(lambda: show_range_help(self))
            else:
                self.help_button.clicked.connect(lambda: show_rating_help(self, field.key))
            row.addWidget(self.help_button)
            layout.addLayout(row)
            return
        elif kind in ("size_class", "size_limit"):
            self.input = choice({size: size_label(size) for size in WEAPON_SIZE_CLASSES})
            self.input.setItemText(0, "Unclassified" if kind == "size_class" else "Automatic")
            self.input.currentIndexChanged.connect(lambda *_: self.changed.emit())
            row = QHBoxLayout()
            row.addWidget(self.input, 1)
            self.help_button = size_help_button(self)
            row.addWidget(self.help_button)
            layout.addLayout(row)
            return
        elif kind == "silhouette":
            self.input = choice({size: f"{size} · {label}" for size, (label, _) in SILHOUETTE_CLASSES.items()
                                 if size >= MIN_SHIP_SILHOUETTE})
            self.input.addItem("11+ · Custom", "custom")
            self.custom_silhouette = QLineEdit("11")
            self.custom_silhouette.setPlaceholderText("Integer ≥ 11")
            self.custom_silhouette.hide()
            self.custom_silhouette.textChanged.connect(lambda *_: self.changed.emit())
            self.input.currentIndexChanged.connect(self._silhouette_changed)
            row = QHBoxLayout()
            row.addWidget(self.input, 1)
            row.addWidget(self.custom_silhouette)
            self.help_button = QPushButton("?")
            self.help_button.setFixedWidth(32)
            self.help_button.setToolTip("Explain FFG silhouettes")
            self.help_button.setAccessibleName("Silhouette help")
            self.help_button.clicked.connect(lambda: show_silhouette_help(self))
            row.addWidget(self.help_button)
            layout.addLayout(row)
            return
        elif kind in ("goods", "facility"):
            self.input = choice(store.references(kind))
            self.input.currentIndexChanged.connect(lambda *_: self.changed.emit())
        elif kind in ("strings", "containers", "goods_list"):
            options = FACTIONS if field.key == "factions" else store.references(kind)
            self.input = ListField(options, free_text=kind == "strings")
            self.input.changed.connect(lambda *_: self.changed.emit())
        elif kind in ("weapons", "materials"):
            self.input = WeaponField(store) if kind == "weapons" else TableField(store.references(kind), False)
            self.input.changed.connect(lambda *_: self.changed.emit())
        else:
            self.input = QLineEdit()
            self.input.setPlaceholderText("Unknown")
            self.input.textChanged.connect(lambda *_: self.changed.emit())
        layout.addWidget(self.input)

    def _silhouette_changed(self, *_):
        self.custom_silhouette.setVisible(self.input.currentData() == "custom")
        self.changed.emit()

    def set_value(self, value):
        if self.field.kind == "silhouette" and value is not None and value > 10:
            self.custom_silhouette.setText(str(value))
            self.input.setCurrentIndex(self.input.findData("custom"))
        elif isinstance(self.input, (ListField, TableField, WeaponField)):
            self.input.set_value(value)
        elif isinstance(self.input, QComboBox):
            self.input.setCurrentIndex(max(0, self.input.findData(value)))
        elif isinstance(self.input, QPlainTextEdit):
            self.input.setPlainText(value or "")
        else:
            self.input.setText("" if value is None else str(value))

    def value(self):
        if self.field.kind == "silhouette" and self.input.currentData() == "custom":
            value = number(self.custom_silhouette.text(), True)
            if value is None or value < 11:
                raise CatalogError("Custom silhouette must be an integer of 11 or higher.")
            return value
        if isinstance(self.input, (ListField, TableField, WeaponField)):
            return self.input.value()
        if isinstance(self.input, QComboBox):
            return self.input.currentData()
        if isinstance(self.input, QPlainTextEdit):
            return self.input.toPlainText().strip() or None
        text = self.input.text().strip()
        if self.field.kind in ("int", "number"):
            return number(text, self.field.kind == "int")
        return text or None
