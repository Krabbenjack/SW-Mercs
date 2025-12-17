"""GUI implementation for the Star Map Editor.

This module contains all PySide6 UI components including the main window,
map view, and workspace controls.
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List

# Add current directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import (
    QMainWindow, QGraphicsView, QGraphicsScene,
    QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QFileDialog, 
    QMessageBox, QLabel, QSlider, QToolBar, QMenuBar, QMenu,
    QGraphicsPathItem, QInputDialog, QGraphicsTextItem, QListWidget,
    QDialog, QDialogButtonBox, QComboBox, QSplitter, QTabWidget,
    QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QPointF, Signal
from PySide6.QtGui import QPixmap, QPen, QColor, QPainter, QKeyEvent, QWheelEvent, QAction, QPainterPath, QFont

from core import (
    MapProject, TemplateData, SystemData, SystemItem, 
    SystemDialog, TemplateItem, RouteData, RouteItem
)
from core.project_model import RouteGroup
from core.project_io import save_project, load_project, export_map_data


class GridOverlay(QGraphicsScene):
    """Custom QGraphicsScene to draw a semi-transparent grid overlay.
    
    WORLD SPACE ARCHITECTURE:
    - Grid spacing represents Hyperspace Units (HSU)
    - 1 grid cell = 1 HSU (or configured HSU size)
    - Grid is infinite and extends dynamically with view
    - Grid is independent of template size/position
    - Only visual rendering occurs in View space, coordinates stay in HSU
    
    The grid is drawn in the foreground, on top of all scene items,
    and scales/moves with the view transformations.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # WORLD SPACE: Grid spacing in HSU (Hyperspace Units)
        self.grid_spacing = 100  # 1 grid cell = 100 scene units (customizable HSU size)
        self.grid_color = QColor(144, 238, 144, 128)  # Semi-transparent light green
        self.show_grid = False
        self.major_grid_interval = 5  # Draw major grid lines every N cells (for low zoom levels)
        
    def drawForeground(self, painter, rect):
        """Draw infinite grid overlay on top of scene items.
        
        Grid extends dynamically based on visible view rectangle,
        independent of any template boundaries.
        
        Args:
            painter: QPainter for drawing
            rect: Visible rectangle in scene coordinates
        """
        if not self.show_grid:
            return
            
        painter.save()
        
        # UI SPACE: Grid line thickness (1 pixel regardless of zoom)
        painter.setPen(QPen(self.grid_color, 0))  # 0 = cosmetic pen (always 1px)
        
        # WORLD SPACE: Calculate grid bounds from visible rect
        # Extend beyond visible area to ensure complete coverage
        left = int(rect.left() / self.grid_spacing) * self.grid_spacing
        top = int(rect.top() / self.grid_spacing) * self.grid_spacing
        right = rect.right()
        bottom = rect.bottom()
        
        # Draw vertical lines (WORLD SPACE: HSU coordinates)
        x = left
        while x <= right:
            painter.drawLine(int(x), int(top), int(x), int(bottom))
            x += self.grid_spacing
            
        # Draw horizontal lines (WORLD SPACE: HSU coordinates)
        y = top
        while y <= bottom:
            painter.drawLine(int(left), int(y), int(right), int(y))
            y += self.grid_spacing
            
        painter.restore()


class MapView(QGraphicsView):
    """Custom QGraphicsView with zoom and pan controls.
    
    VIEW SPACE ARCHITECTURE:
    - View zoom is a CAMERA transformation only
    - Zooming changes pixels-per-HSU ratio, not world coordinates
    - All world objects (systems, routes) remain at fixed HSU positions
    - Grid extends infinitely and dynamically with view
    - Zoom indicator shows relationship between screen (pixels) and world (HSU)
    
    Features:
    - Mouse wheel zoom centered on cursor position with min/max limits
    - Continuous WASD/Arrow key panning with zoom-scaled speed
    - Middle mouse button drag panning
    - Space + left mouse button drag panning
    - Automatic scene update to refresh grid overlay
    - System placement mode support
    - Template mode support with Ctrl+wheel for template scaling (IMAGE LAYER)
    - Zoom indicator overlay (bottom-right corner)
    """
    
    # Signal emitted when user clicks to place/edit a system
    system_click = Signal(QPointF, bool)  # (position, is_right_click)
    
    # Signal emitted when starting route drawing
    start_route_drawing = Signal(object)  # (SystemItem)
    
    # Signal emitted when finishing route drawing
    finish_route_drawing = Signal(object)  # (SystemItem)
    
    # Signal emitted when a route is toggled for group selection
    route_group_toggle = Signal(str)  # (route_id)
    
    # Signal emitted when requesting route deletion from context menu
    route_delete_requested = Signal(str)  # (route_id)
    
    # Signal emitted when an item is moved/modified
    item_modified = Signal()  # Emitted when items are moved
    
    # Signals for route editing context menus
    system_context_menu_requested = Signal(object, object)  # (SystemItem, global_pos)
    segment_context_menu_requested = Signal(object, object, object)  # (RouteItem, segment_info, global_pos)
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        
        # Zoom configuration
        self.zoom_factor = 1.15  # Zoom step per wheel event
        self.min_zoom = 0.1  # Minimum zoom level (10%)
        self.max_zoom = 10.0  # Maximum zoom level (1000%)
        self.current_zoom = 1.0  # Current zoom level tracking
        
        # Template scaling configuration
        self.template_scale_base_factor = 0.1  # Base scale change per wheel tick
        
        # Panning configuration
        self.pan_speed = 15  # Base pan speed in pixels
        self.pan_sensitivity = 1.0  # Pan sensitivity multiplier
        self.keys_pressed = set()  # Currently pressed navigation keys
        self.pan_timer = QTimer(self)
        self.pan_timer.timeout.connect(self._handle_continuous_pan)
        self.pan_timer.setInterval(33)  # ~30 FPS for smooth panning
        
        # Mouse panning state
        self.is_panning = False
        self.pan_start_pos = None
        self.space_pressed = False
        
        # Mode state
        self.systems_mode_active = False
        self.template_mode_active = False
        self.routes_mode_active = False
        self.route_editing_mode_active = False  # Active when a route is selected
        
        # Template scaling sensitivity
        self.template_scale_sensitivity = 1.0  # Scale sensitivity multiplier
        
        # Item drag tracking
        self.dragging_item = False
        
        # Route drawing state (click-to-add polyline)
        self.route_drawing_active = False
        self.route_drawing_start_system_id: Optional[str] = None
        self.route_drawing_points: List[QPointF] = []  # Intermediate vertices
        self.route_drawing_preview_item: Optional[QGraphicsPathItem] = None  # Visual preview during drawing
        
        # Zoom indicator overlay (UI SPACE: always visible in corner)
        self.zoom_indicator = QLabel(self)
        self.zoom_indicator.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        self.zoom_indicator.setAlignment(Qt.AlignLeft)
        self.update_zoom_indicator()

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming or template scaling.
        
        In template mode with Ctrl held: scale the selected template
        Otherwise: zoom the view centered on cursor
        """
        # Check if in template mode with Ctrl pressed
        if self.template_mode_active and event.modifiers() & Qt.ControlModifier:
            # Scale selected template
            item = self.scene().mouseGrabberItem()
            if not item:
                # Get item under cursor
                pos = event.position().toPoint()
                item = self.itemAt(pos)
            
            if isinstance(item, TemplateItem):
                # Calculate scale factor with sensitivity applied
                # Use multiplicative approach to avoid invalid scale values
                if event.angleDelta().y() > 0:
                    # Zoom in: multiply by (1 + factor)
                    scale_change = 1.0 + (self.template_scale_base_factor * self.template_scale_sensitivity)
                else:
                    # Zoom out: divide by (1 + factor) to ensure value stays positive
                    scale_change = 1.0 / (1.0 + (self.template_scale_base_factor * self.template_scale_sensitivity))
                
                item.scale_relative(scale_change)
                event.accept()
                return
        
        # Normal view zoom
        # Calculate zoom factor
        if event.angleDelta().y() > 0:
            zoom = self.zoom_factor
        else:
            zoom = 1.0 / self.zoom_factor
        
        # Check zoom limits
        new_zoom = self.current_zoom * zoom
        if new_zoom < self.min_zoom or new_zoom > self.max_zoom:
            return
        
        # Get the position of the mouse in scene coordinates before zoom
        old_pos = self.mapToScene(event.position().toPoint())
        
        # Apply zoom (VIEW SPACE: only affects how many pixels per HSU)
        self.scale(zoom, zoom)
        self.current_zoom = new_zoom
        
        # Get the new position of the mouse in scene coordinates after zoom
        new_pos = self.mapToScene(event.position().toPoint())
        
        # Calculate the difference and adjust view to keep it under the mouse
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        
        # Update zoom indicator
        self.update_zoom_indicator()
        
        # Update the scene to refresh grid
        self.scene().update()
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press for continuous WASD/Arrow panning, Space for mouse pan, and ESC for cancel."""
        if event.key() in (Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D,
                          Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            self.keys_pressed.add(event.key())
            if not self.pan_timer.isActive():
                self.pan_timer.start()
            event.accept()
        elif event.key() == Qt.Key_Space:
            self.space_pressed = True
            event.accept()
        elif event.key() == Qt.Key_Escape:
            # Cancel route drawing if active
            if self.route_drawing_active:
                self.cancel_route_drawing()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event: QKeyEvent):
        """Handle key release to stop continuous panning."""
        if event.key() in (Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D,
                          Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            self.keys_pressed.discard(event.key())
            if not self.keys_pressed:
                self.pan_timer.stop()
            event.accept()
        elif event.key() == Qt.Key_Space:
            self.space_pressed = False
            if self.is_panning:
                self.is_panning = False
                self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().keyReleaseEvent(event)
    
    def _handle_continuous_pan(self):
        """Handle continuous panning based on pressed keys."""
        if not self.keys_pressed:
            return
        
        # Calculate pan speed scaled by zoom level and pan sensitivity
        # Ensure safe division by using max of current zoom and min zoom (0.1)
        safe_zoom = max(self.current_zoom, self.min_zoom)
        scaled_speed = (self.pan_speed / safe_zoom) * self.pan_sensitivity
        
        # Handle vertical panning
        if Qt.Key_W in self.keys_pressed or Qt.Key_Up in self.keys_pressed:
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(scaled_speed)
            )
        if Qt.Key_S in self.keys_pressed or Qt.Key_Down in self.keys_pressed:
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() + int(scaled_speed)
            )
        
        # Handle horizontal panning
        if Qt.Key_A in self.keys_pressed or Qt.Key_Left in self.keys_pressed:
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(scaled_speed)
            )
        if Qt.Key_D in self.keys_pressed or Qt.Key_Right in self.keys_pressed:
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() + int(scaled_speed)
            )
        
        # Update the scene to refresh grid
        self.scene().update()
    
    def mousePressEvent(self, event):
        """Handle mouse press for panning, system placement, and route creation.
        
        In routes mode:
        - Click System A: Start route drawing
        - Click empty space: Add intermediate control point
        - Click System B: Finish route
        - Right-click or ESC: Cancel route drawing
        - Ctrl + Click on RouteItem: Toggle route for group selection
        - Click on RouteItem: Select the route
        """
        # Middle mouse button or Space + left mouse button for panning
        if event.button() == Qt.MiddleButton or \
           (event.button() == Qt.LeftButton and self.space_pressed):
            self.is_panning = True
            self.pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        # In routes mode, handle clicks for polyline route creation
        elif self.routes_mode_active:
            if event.button() == Qt.LeftButton:
                # Get item at click position
                item = self.itemAt(event.pos())
                scene_pos = self.mapToScene(event.pos())
                
                # Check if item is a system or if parent is a system (for label clicks)
                system_item = None
                if isinstance(item, SystemItem):
                    system_item = item
                elif item and isinstance(item.parentItem(), SystemItem):
                    system_item = item.parentItem()
                
                # Check if CTRL is pressed for group selection (not while drawing)
                if not self.route_drawing_active and (event.modifiers() & Qt.ControlModifier):
                    if isinstance(item, RouteItem):
                        # Toggle route for group selection
                        self.toggle_route_group_selection(item)
                        event.accept()
                        return
                
                # If currently drawing a route
                if self.route_drawing_active:
                    # Check if clicking on a system (to finish route)
                    if system_item:
                        # Emit signal to finish route creation with end system
                        self.finish_route_drawing.emit(system_item)
                        event.accept()
                        return
                    else:
                        # Clicking on empty space - add intermediate point
                        self.route_drawing_points.append(scene_pos)
                        
                        # Update visual preview
                        # Find start system position
                        start_system_item = None
                        for item in self.scene().items():
                            if isinstance(item, SystemItem):
                                if item.get_system_data().id == self.route_drawing_start_system_id:
                                    start_system_item = item
                                    break
                        
                        if start_system_item:
                            self.update_route_drawing_preview(start_system_item.pos())
                        
                        event.accept()
                        return
                
                # Not currently drawing - check what was clicked
                if system_item:
                    # Clicking on system - start route drawing
                    self.start_route_drawing.emit(system_item)
                    event.accept()
                    return
                elif isinstance(item, RouteItem):
                    # Just select the route (no more ghost-line editing)
                    super().mousePressEvent(event)
                    return
                else:
                    # Clicking on empty space - do nothing in routes mode when not drawing
                    event.accept()
                    return
                    
            elif event.button() == Qt.RightButton:
                # Right click - cancel drawing or show context menu
                if self.route_drawing_active:
                    self.cancel_route_drawing()
                    event.accept()
                    return
                else:
                    scene_pos = self.mapToScene(event.pos())
                    item = self.itemAt(event.pos())
                    
                    # Check if we're in route editing mode
                    if self.route_editing_mode_active:
                        # Check if clicking on a system
                        system_item = None
                        if isinstance(item, SystemItem):
                            system_item = item
                        elif item and isinstance(item.parentItem(), SystemItem):
                            system_item = item.parentItem()
                        
                        if system_item:
                            # Show system context menu for route editing
                            self.system_context_menu_requested.emit(system_item, event.globalPos())
                            event.accept()
                            return
                        elif isinstance(item, RouteItem):
                            # Check if clicking on a route segment
                            segment_info = item.get_segment_at_point(scene_pos)
                            if segment_info:
                                self.segment_context_menu_requested.emit(item, segment_info, event.globalPos())
                                event.accept()
                                return
                            else:
                                # Clicked on route but not near a segment - show route context menu
                                self.show_route_context_menu(event.globalPos(), item)
                                event.accept()
                                return
                    else:
                        # Not in editing mode - show normal route context menu
                        if isinstance(item, RouteItem):
                            self.show_route_context_menu(event.globalPos(), item)
                            event.accept()
                        return
                    super().mousePressEvent(event)
            else:
                super().mousePressEvent(event)
        # In systems mode, handle clicks for placement/editing
        elif self.systems_mode_active:
            scene_pos = self.mapToScene(event.pos())
            if event.button() == Qt.LeftButton:
                # Check if clicking on an existing system
                item = self.itemAt(event.pos())
                if not isinstance(item, SystemItem):
                    # Left click on empty space - place new system
                    self.system_click.emit(scene_pos, False)
                    event.accept()
                    return
                else:
                    # Clicking on a system to drag it
                    self.dragging_item = True
            elif event.button() == Qt.RightButton:
                # Right click - edit existing system if clicked
                item = self.itemAt(event.pos())
                if isinstance(item, SystemItem):
                    self.system_click.emit(scene_pos, True)
                    event.accept()
                    return
            # Let default behavior handle system dragging
            super().mousePressEvent(event)
        # In template mode, check if clicking on a template
        elif self.template_mode_active:
            if event.button() == Qt.LeftButton:
                item = self.itemAt(event.pos())
                if isinstance(item, TemplateItem):
                    self.dragging_item = True
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning."""
        if self.is_panning and self.pan_start_pos is not None:
            # Calculate delta
            delta = event.pos() - self.pan_start_pos
            self.pan_start_pos = event.pos()
            
            # Update scroll bars
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            
            # Update the scene to refresh grid
            self.scene().update()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop panning and track item movements."""
        if event.button() == Qt.MiddleButton or \
           (event.button() == Qt.LeftButton and self.is_panning):
            self.is_panning = False
            self.pan_start_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            # Check if we were dragging an item
            if self.dragging_item and event.button() == Qt.LeftButton:
                self.item_modified.emit()
                self.dragging_item = False
            super().mouseReleaseEvent(event)
    
    def show_route_context_menu(self, global_pos, route_item: RouteItem):
        """Show context menu for a route.
        
        Args:
            global_pos: Global position for the menu
            route_item: The RouteItem to show menu for
        """
        menu = QMenu()
        rename_action = menu.addAction("Rename Route")
        delete_action = menu.addAction("Delete Route")
        
        action = menu.exec(global_pos)
        if action == rename_action:
            # Show rename dialog
            route_data = route_item.get_route_data()
            new_name, ok = QInputDialog.getText(
                self,
                "Rename Route",
                "Enter new name for route:",
                text=route_data.name
            )
            if ok and new_name and new_name.strip():
                route_item.update_name(new_name.strip())
                # Emit signal to mark unsaved changes
                self.item_modified.emit()
        elif action == delete_action:
            # Emit signal to request route deletion
            route_data = route_item.get_route_data()
            self.route_delete_requested.emit(route_data.id)
    
    def toggle_route_group_selection(self, route_item: RouteItem):
        """Toggle a route's group selection state.
        
        Args:
            route_item: The RouteItem to toggle
        """
        # Emit signal to let main window handle the logic
        route_id = route_item.get_route_data().id
        self.route_group_toggle.emit(route_id)
    
    def cancel_route_drawing(self):
        """Cancel the current route drawing operation."""
        self.route_drawing_active = False
        self.route_drawing_start_system_id = None
        self.route_drawing_points = []
        
        # Remove preview path if it exists
        if self.route_drawing_preview_item:
            self.scene().removeItem(self.route_drawing_preview_item)
            self.route_drawing_preview_item = None
        
        self.setCursor(Qt.ArrowCursor)
    
    def update_route_drawing_preview(self, start_pos: QPointF):
        """Update the visual preview of the route being drawn.
        
        Args:
            start_pos: Position of the start system
        """
        # Remove old preview if it exists
        if self.route_drawing_preview_item:
            self.scene().removeItem(self.route_drawing_preview_item)
            self.route_drawing_preview_item = None
        
        # Create path for preview
        if len(self.route_drawing_points) > 0:
            from PySide6.QtGui import QPainterPath, QPen
            from PySide6.QtCore import Qt
            
            path = QPainterPath()
            path.moveTo(start_pos)
            
            # Draw through all intermediate points
            for point in self.route_drawing_points:
                path.lineTo(point)
            
            # Create preview item with dashed line style
            self.route_drawing_preview_item = QGraphicsPathItem(path)
            pen = QPen(QColor(100, 150, 255), 2, Qt.DashLine)  # Blue dashed line
            self.route_drawing_preview_item.setPen(pen)
            self.route_drawing_preview_item.setZValue(-1)  # Below other items
            self.scene().addItem(self.route_drawing_preview_item)
    
    def set_pan_sensitivity(self, sensitivity: float):
        """Set the pan sensitivity multiplier.
        
        Args:
            sensitivity: Pan sensitivity value (0.5 - 5.0)
        """
        self.pan_sensitivity = max(0.5, min(5.0, sensitivity))
    
    def set_template_scale_sensitivity(self, sensitivity: float):
        """Set the template scale sensitivity multiplier.
        
        Args:
            sensitivity: Scale sensitivity value (0.1 - 3.0)
        """
        self.template_scale_sensitivity = max(0.1, min(3.0, sensitivity))
    
    def update_zoom_indicator(self):
        """Update the zoom indicator display.
        
        Shows current zoom percentage and pixels-per-HSU ratio.
        This helps users understand the relationship between screen space (pixels)
        and world space (HSU).
        """
        zoom_percent = int(self.current_zoom * 100)
        # Calculate pixels per HSU: base is 1 HSU = 1 pixel at 100% zoom
        # At current zoom, 1 HSU = current_zoom pixels
        pixels_per_hsu = self.current_zoom
        
        self.zoom_indicator.setText(
            f"Zoom: {zoom_percent}%\n"
            f"1 HSU = {pixels_per_hsu:.1f} px"
        )
        self.position_zoom_indicator()
    
    def position_zoom_indicator(self):
        """Position the zoom indicator in the bottom-right corner."""
        margin = 10
        indicator_width = self.zoom_indicator.sizeHint().width()
        indicator_height = self.zoom_indicator.sizeHint().height()
        
        x = self.width() - indicator_width - margin
        y = self.height() - indicator_height - margin
        
        self.zoom_indicator.move(x, y)
    
    def resizeEvent(self, event):
        """Handle widget resize to reposition overlay elements.
        
        Args:
            event: QResizeEvent
        """
        super().resizeEvent(event)
        self.position_zoom_indicator()


def prettify_id(id_string: str) -> str:
    """Convert an ID string to a human-readable label.
    
    Args:
        id_string: ID string with underscores (e.g., "mining_facility")
        
    Returns:
        Prettified string (e.g., "Mining Facility")
    """
    return id_string.replace('_', ' ').title()


class FacilityPopup(QDialog):
    """Dialog for selecting facilities organized by category.
    
    Displays facilities from facility_flags.json in a tab-based interface,
    with one tab per category containing checkboxes for each facility.
    """
    
    def __init__(self, selected_facilities: list[str], parent=None):
        """Initialize the facility selection dialog.
        
        Args:
            selected_facilities: List of currently selected facility IDs
            parent: Parent widget
        """
        super().__init__(parent)
        self.selected_facilities = selected_facilities.copy()
        self.setWindowTitle("Edit Facilities")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Import data loader here to avoid circular import
        from core.data_loader import get_data_loader
        data_loader = get_data_loader()
        
        # Create tab widget
        from PySide6.QtWidgets import QTabWidget, QCheckBox, QScrollArea
        self.tab_widget = QTabWidget()
        
        # Store checkboxes for retrieval
        self.checkboxes = {}
        
        # Get facility categories
        categories = data_loader.get_facility_categories()
        
        # Create a tab for each category
        for category_name, facility_ids in categories.items():
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            
            # Create checkboxes for each facility
            for facility_id in facility_ids:
                # Prettify the facility ID for display
                display_name = prettify_id(facility_id)
                checkbox = QCheckBox(display_name)
                checkbox.setChecked(facility_id in self.selected_facilities)
                self.checkboxes[facility_id] = checkbox
                tab_layout.addWidget(checkbox)
            
            # Add stretch to push checkboxes to top
            tab_layout.addStretch()
            
            # Create scroll area
            scroll = QScrollArea()
            scroll.setWidget(tab_widget)
            scroll.setWidgetResizable(True)
            
            # Add tab with prettified name
            tab_title = prettify_id(category_name)
            self.tab_widget.addTab(scroll, tab_title)
        
        layout.addWidget(self.tab_widget)
        
        # Add OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_selected_facilities(self) -> list[str]:
        """Get the list of selected facility IDs.
        
        Returns:
            List of selected facility IDs
        """
        selected = []
        for facility_id, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                selected.append(facility_id)
        return selected


class GoodsPopup(QDialog):
    """Dialog for selecting goods for imports or exports.
    
    Displays goods from goods.json in a multi-select list with optional filtering.
    """
    
    def __init__(self, selected_goods: list[str], mode: str = "imports", parent=None):
        """Initialize the goods selection dialog.
        
        Args:
            selected_goods: List of currently selected good IDs
            mode: Either "imports" or "exports" for dialog title
            parent: Parent widget
        """
        super().__init__(parent)
        self.selected_goods = selected_goods.copy()
        self.mode = mode
        self.setWindowTitle(f"Edit {mode.capitalize()}")
        self.setModal(True)
        self.setMinimumSize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # Import data loader here to avoid circular import
        from core.data_loader import get_data_loader
        from PySide6.QtWidgets import QLineEdit
        data_loader = get_data_loader()
        
        # Add search/filter bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search goods...")
        self.search_input.textChanged.connect(self.filter_goods)
        layout.addWidget(self.search_input)
        
        # Create list widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        
        # Get goods data
        self.goods_data = data_loader.get_goods()
        
        # Populate list
        self.populate_list()
        
        layout.addWidget(self.list_widget)
        
        # Add info label
        info_label = QLabel("Hold Ctrl/Cmd to select multiple items")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)
        
        # Add OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def populate_list(self, filter_text: str = ""):
        """Populate the list widget with goods.
        
        Args:
            filter_text: Optional filter string to limit displayed goods
        """
        self.list_widget.clear()
        
        for good in self.goods_data:
            good_id = good.get("id", "")
            name = good.get("name", good_id)
            tier = good.get("tier", "")
            
            # Apply filter
            if filter_text and filter_text.lower() not in name.lower():
                continue
            
            # Create display text
            display_text = f"{name} (Tier {tier})"
            
            # Add item
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, good_id)
            self.list_widget.addItem(item)
            
            # Select if in selected_goods
            if good_id in self.selected_goods:
                item.setSelected(True)
    
    def filter_goods(self, text: str):
        """Filter the goods list based on search text.
        
        Args:
            text: Search text
        """
        self.populate_list(text)
    
    def get_selected_goods(self) -> list[str]:
        """Get the list of selected good IDs.
        
        Returns:
            List of selected good IDs
        """
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.isSelected():
                good_id = item.data(Qt.UserRole)
                selected.append(good_id)
        return selected


class StatsWidget(QWidget):
    """Widget for editing system statistics in the Stats tab.
    
    Displays and allows editing of population, facilities, imports, and exports
    for the currently selected system.
    """
    
    def __init__(self, parent=None):
        """Initialize the stats widget."""
        super().__init__(parent)
        self.current_system: Optional[SystemData] = None
        
        # Import data loader
        from core.data_loader import get_data_loader
        self.data_loader = get_data_loader()
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        
        # Title
        title_label = QLabel("System Statistics")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addSpacing(10)
        
        # No system selected message (initially hidden)
        self.no_system_label = QLabel("No system selected")
        self.no_system_label.setStyleSheet("color: gray; font-style: italic;")
        self.no_system_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.no_system_label)
        
        # Content widget (initially hidden)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # System name display
        self.system_name_label = QLabel()
        system_name_font = QFont()
        system_name_font.setPointSize(12)
        system_name_font.setBold(True)
        self.system_name_label.setFont(system_name_font)
        content_layout.addWidget(self.system_name_label)
        
        content_layout.addSpacing(10)
        
        # Population section
        pop_label = QLabel("Population:")
        pop_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(pop_label)
        
        self.population_combo = QComboBox()
        self.population_combo.currentIndexChanged.connect(self.on_population_changed)
        content_layout.addWidget(self.population_combo)
        
        content_layout.addSpacing(10)
        
        # Facilities section
        facilities_label = QLabel("Facilities:")
        facilities_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(facilities_label)
        
        facilities_row = QHBoxLayout()
        self.facilities_btn = QPushButton("Edit Facilities...")
        self.facilities_btn.clicked.connect(self.edit_facilities)
        facilities_row.addWidget(self.facilities_btn)
        
        self.facilities_summary = QLabel("0 facilities")
        self.facilities_summary.setStyleSheet("color: gray;")
        facilities_row.addWidget(self.facilities_summary)
        facilities_row.addStretch()
        
        content_layout.addLayout(facilities_row)
        
        content_layout.addSpacing(10)
        
        # Imports section
        imports_label = QLabel("Imports:")
        imports_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(imports_label)
        
        imports_row = QHBoxLayout()
        self.imports_btn = QPushButton("Edit Imports...")
        self.imports_btn.clicked.connect(self.edit_imports)
        imports_row.addWidget(self.imports_btn)
        
        self.imports_summary = QLabel("0 goods")
        self.imports_summary.setStyleSheet("color: gray;")
        imports_row.addWidget(self.imports_summary)
        imports_row.addStretch()
        
        content_layout.addLayout(imports_row)
        
        content_layout.addSpacing(10)
        
        # Exports section
        exports_label = QLabel("Exports:")
        exports_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(exports_label)
        
        exports_row = QHBoxLayout()
        self.exports_btn = QPushButton("Edit Exports...")
        self.exports_btn.clicked.connect(self.edit_exports)
        exports_row.addWidget(self.exports_btn)
        
        self.exports_summary = QLabel("0 goods")
        self.exports_summary.setStyleSheet("color: gray;")
        exports_row.addWidget(self.exports_summary)
        exports_row.addStretch()
        
        content_layout.addLayout(exports_row)
        
        content_layout.addStretch()
        
        layout.addWidget(self.content_widget)
        
        # Initialize population combo
        self.populate_population_combo()
        
        # Initially show no system selected
        self.set_system(None)
    
    def populate_population_combo(self):
        """Populate the population combo box from data."""
        self.population_combo.clear()
        self.population_combo.addItem("(No population)", None)
        
        population_levels = self.data_loader.get_population_levels()
        for level in population_levels:
            level_id = level.get("id", "")
            label = level.get("label", level_id)
            self.population_combo.addItem(label, level_id)
    
    def set_system(self, system: Optional[SystemData]):
        """Set the current system to display/edit.
        
        Args:
            system: The SystemData to display, or None if no system selected
        """
        self.current_system = system
        
        if system is None:
            # Show "no system" message
            self.no_system_label.show()
            self.content_widget.hide()
        else:
            # Show system data
            self.no_system_label.hide()
            self.content_widget.show()
            
            # Update UI
            self.system_name_label.setText(f"System: {system.name}")
            
            # Set population
            if system.population_id:
                index = self.population_combo.findData(system.population_id)
                if index >= 0:
                    self.population_combo.setCurrentIndex(index)
                else:
                    self.population_combo.setCurrentIndex(0)
            else:
                self.population_combo.setCurrentIndex(0)
            
            # Update summaries
            self.update_summaries()
    
    def update_summaries(self):
        """Update the summary labels for facilities, imports, and exports."""
        if self.current_system is None:
            return
        
        # Update facilities summary
        num_facilities = len(self.current_system.facilities)
        self.facilities_summary.setText(f"{num_facilities} facility" + ("ies" if num_facilities != 1 else "y"))
        
        # Update imports summary
        num_imports = len(self.current_system.imports)
        self.imports_summary.setText(f"{num_imports} good" + ("s" if num_imports != 1 else ""))
        
        # Update exports summary
        num_exports = len(self.current_system.exports)
        self.exports_summary.setText(f"{num_exports} good" + ("s" if num_exports != 1 else ""))
    
    def on_population_changed(self, index: int):
        """Handle population combo box change.
        
        Args:
            index: The new combo box index
        """
        if self.current_system is None:
            return
        
        population_id = self.population_combo.itemData(index)
        self.current_system.population_id = population_id
    
    def edit_facilities(self):
        """Open the facilities editor dialog."""
        if self.current_system is None:
            return
        
        dialog = FacilityPopup(self.current_system.facilities, self)
        if dialog.exec() == QDialog.Accepted:
            self.current_system.facilities = dialog.get_selected_facilities()
            self.update_summaries()
    
    def edit_imports(self):
        """Open the imports editor dialog."""
        if self.current_system is None:
            return
        
        dialog = GoodsPopup(self.current_system.imports, "imports", self)
        if dialog.exec() == QDialog.Accepted:
            self.current_system.imports = dialog.get_selected_goods()
            self.update_summaries()
    
    def edit_exports(self):
        """Open the exports editor dialog."""
        if self.current_system is None:
            return
        
        dialog = GoodsPopup(self.current_system.exports, "exports", self)
        if dialog.exec() == QDialog.Accepted:
            self.current_system.exports = dialog.get_selected_goods()
            self.update_summaries()


class RouteStatsWidget(QWidget):
    """Widget for editing route statistics in the Stats tab.
    
    Displays and allows editing of route class, travel type, and hazards
    for the currently selected route.
    """
    
    # Available hazards for route selection
    AVAILABLE_HAZARDS = [
        "nebula",
        "hypershadow",
        "quasar",
        "minefield",
        "pirate_activity"
    ]
    
    # Travel types
    TRAVEL_TYPES = [
        "normal",
        "express_lane",
        "ancient_hyperlane",
        "backwater"
    ]
    
    def __init__(self, system_items_dict: Dict[str, SystemItem], parent=None):
        """Initialize the route stats widget.
        
        Args:
            system_items_dict: Dictionary mapping system IDs to SystemItem instances
            parent: Parent widget
        """
        super().__init__(parent)
        self.current_route_item: Optional[RouteItem] = None
        self.system_items = system_items_dict
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        
        # Title
        title_label = QLabel("Route Statistics")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addSpacing(10)
        
        # No route selected message (initially visible)
        self.no_route_label = QLabel("No route selected")
        self.no_route_label.setStyleSheet("color: gray; font-style: italic;")
        self.no_route_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.no_route_label)
        
        # Content widget (initially hidden)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Route name display
        self.route_name_label = QLabel()
        route_name_font = QFont()
        route_name_font.setPointSize(12)
        route_name_font.setBold(True)
        self.route_name_label.setFont(route_name_font)
        content_layout.addWidget(self.route_name_label)
        
        content_layout.addSpacing(10)
        
        # Route length (read-only)
        length_label = QLabel("Route Length (HSU):")
        length_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(length_label)
        
        self.length_value_label = QLabel("0.0 HSU")
        self.length_value_label.setStyleSheet("color: gray;")
        content_layout.addWidget(self.length_value_label)
        
        content_layout.addSpacing(10)
        
        # Route class section
        class_label = QLabel("Route Class (1=Fast, 5=Slow):")
        class_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(class_label)
        
        self.route_class_spin = QSpinBox()
        self.route_class_spin.setMinimum(1)
        self.route_class_spin.setMaximum(5)
        self.route_class_spin.setValue(3)
        self.route_class_spin.valueChanged.connect(self.on_route_class_changed)
        content_layout.addWidget(self.route_class_spin)
        
        content_layout.addSpacing(10)
        
        # Travel type section
        travel_type_label = QLabel("Base Travel Type:")
        travel_type_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(travel_type_label)
        
        self.travel_type_combo = QComboBox()
        for travel_type in self.TRAVEL_TYPES:
            display_name = travel_type.replace("_", " ").title()
            self.travel_type_combo.addItem(display_name, travel_type)
        self.travel_type_combo.currentIndexChanged.connect(self.on_travel_type_changed)
        content_layout.addWidget(self.travel_type_combo)
        
        content_layout.addSpacing(10)
        
        # Hazards section
        hazards_label = QLabel("Hazards:")
        hazards_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(hazards_label)
        
        # Create checkboxes for each hazard
        self.hazard_checkboxes: Dict[str, QCheckBox] = {}
        for hazard in self.AVAILABLE_HAZARDS:
            display_name = hazard.replace("_", " ").title()
            checkbox = QCheckBox(display_name)
            checkbox.stateChanged.connect(lambda state, h=hazard: self.on_hazard_changed(h, state))
            self.hazard_checkboxes[hazard] = checkbox
            content_layout.addWidget(checkbox)
        
        content_layout.addStretch()
        
        layout.addWidget(self.content_widget)
        
        # Initially show no route selected
        self.set_route(None)
    
    def set_route(self, route_item: Optional[RouteItem]):
        """Set the current route to display/edit.
        
        Args:
            route_item: The RouteItem to display, or None if no route selected
        """
        self.current_route_item = route_item
        
        if route_item is None:
            # Show "no route" message
            self.no_route_label.show()
            self.content_widget.hide()
        else:
            # Show route data
            self.no_route_label.hide()
            self.content_widget.show()
            
            route_data = route_item.get_route_data()
            
            # Update UI
            self.route_name_label.setText(f"Route: {route_data.name}")
            
            # Update length
            length = route_item.calculate_length()
            self.length_value_label.setText(f"{length:.1f} HSU")
            
            # Set route class
            self.route_class_spin.setValue(route_data.route_class)
            
            # Set travel type
            index = self.travel_type_combo.findData(route_data.travel_type)
            if index >= 0:
                self.travel_type_combo.setCurrentIndex(index)
            else:
                self.travel_type_combo.setCurrentIndex(0)
            
            # Set hazards
            for hazard, checkbox in self.hazard_checkboxes.items():
                checkbox.setChecked(hazard in route_data.hazards)
    
    def on_route_class_changed(self, value: int):
        """Handle route class spinbox change.
        
        Args:
            value: The new route class value
        """
        if self.current_route_item is None:
            return
        
        route_data = self.current_route_item.get_route_data()
        route_data.route_class = value
    
    def on_travel_type_changed(self, index: int):
        """Handle travel type combo box change.
        
        Args:
            index: The new combo box index
        """
        if self.current_route_item is None:
            return
        
        travel_type = self.travel_type_combo.itemData(index)
        route_data = self.current_route_item.get_route_data()
        route_data.travel_type = travel_type
    
    def on_hazard_changed(self, hazard: str, state: int):
        """Handle hazard checkbox state change.
        
        Args:
            hazard: The hazard identifier
            state: The checkbox state (Qt.Checked or Qt.Unchecked)
        """
        if self.current_route_item is None:
            return
        
        route_data = self.current_route_item.get_route_data()
        
        if state == Qt.Checked:
            if hazard not in route_data.hazards:
                route_data.hazards.append(hazard)
        else:
            if hazard in route_data.hazards:
                route_data.hazards.remove(hazard)


class TravelCalculatorWidget(QWidget):
    """Widget for calculating travel time based on route and ship parameters.
    
    Displays route length and allows user to select hyperdrive rating
    to calculate travel time estimates.
    """
    
    # Hyperdrive ratings and their multipliers
    HYPERDRIVE_RATINGS = {
        "x1": 1.0,
        "x2": 2.0,
        "x3": 3.0,
        "x4": 4.0
    }
    
    # Speed modifiers based on route class (placeholder values)
    ROUTE_CLASS_MODIFIERS = {
        1: 1.5,   # Fast route
        2: 1.2,
        3: 1.0,   # Normal
        4: 0.8,
        5: 0.6    # Slow route
    }
    
    # Travel type modifiers (placeholder values)
    TRAVEL_TYPE_MODIFIERS = {
        "normal": 1.0,
        "express_lane": 1.3,
        "ancient_hyperlane": 0.9,
        "backwater": 0.7
    }
    
    # Hazard modifiers (placeholder values, each adds penalty)
    HAZARD_MODIFIERS = {
        "nebula": 0.9,
        "hypershadow": 0.85,
        "quasar": 0.8,
        "minefield": 0.95,
        "pirate_activity": 0.95
    }
    
    def __init__(self, parent=None):
        """Initialize the travel calculator widget."""
        super().__init__(parent)
        self.current_route_item: Optional[RouteItem] = None
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        
        # Title
        title_label = QLabel("Travel Calculator")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addSpacing(10)
        
        # No route selected message (initially visible)
        self.no_route_label = QLabel("No route selected")
        self.no_route_label.setStyleSheet("color: gray; font-style: italic;")
        self.no_route_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.no_route_label)
        
        # Content widget (initially hidden)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Route name display
        self.route_name_label = QLabel()
        route_name_font = QFont()
        route_name_font.setPointSize(12)
        route_name_font.setBold(True)
        self.route_name_label.setFont(route_name_font)
        content_layout.addWidget(self.route_name_label)
        
        content_layout.addSpacing(10)
        
        # Hyperdrive rating selection
        hyperdrive_label = QLabel("Hyperdrive Rating:")
        hyperdrive_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(hyperdrive_label)
        
        self.hyperdrive_combo = QComboBox()
        for rating_name in self.HYPERDRIVE_RATINGS.keys():
            self.hyperdrive_combo.addItem(rating_name, rating_name)
        self.hyperdrive_combo.currentIndexChanged.connect(self.update_calculations)
        content_layout.addWidget(self.hyperdrive_combo)
        
        content_layout.addSpacing(10)
        
        # Read-only display values
        info_label = QLabel("Route Information:")
        info_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(info_label)
        
        # Route length
        self.length_display = QLabel("Length: 0.0 HSU")
        content_layout.addWidget(self.length_display)
        
        # Route class
        self.class_display = QLabel("Class: 3")
        content_layout.addWidget(self.class_display)
        
        # Travel type
        self.type_display = QLabel("Type: Normal")
        content_layout.addWidget(self.type_display)
        
        # Hazards
        self.hazards_display = QLabel("Hazards: None")
        content_layout.addWidget(self.hazards_display)
        
        content_layout.addSpacing(10)
        
        # Calculated values
        calc_label = QLabel("Estimated Travel:")
        calc_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(calc_label)
        
        self.speed_display = QLabel("Speed Factor: 1.0x")
        content_layout.addWidget(self.speed_display)
        
        self.time_display = QLabel("Travel Time: -- hours")
        content_layout.addWidget(self.time_display)
        
        # Placeholder for fuel estimate
        self.fuel_display = QLabel("Fuel Estimate: TBD")
        self.fuel_display.setStyleSheet("color: gray; font-style: italic;")
        content_layout.addWidget(self.fuel_display)
        
        content_layout.addStretch()
        
        layout.addWidget(self.content_widget)
        
        # Initially show no route selected
        self.set_route(None)
    
    def set_route(self, route_item: Optional[RouteItem]):
        """Set the current route for calculations.
        
        Args:
            route_item: The RouteItem to use for calculations, or None
        """
        self.current_route_item = route_item
        
        if route_item is None:
            # Show "no route" message
            self.no_route_label.show()
            self.content_widget.hide()
        else:
            # Show calculator
            self.no_route_label.hide()
            self.content_widget.show()
            
            route_data = route_item.get_route_data()
            self.route_name_label.setText(f"Route: {route_data.name}")
            
            # Update calculations
            self.update_calculations()
    
    def update_calculations(self):
        """Update all calculated values based on current route and hyperdrive."""
        if self.current_route_item is None:
            return
        
        route_data = self.current_route_item.get_route_data()
        
        # Get route length
        length = self.current_route_item.calculate_length()
        self.length_display.setText(f"Length: {length:.1f} HSU")
        
        # Display route class
        self.class_display.setText(f"Class: {route_data.route_class}")
        
        # Display travel type
        travel_type_display = route_data.travel_type.replace("_", " ").title()
        self.type_display.setText(f"Type: {travel_type_display}")
        
        # Display hazards
        if route_data.hazards:
            hazards_str = ", ".join([h.replace("_", " ").title() for h in route_data.hazards])
            self.hazards_display.setText(f"Hazards: {hazards_str}")
        else:
            self.hazards_display.setText("Hazards: None")
        
        # Calculate speed factor
        speed_factor = 1.0
        
        # Apply route class modifier
        speed_factor *= self.ROUTE_CLASS_MODIFIERS.get(route_data.route_class, 1.0)
        
        # Apply travel type modifier
        speed_factor *= self.TRAVEL_TYPE_MODIFIERS.get(route_data.travel_type, 1.0)
        
        # Apply hazard modifiers (multiplicative)
        for hazard in route_data.hazards:
            speed_factor *= self.HAZARD_MODIFIERS.get(hazard, 1.0)
        
        self.speed_display.setText(f"Speed Factor: {speed_factor:.2f}x")
        
        # Calculate travel time (placeholder formula)
        # Base: 1 HSU = 1 hour at x1 hyperdrive
        hyperdrive_rating = self.hyperdrive_combo.currentData()
        hyperdrive_multiplier = self.HYPERDRIVE_RATINGS.get(hyperdrive_rating, 1.0)
        
        # Time = (length / hyperdrive) / speed_factor
        base_time = length / hyperdrive_multiplier
        travel_time = base_time / speed_factor
        
        self.time_display.setText(f"Travel Time: {travel_time:.1f} hours")


class StatsInspector(QWidget):
    """Container widget with tabs for System, Route, and Calculator stats.
    
    This widget contains a QTabWidget that switches between different
    stats editors based on what is selected in the scene.
    """
    
    def __init__(self, system_items_dict: Dict[str, SystemItem], parent=None):
        """Initialize the stats inspector.
        
        Args:
            system_items_dict: Dictionary mapping system IDs to SystemItem instances
            parent: Parent widget
        """
        super().__init__(parent)
        self.system_items = system_items_dict
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create the three tabs
        self.system_stats_widget = StatsWidget()
        self.route_stats_widget = RouteStatsWidget(system_items_dict)
        self.calculator_widget = TravelCalculatorWidget()
        
        # Add tabs
        self.tab_widget.addTab(self.system_stats_widget, "System")
        self.tab_widget.addTab(self.route_stats_widget, "Route")
        self.tab_widget.addTab(self.calculator_widget, "Calculator")
        
        layout.addWidget(self.tab_widget)
    
    def set_selected_system(self, system_data: Optional[SystemData]):
        """Set the selected system and switch to System tab.
        
        Args:
            system_data: The selected SystemData, or None
        """
        self.system_stats_widget.set_system(system_data)
        if system_data is not None:
            self.tab_widget.setCurrentWidget(self.system_stats_widget)
    
    def set_selected_route(self, route_item: Optional[RouteItem]):
        """Set the selected route and switch to Route tab.
        
        Args:
            route_item: The selected RouteItem, or None
        """
        self.route_stats_widget.set_route(route_item)
        self.calculator_widget.set_route(route_item)
        if route_item is not None:
            self.tab_widget.setCurrentWidget(self.route_stats_widget)
    
    def clear_selection(self):
        """Clear all selections (no system or route selected)."""
        self.system_stats_widget.set_system(None)
        self.route_stats_widget.set_route(None)
        self.calculator_widget.set_route(None)


class StarMapEditor(QMainWindow):
    """Main window for the Star Map Editor application."""
    
    # UI Constants
    SENSITIVITY_SCALE_FACTOR = 100  # Multiplier for slider values to sensitivity values
    
    def __init__(self):
        super().__init__()
        
        # Project data
        self.project = MapProject()
        self.current_file_path: Optional[Path] = None
        self.unsaved_changes = False
        
        # Graphics items storage
        self.template_items: Dict[str, TemplateItem] = {}  # id -> TemplateItem
        self.system_items: Dict[str, SystemItem] = {}  # id -> SystemItem
        self.route_items: Dict[str, RouteItem] = {}  # id -> RouteItem
        self.route_group_labels: Dict[str, QGraphicsTextItem] = {}  # group_id -> label
        
        # Current mode
        self.current_mode = None  # None, 'template', 'systems', 'routes', 'zones'
        
        # Selected template for workspace operations
        self.selected_template: Optional[TemplateItem] = None
        
        # Selected route for editing operations
        self.selected_route: Optional[RouteItem] = None
        
        # Preview item for new system placement
        self.preview_system_item: Optional[SystemItem] = None
        
        # Route creation state
        self.route_creation_start_system_id: Optional[str] = None
        self.route_preview_line: Optional[QGraphicsPathItem] = None
        
        # Route group selection state
        self.routes_selected_for_group: set[str] = set()  # Track route IDs selected for grouping
        
        # Theme state
        self.is_dark_mode = True  # Default to dark mode
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Star Map Editor')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create mode button bar (wrapped in widget with fixed height)
        self.mode_toolbar_widget = QWidget()
        self.mode_toolbar_widget.setFixedHeight(40)
        mode_layout = QHBoxLayout(self.mode_toolbar_widget)
        mode_layout.setContentsMargins(4, 2, 4, 2)
        mode_layout.setSpacing(4)
        
        # Template mode button
        self.template_btn = QPushButton('Template Mode')
        self.template_btn.setCheckable(True)
        self.template_btn.clicked.connect(self.toggle_template_mode)
        mode_layout.addWidget(self.template_btn)
        
        # Systems mode button
        self.systems_btn = QPushButton('Systems Mode')
        self.systems_btn.setCheckable(True)
        self.systems_btn.clicked.connect(self.toggle_systems_mode)
        mode_layout.addWidget(self.systems_btn)
        
        # Routes mode button (placeholder)
        self.routes_btn = QPushButton('Routes')
        self.routes_btn.setCheckable(True)
        self.routes_btn.clicked.connect(self.show_routes)
        mode_layout.addWidget(self.routes_btn)
        
        # Zones mode button (placeholder)
        self.zones_btn = QPushButton('Zones')
        self.zones_btn.setCheckable(True)
        self.zones_btn.clicked.connect(self.show_zones)
        mode_layout.addWidget(self.zones_btn)
        
        # Stats button
        self.stats_btn = QPushButton('Stats')
        self.stats_btn.setCheckable(True)
        self.stats_btn.clicked.connect(self.show_stats)
        mode_layout.addWidget(self.stats_btn)
        
        # Add separator
        mode_layout.addSpacing(20)
        
        # System Icon Size control (UI SPACE: affects visual size only)
        mode_layout.addWidget(QLabel('System Icon Size:'))
        self.icon_size_small_btn = QPushButton('Small')
        self.icon_size_small_btn.setCheckable(True)
        self.icon_size_small_btn.clicked.connect(lambda: self.set_system_icon_size('small'))
        mode_layout.addWidget(self.icon_size_small_btn)
        
        self.icon_size_medium_btn = QPushButton('Medium')
        self.icon_size_medium_btn.setCheckable(True)
        self.icon_size_medium_btn.setChecked(True)  # Default
        self.icon_size_medium_btn.clicked.connect(lambda: self.set_system_icon_size('medium'))
        mode_layout.addWidget(self.icon_size_medium_btn)
        
        self.icon_size_large_btn = QPushButton('Large')
        self.icon_size_large_btn.setCheckable(True)
        self.icon_size_large_btn.clicked.connect(lambda: self.set_system_icon_size('large'))
        mode_layout.addWidget(self.icon_size_large_btn)
        
        mode_layout.addStretch()
        
        main_layout.addWidget(self.mode_toolbar_widget)
        
        # Create pan sensitivity controls (always visible, wrapped in widget with fixed height)
        self.pan_sensitivity_widget = QWidget()
        self.pan_sensitivity_widget.setFixedHeight(28)
        pan_sensitivity_layout = QHBoxLayout(self.pan_sensitivity_widget)
        pan_sensitivity_layout.setContentsMargins(4, 2, 4, 2)
        pan_sensitivity_layout.setSpacing(4)
        
        pan_sensitivity_layout.addWidget(QLabel('Pan Sensitivity:'))
        self.pan_sensitivity_slider = QSlider(Qt.Horizontal)
        self.pan_sensitivity_slider.setMinimum(int(0.5 * self.SENSITIVITY_SCALE_FACTOR))
        self.pan_sensitivity_slider.setMaximum(int(5.0 * self.SENSITIVITY_SCALE_FACTOR))
        self.pan_sensitivity_slider.setValue(int(1.0 * self.SENSITIVITY_SCALE_FACTOR))
        self.pan_sensitivity_slider.setMaximumWidth(200)
        self.pan_sensitivity_slider.valueChanged.connect(self.on_pan_sensitivity_changed)
        pan_sensitivity_layout.addWidget(self.pan_sensitivity_slider)
        
        self.pan_sensitivity_label = QLabel('1.0x')
        self.pan_sensitivity_label.setMinimumWidth(40)
        pan_sensitivity_layout.addWidget(self.pan_sensitivity_label)
        
        pan_sensitivity_layout.addStretch()
        main_layout.addWidget(self.pan_sensitivity_widget)
        
        # Create status label for mode indication (before toolbars, so we can embed it)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #f0f0f0; }")
        
        # Create workspace toolbar (visible only in template mode)
        self.workspace_toolbar = self.create_workspace_toolbar()
        main_layout.addWidget(self.workspace_toolbar)
        self.workspace_toolbar.hide()
        
        # Create routes workspace toolbar (visible only in routes mode)
        self.routes_toolbar = self.create_routes_toolbar()
        main_layout.addWidget(self.routes_toolbar)
        self.routes_toolbar.hide()
        
        # Create fallback status bar (visible when no toolbar with status is shown)
        self.fallback_status_widget = QWidget()
        self.fallback_status_widget.setFixedHeight(24)
        self.fallback_status_widget.setStyleSheet("QWidget { background-color: #e0e0e0; }")
        fallback_status_layout = QHBoxLayout(self.fallback_status_widget)
        fallback_status_layout.setContentsMargins(4, 2, 4, 2)
        fallback_status_layout.setSpacing(4)
        fallback_status_layout.addStretch()
        # Create a second status label for fallback (when no toolbar is visible)
        self.fallback_status_label = QLabel()
        self.fallback_status_label.setStyleSheet("QLabel { padding: 5px; background-color: #f0f0f0; }")
        fallback_status_layout.addWidget(self.fallback_status_label)
        main_layout.addWidget(self.fallback_status_widget)
        self.fallback_status_widget.hide()  # Hidden by default
        
        # Update status message after toolbars are created
        self.update_status_message()
        
        # Create graphics scene and view (need to do this before stats inspector)
        self.scene = GridOverlay()
        self.view = MapView(self.scene)
        self.view.setFocusPolicy(Qt.StrongFocus)
        self.view.system_click.connect(self.handle_system_click)
        self.view.start_route_drawing.connect(self.handle_start_route_drawing)
        self.view.finish_route_drawing.connect(self.handle_finish_route_drawing)
        self.view.route_group_toggle.connect(self.toggle_route_for_group)
        self.view.route_delete_requested.connect(self.handle_route_delete_request)
        self.view.item_modified.connect(self.on_item_modified)
        self.view.system_context_menu_requested.connect(self.show_system_route_context_menu)
        self.view.segment_context_menu_requested.connect(self.show_segment_context_menu)
        
        # Connect scene selection changed signal
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
        # Create stats inspector (will be placed in splitter, visible only in stats mode)
        # Pass system_items dict for route calculations
        self.stats_inspector = StatsInspector(self.system_items)
        self.stats_inspector.hide()
        
        # Fixed, narrow width for the stats sidebar
        self.stats_inspector.setMinimumWidth(260)
        self.stats_inspector.setMaximumWidth(320)
        
        # Create a horizontal splitter for main content
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.view)
        self.main_splitter.addWidget(self.stats_inspector)
        
        # Give more weight to the map view
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 1)
        
        # Initial sizes: full width for map, collapsed stats sidebar
        # Note: Using [1, 0] to indicate map gets all available width (any positive value works)
        # and stats sidebar is collapsed (0 width). Actual pixel values will be calculated by Qt.
        self.main_splitter.setSizes([1, 0])
        
        # Add splitter to main_layout instead of adding view and stats_inspector vertically
        main_layout.addWidget(self.main_splitter)
        
        # Apply dark mode by default
        self.apply_dark_mode()
        
        self.show()
    
    def create_menu_bar(self):
        """Create the File menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # New Project
        new_action = QAction('&New Project', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        # Open Project
        open_action = QAction('&Open Project...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Save Project
        save_action = QAction('&Save Project', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        # Save Project As
        save_as_action = QAction('Save Project &As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Export Map Data (placeholder)
        export_action = QAction('&Export Map Data...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_map_data_action)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Quit
        quit_action = QAction('&Quit', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        # Dark Mode action
        self.dark_mode_action = QAction('&Dark Mode', self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setChecked(True)  # Default to dark mode
        self.dark_mode_action.triggered.connect(self.apply_dark_mode)
        view_menu.addAction(self.dark_mode_action)
        
        # Light Mode action
        self.light_mode_action = QAction('&Light Mode', self)
        self.light_mode_action.setCheckable(True)
        self.light_mode_action.setChecked(False)
        self.light_mode_action.triggered.connect(self.apply_light_mode)
        view_menu.addAction(self.light_mode_action)
    
    def create_workspace_toolbar(self) -> QWidget:
        """Create the workspace toolbar for template mode."""
        toolbar_widget = QWidget()
        toolbar_widget.setFixedHeight(32)
        toolbar_widget.setStyleSheet("QWidget { background-color: #e0e0e0; }")
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(4, 2, 4, 2)
        toolbar_layout.setSpacing(4)
        
        # Load Template button
        self.load_template_btn = QPushButton('Load Template')
        self.load_template_btn.clicked.connect(self.load_template)
        toolbar_layout.addWidget(self.load_template_btn)
        
        # Delete Template button
        self.delete_template_btn = QPushButton('Delete Template')
        self.delete_template_btn.clicked.connect(self.delete_template)
        self.delete_template_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_template_btn)
        
        # Reset Transform button
        self.reset_transform_btn = QPushButton('Reset Transform')
        self.reset_transform_btn.clicked.connect(self.reset_template_transform)
        self.reset_transform_btn.setEnabled(False)
        toolbar_layout.addWidget(self.reset_transform_btn)
        
        # Lock/Unlock button
        self.lock_btn = QPushButton('Lock Template')
        self.lock_btn.setCheckable(True)
        self.lock_btn.clicked.connect(self.toggle_template_lock)
        self.lock_btn.setEnabled(False)
        toolbar_layout.addWidget(self.lock_btn)
        
        # Opacity controls
        toolbar_layout.addWidget(QLabel('Opacity:'))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setMaximumWidth(150)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.opacity_slider.setEnabled(False)
        toolbar_layout.addWidget(self.opacity_slider)
        
        self.opacity_label = QLabel('100%')
        self.opacity_label.setMinimumWidth(40)
        toolbar_layout.addWidget(self.opacity_label)
        
        # Template Scale controls (IMAGE LAYER: affects pixmap rendering only)
        toolbar_layout.addWidget(QLabel('Template Scale:'))
        self.template_scale_slider = QSlider(Qt.Horizontal)
        self.template_scale_slider.setMinimum(10)  # 10% = 0.1x
        self.template_scale_slider.setMaximum(500)  # 500% = 5.0x
        self.template_scale_slider.setValue(100)  # 100% = 1.0x
        self.template_scale_slider.setMaximumWidth(150)
        self.template_scale_slider.valueChanged.connect(self.on_template_scale_changed)
        self.template_scale_slider.setEnabled(False)
        toolbar_layout.addWidget(self.template_scale_slider)
        
        self.template_scale_label = QLabel('100%')
        self.template_scale_label.setMinimumWidth(50)
        toolbar_layout.addWidget(self.template_scale_label)
        
        # Scale Sensitivity controls
        toolbar_layout.addWidget(QLabel('Scale Sensitivity:'))
        self.scale_sensitivity_slider = QSlider(Qt.Horizontal)
        self.scale_sensitivity_slider.setMinimum(int(0.1 * self.SENSITIVITY_SCALE_FACTOR))
        self.scale_sensitivity_slider.setMaximum(int(3.0 * self.SENSITIVITY_SCALE_FACTOR))
        self.scale_sensitivity_slider.setValue(int(1.0 * self.SENSITIVITY_SCALE_FACTOR))
        self.scale_sensitivity_slider.setMaximumWidth(150)
        self.scale_sensitivity_slider.valueChanged.connect(self.on_scale_sensitivity_changed)
        toolbar_layout.addWidget(self.scale_sensitivity_slider)
        
        self.scale_sensitivity_label = QLabel('1.0x')
        self.scale_sensitivity_label.setMinimumWidth(40)
        toolbar_layout.addWidget(self.scale_sensitivity_label)
        
        toolbar_layout.addStretch()
        
        # Add status label (right-aligned)
        toolbar_layout.addWidget(self.status_label)
        
        return toolbar_widget
    
    def create_routes_toolbar(self) -> QWidget:
        """Create the workspace toolbar for routes mode - compact 3-row design."""
        toolbar_widget = QWidget()
        toolbar_widget.setFixedHeight(80)
        toolbar_widget.setStyleSheet("QWidget { background-color: #e0e0e0; }")
        toolbar_layout = QVBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(4, 2, 4, 2)
        toolbar_layout.setSpacing(2)  # Minimal spacing between rows (vertical layout)
        
        # === Row 1: Route creation instructions ===
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(5)
        
        # Info label for polyline route creation (smaller font)
        info_label = QLabel('Click System A → intermediate points → System B | ESC/Right-click to cancel')
        info_label.setStyleSheet("color: #555; font-style: italic; font-size: 9pt;")
        row1_layout.addWidget(info_label)
        
        row1_layout.addStretch()
        
        # Add status label (right-aligned, smaller)
        self.status_label.setStyleSheet("QLabel { padding: 2px; background-color: #f0f0f0; font-size: 9pt; }")
        row1_layout.addWidget(self.status_label)
        
        toolbar_layout.addLayout(row1_layout)
        
        # === Row 2: Route selection and grouping ===
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(5)
        
        # Current Route label and dropdown
        route_label = QLabel('Route:')
        route_label.setStyleSheet("font-size: 9pt;")
        row2_layout.addWidget(route_label)
        
        # Route selection dropdown (more compact)
        self.route_selector = QComboBox()
        self.route_selector.setMinimumWidth(150)
        self.route_selector.setMaximumWidth(250)
        self.route_selector.setStyleSheet("QComboBox { font-size: 9pt; }")
        self.route_selector.currentIndexChanged.connect(self.on_route_selector_changed)
        row2_layout.addWidget(self.route_selector)
        
        row2_layout.addSpacing(10)
        
        # Create Route Group button (smaller)
        self.create_group_btn = QPushButton('Create Group')
        self.create_group_btn.setStyleSheet("QPushButton { font-size: 9pt; padding: 2px 8px; }")
        self.create_group_btn.setToolTip('Create a route group from selected routes (CTRL+Click to select)')
        self.create_group_btn.clicked.connect(self.create_route_group_dialog)
        row2_layout.addWidget(self.create_group_btn)
        
        # Info label for grouping (smaller)
        group_info_label = QLabel('CTRL+Click routes to select')
        group_info_label.setStyleSheet("color: #555; font-style: italic; font-size: 8pt;")
        row2_layout.addWidget(group_info_label)
        
        row2_layout.addStretch()
        
        toolbar_layout.addLayout(row2_layout)
        
        # === Row 3: Route editing buttons ===
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(5)
        
        # Compact system chain display (inline text instead of list widget)
        chain_label = QLabel('Systems:')
        chain_label.setStyleSheet("font-size: 9pt;")
        row3_layout.addWidget(chain_label)
        
        # Use a label instead of QListWidget for compact display
        self.route_system_chain_label = QLabel('(No route selected)')
        self.route_system_chain_label.setStyleSheet("QLabel { background-color: white; padding: 2px 5px; border: 1px solid #aaa; font-size: 9pt; }")
        self.route_system_chain_label.setMinimumWidth(150)
        row3_layout.addWidget(self.route_system_chain_label)
        
        row3_layout.addSpacing(10)
        
        # Action buttons for route editing (smaller, compact)
        button_style = "QPushButton { font-size: 9pt; padding: 2px 6px; }"
        
        self.insert_system_btn = QPushButton('Insert')
        self.insert_system_btn.setStyleSheet(button_style)
        self.insert_system_btn.setToolTip('Insert selected system into route')
        self.insert_system_btn.clicked.connect(self.insert_system_into_route)
        self.insert_system_btn.setEnabled(False)
        row3_layout.addWidget(self.insert_system_btn)
        
        self.remove_system_btn = QPushButton('Remove')
        self.remove_system_btn.setStyleSheet(button_style)
        self.remove_system_btn.setToolTip('Remove selected system from route')
        self.remove_system_btn.clicked.connect(self.remove_system_from_route)
        self.remove_system_btn.setEnabled(False)
        row3_layout.addWidget(self.remove_system_btn)
        
        self.split_route_btn = QPushButton('Split')
        self.split_route_btn.setStyleSheet(button_style)
        self.split_route_btn.setToolTip('Split route at selected system')
        self.split_route_btn.clicked.connect(self.split_route_at_system)
        self.split_route_btn.setEnabled(False)
        row3_layout.addWidget(self.split_route_btn)
        
        self.merge_routes_btn = QPushButton('Merge')
        self.merge_routes_btn.setStyleSheet(button_style)
        self.merge_routes_btn.setToolTip('Merge two routes (CTRL+Click to select)')
        self.merge_routes_btn.clicked.connect(self.merge_selected_routes)
        self.merge_routes_btn.setEnabled(False)
        row3_layout.addWidget(self.merge_routes_btn)
        
        row3_layout.addStretch()
        
        toolbar_layout.addLayout(row3_layout)
        
        return toolbar_widget
    
    # ===== Theme Management =====
    
    def apply_dark_mode(self):
        """Apply dark mode theme to the application."""
        if not self.dark_mode_action.isChecked():
            # User unchecked dark mode, switch to light
            self.light_mode_action.setChecked(True)
            self.apply_light_mode()
            return
        
        # Uncheck light mode
        self.light_mode_action.setChecked(False)
        self.is_dark_mode = True
        
        # Set dark background for the scene
        self.scene.setBackgroundBrush(QColor(5, 8, 20))  # ≈ #050814
        
        # Update grid color for dark mode
        self.scene.grid_color = QColor(144, 238, 144, 80)  # Lighter, more transparent green
        
        # Update route colors for better visibility on dark background
        RouteItem.NORMAL_COLOR = QColor(100, 200, 255)  # Light blue
        RouteItem.SELECTED_COLOR = QColor(255, 255, 100)  # Yellow
        RouteItem.GROUP_SELECTION_COLOR = QColor(255, 150, 255)  # Magenta
        
        # Update all existing routes
        for route_item in self.route_items.values():
            route_item.update_visual_state()
        
        # Update system label colors
        for system_item in self.system_items.values():
            if hasattr(system_item, 'label'):
                system_item.label.setDefaultTextColor(Qt.white)
        
        # Update route group label colors
        for label in self.route_group_labels.values():
            label.setDefaultTextColor(QColor(200, 220, 255))
        
        # Force scene update
        self.scene.update()
    
    def apply_light_mode(self):
        """Apply light mode theme to the application."""
        if not self.light_mode_action.isChecked():
            # User unchecked light mode, switch to dark
            self.dark_mode_action.setChecked(True)
            self.apply_dark_mode()
            return
        
        # Uncheck dark mode
        self.dark_mode_action.setChecked(False)
        self.is_dark_mode = False
        
        # Set light background for the scene
        self.scene.setBackgroundBrush(QColor(240, 240, 240))  # Light gray
        
        # Update grid color for light mode
        self.scene.grid_color = QColor(100, 150, 100, 128)  # Darker green, more visible
        
        # Update route colors for better visibility on light background
        RouteItem.NORMAL_COLOR = QColor(50, 100, 200)  # Darker blue
        RouteItem.SELECTED_COLOR = QColor(200, 150, 0)  # Dark yellow/gold
        RouteItem.GROUP_SELECTION_COLOR = QColor(200, 50, 200)  # Dark magenta
        
        # Update all existing routes
        for route_item in self.route_items.values():
            route_item.update_visual_state()
        
        # Update system label colors
        for system_item in self.system_items.values():
            if hasattr(system_item, 'label'):
                system_item.label.setDefaultTextColor(Qt.black)
        
        # Update route group label colors
        for label in self.route_group_labels.values():
            label.setDefaultTextColor(QColor(0, 0, 100))
        
        # Force scene update
        self.scene.update()
    
    # ===== File Menu Actions =====
    
    def new_project(self):
        """Create a new project."""
        if not self.check_unsaved_changes():
            return
        
        # Clear everything
        self.scene.clear()
        self.project = MapProject()
        self.template_items.clear()
        self.system_items.clear()
        self.route_items.clear()
        self.route_group_labels.clear()
        self.current_file_path = None
        self.unsaved_changes = False
        
        # Refresh route selector (should be empty now)
        self.refresh_route_selector()
        
        # Reset view
        self.view.resetTransform()
        self.view.current_zoom = 1.0
        self.scene.show_grid = False
        
        # Reset mode
        self.set_mode(None)
        
        self.update_window_title()
        self.update_status_message()
    
    def open_project(self):
        """Open an existing project."""
        if not self.check_unsaved_changes():
            return
        
        # Default to Saves directory
        saves_dir = Path(__file__).parent / "Saves"
        saves_dir.mkdir(exist_ok=True)
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            str(saves_dir),
            "Star Map Project Files (*.swmproj);;All Files (*)"
        )
        
        if file_path:
            project = load_project(Path(file_path))
            if project:
                # Clear current state
                self.scene.clear()
                self.template_items.clear()
                self.system_items.clear()
                self.route_items.clear()
                self.route_group_labels.clear()
                
                # Load project
                self.project = project
                self.current_file_path = Path(file_path)
                self.unsaved_changes = False
                
                # Restore templates
                for template_data in self.project.templates:
                    self.add_template_to_scene(template_data)
                
                # Restore systems
                for system_data in self.project.systems.values():
                    self.add_system_to_scene(system_data)
                
                # Restore routes
                for route_data in self.project.routes.values():
                    self.add_route_to_scene(route_data)
                
                # Restore route group labels
                self.rebuild_route_group_labels()
                
                # Refresh route selector with loaded routes and groups
                self.refresh_route_selector()
                
                # Enable grid if there are templates or systems
                # Grid is now infinite and independent of template size
                if self.project.templates or self.project.systems:
                    self.scene.show_grid = True
                    
                # Set a reasonable initial scene rect for viewing
                if self.template_items:
                    first_template = list(self.template_items.values())[0]
                    template_bounds = first_template.boundingRect()
                    padding = 1000
                    self.scene.setSceneRect(
                        template_bounds.x() - padding,
                        template_bounds.y() - padding,
                        template_bounds.width() + 2 * padding,
                        template_bounds.height() + 2 * padding
                    )
                    self.view.fitInView(first_template.boundingRect(), Qt.KeepAspectRatio)
                    self.view.update_zoom_indicator()
                elif self.project.systems:
                    # No templates but has systems - set view based on systems
                    # Calculate bounding box of all systems
                    min_x = min_y = float('inf')
                    max_x = max_y = float('-inf')
                    for system_data in self.project.systems.values():
                        pos = system_data.position
                        min_x = min(min_x, pos.x())
                        min_y = min(min_y, pos.y())
                        max_x = max(max_x, pos.x())
                        max_y = max(max_y, pos.y())
                    
                    padding = 500
                    self.scene.setSceneRect(
                        min_x - padding,
                        min_y - padding,
                        (max_x - min_x) + 2 * padding,
                        (max_y - min_y) + 2 * padding
                    )
                    self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
                    self.view.update_zoom_indicator()
                
                self.update_window_title()
                QMessageBox.information(
                    self,
                    "Project Loaded",
                    f"Project loaded successfully from:\n{file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Load Failed",
                    f"Could not load project from:\n{file_path}"
                )
    
    def save_project(self):
        """Save the current project."""
        if self.current_file_path:
            if save_project(self.project, self.current_file_path):
                self.unsaved_changes = False
                self.update_window_title()
                self.set_status_text("Project saved successfully")
            else:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    f"Could not save project to:\n{self.current_file_path}"
                )
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Save the current project with a new name."""
        # Default to Saves directory
        saves_dir = Path(__file__).parent / "Saves"
        saves_dir.mkdir(exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            str(saves_dir / "map.swmproj"),
            "Star Map Project Files (*.swmproj);;All Files (*)"
        )
        
        if file_path:
            # Ensure .swmproj extension
            file_path = Path(file_path)
            if file_path.suffix != '.swmproj':
                file_path = file_path.with_suffix('.swmproj')
            
            if save_project(self.project, file_path):
                self.current_file_path = file_path
                self.unsaved_changes = False
                self.update_window_title()
                QMessageBox.information(
                    self,
                    "Save Successful",
                    f"Project saved to:\n{file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    f"Could not save project to:\n{file_path}"
                )
    
    def export_map_data_action(self):
        """Export map data to game-readable format."""
        # Default to Exports directory
        exports_dir = Path(__file__).parent / "Exports"
        exports_dir.mkdir(exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Map Data",
            str(exports_dir / "map.json"),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if export_map_data(self.project, Path(file_path)):
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Map data exported to:\n{file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Could not export map data to:\n{file_path}"
                )
    
    def check_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes and prompt user.
        
        Returns:
            True if it's safe to proceed, False if user cancelled
        """
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before proceeding?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_project()
                return not self.unsaved_changes  # Only proceed if save succeeded
            elif reply == QMessageBox.Cancel:
                return False
        
        return True
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events for the main window."""
        if event.key() == Qt.Key_Delete:
            # Delete selected route in routes mode
            if self.current_mode == 'routes':
                selected_items = self.scene.selectedItems()
                for item in selected_items:
                    if isinstance(item, RouteItem):
                        route_data = item.get_route_data()
                        reply = QMessageBox.question(
                            self,
                            "Delete Route",
                            f"Delete route '{route_data.name}'?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.Yes:
                            self.remove_route(route_data.id)
                        event.accept()
                        return
        super().keyPressEvent(event)
    
    def update_window_title(self):
        """Update the window title with current file name."""
        if self.current_file_path:
            title = f"Star Map Editor - {self.current_file_path.name}"
        else:
            title = "Star Map Editor - Untitled"
        
        if self.unsaved_changes:
            title += " *"
        
        self.setWindowTitle(title)
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes."""
        self.unsaved_changes = True
        self.update_window_title()
    
    # ===== Mode Management =====
    
    def update_status_message(self):
        """Update the status label based on current mode."""
        if self.current_mode == 'template':
            self.status_label.setText("Template mode active: Click to select template, drag to move, Ctrl+wheel to scale.")
        elif self.current_mode == 'systems':
            self.fallback_status_label.setText("Mode: System placement – left-click to place a system, right-click to edit")
        elif self.current_mode == 'routes':
            self.status_label.setText("Routes mode: Click system A → click intermediate points → click system B. ESC or right-click to cancel.")
        else:
            self.fallback_status_label.setText("Ready")
    
    def set_status_text(self, text: str):
        """Set status text in the appropriate label based on current mode.
        
        Args:
            text: The status text to display
        """
        if self.current_mode in ('template', 'routes'):
            self.status_label.setText(text)
        else:
            self.fallback_status_label.setText(text)
    
    def set_mode(self, mode: Optional[str]):
        """Set the current editor mode.
        
        Args:
            mode: The mode to activate ('template', 'systems', 'routes', 'zones', 'stats', or None)
        """
        self.current_mode = mode
        
        # Update button states
        self.template_btn.setChecked(mode == 'template')
        self.systems_btn.setChecked(mode == 'systems')
        self.routes_btn.setChecked(mode == 'routes')
        self.zones_btn.setChecked(mode == 'zones')
        self.stats_btn.setChecked(mode == 'stats')
        
        # Update button styles
        for btn, btn_mode in [(self.template_btn, 'template'),
                               (self.systems_btn, 'systems'), 
                               (self.routes_btn, 'routes'),
                               (self.zones_btn, 'zones'),
                               (self.stats_btn, 'stats')]:
            if mode == btn_mode:
                btn.setStyleSheet("QPushButton:checked { background-color: #90EE90; }")
            else:
                btn.setStyleSheet("")
        
        # Update view mode
        self.view.systems_mode_active = (mode == 'systems')
        self.view.template_mode_active = (mode == 'template')
        self.view.routes_mode_active = (mode == 'routes')
        
        # Clear route creation state when leaving routes mode
        if mode != 'routes':
            self.cancel_route_creation()
            # Clear group selection when leaving routes mode
            for route_id in list(self.routes_selected_for_group):
                if route_id in self.route_items:
                    self.route_items[route_id].set_group_selection(False)
            self.routes_selected_for_group.clear()
        
        # Show/hide workspace toolbars and widgets
        if mode == 'template':
            self.workspace_toolbar.show()
            self.routes_toolbar.hide()
            self.fallback_status_widget.hide()
            self.stats_inspector.hide()
            # Collapse stats sidebar (main_splitter is always initialized in __init__)
            self.main_splitter.setSizes([1, 0])
        elif mode == 'routes':
            self.workspace_toolbar.hide()
            self.routes_toolbar.show()
            self.fallback_status_widget.hide()
            self.stats_inspector.hide()
            # Collapse stats sidebar
            self.main_splitter.setSizes([1, 0])
            # Refresh route selector when entering routes mode
            self.refresh_route_selector()
        elif mode == 'stats':
            self.workspace_toolbar.hide()
            self.routes_toolbar.hide()
            self.fallback_status_widget.hide()
            self.stats_inspector.show()
            # Map : Stats ≈ 3 : 1
            # Calculate reasonable sizes for stats sidebar
            total_width = self.main_splitter.width()
            # Handle case where widget hasn't been resized yet
            if total_width <= 0:
                total_width = 1200  # Use default window width as fallback
            stats_width = 280  # Default width for stats sidebar
            map_width = max(total_width - stats_width, total_width * 3 // 4)
            self.main_splitter.setSizes([map_width, stats_width])
            # Update stats inspector with current selection
            self.update_stats_inspector()
        else:
            self.workspace_toolbar.hide()
            self.routes_toolbar.hide()
            self.fallback_status_widget.show()
            self.stats_inspector.hide()
            # Collapse stats sidebar
            self.main_splitter.setSizes([1, 0])
        
        # Update status
        self.update_status_message()
    
    def toggle_template_mode(self):
        """Toggle template mode on/off."""
        if self.current_mode == 'template':
            self.set_mode(None)
        else:
            self.set_mode('template')
    
    def toggle_systems_mode(self):
        """Toggle systems placement mode on/off."""
        if self.current_mode == 'systems':
            self.set_mode(None)
        else:
            self.set_mode('systems')
    
    # ===== Template Management =====
    
    def load_template(self):
        """Load a new template image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Template Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        
        if file_path:
            # Create template data (IMAGE LAYER)
            template_data = TemplateData.create_new(file_path)
            self.project.add_template(template_data)
            
            # Add to scene
            template_item = self.add_template_to_scene(template_data)
            
            # If this is the first template, enable grid and fit view
            # Grid is now infinite and independent of template size
            if len(self.project.templates) == 1:
                self.scene.show_grid = True
                # Set a large scene rect for infinite grid coverage
                # This doesn't limit the grid, just provides a sensible initial view area
                template_bounds = template_item.boundingRect()
                padding = 1000  # Extra space around template
                self.scene.setSceneRect(
                    template_bounds.x() - padding,
                    template_bounds.y() - padding,
                    template_bounds.width() + 2 * padding,
                    template_bounds.height() + 2 * padding
                )
                self.view.resetTransform()
                self.view.current_zoom = 1.0
                self.view.fitInView(template_item.boundingRect(), Qt.KeepAspectRatio)
                self.view.update_zoom_indicator()
            
            # Update scene
            self.scene.update()
            self.view.setFocus()
            
            self.mark_unsaved_changes()
    
    def add_template_to_scene(self, template_data: TemplateData) -> TemplateItem:
        """Add a template to the scene.
        
        Args:
            template_data: The TemplateData to add
            
        Returns:
            The created TemplateItem
        """
        template_item = TemplateItem(template_data)
        self.scene.addItem(template_item)
        self.template_items[template_data.id] = template_item
        return template_item
    
    def delete_template(self):
        """Delete the currently selected template."""
        if self.selected_template:
            template_data = self.selected_template.get_template_data()
            
            # Remove from scene
            self.scene.removeItem(self.selected_template)
            
            # Remove from storage
            del self.template_items[template_data.id]
            self.project.remove_template(template_data.id)
            
            # Clear selection
            self.selected_template = None
            self.update_workspace_controls()
            
            self.mark_unsaved_changes()
    
    def reset_template_transform(self):
        """Reset the selected template's transform."""
        if self.selected_template:
            self.selected_template.reset_transform()
            self.mark_unsaved_changes()
    
    def toggle_template_lock(self):
        """Toggle lock state of selected template."""
        if self.selected_template:
            is_locked = self.lock_btn.isChecked()
            self.selected_template.set_locked(is_locked)
            self.lock_btn.setText('Unlock Template' if is_locked else 'Lock Template')
            self.mark_unsaved_changes()
    
    def on_opacity_changed(self, value: int):
        """Handle opacity slider change.
        
        Args:
            value: Opacity percentage (0-100)
        """
        if self.selected_template:
            opacity = value / 100.0
            self.selected_template.set_template_opacity(opacity)
            self.opacity_label.setText(f'{value}%')
            self.mark_unsaved_changes()
    
    def on_template_scale_changed(self, value: int):
        """Handle template scale slider change.
        
        IMAGE LAYER: This only affects pixmap rendering, not world coordinates.
        
        Args:
            value: Scale percentage (10-500 = 0.1x to 5.0x)
        """
        if self.selected_template:
            scale = value / 100.0
            # Set the scale directly (affects pixmap rendering only)
            self.selected_template.setScale(scale)
            self.selected_template.template_data.scale = scale
            self.template_scale_label.setText(f'{value}%')
            self.mark_unsaved_changes()
    
    def on_scale_sensitivity_changed(self, value: int):
        """Handle scale sensitivity slider change.
        
        Args:
            value: Scale sensitivity slider value (scaled by SENSITIVITY_SCALE_FACTOR)
        """
        sensitivity = value / self.SENSITIVITY_SCALE_FACTOR
        self.view.set_template_scale_sensitivity(sensitivity)
        self.scale_sensitivity_label.setText(f'{sensitivity:.1f}x')
    
    def on_pan_sensitivity_changed(self, value: int):
        """Handle pan sensitivity slider change.
        
        Args:
            value: Pan sensitivity slider value (scaled by SENSITIVITY_SCALE_FACTOR)
        """
        sensitivity = value / self.SENSITIVITY_SCALE_FACTOR
        self.view.set_pan_sensitivity(sensitivity)
        self.pan_sensitivity_label.setText(f'{sensitivity:.1f}x')
    
    def on_selection_changed(self):
        """Handle scene selection change."""
        # Find selected template
        selected_items = self.scene.selectedItems()
        template_selected = None
        route_selected = None
        
        for item in selected_items:
            if isinstance(item, TemplateItem):
                template_selected = item
            elif isinstance(item, RouteItem):
                route_selected = item
        
        self.selected_template = template_selected
        self.update_workspace_controls()
        self.update_route_workspace_controls(route_selected)
        
        # Enable/disable route editing mode in the view
        if self.current_mode == 'routes' and route_selected:
            self.view.route_editing_mode_active = True
        else:
            self.view.route_editing_mode_active = False
        
        # Update stats inspector if in stats mode
        if self.current_mode == 'stats':
            self.update_stats_inspector()
    
    def on_item_modified(self):
        """Handle item modification (movement, etc.)."""
        # Mark project as having unsaved changes
        self.mark_unsaved_changes()
        # Update routes when systems are moved
        self.update_routes_for_system_movement()
    
    def update_workspace_controls(self):
        """Update workspace controls based on selection."""
        has_selection = self.selected_template is not None
        
        self.delete_template_btn.setEnabled(has_selection)
        self.reset_transform_btn.setEnabled(has_selection)
        self.lock_btn.setEnabled(has_selection)
        self.opacity_slider.setEnabled(has_selection)
        self.template_scale_slider.setEnabled(has_selection)
        
        if has_selection:
            # Update lock button
            is_locked = self.selected_template.get_template_data().locked
            self.lock_btn.setChecked(is_locked)
            self.lock_btn.setText('Unlock Template' if is_locked else 'Lock Template')
            
            # Update opacity slider
            opacity_value = int(self.selected_template.get_template_data().opacity * 100)
            self.opacity_slider.blockSignals(True)
            self.opacity_slider.setValue(opacity_value)
            self.opacity_slider.blockSignals(False)
            self.opacity_label.setText(f'{opacity_value}%')
            
            # Update template scale slider
            scale_value = int(self.selected_template.get_template_data().scale * 100)
            self.template_scale_slider.blockSignals(True)
            self.template_scale_slider.setValue(scale_value)
            self.template_scale_slider.blockSignals(False)
            self.template_scale_label.setText(f'{scale_value}%')
        else:
            self.lock_btn.setChecked(False)
            self.lock_btn.setText('Lock Template')
            self.opacity_slider.setValue(100)
            self.opacity_label.setText('100%')
            self.template_scale_slider.setValue(100)
            self.template_scale_label.setText('100%')
    
    def update_route_workspace_controls(self, route_selected: Optional[RouteItem]):
        """Update route workspace controls based on selection.
        
        Args:
            route_selected: The selected RouteItem, or None if no route selected
        """
        if not hasattr(self, 'route_selector'):
            return
        
        # Store currently selected route
        self.selected_route = route_selected
        
        # Get currently selected system (if any)
        selected_system = None
        for item in self.scene.selectedItems():
            if isinstance(item, SystemItem):
                selected_system = item
                break
        
        if route_selected:
            route_data = route_selected.get_route_data()
            
            # Update the route selector to match the selected route
            self.refresh_route_selector()
            
            # Set the selector to the current route (without triggering signal)
            for i in range(self.route_selector.count()):
                item_data = self.route_selector.itemData(i)
                if item_data and item_data.get('type') == 'route' and item_data.get('id') == route_data.id:
                    self.route_selector.blockSignals(True)
                    self.route_selector.setCurrentIndex(i)
                    self.route_selector.blockSignals(False)
                    break
            
            # Update system chain display (compact inline format)
            system_chain = route_data.get_system_chain()
            if hasattr(self, 'route_system_chain_label'):
                # Create compact system chain text
                system_names = []
                for sys_id in system_chain:
                    if sys_id in self.project.systems:
                        sys_name = self.project.systems[sys_id].name
                        system_names.append(sys_name)
                
                if system_names:
                    chain_text = ' → '.join(system_names)
                    # Truncate if too long
                    if len(chain_text) > 60:
                        chain_text = chain_text[:57] + '...'
                    self.route_system_chain_label.setText(chain_text)
                else:
                    self.route_system_chain_label.setText('(Empty route)')
            elif hasattr(self, 'route_system_list'):
                # Legacy support for QListWidget if it exists
                self.route_system_list.clear()
                for sys_id in system_chain:
                    if sys_id in self.project.systems:
                        sys_name = self.project.systems[sys_id].name
                        id_display = f"{sys_id[:8]}{'...' if len(sys_id) > 8 else ''}"
                        self.route_system_list.addItem(f"{sys_name} ({id_display})")
            
            # Enable/disable buttons based on context
            chain_length = len(system_chain)
            
            # Remove System: enabled if a system in the route is selected and route has >2 systems
            can_remove = (selected_system is not None and 
                         route_data.contains_system(selected_system.get_system_data().id) and
                         chain_length > 2)
            self.remove_system_btn.setEnabled(can_remove)
            
            # Split Route: enabled if a system in the route is selected and not at ends
            can_split = False
            if selected_system:
                sys_id = selected_system.get_system_data().id
                sys_index = route_data.get_system_index(sys_id)
                can_split = (sys_index > 0 and sys_index < chain_length - 1)
            self.split_route_btn.setEnabled(can_split)
            
            # Insert System: enabled if a system NOT in the route is selected
            can_insert = (selected_system is not None and
                         not route_data.contains_system(selected_system.get_system_data().id))
            self.insert_system_btn.setEnabled(can_insert)
            
            # Merge Routes: enabled if exactly 2 routes are selected for grouping
            can_merge = len(self.routes_selected_for_group) == 2
            self.merge_routes_btn.setEnabled(can_merge)
        else:
            # Refresh selector to show all routes/groups
            self.refresh_route_selector()
            
            # Reset selector to default
            self.route_selector.blockSignals(True)
            self.route_selector.setCurrentIndex(0)  # Select first item or empty
            self.route_selector.blockSignals(False)
            
            # Clear system chain display
            if hasattr(self, 'route_system_chain_label'):
                self.route_system_chain_label.setText('(No route selected)')
            elif hasattr(self, 'route_system_list'):
                self.route_system_list.clear()
            
            self.insert_system_btn.setEnabled(False)
            self.remove_system_btn.setEnabled(False)
            self.split_route_btn.setEnabled(False)
            
            # Merge can still work with group selection
            can_merge = len(self.routes_selected_for_group) == 2
            self.merge_routes_btn.setEnabled(can_merge)
    
    def refresh_route_selector(self):
        """Refresh the route selector dropdown with current routes and groups.
        
        Populates the dropdown with:
        - Route Groups (bold font)
        - Individual Routes (italic font)
        """
        if not hasattr(self, 'route_selector'):
            return
        
        # Block signals during refresh
        self.route_selector.blockSignals(True)
        
        # Store currently selected item
        current_index = self.route_selector.currentIndex()
        current_data = self.route_selector.itemData(current_index) if current_index >= 0 else None
        
        # Clear existing items
        self.route_selector.clear()
        
        # Add default "No selection" item
        self.route_selector.addItem("(No route selected)", {"type": "none"})
        
        # Add route groups with bold font
        for group_id, group in self.project.route_groups.items():
            self.route_selector.addItem(group.name, {"type": "group", "id": group_id})
            index = self.route_selector.count() - 1
            # Set bold font for groups
            font = QFont()
            font.setBold(True)
            self.route_selector.setItemData(index, font, Qt.FontRole)
        
        # Add individual routes with italic font
        for route_id, route in self.project.routes.items():
            self.route_selector.addItem(route.name, {"type": "route", "id": route_id})
            index = self.route_selector.count() - 1
            # Set italic font for routes
            font = QFont()
            font.setItalic(True)
            self.route_selector.setItemData(index, font, Qt.FontRole)
        
        # Try to restore previous selection
        if current_data:
            for i in range(self.route_selector.count()):
                item_data = self.route_selector.itemData(i)
                if item_data == current_data:
                    self.route_selector.setCurrentIndex(i)
                    break
        else:
            self.route_selector.setCurrentIndex(0)
        
        # Unblock signals
        self.route_selector.blockSignals(False)
    
    def on_route_selector_changed(self, index: int):
        """Handle route selector dropdown change.
        
        Args:
            index: The new index in the dropdown
        """
        if index < 0:
            return
        
        item_data = self.route_selector.itemData(index)
        if not item_data:
            return
        
        item_type = item_data.get('type')
        item_id = item_data.get('id')
        
        if item_type == 'route' and item_id:
            # Select the route in the scene
            if item_id in self.route_items:
                route_item = self.route_items[item_id]
                # Clear existing selection
                self.scene.clearSelection()
                # Select this route
                route_item.setSelected(True)
                # The selection change will trigger update_route_workspace_controls
        elif item_type == 'group' and item_id:
            # For groups, we could highlight all routes in the group
            # For now, just select all routes in the group
            if item_id in self.project.route_groups:
                group = self.project.route_groups[item_id]
                self.scene.clearSelection()
                for route_id in group.route_ids:
                    if route_id in self.route_items:
                        self.route_items[route_id].setSelected(True)
        elif item_type == 'none':
            # Clear selection
            self.scene.clearSelection()
    
    def set_system_icon_size(self, size: str):
        """Set the system icon size (UI SPACE only).
        
        Changes visual appearance of all system icons without affecting
        their world coordinates.
        
        Args:
            size: Icon size ('small', 'medium', or 'large')
        """
        # Update button states
        self.icon_size_small_btn.setChecked(size == 'small')
        self.icon_size_medium_btn.setChecked(size == 'medium')
        self.icon_size_large_btn.setChecked(size == 'large')
        
        # Determine radius (UI SPACE)
        if size == 'small':
            radius = SystemItem.ICON_SIZE_SMALL
        elif size == 'large':
            radius = SystemItem.ICON_SIZE_LARGE
        else:  # medium
            radius = SystemItem.ICON_SIZE_MEDIUM
        
        # Update class variable so new systems use this size
        SystemItem.RADIUS = radius
        
        # Update all existing system items (UI SPACE: visual only)
        for system_item in self.system_items.values():
            system_item.set_icon_size(radius)
        
        # Mark as unsaved since this affects the visual state
        self.mark_unsaved_changes()
    
    
    def add_route_group_label(self, route_group: RouteGroup):
        """Add a label for a route group on the map.
        
        Args:
            route_group: The RouteGroup to create a label for
        """
        # Remove existing label if any
        if route_group.id in self.route_group_labels:
            self.scene.removeItem(self.route_group_labels[route_group.id])
            del self.route_group_labels[route_group.id]
        
        # Calculate position (center of all routes in the group)
        position = self.calculate_route_group_center(route_group)
        if position is None:
            return
        
        # Create label
        label = QGraphicsTextItem()
        label.setPlainText(route_group.name)
        label.setDefaultTextColor(QColor(200, 220, 255) if self.is_dark_mode else QColor(0, 0, 100))
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        label.setFont(font)
        
        # Make it non-selectable and non-movable
        label.setFlag(QGraphicsTextItem.ItemIsSelectable, False)
        label.setFlag(QGraphicsTextItem.ItemIsMovable, False)
        
        # Position the label (centered on the group center)
        label_bounds = label.boundingRect()
        label.setPos(position.x() - label_bounds.width() / 2,
                    position.y() - label_bounds.height() / 2)
        
        # Set z-order above routes but below systems
        label.setZValue(7)
        
        # Add to scene and store
        self.scene.addItem(label)
        self.route_group_labels[route_group.id] = label
    
    def calculate_route_group_center(self, route_group: RouteGroup) -> Optional[QPointF]:
        """Calculate the center position for a route group label.
        
        Args:
            route_group: The RouteGroup to calculate center for
            
        Returns:
            Center position, or None if no valid routes
        """
        if not route_group.route_ids:
            return None
        
        # Collect midpoints of all routes in the group
        midpoints = []
        for route_id in route_group.route_ids:
            if route_id not in self.route_items:
                continue
            
            route_item = self.route_items[route_id]
            start_pos = route_item.get_start_position()
            end_pos = route_item.get_end_position()
            
            if start_pos and end_pos:
                mid_x = (start_pos.x() + end_pos.x()) / 2.0
                mid_y = (start_pos.y() + end_pos.y()) / 2.0
                midpoints.append((mid_x, mid_y))
        
        if not midpoints:
            return None
        
        # Average all midpoints
        avg_x = sum(p[0] for p in midpoints) / len(midpoints)
        avg_y = sum(p[1] for p in midpoints) / len(midpoints)
        
        return QPointF(avg_x, avg_y)
    
    def update_route_group_labels(self):
        """Update positions of all route group labels."""
        for group_id, route_group in self.project.route_groups.items():
            if group_id in self.route_group_labels:
                # Recalculate position
                position = self.calculate_route_group_center(route_group)
                if position:
                    label = self.route_group_labels[group_id]
                    label_bounds = label.boundingRect()
                    label.setPos(position.x() - label_bounds.width() / 2,
                               position.y() - label_bounds.height() / 2)
    
    def rebuild_route_group_labels(self):
        """Rebuild all route group labels from scratch."""
        # Remove all existing labels
        for label in self.route_group_labels.values():
            self.scene.removeItem(label)
        self.route_group_labels.clear()
        
        # Add labels for all groups
        for route_group in self.project.route_groups.values():
            self.add_route_group_label(route_group)
    
    # ===== System Management =====
    
    def handle_system_click(self, scene_pos: QPointF, is_right_click: bool):
        """Handle clicks in system placement mode.
        
        Args:
            scene_pos: Position in scene coordinates
            is_right_click: True for right-click (edit), False for left-click (place)
        """
        if is_right_click:
            # Find and edit the clicked system
            item = self.view.itemAt(self.view.mapFromScene(scene_pos))
            if isinstance(item, SystemItem):
                self.edit_system(item)
        else:
            # Create new system at clicked position
            self.create_system_at(scene_pos)
    
    def create_system_at(self, position: QPointF):
        """Create a new system at the specified position.
        
        Args:
            position: Scene coordinates for the new system
        """
        # Create temporary system data for preview
        temp_system = SystemData.create_new("New System", position)
        
        # Create preview item
        self.preview_system_item = SystemItem(temp_system)
        self.scene.addItem(self.preview_system_item)
        
        # Show dialog
        dialog = SystemDialog(temp_system, is_new=True, parent=self)
        if dialog.exec():
            if dialog.result_action == 'save':
                # Update name and save
                temp_system.name = dialog.get_name()
                self.project.systems[temp_system.id] = temp_system
                self.system_items[temp_system.id] = self.preview_system_item
                self.preview_system_item.update_name(temp_system.name)
                self.preview_system_item = None
                self.mark_unsaved_changes()
            else:
                # Cancel or close - remove preview
                self.scene.removeItem(self.preview_system_item)
                self.preview_system_item = None
        else:
            # Dialog rejected - remove preview
            self.scene.removeItem(self.preview_system_item)
            self.preview_system_item = None
    
    def add_system_to_scene(self, system_data: SystemData) -> SystemItem:
        """Add a system to the scene.
        
        Args:
            system_data: The SystemData to add
            
        Returns:
            The created SystemItem
        """
        system_item = SystemItem(system_data)
        self.scene.addItem(system_item)
        self.system_items[system_data.id] = system_item
        return system_item
    
    def edit_system(self, system_item: SystemItem):
        """Edit an existing system.
        
        Args:
            system_item: The SystemItem to edit
        """
        system_data = system_item.get_system_data()
        
        # Show dialog
        dialog = SystemDialog(system_data, is_new=False, parent=self)
        if dialog.exec():
            if dialog.result_action == 'save':
                # Update name
                new_name = dialog.get_name()
                system_item.update_name(new_name)
                self.mark_unsaved_changes()
            elif dialog.result_action == 'delete':
                # Remove system
                self.remove_system(system_data.id)
                self.mark_unsaved_changes()
    
    def remove_system(self, system_id: str):
        """Remove a system from the map.
        
        Args:
            system_id: The ID of the system to remove
        """
        if system_id in self.system_items:
            # Remove from scene
            self.scene.removeItem(self.system_items[system_id])
            # Remove from storage
            del self.system_items[system_id]
            del self.project.systems[system_id]
    
    # ===== Route Management =====
    
    def show_routes(self):
        """Toggle routes mode."""
        if self.current_mode == 'routes':
            self.set_mode(None)
        else:
            self.set_mode('routes')
    
    def handle_start_route_drawing(self, system_item):
        """Handle starting route drawing by clicking on a system.
        
        Args:
            system_item: SystemItem that was clicked
        """
        # Start route drawing mode
        system_data = system_item.get_system_data()
        self.view.route_drawing_active = True
        self.view.route_drawing_start_system_id = system_data.id
        self.view.route_drawing_points = []
        
        self.set_status_text(f"Route drawing: Click intermediate points, then click end system. Right-click or ESC to cancel.")
    
    def handle_finish_route_drawing(self, system_item):
        """Handle finishing route drawing by clicking on end system.
        
        Args:
            system_item: SystemItem that was clicked as end system
        """
        if not self.view.route_drawing_active:
            return
        
        start_system_id = self.view.route_drawing_start_system_id
        end_system_id = system_item.get_system_data().id
        intermediate_points = self.view.route_drawing_points.copy()
        
        # Reset drawing state
        self.view.cancel_route_drawing()
        
        # Don't allow route to same system
        if start_system_id == end_system_id:
            self.set_status_text("Routes mode: Click system to start route.")
            return
        
        # Check if route already exists between these systems
        for route_data in self.project.routes.values():
            if ((route_data.start_system_id == start_system_id and route_data.end_system_id == end_system_id) or
                (route_data.start_system_id == end_system_id and route_data.end_system_id == start_system_id)):
                QMessageBox.warning(
                    self,
                    "Route Exists",
                    "A route already exists between these systems."
                )
                self.set_status_text("Routes mode: Click system to start route.")
                return
        
        # Create new route with intermediate control points
        start_sys = self.project.systems[start_system_id]
        end_sys = self.project.systems[end_system_id]
        route_name = f"{start_sys.name} - {end_sys.name}"
        
        # Convert intermediate points to tuples
        control_points = [(p.x(), p.y()) for p in intermediate_points]
        
        # Create route with control points
        route_data = RouteData.create_new(route_name, start_system_id, end_system_id, control_points)
        self.project.add_route(route_data)
        
        # Add to scene
        route_item = self.add_route_to_scene(route_data)
        
        # Auto-select the newly created route
        route_item.setSelected(True)
        
        # Refresh route selector to include new route
        self.refresh_route_selector()
        
        self.mark_unsaved_changes()
        self.set_status_text("Routes mode: Click system to start route.")
    
    def handle_route_delete_request(self, route_id: str):
        """Handle route deletion request from context menu.
        
        Args:
            route_id: ID of the route to delete
        """
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Route",
            "Are you sure you want to delete this route?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from scene
            if route_id in self.route_items:
                route_item = self.route_items[route_id]
                self.scene.removeItem(route_item)
                del self.route_items[route_id]
            
            # Remove from project
            if route_id in self.project.routes:
                del self.project.routes[route_id]
            
            # Update route groups to remove this route
            groups_to_remove = []
            for group_id, group in self.project.route_groups.items():
                if route_id in group.route_ids:
                    group.route_ids.remove(route_id)
                    # Mark group for removal if empty
                    if len(group.route_ids) == 0:
                        groups_to_remove.append(group_id)
            
            # Remove empty groups
            for group_id in groups_to_remove:
                del self.project.route_groups[group_id]
                # Remove group label if exists
                if group_id in self.route_group_labels:
                    self.scene.removeItem(self.route_group_labels[group_id])
                    del self.route_group_labels[group_id]
            
            # Update remaining group labels
            self.update_route_group_labels()
            
            # Refresh route selector after deletion
            self.refresh_route_selector()
            
            self.mark_unsaved_changes()
            self.set_status_text("Route deleted.")
    
    def find_system_at_position(self, scene_pos: QPointF, snap_radius: float = 20) -> Optional[SystemItem]:
        """Find a system near the given position.
        
        Args:
            scene_pos: Position in scene coordinates
            snap_radius: Radius within which to snap to a system
            
        Returns:
            SystemItem if found within snap radius, None otherwise
        """
        for system_item in self.system_items.values():
            system_pos = system_item.pos()
            distance = ((system_pos.x() - scene_pos.x()) ** 2 + 
                       (system_pos.y() - scene_pos.y()) ** 2) ** 0.5
            if distance <= snap_radius:
                return system_item
        return None
    
    def cancel_route_creation(self):
        """Cancel the current route creation process."""
        self.route_creation_start_system_id = None
        if self.route_preview_line:
            self.scene.removeItem(self.route_preview_line)
            self.route_preview_line = None
        if self.current_mode == 'routes':
            self.update_status_message()
    
    def add_route_to_scene(self, route_data: RouteData) -> RouteItem:
        """Add a route to the scene.
        
        Args:
            route_data: The RouteData to add
            
        Returns:
            The created RouteItem
        """
        route_item = RouteItem(route_data, self.system_items)
        self.scene.addItem(route_item)
        self.route_items[route_data.id] = route_item
        return route_item
    
    def remove_route(self, route_id: str):
        """Remove a route from the map.
        
        Args:
            route_id: The ID of the route to remove
        """
        if route_id in self.route_items:
            # Remove from scene
            route_item = self.route_items[route_id]
            self.scene.removeItem(route_item)
            # Remove from storage
            del self.route_items[route_id]
            self.project.remove_route(route_id)
            self.mark_unsaved_changes()
    
    def update_routes_for_system_movement(self):
        """Update all routes when systems have been moved."""
        for route_item in self.route_items.values():
            route_item.update_from_system_movement()
        # Also update route group label positions
        self.update_route_group_labels()
    
    def toggle_route_for_group(self, route_id: str):
        """Toggle a route's selection for group creation.
        
        Args:
            route_id: ID of the route to toggle
        """
        if route_id in self.routes_selected_for_group:
            # Deselect
            self.routes_selected_for_group.remove(route_id)
            if route_id in self.route_items:
                self.route_items[route_id].set_group_selection(False)
        else:
            # Select
            self.routes_selected_for_group.add(route_id)
            if route_id in self.route_items:
                self.route_items[route_id].set_group_selection(True)
    
    def create_route_group_dialog(self):
        """Show dialog to create a named route group from selected routes."""
        if not self.routes_selected_for_group:
            QMessageBox.warning(
                self,
                "No Routes Selected",
                "Please select routes using CTRL+click before creating a group."
            )
            return
        
        name, ok = QInputDialog.getText(
            self,
            "Create Route Group",
            f"Enter name for group ({len(self.routes_selected_for_group)} routes selected):"
        )
        
        if ok and name and name.strip():
            route_group = RouteGroup.create_new(name.strip(), list(self.routes_selected_for_group))
            self.project.add_route_group(route_group)
            
            # Clear selection and highlight
            for route_id in list(self.routes_selected_for_group):
                if route_id in self.route_items:
                    self.route_items[route_id].set_group_selection(False)
            self.routes_selected_for_group.clear()
            
            # Add label for the new group
            self.add_route_group_label(route_group)
            
            # Refresh route selector to include new group
            self.refresh_route_selector()
            
            self.mark_unsaved_changes()
            QMessageBox.information(
                self,
                "Route Group Created",
                f"Route group '{route_group.name}' created with {len(route_group.route_ids)} routes."
            )
    
    # ===== Route Editing Actions =====
    
    def insert_system_into_route(self):
        """Insert a selected system into the selected route.
        
        Prompts user to select where to insert the system in the route chain.
        """
        if not self.selected_route:
            QMessageBox.warning(self, "No Route Selected", "Please select a route first.")
            return
        
        # Find selected system
        selected_system = None
        for item in self.scene.selectedItems():
            if isinstance(item, SystemItem):
                selected_system = item
                break
        
        if not selected_system:
            QMessageBox.warning(self, "No System Selected", "Please select a system to insert.")
            return
        
        route_data = self.selected_route.get_route_data()
        sys_id = selected_system.get_system_data().id
        
        # Check if system is already in route
        if route_data.contains_system(sys_id):
            QMessageBox.warning(self, "System Already in Route", 
                              "This system is already part of the selected route.")
            return
        
        # Get system chain and let user choose insertion point
        system_chain = route_data.get_system_chain()
        
        # Build menu of insertion points
        dialog = QDialog(self)
        dialog.setWindowTitle("Insert System - Choose Position")
        layout = QVBoxLayout(dialog)
        
        label = QLabel(f"Insert '{selected_system.get_system_data().name}' after:")
        layout.addWidget(label)
        
        list_widget = QListWidget()
        list_widget.addItem("(Start of route)")
        for i, sys_id_in_chain in enumerate(system_chain):
            sys_name = self.project.systems[sys_id_in_chain].name
            list_widget.addItem(f"{i+1}. {sys_name}")
        list_widget.setCurrentRow(0)
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            insert_index = list_widget.currentRow()
            route_data.insert_system_at(insert_index, sys_id)
            self.selected_route.recompute_path()
            self.mark_unsaved_changes()
            self.update_route_workspace_controls(self.selected_route)
    
    def remove_system_from_route(self):
        """Remove a selected system from the selected route."""
        if not self.selected_route:
            QMessageBox.warning(self, "No Route Selected", "Please select a route first.")
            return
        
        # Find selected system
        selected_system = None
        for item in self.scene.selectedItems():
            if isinstance(item, SystemItem):
                selected_system = item
                break
        
        if not selected_system:
            QMessageBox.warning(self, "No System Selected", "Please select a system to remove.")
            return
        
        route_data = self.selected_route.get_route_data()
        sys_id = selected_system.get_system_data().id
        
        # Check if system is in route
        if not route_data.contains_system(sys_id):
            QMessageBox.warning(self, "System Not in Route", 
                              "This system is not part of the selected route.")
            return
        
        # Check if route would be too short
        if len(route_data.get_system_chain()) <= 2:
            QMessageBox.warning(self, "Cannot Remove System", 
                              "Route must have at least 2 systems. Delete the route instead.")
            return
        
        # Confirm removal
        sys_name = selected_system.get_system_data().name
        reply = QMessageBox.question(
            self,
            "Remove System from Route",
            f"Remove '{sys_name}' from route '{route_data.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                route_data.remove_system_by_id(sys_id)
                self.selected_route.recompute_path()
                self.mark_unsaved_changes()
                self.update_route_workspace_controls(self.selected_route)
            except ValueError as e:
                QMessageBox.critical(self, "Error", f"Failed to remove system: {e}")
    
    def split_route_at_system(self):
        """Split the selected route at the selected system."""
        if not self.selected_route:
            QMessageBox.warning(self, "No Route Selected", "Please select a route first.")
            return
        
        # Find selected system
        selected_system = None
        for item in self.scene.selectedItems():
            if isinstance(item, SystemItem):
                selected_system = item
                break
        
        if not selected_system:
            QMessageBox.warning(self, "No System Selected", "Please select a system to split at.")
            return
        
        route_data = self.selected_route.get_route_data()
        sys_id = selected_system.get_system_data().id
        
        # Check if system is in route and not at ends
        sys_index = route_data.get_system_index(sys_id)
        if sys_index < 0:
            QMessageBox.warning(self, "System Not in Route", 
                              "This system is not part of the selected route.")
            return
        
        if sys_index == 0 or sys_index == len(route_data.get_system_chain()) - 1:
            QMessageBox.warning(self, "Cannot Split at End", 
                              "Cannot split route at the first or last system.")
            return
        
        # Confirm split
        sys_name = selected_system.get_system_data().name
        reply = QMessageBox.question(
            self,
            "Split Route",
            f"Split route '{route_data.name}' at '{sys_name}'?\n\n"
            f"This will create two separate routes.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Perform split
            new_route_data = route_data.split_at_system(sys_id)
            
            if new_route_data:
                # Add new route to project and scene
                self.project.add_route(new_route_data)
                new_route_item = self.add_route_to_scene(new_route_data)
                
                # Update existing route rendering
                self.selected_route.recompute_path()
                
                # Select the new route
                self.selected_route.setSelected(False)
                new_route_item.setSelected(True)
                
                # Refresh route selector after split
                self.refresh_route_selector()
                
                self.mark_unsaved_changes()
                QMessageBox.information(
                    self,
                    "Route Split",
                    f"Route split successfully into:\n"
                    f"- {route_data.name}\n"
                    f"- {new_route_data.name}"
                )
            else:
                QMessageBox.critical(self, "Error", "Failed to split route.")
    
    def merge_selected_routes(self):
        """Merge two routes that are selected for grouping."""
        if len(self.routes_selected_for_group) != 2:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Please select exactly 2 routes (CTRL+click) to merge."
            )
            return
        
        # Get the two routes
        route_ids = list(self.routes_selected_for_group)
        route_data_1 = self.project.get_route(route_ids[0])
        route_data_2 = self.project.get_route(route_ids[1])
        
        if not route_data_1 or not route_data_2:
            QMessageBox.critical(self, "Error", "Could not find selected routes.")
            return
        
        # Try to merge
        merged_route = RouteData.merge_routes(route_data_1, route_data_2)
        
        if not merged_route:
            QMessageBox.warning(
                self,
                "Cannot Merge",
                "These routes cannot be merged.\n\n"
                "Routes must share a common endpoint:\n"
                "- End of route 1 connects to start of route 2\n"
                "- End of route 1 connects to end of route 2\n"
                "- Start of route 1 connects to end of route 2\n"
                "- Start of route 1 connects to start of route 2"
            )
            return
        
        # Confirm merge
        reply = QMessageBox.question(
            self,
            "Merge Routes",
            f"Merge these routes?\n\n"
            f"Route 1: {route_data_1.name}\n"
            f"Route 2: {route_data_2.name}\n\n"
            f"New route: {merged_route.name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove old routes
            self.remove_route(route_ids[0])
            self.remove_route(route_ids[1])
            
            # Clear group selection
            self.routes_selected_for_group.clear()
            
            # Add merged route
            self.project.add_route(merged_route)
            merged_item = self.add_route_to_scene(merged_route)
            merged_item.setSelected(True)
            
            # Refresh route selector after merge
            self.refresh_route_selector()
            
            self.mark_unsaved_changes()
            QMessageBox.information(
                self,
                "Routes Merged",
                f"Routes merged successfully into:\n{merged_route.name}"
            )
    
    def show_system_route_context_menu(self, system_item: SystemItem, global_pos):
        """Show context menu for a system in route editing mode.
        
        Args:
            system_item: The SystemItem that was right-clicked
            global_pos: Global position for the menu
        """
        if not self.selected_route:
            return
        
        route_data = self.selected_route.get_route_data()
        sys_id = system_item.get_system_data().id
        sys_name = system_item.get_system_data().name
        
        menu = QMenu()
        
        # Check if system is in the selected route
        if route_data.contains_system(sys_id):
            # System is in route - offer removal and splitting
            remove_action = menu.addAction(f"Remove '{sys_name}' from Route")
            
            # Only allow split if not at ends
            sys_index = route_data.get_system_index(sys_id)
            split_action = None
            if sys_index > 0 and sys_index < len(route_data.get_system_chain()) - 1:
                split_action = menu.addAction(f"Split Route at '{sys_name}'")
        else:
            # System is not in route - offer insertion
            insert_action = menu.addAction(f"Insert '{sys_name}' into Route")
        
        action = menu.exec(global_pos)
        
        if action:
            action_text = action.text()
            if "Remove" in action_text:
                # Programmatically trigger remove
                self.remove_system_from_route_by_id(sys_id)
            elif "Split" in action_text:
                # Programmatically trigger split
                self.split_route_at_system_by_id(sys_id)
            elif "Insert" in action_text:
                # Select the system and trigger insert dialog
                system_item.setSelected(True)
                self.insert_system_into_route()
    
    def show_segment_context_menu(self, route_item: RouteItem, segment_info: tuple, global_pos):
        """Show context menu for a route segment in route editing mode.
        
        Args:
            route_item: The RouteItem that was right-clicked
            segment_info: Tuple of (segment_index, system_id_1, system_id_2)
            global_pos: Global position for the menu
        """
        segment_index, sys_id_1, sys_id_2 = segment_info
        route_data = route_item.get_route_data()
        
        sys_name_1 = self.project.systems[sys_id_1].name if sys_id_1 in self.project.systems else sys_id_1
        sys_name_2 = self.project.systems[sys_id_2].name if sys_id_2 in self.project.systems else sys_id_2
        
        menu = QMenu()
        insert_action = menu.addAction(f"Insert System into Route Here")
        split_action = menu.addAction(f"Split Route between '{sys_name_1}' and '{sys_name_2}'")
        
        action = menu.exec(global_pos)
        
        if action == insert_action:
            # Find a selected system to insert
            selected_system = None
            for item in self.scene.selectedItems():
                if isinstance(item, SystemItem):
                    selected_system = item
                    break
            
            if not selected_system:
                QMessageBox.warning(
                    self,
                    "No System Selected",
                    "Please select a system to insert into the route."
                )
                return
            
            sys_id = selected_system.get_system_data().id
            
            # Check if system is already in route
            if route_data.contains_system(sys_id):
                QMessageBox.warning(
                    self,
                    "System Already in Route",
                    "This system is already part of the route."
                )
                return
            
            # Insert after sys_id_1 (at segment_index + 1)
            route_data.insert_system_at(segment_index + 1, sys_id)
            route_item.recompute_path()
            self.mark_unsaved_changes()
            self.update_route_workspace_controls(route_item)
            
        elif action == split_action:
            # Split at the second system of the segment
            self.selected_route = route_item
            self.split_route_at_system_by_id(sys_id_2)
    
    def remove_system_from_route_by_id(self, sys_id: str):
        """Remove a system from the selected route by ID.
        
        Args:
            sys_id: ID of the system to remove
        """
        if not self.selected_route:
            return
        
        route_data = self.selected_route.get_route_data()
        
        # Check if route would be too short
        if len(route_data.get_system_chain()) <= 2:
            QMessageBox.warning(
                self,
                "Cannot Remove System",
                "Route must have at least 2 systems. Delete the route instead."
            )
            return
        
        try:
            route_data.remove_system_by_id(sys_id)
            self.selected_route.recompute_path()
            self.mark_unsaved_changes()
            self.update_route_workspace_controls(self.selected_route)
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Failed to remove system: {e}")
    
    def split_route_at_system_by_id(self, sys_id: str):
        """Split the selected route at a system by ID.
        
        Args:
            sys_id: ID of the system to split at
        """
        if not self.selected_route:
            return
        
        route_data = self.selected_route.get_route_data()
        
        # Check if system is in route and not at ends
        sys_index = route_data.get_system_index(sys_id)
        if sys_index < 0:
            return
        
        if sys_index == 0 or sys_index == len(route_data.get_system_chain()) - 1:
            QMessageBox.warning(
                self,
                "Cannot Split at End",
                "Cannot split route at the first or last system."
            )
            return
        
        # Perform split
        new_route_data = route_data.split_at_system(sys_id)
        
        if new_route_data:
            # Add new route to project and scene
            self.project.add_route(new_route_data)
            new_route_item = self.add_route_to_scene(new_route_data)
            
            # Update existing route rendering
            self.selected_route.recompute_path()
            
            # Select the new route
            self.selected_route.setSelected(False)
            new_route_item.setSelected(True)
            
            self.mark_unsaved_changes()
    
    # ===== Placeholder Mode Actions =====
    
    def show_zones(self):
        """Toggle zones mode (placeholder)."""
        if self.current_mode == 'zones':
            self.set_mode(None)
        else:
            self.set_mode('zones')
            QMessageBox.information(
                self,
                "Zones",
                "Zones editor coming soon!\n\n"
                "This will allow you to define territorial zones and regions."
            )
            self.set_mode(None)
    
    def show_stats(self):
        """Toggle stats mode."""
        if self.current_mode == 'stats':
            self.set_mode(None)
        else:
            self.set_mode('stats')
    
    def update_stats_inspector(self):
        """Update the stats inspector with the currently selected system or route."""
        # Find the currently selected system or route
        selected_system = None
        selected_route = None
        
        for item in self.scene.selectedItems():
            if isinstance(item, SystemItem):
                selected_system = item.get_system_data()
                break
            elif isinstance(item, RouteItem):
                selected_route = item
                break
        
        # Update the stats inspector based on what's selected
        if selected_system is not None:
            self.stats_inspector.set_selected_system(selected_system)
        elif selected_route is not None:
            self.stats_inspector.set_selected_route(selected_route)
        else:
            self.stats_inspector.clear_selection()
