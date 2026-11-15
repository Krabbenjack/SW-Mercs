"""Real Qt smoke test for launch, navigation, map graphics and persistence."""
import json
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
from app.launcher.window import Launcher
from app.editors.starmap import SystemData, RouteData, TemplateData
from app.editors.starmap.data_loader import get_data_loader
from app.editors.starmap.project_io import save_project, load_project, export_map_data
from app.shared.paths import DATA_DIR, ROOT


def main():
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        # Startup must work from outside the repository.
        previous = Path.cwd()
        os.chdir(directory)
        try:
            window = Launcher()
            window.show()
            app.processEvents()
            assert window.isVisible() and window.pages.currentWidget() is window.home
            assert not window.play_button.isEnabled()
            window.editor_button.click()
            assert window.pages.currentWidget() is window.center
            assert not window.ship_button.isEnabled() and not window.industry_button.isEnabled()
            window.back_button.click()
            assert window.pages.currentWidget() is window.home
            window.editor_button.click()
            window.open_map()
            app.processEvents()
            editor = window.map_window
            assert editor is not None and editor.isVisible()
            assert not app.styleSheet()  # launcher styling is local
            assert DATA_DIR == ROOT / "data"
            loader = get_data_loader()
            assert loader.get_goods() and loader.get_population_levels() and loader.get_facility_categories()
            for mode in ("template", "systems", "routes", "stats", None):
                editor.set_mode(mode)
                app.processEvents()
            image = QPixmap(100, 100)
            image.fill()
            image_path = Path(directory) / "template.png"
            assert image.save(str(image_path))
            template = TemplateData.create_new(str(image_path))
            editor.project.add_template(template)
            assert not editor.add_template_to_scene(template).pixmap().isNull()
            a = SystemData.create_new("A", QPointF(0, 0))
            b = SystemData.create_new("B", QPointF(100, 0))
            for system in (a, b):
                editor.project.systems[system.id] = system
                editor.add_system_to_scene(system)
            route = RouteData.create_new("A-B", a.id, b.id, [(50, 50)])
            route.route_class = 1
            editor.project.add_route(route)
            item = editor.add_route_to_scene(route)
            assert item.path().elementCount() == 3 and item.calculate_length() > 100
            editor.set_mode("stats")
            item.setSelected(True)
            app.processEvents()
            editor.light_mode_action.setChecked(True)
            editor.apply_light_mode()
            editor.dark_mode_action.setChecked(True)
            editor.apply_dark_mode()
            project_path = Path(directory) / "test.swmproj"
            export_path = Path(directory) / "test.json"
            assert save_project(editor.project, project_path)
            restored = load_project(project_path)
            assert restored and len(restored.systems) == 2 and len(restored.templates) == 1
            assert restored.routes[route.id].route_class == 1
            assert restored.routes[route.id].control_points == [(50, 50)]
            assert export_map_data(restored, export_path)
            assert len(json.loads(export_path.read_text())["routes"]) == 1
            editor.unsaved_changes = False
            assert editor.close()
            window.open_map()
            assert window.map_window is editor and editor.isVisible()
            assert window.close()
            app.processEvents()
            assert not window.isVisible() and not editor.isVisible()
        finally:
            os.chdir(previous)
    print("Launcher, editor navigation, data, graphics, save/load and export passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
