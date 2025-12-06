"""GUI implementation for the Star Map Editor.

This module contains all PySide6 UI components including the main window,
map view, and workspace controls.
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# Add current directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import (
    QMainWindow, QGraphicsView, QGraphicsScene,
    QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QFileDialog, 
    QMessageBox, QLabel, QSlider, QToolBar, QMenuBar, QMenu,
    QGraphicsPathItem, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, QPointF, Signal
from PySide6.QtGui import QPixmap, QPen, QColor, QPainter, QKeyEvent, QWheelEvent, QAction, QPainterPath

from core import (
    MapProject, TemplateData, SystemData, SystemItem, 
    SystemDialog, TemplateItem, RouteData, RouteItem, RouteHandleItem
)
from core.project_model import RouteGroup
from core.project_io import save_project, load_project, export_map_data


class GridOverlay(QGraphicsScene):
    """Custom QGraphicsScene to draw a semi-transparent grid overlay.
    
    The grid is drawn in the foreground, on top of all scene items,
    and scales/moves with the view transformations.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_spacing = 100  # Grid spacing in scene coordinates
        self.grid_color = QColor(144, 238, 144, 128)  # Semi-transparent light green
        self.show_grid = False
        
    def drawForeground(self, painter, rect):
        """Draw the grid overlay on top of scene items."""
        if not self.show_grid:
            return
            
        painter.save()
        painter.setPen(QPen(self.grid_color, 1))
        
        # Get scene bounds
        scene_rect = self.sceneRect()
        left = int(scene_rect.left() / self.grid_spacing) * self.grid_spacing
        top = int(scene_rect.top() / self.grid_spacing) * self.grid_spacing
        
        # Draw vertical lines
        x = left
        while x <= scene_rect.right():
            painter.drawLine(int(x), int(scene_rect.top()), int(x), int(scene_rect.bottom()))
            x += self.grid_spacing
            
        # Draw horizontal lines
        y = top
        while y <= scene_rect.bottom():
            painter.drawLine(int(scene_rect.left()), int(y), int(scene_rect.right()), int(y))
            y += self.grid_spacing
            
        painter.restore()


class MapView(QGraphicsView):
    """Custom QGraphicsView with zoom and pan controls.
    
    Features:
    - Mouse wheel zoom centered on cursor position with min/max limits
    - Continuous WASD/Arrow key panning with zoom-scaled speed
    - Middle mouse button drag panning
    - Space + left mouse button drag panning
    - Automatic scene update to refresh grid overlay
    - System placement mode support
    - Template mode support with Ctrl+wheel for template scaling
    """
    
    # Signal emitted when user clicks to place/edit a system
    system_click = Signal(QPointF, bool)  # (position, is_right_click)
    
    # Signal emitted when user clicks in routes mode
    route_click = Signal(QPointF)  # (position)
    
    # Signal emitted when a route is toggled for group selection
    route_group_toggle = Signal(str)  # (route_id)
    
    # Signal emitted when an item is moved/modified
    item_modified = Signal()  # Emitted when items are moved
    
    # Signal emitted when inserting a control point on a route
    control_point_insert = Signal(object, QPointF)  # (route_item, position)
    
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
        
        # Template scaling sensitivity
        self.template_scale_sensitivity = 1.0  # Scale sensitivity multiplier
        
        # Item drag tracking
        self.dragging_item = False
        
        # P key state for adding control points
        self.p_key_pressed = False

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
        
        # Apply zoom
        self.scale(zoom, zoom)
        self.current_zoom = new_zoom
        
        # Get the new position of the mouse in scene coordinates after zoom
        new_pos = self.mapToScene(event.position().toPoint())
        
        # Calculate the difference and adjust view to keep it under the mouse
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        
        # Update the scene to refresh grid
        self.scene().update()
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press for continuous WASD/Arrow panning and Space for mouse pan."""
        if event.key() in (Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D,
                          Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            self.keys_pressed.add(event.key())
            if not self.pan_timer.isActive():
                self.pan_timer.start()
            event.accept()
        elif event.key() == Qt.Key_Space:
            self.space_pressed = True
            event.accept()
        elif event.key() == Qt.Key_P:
            self.p_key_pressed = True
            event.accept()
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
        elif event.key() == Qt.Key_P:
            self.p_key_pressed = False
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
        """Handle mouse press for panning, system placement, route creation, and template selection."""
        # Middle mouse button or Space + left mouse button for panning
        if event.button() == Qt.MiddleButton or \
           (event.button() == Qt.LeftButton and self.space_pressed):
            self.is_panning = True
            self.pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        # In routes mode, handle clicks for route creation and control point insertion
        elif self.routes_mode_active:
            if event.button() == Qt.LeftButton:
                # Get item at click position
                item = self.itemAt(event.pos())
                
                # If clicking on a RouteHandleItem, let it handle the event (for dragging)
                if isinstance(item, RouteHandleItem):
                    super().mousePressEvent(event)
                    return
                
                # If P key is pressed and clicking on a RouteItem, insert control point
                if self.p_key_pressed and isinstance(item, RouteItem):
                    scene_pos = self.mapToScene(event.pos())
                    self.insert_control_point_on_route(item, scene_pos)
                    event.accept()
                    return
                
                # Check if CTRL is pressed for group selection
                if event.modifiers() & Qt.ControlModifier:
                    if isinstance(item, RouteItem):
                        # Toggle route for group selection
                        self.toggle_route_group_selection(item)
                        event.accept()
                        return
                
                # If clicking on a RouteItem (not for group selection), allow selection
                if isinstance(item, RouteItem):
                    super().mousePressEvent(event)
                    return
                
                # Otherwise, emit signal for route click handling (system selection)
                scene_pos = self.mapToScene(event.pos())
                self.route_click.emit(scene_pos)
                event.accept()
            elif event.button() == Qt.RightButton:
                # Right click on route - show context menu
                item = self.itemAt(event.pos())
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
    
    def toggle_route_group_selection(self, route_item: RouteItem):
        """Toggle a route's group selection state.
        
        Args:
            route_item: The RouteItem to toggle
        """
        # Emit signal to let main window handle the logic
        route_id = route_item.get_route_data().id
        self.route_group_toggle.emit(route_id)
    
    def insert_control_point_on_route(self, route_item: RouteItem, scene_pos: QPointF):
        """Insert a control point on a route at the given position.
        
        Args:
            route_item: The RouteItem to insert a control point on
            scene_pos: Position in scene coordinates
        """
        # Emit signal to let main window handle the logic
        self.control_point_insert.emit(route_item, scene_pos)
    
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
        
        # Create mode button bar
        mode_layout = QHBoxLayout()
        
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
        self.stats_btn.clicked.connect(self.show_stats)
        mode_layout.addWidget(self.stats_btn)
        
        mode_layout.addStretch()
        
        main_layout.addLayout(mode_layout)
        
        # Create pan sensitivity controls (always visible)
        pan_sensitivity_layout = QHBoxLayout()
        pan_sensitivity_layout.setContentsMargins(5, 5, 5, 5)
        
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
        main_layout.addLayout(pan_sensitivity_layout)
        
        # Create workspace toolbar (visible only in template mode)
        self.workspace_toolbar = self.create_workspace_toolbar()
        main_layout.addWidget(self.workspace_toolbar)
        self.workspace_toolbar.hide()
        
        # Create routes workspace toolbar (visible only in routes mode)
        self.routes_toolbar = self.create_routes_toolbar()
        main_layout.addWidget(self.routes_toolbar)
        self.routes_toolbar.hide()
        
        # Status label for mode indication
        self.status_label = QLabel()
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #f0f0f0; }")
        self.update_status_message()
        main_layout.addWidget(self.status_label)
        
        # Create graphics scene and view
        self.scene = GridOverlay()
        self.view = MapView(self.scene)
        self.view.setFocusPolicy(Qt.StrongFocus)
        self.view.system_click.connect(self.handle_system_click)
        self.view.route_click.connect(self.handle_route_click)
        self.view.route_group_toggle.connect(self.toggle_route_for_group)
        self.view.control_point_insert.connect(self.insert_control_point_on_route)
        self.view.item_modified.connect(self.on_item_modified)
        
        # Connect scene selection changed signal
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
        main_layout.addWidget(self.view)
        
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
        toolbar_widget.setStyleSheet("QWidget { background-color: #e0e0e0; padding: 5px; }")
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
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
        
        return toolbar_widget
    
    def create_routes_toolbar(self) -> QWidget:
        """Create the workspace toolbar for routes mode."""
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("QWidget { background-color: #e0e0e0; padding: 5px; }")
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Current Route label
        self.current_route_label = QLabel('Current Route: None')
        self.current_route_label.setStyleSheet("font-weight: bold; color: #333;")
        toolbar_layout.addWidget(self.current_route_label)
        
        toolbar_layout.addSpacing(20)
        
        # Info label for control point creation
        info_label = QLabel('Press P + Click on route to add control point')
        info_label.setStyleSheet("color: #555; font-style: italic;")
        toolbar_layout.addWidget(info_label)
        
        toolbar_layout.addSpacing(20)
        
        # Create Route Group button
        self.create_group_btn = QPushButton('Create Route Group')
        self.create_group_btn.clicked.connect(self.create_route_group_dialog)
        toolbar_layout.addWidget(self.create_group_btn)
        
        # Info label for grouping
        group_info_label = QLabel('CTRL+Click routes to select for grouping')
        group_info_label.setStyleSheet("color: #555; font-style: italic;")
        toolbar_layout.addWidget(group_info_label)
        
        toolbar_layout.addStretch()
        
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
                
                # Enable grid if there are templates
                if self.project.templates:
                    self.scene.show_grid = True
                    # Fit view to first template
                    if self.template_items:
                        first_template = list(self.template_items.values())[0]
                        self.scene.setSceneRect(first_template.boundingRect())
                        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
                
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
                self.status_label.setText("Project saved successfully")
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
            self.status_label.setText("Mode: System placement – left-click to place a system, right-click to edit")
        elif self.current_mode == 'routes':
            self.status_label.setText("Routes mode: Click systems to create routes. Select route to edit. Press P + Click on route to add control point.")
        else:
            self.status_label.setText("Ready")
    
    def set_mode(self, mode: Optional[str]):
        """Set the current editor mode.
        
        Args:
            mode: The mode to activate ('template', 'systems', 'routes', 'zones', or None)
        """
        self.current_mode = mode
        
        # Update button states
        self.template_btn.setChecked(mode == 'template')
        self.systems_btn.setChecked(mode == 'systems')
        self.routes_btn.setChecked(mode == 'routes')
        self.zones_btn.setChecked(mode == 'zones')
        
        # Update button styles
        for btn, btn_mode in [(self.template_btn, 'template'),
                               (self.systems_btn, 'systems'), 
                               (self.routes_btn, 'routes'),
                               (self.zones_btn, 'zones')]:
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
        
        # Show/hide workspace toolbars
        if mode == 'template':
            self.workspace_toolbar.show()
            self.routes_toolbar.hide()
        elif mode == 'routes':
            self.workspace_toolbar.hide()
            self.routes_toolbar.show()
        else:
            self.workspace_toolbar.hide()
            self.routes_toolbar.hide()
        
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
            # Create template data
            template_data = TemplateData.create_new(file_path)
            self.project.add_template(template_data)
            
            # Add to scene
            template_item = self.add_template_to_scene(template_data)
            
            # If this is the first template, set up the scene
            if len(self.project.templates) == 1:
                self.scene.show_grid = True
                self.scene.setSceneRect(template_item.boundingRect())
                self.view.resetTransform()
                self.view.current_zoom = 1.0
                self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            
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
        else:
            self.lock_btn.setChecked(False)
            self.lock_btn.setText('Lock Template')
            self.opacity_slider.setValue(100)
            self.opacity_label.setText('100%')
    
    def update_route_workspace_controls(self, route_selected: Optional[RouteItem]):
        """Update route workspace controls based on selection.
        
        Args:
            route_selected: The selected RouteItem, or None if no route selected
        """
        if hasattr(self, 'current_route_label'):
            if route_selected:
                route_name = route_selected.get_route_data().name
                self.current_route_label.setText(f'Current Route: {route_name}')
            else:
                self.current_route_label.setText('Current Route: None')
    
    
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
    
    def handle_route_click(self, scene_pos: QPointF):
        """Handle clicks in routes mode for route creation.
        
        Args:
            scene_pos: Position in scene coordinates
        """
        # Find system under click position (with snap radius)
        clicked_system = self.find_system_at_position(scene_pos, snap_radius=20)
        
        if not clicked_system:
            # Click on empty space - cancel current route creation
            self.cancel_route_creation()
            return
        
        if self.route_creation_start_system_id is None:
            # First click - set start system
            self.route_creation_start_system_id = clicked_system.get_system_data().id
            self.status_label.setText(f"Routes mode: Start system selected. Click another system to complete route.")
        else:
            # Second click - create the route
            start_system_id = self.route_creation_start_system_id
            end_system_id = clicked_system.get_system_data().id
            
            # Don't allow route to same system
            if start_system_id == end_system_id:
                self.cancel_route_creation()
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
                    self.cancel_route_creation()
                    return
            
            # Create new route
            start_sys = self.project.systems[start_system_id]
            end_sys = self.project.systems[end_system_id]
            route_name = f"{start_sys.name} - {end_sys.name}"
            
            # Create route with no control points initially
            # Users can add control points using P + Click
            route_data = RouteData.create_new(route_name, start_system_id, end_system_id)
            self.project.add_route(route_data)
            
            # Add to scene
            route_item = self.add_route_to_scene(route_data)
            
            # Auto-select the newly created route to show handles immediately
            route_item.setSelected(True)
            
            # Reset creation state
            self.cancel_route_creation()
            self.mark_unsaved_changes()
    
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
            route_item.hide_handles()  # Clean up handles first
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
    
    def insert_control_point_on_route(self, route_item: RouteItem, scene_pos: QPointF):
        """Insert a control point on a route at the given position.
        
        Args:
            route_item: The RouteItem to insert a control point on
            scene_pos: Position in scene coordinates
        """
        route_item.insert_control_point(scene_pos)
        self.mark_unsaved_changes()
    
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
            
            self.mark_unsaved_changes()
            QMessageBox.information(
                self,
                "Route Group Created",
                f"Route group '{route_group.name}' created with {len(route_group.route_ids)} routes."
            )
    
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
        """Placeholder for Stats functionality."""
        stats_text = f"""Map Statistics:

Templates: {len(self.project.templates)}
Systems: {len(self.project.systems)}
Routes: {len(self.project.routes)}
Route Groups: {len(self.project.route_groups)}
Zones: {len(self.project.zones)}
"""
        QMessageBox.information(
            self,
            "Map Statistics",
            stats_text
        )
