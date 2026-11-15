"""Starship Database and weapon Component Database."""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFileDialog, QInputDialog, QMessageBox,
    QCheckBox, QGroupBox, QGridLayout,
)

from app.shared.paths import EXPORTS_DIR
from app.shared.theme import apply_theme
from .fields import FieldInput
from .schema import blank_record, sections_for, visibility_groups, group_is_visible, default_weapon_limit, size_label
from .store import CatalogStore, CatalogError


def pretty(key):
    return key.replace("_", " ").title()


class RecordForm(QWidget):
    changed = Signal()

    def __init__(self, record, store):
        super().__init__()
        self.record, self.store = record, store
        self.inputs = {}
        self.forms, self.pages = {}, {}
        self.groups = visibility_groups(record)
        self.visibility_overrides = dict(record.get("field_visibility", {}))
        self.group_checks = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        heading = QLabel(f"{record['id']}  ·  {pretty(record['category'])}")
        heading.setProperty("role", "title")
        layout.addWidget(heading)
        name_row = QFormLayout()
        self.name = QLineEdit(record["name"])
        name_row.addRow("Name", self.name)
        layout.addLayout(name_row)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.cargo_summary = None
        for section, (title, fields) in sections_for(record["object_type"]).items():
            page = QWidget()
            content = QVBoxLayout(page)
            form = QFormLayout()
            form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
            form.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
            form.setRowWrapPolicy(QFormLayout.WrapLongRows)
            form.setVerticalSpacing(12)
            self.forms[section] = form
            content.addLayout(form)
            for field in fields:
                label = QLabel(f"{field.label}" + (f" ({field.unit})" if field.unit else ""))
                label.setWordWrap(True)
                widget = FieldInput(field, store)
                widget.set_value(record[section][field.key])
                self.inputs[(section, field.key)] = widget
                form.addRow(label, widget)
                widget.changed.connect(self._changed)
            if section == "general" and self.groups:
                box = QGroupBox("Optional fields / capabilities")
                grid = QGridLayout(box)
                hint = QLabel("Choose which optional fields to display. Hidden values are preserved.")
                hint.setWordWrap(True)
                hint.setProperty("role", "hint")
                grid.addWidget(hint, 0, 0, 1, 3)
                for index, (key, (label, _, _)) in enumerate(self.groups.items()):
                    check = QCheckBox(label)
                    check.setChecked(group_is_visible(record, key))
                    check.toggled.connect(lambda checked, group=key: self._visibility_changed(group, checked))
                    self.group_checks[key] = check
                    grid.addWidget(check, 1 + index // 3, index % 3)
                content.insertWidget(0, box)
            if section == "cargo":
                self.cargo_summary = QLabel()
                self.cargo_summary.setProperty("role", "section")
                self.cargo_summary.setWordWrap(True)
                content.addWidget(self.cargo_summary)
            content.addStretch()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            scroll.setObjectName("recordScroll")
            self.tabs.addTab(scroll, title)
            self.pages[section] = scroll
        self.name.textChanged.connect(self._changed)
        if ("combat", "max_weapon_size_class") in self.inputs:
            limit_input = self.inputs[("combat", "max_weapon_size_class")]
            default = default_weapon_limit(record)
            limit_input.input.setItemText(0, f"Automatic · {size_label(default)}")
            self.inputs[("combat", "weapons")].input.weapon_limit = (
                lambda: limit_input.value() if limit_input.value() is not None else default)
        self._apply_visibility()
        self._update_cargo()

    def _visibility_changed(self, group, checked):
        self.visibility_overrides[group] = checked
        self._apply_visibility()
        self.changed.emit()

    def _apply_visibility(self):
        for group, (_, _, fields) in self.groups.items():
            visible = self.group_checks[group].isChecked()
            for section, key in fields:
                widget = self.inputs.get((section, key))
                if widget is not None:
                    self.forms[section].setRowVisible(widget, visible)
        if "hangar" in self.pages:
            visible = self.group_checks["hangar"].isChecked() or self.group_checks["repair"].isChecked()
            self.tabs.setTabVisible(self.tabs.indexOf(self.pages["hangar"]), visible)

    def _changed(self, *args):
        self._update_cargo()
        self.changed.emit()

    def _update_cargo(self):
        if self.cargo_summary is None:
            return
        try:
            get = lambda key: self.inputs[("cargo", key)].value()
            internal, external = get("internal_cargo_cu"), get("external_cargo_cu")
            total = internal + external if internal is not None and external is not None else None
            summary = f"Total nominal cargo: {total:g} CU" if total is not None else "Total nominal cargo: unknown"
            slots, containers = get("container_slots"), get("compatible_containers")
            if slots is not None and containers:
                capacities = []
                for container_id in containers:
                    capacity = self.store.read(container_id)["container"]["cargo_capacity_cu"]
                    if capacity is not None:
                        capacities.append(capacity * slots)
                if len(capacities) == len(containers):
                    low, high = min(capacities), max(capacities)
                    summary += f" | Fitted container capacity: {low:g}" + (f"–{high:g}" if low != high else "") + " CU"
                    if external is not None and not low <= external <= high:
                        summary += " (check nominal external capacity)"
            self.cargo_summary.setText(summary)
        except (CatalogError, OSError, ValueError, TypeError):
            self.cargo_summary.setText("Total nominal cargo: check values")

    def value(self):
        result = dict(self.record)
        result["name"] = self.name.text().strip()
        if self.visibility_overrides:
            result["field_visibility"] = dict(self.visibility_overrides)
        for (section, key), widget in self.inputs.items():
            if section not in result or result[section] is self.record[section]:
                result[section] = dict(result.get(section, {}))
            result[section][key] = widget.value()
        return result


class CatalogPanel(QWidget):
    def __init__(self, store, weapons=False):
        super().__init__()
        self.store, self.weapons = store, weapons
        self.current_id = None
        self.form = None
        self.dirty = False
        self._changing = False
        layout = QVBoxLayout(self)
        tools = QHBoxLayout()
        self.new_button = QPushButton("+ New entry")
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("primary")
        self.import_button = QPushButton("Import JSON")
        self.export_button = QPushButton("Export JSON")
        for button in (self.new_button, self.save_button, self.import_button, self.export_button):
            tools.addWidget(button)
        tools.addStretch()
        self.status = QLabel()
        self.status.setProperty("role", "muted")
        tools.addWidget(self.status)
        layout.addLayout(tools)
        self.splitter = QSplitter(Qt.Horizontal)
        sidebar = QWidget()
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 0, 0, 0)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name, ID or category…")
        side.addWidget(self.search)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumWidth(260)
        side.addWidget(self.tree)
        self.splitter.addWidget(sidebar)
        self.detail = QWidget()
        self.detail_layout = QVBoxLayout(self.detail)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.detail)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([320, 850])
        layout.addWidget(self.splitter, 1)
        self.tree.currentItemChanged.connect(self._select)
        self.search.textChanged.connect(self._filter)
        self.new_button.clicked.connect(self.new_record)
        self.save_button.clicked.connect(self.save_record)
        self.import_button.clicked.connect(self.import_records)
        self.export_button.clicked.connect(self.export_records)
        self.refresh()

    def _error(self, title, error):
        QMessageBox.critical(self, title, str(error))

    def _status(self):
        count = len(self.items)
        self.status.setText(f"{count} records" + ("  ·  Unsaved changes" if self.dirty else ""))
        self.save_button.setEnabled(self.form is not None and self.dirty)

    def _mark_dirty(self):
        self.dirty = True
        self._status()

    def _show_form(self, record=None, new=False):
        if self.form is not None:
            self.detail_layout.removeWidget(self.form)
            self.form.deleteLater()
            self.form = None
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if record is None:
            hint = QLabel("Select a record or create a new one.")
            hint.setProperty("role", "hint")
            hint.setAlignment(Qt.AlignCenter)
            self.detail_layout.addWidget(hint, 1)
            self.current_id = None
        else:
            self.form = RecordForm(record, self.store)
            self.form.changed.connect(self._mark_dirty)
            self.detail_layout.addWidget(self.form)
            self.current_id = record["id"]
        self.dirty = new
        self._status()

    def refresh(self, select_id=None):
        previous_tab = (self.form.tabs.currentIndex()
                        if self.form is not None and self.current_id == select_id else 0)
        self._changing = True
        try:
            self.tree.clear()
            self.items = {}
            groups = {}
            categories = {}
            entries = self.store.listing(self.weapons)
            for record_id, (object_type, category, name) in sorted(entries.items()):
                if object_type not in groups:
                    group = QTreeWidgetItem([pretty(object_type)])
                    group.setFlags(group.flags() & ~Qt.ItemIsSelectable)
                    self.tree.addTopLevelItem(group)
                    groups[object_type] = group
                key = (object_type, category)
                if key not in categories:
                    item = QTreeWidgetItem([pretty(category)])
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                    groups[object_type].addChild(item)
                    categories[key] = item
                item = QTreeWidgetItem([f"{record_id}  ·  {name}"])
                item.setData(0, Qt.UserRole, record_id)
                categories[key].addChild(item)
                self.items[record_id] = item
            self.tree.expandAll()
            self._filter(self.search.text())
            if select_id not in entries:
                select_id = next(iter(sorted(entries)), None)
            if select_id is not None:
                self.tree.setCurrentItem(self.items[select_id])
                self._show_form(self.store.read(select_id, self.weapons))
                self.form.tabs.setCurrentIndex(min(previous_tab, self.form.tabs.count() - 1))
            else:
                self._show_form()
        finally:
            self._changing = False

    def _filter(self, text):
        text = text.strip().casefold()
        entries = self.store.listing(self.weapons)
        for record_id, item in self.items.items():
            object_type, category, name = entries[record_id]
            haystack = f"{record_id} {name} {pretty(object_type)} {pretty(category)}".casefold()
            item.setHidden(text not in haystack)
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            for j in range(group.childCount()):
                category = group.child(j)
                category.setHidden(all(category.child(k).isHidden() for k in range(category.childCount())))
            group.setHidden(all(group.child(k).isHidden() for k in range(group.childCount())))

    def _select(self, item, previous):
        if self._changing or item is None:
            return
        record_id = item.data(0, Qt.UserRole)
        if record_id is None or record_id == self.current_id:
            return
        old = self.current_id
        if not self.confirm_leave():
            self._changing = True
            self.tree.setCurrentItem(self.items.get(old))
            self._changing = False
            return
        try:
            record = self.store.read(record_id, self.weapons)
            self._changing = True
            self.tree.setCurrentItem(self.items[record_id])
            self._show_form(record)
        except (CatalogError, OSError, ValueError) as exc:
            self._error("Cannot load record", exc)
        finally:
            self._changing = False

    def confirm_leave(self):
        if not self.dirty:
            return True
        answer = QMessageBox.question(self, "Unsaved changes", "Save the current record before continuing?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                      QMessageBox.Save)
        if answer == QMessageBox.Save:
            return self.save_record()
        if answer == QMessageBox.Discard:
            self.refresh(self.current_id)
            return True
        return False

    def new_record(self):
        if not self.confirm_leave():
            return
        if self.weapons:
            object_type = category = "weapons"
        else:
            categories = {f"{pretty(kind)} / {pretty(cat)}": (kind, cat)
                          for kind, group in self.store.enum.items() for cat in group}
            selected, ok = QInputDialog.getItem(self, "New record", "Category", list(categories), 0, False)
            if not ok:
                return
            object_type, category = categories[selected]
        name, ok = QInputDialog.getText(self, "New record", "Name")
        if not ok or not name.strip():
            return
        try:
            record_id = self.store.allocate(object_type, category)
            self._changing = True
            self.tree.setCurrentItem(None)
            self._changing = False
            self._show_form(blank_record(object_type, category, record_id, name.strip()), new=True)
        except (CatalogError, OSError, ValueError) as exc:
            self._error("Cannot create record", exc)

    def save_record(self):
        if self.form is None:
            return False
        try:
            record = self.form.value()
            self.store.save([record], self.weapons)
            self.refresh(record["id"])
            self.status.setText(f"Saved {record['id']} · {record['name']}")
            return True
        except (CatalogError, OSError, ValueError, TypeError) as exc:
            self._error("Cannot save record", exc)
            return False

    def import_records(self):
        if not self.confirm_leave():
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Import JSON records", "", "JSON (*.json)")
        if not paths:
            return
        try:
            records = self.store.import_files(paths, self.weapons)
            existing = self.store.listing(self.weapons)
            overlaps = [record for record in records if record["id"] in existing]
            if overlaps:
                answer = QMessageBox.question(self, "Confirm import",
                    f"Import {len(records)} record(s), updating {len(overlaps)} existing ID(s)? "
                    "Fields provided in the import replace existing values. Omitted fields are preserved.",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if answer != QMessageBox.Yes:
                    return
            self.store.save(records, self.weapons)
            self.refresh(records[0]["id"])
            self.status.setText(f"Imported {len(records)} records")
        except (CatalogError, OSError, ValueError, TypeError) as exc:
            self._error("Import failed", exc)

    def export_records(self):
        if not self.confirm_leave():
            return
        modes = ["Current record", "Filtered records", "All records"] if self.current_id else ["All records"]
        mode, ok = QInputDialog.getItem(self, "Export", "Records to export", modes, 0, False)
        if not ok:
            return
        if mode == "Current record":
            ids = [self.current_id]
        elif mode == "Filtered records":
            ids = sorted(key for key, item in self.items.items() if not item.isHidden())
        else:
            ids = sorted(self.store.listing(self.weapons))
        if not ids:
            QMessageBox.information(self, "Export", "No records to export.")
            return
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        default = f"{ids[0]}.json" if len(ids) == 1 else "weapons.json" if self.weapons else "starship_catalog.json"
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", str(EXPORTS_DIR / default), "JSON (*.json)")
        if path:
            try:
                self.store.export(Path(path).with_suffix(".json"), ids, self.weapons)
                self.status.setText(f"Exported {len(ids)} records")
            except (CatalogError, OSError, ValueError) as exc:
                self._error("Export failed", exc)


class StarshipEditor(QMainWindow):
    def __init__(self, store=None):
        super().__init__()
        self.store = store or CatalogStore()
        self.setWindowTitle("SW-Mercs · Starship Editor")
        self.resize(1200, 800)
        self.setMinimumSize(850, 550)
        central = QWidget()
        layout = QVBoxLayout(central)
        title = QLabel("STARSHIP & COMPONENT DATABASE")
        title.setObjectName("databaseHeading")
        layout.addWidget(title)
        self.tabs = QTabWidget()
        self.ship_panel = CatalogPanel(self.store)
        self.weapon_panel = CatalogPanel(self.store, weapons=True)
        self.tabs.addTab(self.ship_panel, "Starship Database")
        self.tabs.addTab(self.weapon_panel, "Component Database · Weapons")
        layout.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        self._active = 0
        self.tabs.currentChanged.connect(self._switch)
        apply_theme(self, "starships")

    def _switch(self, index):
        old = self.tabs.widget(self._active)
        if not old.confirm_leave():
            self.tabs.blockSignals(True)
            self.tabs.setCurrentIndex(self._active)
            self.tabs.blockSignals(False)
            return
        self._active = index
        panel = self.tabs.widget(index)
        panel.refresh(panel.current_id)

    def closeEvent(self, event):
        if self.ship_panel.confirm_leave() and self.weapon_panel.confirm_leave():
            event.accept()
        else:
            event.ignore()
