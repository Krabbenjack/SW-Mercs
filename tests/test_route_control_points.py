"""Regression checks for the current non-draggable polyline route system."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QGraphicsScene
from app.editors.starmap import RouteData, RouteItem, SystemData, SystemItem


def main():
    app = QApplication.instance() or QApplication([])
    scene = QGraphicsScene()
    a = SystemData.create_new("A", QPointF(0, 0))
    b = SystemData.create_new("B", QPointF(100, 0))
    items = {s.id: SystemItem(s) for s in (a, b)}
    for item in items.values():
        scene.addItem(item)
    data = RouteData.create_new("A-B", a.id, b.id, [(50, 50)])
    route = RouteItem(data, items)
    scene.addItem(route)
    assert route.path().elementCount() == 3
    assert abs(route.calculate_length() - 2 * (50**2 + 50**2)**0.5) < 1e-6
    assert route._point_to_segment_distance(QPointF(50, 50), QPointF(0, 0), QPointF(100, 0)) == 50
    data.control_points.insert(0, (25, 0))
    route.recompute_path()
    assert route.path().elementCount() == 4
    del data.control_points[0]
    route.recompute_path()
    assert route.path().elementCount() == 3
    print("Polyline geometry and control-point operations passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

