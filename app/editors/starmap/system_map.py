"""Static, spatial in-system map. Coordinates are grid cells, not galactic HSU."""
import copy
import json
from app.shared.paths import DATA_DIR
import math
import uuid

from PySide6.QtCore import Qt, QPointF, QMimeData, QEvent
from PySide6.QtGui import QColor, QBrush, QPen, QDrag, QPainter, QPixmap, QIcon
from PySide6.QtWidgets import (
    QDialog, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel,
    QPushButton, QListWidget, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsTextItem, QDoubleSpinBox, QMessageBox,
    QInputDialog, QDialogButtonBox,
)
from app.editors.starmap.data_loader import get_data_loader

CELL_PX = 32
MIME = "application/x-swmercs-system-object"
def allowed_placements(facility_id):
    path = DATA_DIR / "facilities" / "facility_placements.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)["placements"].get(facility_id, [])


DEFAULT_MAP = {"cell_au": 0.1, "habitable_inner_au": 0.8,
               "habitable_outer_au": 1.5, "objects": []}


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
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return
        mime = QMimeData()
        mime.setData(MIME, item.data(Qt.UserRole).encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        # Visible feedback while dragging, independent of any external SVG assets.
        preview = QPixmap(132, 34)
        preview.fill(QColor("#23334b"))
        painter = QPainter(preview)
        painter.setPen(QColor("#ffffff"))
        painter.setBrush(QBrush(QColor("#70b9ef")))
        painter.drawEllipse(6, 9, 16, 16)
        painter.drawText(29, 23, item.text()[:19])
        painter.end()
        drag.setPixmap(preview)
        drag.setHotSpot(QPointF(8, 17).toPoint())
        drag.exec(Qt.CopyAction)


class SystemCanvas(QGraphicsView):
    def __init__(self, owner):
        self.scene_model = QGraphicsScene()
        super().__init__(self.scene_model)
        self.owner = owner
        self.setAcceptDrops(True)
        # The QGraphicsView viewport receives native DnD events; intercept them
        # before QGraphicsScene forwards them to a scene with no drop targets.
        self.viewport().setAcceptDrops(True)
        self.viewport().installEventFilter(self)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setSceneRect(-1200, -1200, 2400, 2400)
        self.redraw()

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#0b1526"))
        painter.setPen(QPen(QColor("#263449"), 0))
        left = math.floor(rect.left() / CELL_PX)
        right = math.ceil(rect.right() / CELL_PX)
        top = math.floor(rect.top() / CELL_PX)
        bottom = math.ceil(rect.bottom() / CELL_PX)
        for x in range(left, right + 1):
            painter.drawLine(x * CELL_PX, rect.top(), x * CELL_PX, rect.bottom())
        for y in range(top, bottom + 1):
            painter.drawLine(rect.left(), y * CELL_PX, rect.right(), y * CELL_PX)

    def redraw(self):
        self.scene_model.clear()
        data = self.owner.working
        scale = data["cell_au"]
        inner = data["habitable_inner_au"] / scale * CELL_PX
        outer = data["habitable_outer_au"] / scale * CELL_PX
        self.scene_model.addEllipse(-outer, -outer, 2*outer, 2*outer,
            QPen(QColor("#44885b"), 1), QBrush(QColor(25, 115, 50, 28)))
        self.scene_model.addEllipse(-inner, -inner, 2*inner, 2*inner,
            QPen(QColor("#44885b"), 1), QBrush(QColor("#0b1526")))
        self.scene_model.addEllipse(-11, -11, 22, 22,
            QPen(QColor("#ffdf7b")), QBrush(QColor("#ffba36")))
        for obj in data["objects"]:
            x, y = obj["x"]*CELL_PX, obj["y"]*CELL_PX
            color = {"planet": "#67b5f7", "moon": "#c7d2dd",
                     "facility": "#f6a65c"}.get(obj["kind"], "#b78be8")
            self.scene_model.addEllipse(x-8, y-8, 16, 16,
                QPen(QColor(color)), QBrush(QColor(color)))
            label = self.scene_model.addText(obj["name"])
            label.setDefaultTextColor(QColor("#e7edf6"))
            label.setPos(x+10, y-12)

    def eventFilter(self, watched, event):
        if watched is self.viewport() and event.type() in (
                QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop):
            if not event.mimeData().hasFormat(MIME):
                return False
            if event.type() == QEvent.Type.Drop:
                point = self.mapToScene(event.position().toPoint())
                x = round(point.x() / CELL_PX)
                y = round(point.y() / CELL_PX)
                payload = bytes(event.mimeData().data(MIME)).decode("utf-8")
                self.owner.place(payload, x, y)
            event.acceptProposedAction()
            return True
        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(MIME):
            point = self.mapToScene(event.position().toPoint())
            self.owner.place(bytes(event.mimeData().data(MIME)).decode("utf-8"),
                             round(point.x() / CELL_PX), round(point.y() / CELL_PX))
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15
        self.scale(factor, factor)


class SystemMapDialog(QDialog):
    """Edits a working copy. Accept commits to SystemData; Cancel discards it."""
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.original = copy.deepcopy(getattr(system, "system_map", None) or DEFAULT_MAP)
        self.working = copy.deepcopy(self.original)
        self.setWindowTitle("System Map — " + system.name)
        self.resize(1150, 750)
        layout = QHBoxLayout(self)
        sidebar = QWidget()
        side = QVBoxLayout(sidebar)
        side.addWidget(QLabel("Drag authorized objects onto the grid"))
        self.sources = SourceList()
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
        side.addLayout(settings)
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
        kind = payload.split(":", 1)[0]
        color = {"planet": "#67b5f7", "moon": "#c7d2dd",
                 "facility": "#f6a65c"}.get(kind, "#b78be8")
        painter.setPen(QPen(QColor(color), 2))
        painter.setBrush(QBrush(QColor(color)))
        if kind == "facility":
            painter.drawRect(3, 3, 12, 12)
        else:
            painter.drawEllipse(3, 3, 12, 12)
        painter.end()
        item.setIcon(QIcon(icon))
        item.setToolTip("Drag onto the system grid to place")
        self.sources.addItem(item)

    def update_scale(self):
        self.working["cell_au"] = self.cell.value()
        self.canvas.redraw()

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
        kind, ref = payload.split(":", 1)
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
            obj = {"id": str(uuid.uuid4()), "kind": kind, "ref_id": ref,
                   "name": name, "x": x, "y": y, "placement": placement,
                   "parent_body_id": parent_id, "influence_cells": 0}
        else:
            name, parent_id = self._lookup(kind, ref)
            if name is None:
                QMessageBox.warning(self, "Missing body", "Object no longer exists")
                return
            self.working["objects"] = [o for o in self.working["objects"]
                                      if not (o["kind"] == kind and o["ref_id"] == ref)]
            obj = {"id": str(uuid.uuid4()), "kind": kind, "ref_id": ref,
                   "name": name, "x": x, "y": y, "parent_body_id": parent_id,
                   "influence_cells": 1}
        self.working["objects"].append(obj)
        self.status.setText(f"{name}: ({x}, {y}) — {distance_au((0,0),(x,y),self.working['cell_au']):.3f} AU")
        self.canvas.redraw()

    def remove_last(self):
        if self.working["objects"]:
            self.working["objects"].pop()
            self.canvas.redraw()

    def accept(self):
        if self.inner.value() >= self.outer.value():
            QMessageBox.warning(self, "Habitable zone",
                "Outer radius must exceed inner radius.")
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
