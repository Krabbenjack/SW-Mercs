"""Static, spatial in-system map. Coordinates are grid cells, not galactic HSU."""
import copy
import json
from app.shared.paths import DATA_DIR
import math
import uuid

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QPixmap, QIcon, QPolygonF, QPainterPath
from PySide6.QtWidgets import (
    QDialog, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel,
    QPushButton, QListWidget, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsTextItem, QDoubleSpinBox, QMessageBox,
    QInputDialog, QDialogButtonBox, QGraphicsItem, QLineEdit,
)
from app.editors.starmap.data_loader import get_data_loader

CELL_PX = 32


def sun_polygon(cx=0, cy=0, outer_radius=12, inner_radius=8, points=12):
    """Return alternating outer/inner vertices for a 12-pointed star."""
    return QPolygonF([
        QPointF(cx + (outer_radius if i % 2 == 0 else inner_radius)
                * math.cos(i * math.pi / points - math.pi / 2),
                cy + (outer_radius if i % 2 == 0 else inner_radius)
                * math.sin(i * math.pi / points - math.pi / 2))
        for i in range(points * 2)
    ])


def military_facility_ids():
    """Military facilities use red; all other facilities default to civilian blue."""
    with (DATA_DIR / "facilities" / "facility_flags.json").open(encoding="utf-8") as handle:
        categories = json.load(handle)["categories"]
    return set(categories.get("military", [])) | {"military_science_lab"}


def facility_color(facility_id):
    return "#e84d55" if facility_id in military_facility_ids() else "#438ee8"


def body_color(kind, planet_type=None, facility_id=None):
    if kind == "moon":
        return "#c7d2dd"
    if kind == "facility":
        return facility_color(facility_id)
    return {"desert": "#edc34b", "temperate": "#55bb78",
            "ice": "#89d9f4", "gas_giant": "#b69ce6"}.get(planet_type, "#8c9dab")


def draw_symbol(painter, kind, x, y, radius, planet_type=None, facility_id=None):
    color = QColor(body_color(kind, planet_type, facility_id))
    painter.setPen(QPen(color.lighter(125), 1))
    painter.setBrush(QBrush(color))
    if kind == "facility":
        from PySide6.QtGui import QPolygonF
        painter.drawPolygon(QPolygonF([
            QPointF(x, y-radius), QPointF(x-radius, y+radius),
            QPointF(x+radius, y+radius)]))
    else:
        painter.drawEllipse(QPointF(x, y), radius, radius)

def allowed_placements(facility_id):
    path = DATA_DIR / "facilities" / "facility_placements.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)["placements"].get(facility_id, [])


DEFAULT_MAP = {"cell_au": 0.1, "habitable_inner_au": 0.8,
               "habitable_outer_au": 1.5, "system_border_au": 5.0, "objects": []}


def grid_cell(x, y, cell_au, border_au):
    n = math.ceil(border_au / cell_au)
    col, row = math.floor(x) + n + 1, math.floor(y) + n + 1
    digits = max(2, len(str(2 * n + 1)))
    return f"{col:0{digits}d}{row:0{digits}d}", x % 1, y % 1


def cell_key(x, y):
    """Stable sparse storage key within the current grid scale."""
    return f"{math.floor(x)},{math.floor(y)}"


def rescale_cell_metadata(cells, old_scale, new_scale):
    """Map annotated cell centers to the new grid, preserving all annotations."""
    updated = {}
    for key, metadata in cells.items():
        try:
            col, row = (int(v) for v in key.split(","))
        except (ValueError, AttributeError):
            continue
        target = cell_key((col + 0.5) * old_scale / new_scale,
                          (row + 0.5) * old_scale / new_scale)
        if target in updated:
            # Keep both names when several former cells merge.
            existing = updated[target].get("name", "")
            incoming = metadata.get("name", "")
            if incoming and incoming not in existing.split(" / "):
                updated[target]["name"] = " / ".join(filter(None, (existing, incoming)))
        else:
            updated[target] = {"name": metadata.get("name", "")}
    return updated


def clear_cell_facilities(data, col, row):
    """Remove facilities in one grid cell; leave celestial bodies untouched."""
    before = len(data["objects"])
    data["objects"] = [
        obj for obj in data["objects"]
        if obj["kind"] != "facility" or
        (math.floor(obj["x"]), math.floor(obj["y"])) != (col, row)
    ]
    data.setdefault("cells", {}).pop(cell_key(col, row), None)
    return before - len(data["objects"])


def distance_au(a, b, cell_au):
    return math.hypot(a[0] - b[0], a[1] - b[1]) * cell_au


def environment_at(data, x, y):
    """Sparse lookup; the most specific facility wins over orbital/empty space."""
    candidates = []
    for obj in data.get("objects", []):
        if obj.get("placement") == "surface":
            continue
        radius = float(obj.get("influence_cells", 0))
        if math.hypot(obj["x"] - x, obj["y"] - y) <= radius:
            kind = obj["kind"]
            priority = {"facility": 3, "planet": 2, "moon": 2,
                        "asteroid_field": 1}.get(kind, 0)
            if priority:
                candidates.append((priority, kind))
    if not candidates:
        return "deep_space"
    kind = max(candidates)[1]
    return {"facility": "station", "planet": "orbital",
            "moon": "orbital", "asteroid_field": "asteroid_field"}[kind]


class SourceList(QListWidget):
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            item = self.itemAt(event.position().toPoint())
            if item is not None:
                self.setCurrentItem(item)
                self.window().arm_source(item.data(Qt.UserRole))


class SystemCanvas(QGraphicsView):
    def __init__(self, owner):
        self.scene_model = QGraphicsScene()
        super().__init__(self.scene_model)
        self.owner = owner
        self._pan_origin = None
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setSceneRect(-1200, -1200, 2400, 2400)
        self.redraw()

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#0b1526"))
        border = self.owner.working["system_border_au"] / self.owner.working["cell_au"] * CELL_PX
        painter.save()
        clip = QPainterPath()
        clip.addEllipse(QPointF(0, 0), border, border)
        painter.setClipPath(clip)
        painter.setPen(QPen(QColor("#263449"), 0))
        left = math.floor(rect.left() / CELL_PX)
        right = math.ceil(rect.right() / CELL_PX)
        top = math.floor(rect.top() / CELL_PX)
        bottom = math.ceil(rect.bottom() / CELL_PX)
        for x in range(left, right + 1):
            painter.drawLine(x * CELL_PX, rect.top(), x * CELL_PX, rect.bottom())
        for y in range(top, bottom + 1):
            painter.drawLine(rect.left(), y * CELL_PX, rect.right(), y * CELL_PX)
        painter.restore()

    def redraw(self):
        self.scene_model.clear()
        data = self.owner.working
        if self.owner.selected_cell is not None:
            cx, cy = self.owner.selected_cell
            selection = self.scene_model.addRect(cx*CELL_PX, cy*CELL_PX,
                CELL_PX, CELL_PX, QPen(QColor("#f7c65e"), 2),
                QBrush(QColor(247, 198, 94, 55)))
            selection.setZValue(5)
        border = data["system_border_au"] / data["cell_au"] * CELL_PX
        self.setSceneRect(-border, -border, 2 * border, 2 * border)
        self.scene_model.addEllipse(-border, -border, 2*border, 2*border,
            QPen(QColor("#86b8d9"), 2), QBrush(Qt.NoBrush))
        scale = data["cell_au"]
        inner = data["habitable_inner_au"] / scale * CELL_PX
        outer = data["habitable_outer_au"] / scale * CELL_PX
        self.scene_model.addEllipse(-outer, -outer, 2*outer, 2*outer,
            QPen(QColor("#44885b"), 1), QBrush(Qt.NoBrush))
        self.scene_model.addEllipse(-inner, -inner, 2*inner, 2*inner,
            QPen(QColor("#44885b"), 1), QBrush(Qt.NoBrush))
        sun = self.scene_model.addPolygon(sun_polygon(),
            QPen(QColor("#ffe69a"), 1.4), QBrush(QColor("#ffbd3d")))
        sun.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        for obj in data["objects"]:
            x, y = obj["x"]*CELL_PX, obj["y"]*CELL_PX
            color = body_color(obj["kind"], self.owner.planet_type_for(
                obj["kind"] + ":" + obj["ref_id"]), obj["ref_id"])
            if obj["kind"] == "facility":
                from PySide6.QtGui import QPolygonF
                polygon = QPolygonF([QPointF(0, -10), QPointF(-10, 9),
                                     QPointF(10, 9)])
                marker = self.scene_model.addPolygon(polygon, QPen(QColor(color)), QBrush(QColor(color)))
            else:
                marker = self.scene_model.addEllipse(-8, -8, 16, 16,
                    QPen(QColor(color)), QBrush(QColor(color)))
            marker.setPos(x, y)
            marker.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            label = self.scene_model.addText(obj["name"])
            label.setDefaultTextColor(QColor("#e7edf6"))
            label.setPos(x+10, y-12)
            label.setFlag(QGraphicsItem.ItemIgnoresTransformations)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._pan_origin = event.position().toPoint()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.RightButton:
            point = self.mapToScene(event.position().toPoint())
            self.owner.arm_map_object(point.x() / CELL_PX, point.y() / CELL_PX,
                                      12 / (CELL_PX * self.transform().m11()))
            event.accept()
            return
        if event.button() == Qt.LeftButton and self.owner.armed_payload:
            point = self.mapToScene(event.position().toPoint())
            self.owner.place(self.owner.armed_payload,
                             point.x() / CELL_PX, point.y() / CELL_PX)
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            point = self.mapToScene(event.position().toPoint())
            self.owner.select_cell(point.x() / CELL_PX, point.y() / CELL_PX)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_origin is not None:
            current = event.position().toPoint()
            delta = current - self._pan_origin
            self._pan_origin = current
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        if self.owner.armed_payload:
            point = self.mapToScene(event.position().toPoint())
            self.owner.status.setText(
                f"Ready to place at ({point.x()/CELL_PX:.2f}, {point.y()/CELL_PX:.2f}) — "
                "left click to place; Esc to cancel")
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._pan_origin is not None:
            self._pan_origin = None
            if self.owner.armed_payload:
                self.viewport().setCursor(Qt.CrossCursor)
            else:
                self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15
        self.scale(factor, factor)


class SystemMapDialog(QDialog):
    """Edits a working copy. Accept commits to SystemData; Cancel discards it."""
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.armed_payload = None
        self.moving_id = None
        self.original = copy.deepcopy(getattr(system, "system_map", None) or DEFAULT_MAP)
        self.working = copy.deepcopy(self.original)
        self.working.setdefault("system_border_au", max(5.0, self.working["habitable_outer_au"] * 2))
        self.working.setdefault("cells", {})
        self.selected_cell = None
        self.setWindowTitle("System Map — " + system.name)
        self.resize(1150, 750)
        layout = QHBoxLayout(self)
        sidebar = QWidget()
        side = QVBoxLayout(sidebar)
        side.addWidget(QLabel("Right-click a list or map object to pick it up; left-click the grid to place. Esc cancels."))
        self.sources = SourceList()
        self.sources.setContextMenuPolicy(Qt.NoContextMenu)
        side.addWidget(self.sources)
        self._populate_sources()
        settings = QFormLayout()
        self.cell = QDoubleSpinBox()
        self.cell.setDecimals(5)
        self.cell.setRange(0.00001, 10000)
        self.cell.setSuffix(" AU / cell")
        self.cell.setValue(self.working["cell_au"])
        self.cell.valueChanged.connect(self.update_scale)
        settings.addRow("Grid scale", self.cell)
        self.inner = QDoubleSpinBox()
        self.outer = QDoubleSpinBox()
        for spin, key in ((self.inner, "habitable_inner_au"),
                          (self.outer, "habitable_outer_au")):
            spin.setRange(0, 100000)
            spin.setDecimals(3)
            spin.setValue(self.working[key])
            spin.valueChanged.connect(self.update_zone)
        settings.addRow("Habitable inner (AU)", self.inner)
        settings.addRow("Habitable outer (AU)", self.outer)
        self.border = QDoubleSpinBox()
        self.border.setDecimals(3)
        self.border.setRange(0.001, 100000)
        self.border.setSuffix(" AU")
        self.border.setValue(self.working["system_border_au"])
        self.border.valueChanged.connect(self.update_border)
        settings.addRow("System border", self.border)
        side.addLayout(settings)
        side.addWidget(QLabel("Selected grid cell"))
        self.cell_id_label = QLabel("None")
        side.addWidget(self.cell_id_label)
        self.cell_name = QLineEdit()
        self.cell_name.setPlaceholderText("Cell name (optional)")
        self.cell_name.editingFinished.connect(self.save_cell_metadata)
        side.addWidget(self.cell_name)
        self.clear_cell_button = QPushButton("Clear Cell")
        self.clear_cell_button.clicked.connect(self.clear_selected_cell)
        side.addWidget(self.clear_cell_button)
        self.status = QLabel("Star at (0,0); positions are static")
        self.status.setWordWrap(True)
        side.addWidget(self.status)
        self.remove_button = QPushButton("Remove last placement")
        self.remove_button.clicked.connect(self.remove_last)
        side.addWidget(self.remove_button)
        side.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        side.addWidget(buttons)
        layout.addWidget(sidebar, 1)
        self.canvas = SystemCanvas(self)
        layout.addWidget(self.canvas, 4)
        self.load_selected_cell()

    def planet_type_for(self, payload):
        kind, ref = payload.split(":", 1)
        if kind == "planet":
            return next((p.planet_type for p in self.system.planets if p.id == ref), None)
        return None

    def arm_source(self, payload):
        self.moving_id = None
        self.armed_payload = payload
        self.status.setText("Picked up: " + payload.replace(":", " — ") +
                            " | Left-click the grid to place; Esc cancels.")
        self.canvas.viewport().setCursor(Qt.CrossCursor)

    def arm_map_object(self, x, y, hit_radius=0.65):
        """Pick the nearest existing marker; preserve its placement UUID."""
        candidates = [(math.hypot(obj["x"] - x, obj["y"] - y), obj)
                      for obj in self.working["objects"]]
        if not candidates:
            return
        distance, obj = min(candidates, key=lambda entry: entry[0])
        if distance > hit_radius:
            return
        self.arm_source(obj["kind"] + ":" + obj["ref_id"])
        self.moving_id = obj["id"]
        self.status.setText("Moving " + obj["name"] +
                            " — left-click to relocate; Esc cancels.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.armed_payload:
            self.armed_payload = None
            self.moving_id = None
            self.canvas.viewport().unsetCursor()
            self.status.setText("Placement cancelled")
            event.accept()
            return
        super().keyPressEvent(event)

    def _populate_sources(self):
        from PySide6.QtWidgets import QListWidgetItem
        for planet in self.system.planets:
            self._add_source("Planet: " + planet.name, "planet:" + planet.id)
            for moon in planet.moons:
                self._add_source("  Moon: " + moon.name, "moon:" + moon.id)
        categories = get_data_loader().get_facility_categories()
        authorized = set(self.system.facilities)
        for category, ids in categories.items():
            for facility_id in ids:
                if facility_id in authorized:
                    self._add_source("Facility: " + facility_id.replace("_", " "),
                                     "facility:" + facility_id)

    def _add_source(self, label, payload):
        from PySide6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, payload)
        icon = QPixmap(18, 18)
        icon.fill(Qt.transparent)
        painter = QPainter(icon)
        draw_symbol(painter, payload.split(":", 1)[0], 9, 9, 7,
                    self.planet_type_for(payload),
                    payload.split(":", 1)[1] if payload.startswith("facility:") else None)
        painter.end()
        item.setIcon(QIcon(icon))
        item.setToolTip("Right-click to pick up, then left-click on grid")
        self.sources.addItem(item)

    def update_scale(self):
        old_scale = self.working["cell_au"]
        new_scale = self.cell.value()
        if old_scale == new_scale:
            return
        for obj in self.working["objects"]:
            obj["x"] *= old_scale / new_scale
            obj["y"] *= old_scale / new_scale
            if "influence_cells" in obj:
                obj["influence_cells"] *= old_scale / new_scale
        self.working["cells"] = rescale_cell_metadata(
            self.working["cells"], old_scale, new_scale)
        if self.selected_cell is not None:
            col, row = self.selected_cell
            self.selected_cell = (
                math.floor((col + 0.5) * old_scale / new_scale),
                math.floor((row + 0.5) * old_scale / new_scale))
        self.working["cell_au"] = new_scale
        self.load_selected_cell()
        self.canvas.redraw()

    def update_border(self):
        self.working["system_border_au"] = self.border.value()
        self.load_selected_cell()
        self.canvas.redraw()

    def select_cell(self, x, y):
        scale = self.working["cell_au"]
        border = self.working["system_border_au"]
        if math.hypot(x, y) * scale > border:
            self.status.setText("Outside system border")
            return
        self.selected_cell = (math.floor(x), math.floor(y))
        self.load_selected_cell()
        self.canvas.redraw()
        cell_id, local_x, local_y = grid_cell(x, y, scale, border)
        self.status.setText(
            f"Cell {cell_id} | within cell: ({local_x:.3f}, {local_y:.3f})"
            f" | AU: ({x*scale:.3f}, {y*scale:.3f})")

    def load_selected_cell(self):
        selected = self.selected_cell
        self.cell_name.blockSignals(True)
        if selected is None:
            self.cell_id_label.setText("None")
            metadata = {}
        else:
            x, y = selected
            cell_id, _, _ = grid_cell(x, y, self.working["cell_au"],
                                      self.working["system_border_au"])
            self.cell_id_label.setText(cell_id)
            metadata = self.working["cells"].get(cell_key(x, y), {})
        self.cell_name.setText(metadata.get("name", ""))
        for widget in (self.cell_name, self.clear_cell_button):
            widget.setEnabled(selected is not None)
            widget.blockSignals(False)

    def save_cell_metadata(self):
        if self.selected_cell is None:
            return
        key = cell_key(*self.selected_cell)
        name = self.cell_name.text().strip()
        if name:
            self.working["cells"][key] = {"name": name}
        else:
            self.working["cells"].pop(key, None)

    def clear_selected_cell(self):
        if self.selected_cell is None:
            return
        col, row = self.selected_cell
        cell_id, _, _ = grid_cell(col, row, self.working["cell_au"],
                                  self.working["system_border_au"])
        facilities = sum(
            obj["kind"] == "facility" and
            (math.floor(obj["x"]), math.floor(obj["y"])) == (col, row)
            for obj in self.working["objects"])
        has_name = bool(self.working["cells"].get(cell_key(col, row), {}).get("name"))
        if not facilities and not has_name:
            self.status.setText(f"Cell {cell_id} is already clear")
            return
        response = QMessageBox.question(
            self, "Clear Cell",
            f"Clear cell {cell_id}?\n\nRemove {facilities} facility placement(s) "
            "and reset the cell name? Planets and moons will be kept.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if response != QMessageBox.Yes:
            return
        removed = clear_cell_facilities(self.working, col, row)
        if self.moving_id is not None and not any(
                obj["id"] == self.moving_id for obj in self.working["objects"]):
            self.moving_id = None
            self.armed_payload = None
            self.canvas.viewport().unsetCursor()
        self.load_selected_cell()
        self.canvas.redraw()
        self.status.setText(f"Cell {cell_id} cleared: {removed} facility placement(s) removed")

    def update_zone(self):
        if self.inner.value() >= self.outer.value():
            return
        self.working["habitable_inner_au"] = self.inner.value()
        self.working["habitable_outer_au"] = self.outer.value()
        self.canvas.redraw()

    def _lookup(self, kind, ref):
        for planet in self.system.planets:
            if kind == "planet" and planet.id == ref:
                return planet.name, None
            for moon in planet.moons:
                if kind == "moon" and moon.id == ref:
                    return moon.name, planet.id
        return None, None

    def place(self, payload, x, y):
        if math.hypot(x, y) * self.working["cell_au"] > self.working["system_border_au"]:
            QMessageBox.information(self, "System border", "Placement must be inside the system border.")
            return
        kind, ref = payload.split(":", 1)
        moving = next((o for o in self.working["objects"] if o["id"] == self.moving_id), None)
        if kind == "facility":
            name = ref.replace("_", " ").title()
            target = next((o for o in reversed(self.working["objects"])
                if o["kind"] in ("planet", "moon")
                and math.hypot(o["x"]-x, o["y"]-y) <= 1), None)
            placement, parent_id = "deep_space", None
            allowed = allowed_placements(ref)
            if target:
                options = [label for label, mode in (("Surface", "surface"), ("Orbit", "orbit"))
                           if mode in allowed]
                if not options:
                    QMessageBox.information(self, "Invalid placement",
                        "This facility cannot be placed on a celestial body.")
                    return
                choice, ok = QInputDialog.getItem(self, "Facility location",
                    "Place at " + target["name"], options, 0, False)
                if not ok:
                    return
                placement, parent_id = choice.lower(), target["ref_id"]
            elif "deep_space" not in allowed:
                QMessageBox.information(self, "Invalid placement",
                    "This facility requires a planet or moon. Drop it on a body.")
                return
            obj = {"id": moving["id"] if moving else str(uuid.uuid4()), "kind": kind, "ref_id": ref,
                   "name": name, "x": x, "y": y, "placement": placement,
                   "parent_body_id": parent_id, "influence_cells": 0}
        else:
            name, parent_id = self._lookup(kind, ref)
            if name is None:
                QMessageBox.warning(self, "Missing body", "Object no longer exists")
                return

            obj = {"id": moving["id"] if moving else str(uuid.uuid4()), "kind": kind, "ref_id": ref,
                   "name": name, "x": x, "y": y, "parent_body_id": parent_id,
                   "influence_cells": 1}
        if moving:
            obj = {**moving, **obj}
            self.working["objects"] = [o for o in self.working["objects"] if o["id"] != moving["id"]]
        elif kind != "facility":
            self.working["objects"] = [o for o in self.working["objects"]
                                      if not (o["kind"] == kind and o["ref_id"] == ref)]
        self.working["objects"].append(obj)
        self.status.setText(f"{name}: ({x:.2f}, {y:.2f}) — {distance_au((0,0),(x,y),self.working['cell_au']):.3f} AU")
        self.canvas.redraw()
        self.armed_payload = None
        self.moving_id = None
        self.canvas.viewport().unsetCursor()

    def remove_last(self):
        if self.working["objects"]:
            self.working["objects"].pop()
            self.canvas.redraw()

    def accept(self):
        if self.inner.value() >= self.outer.value() or self.outer.value() >= self.border.value():
            QMessageBox.warning(self, "Habitable zone",
                "System border must exceed habitable outer radius, which must exceed inner radius.")
            return
        self.system.system_map = copy.deepcopy(self.working)
        super().accept()

    def reject(self):
        if self.working != self.original:
            choice = QMessageBox.question(self, "Unsaved system map",
                "Discard changes to this system map?",
                QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Cancel)
            if choice != QMessageBox.Discard:
                return
        super().reject()
