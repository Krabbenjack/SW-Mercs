import json
from PySide6.QtWidgets import (
    QMainWindow, QGraphicsView, QGraphicsScene,
    QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPixmap, QPen, QColor, QPainter, QKeyEvent, QWheelEvent


class GridOverlay(QGraphicsScene):
    """Custom QGraphicsScene to draw a semi-transparent grid overlay."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_spacing = 100
        self.grid_color = QColor(144, 238, 144, 100)  # Semi-transparent light green
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
    """Custom QGraphicsView with zoom and pan controls."""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        
        # Zoom configuration
        self.zoom_factor = 1.15
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.current_zoom = 1.0
        
        # Panning configuration
        self.pan_speed = 15
        self.keys_pressed = set()
        self.pan_timer = QTimer(self)
        self.pan_timer.timeout.connect(self._handle_continuous_pan)
        self.pan_timer.setInterval(16)  # ~60 FPS
        
        # Mouse panning state
        self.is_panning = False
        self.pan_start_pos = None
        self.space_pressed = False
        
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming, anchored under cursor with limits."""
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
        
        # Calculate pan speed scaled by zoom level
        scaled_speed = self.pan_speed / self.current_zoom
        
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
        """Handle mouse press for panning."""
        # Middle mouse button or Space + left mouse button for panning
        if event.button() == Qt.MiddleButton or \
           (event.button() == Qt.LeftButton and self.space_pressed):
            self.is_panning = True
            self.pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
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
        """Handle mouse release to stop panning."""
        if event.button() == Qt.MiddleButton or \
           (event.button() == Qt.LeftButton and self.is_panning):
            self.is_panning = False
            self.pan_start_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class StarMapEditor(QMainWindow):
    """Main window for the Star Map Editor application."""
    
    def __init__(self):
        super().__init__()
        self.current_pixmap = None
        self.map_name = "Unnamed Map"
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Star Map Editor')
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create button bar
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton('Load Template')
        self.load_btn.clicked.connect(self.load_template)
        button_layout.addWidget(self.load_btn)
        
        self.systems_btn = QPushButton('Systems')
        self.systems_btn.clicked.connect(self.show_systems)
        button_layout.addWidget(self.systems_btn)
        
        self.routes_btn = QPushButton('Routes')
        self.routes_btn.clicked.connect(self.show_routes)
        button_layout.addWidget(self.routes_btn)
        
        self.zones_btn = QPushButton('Zones')
        self.zones_btn.clicked.connect(self.show_zones)
        button_layout.addWidget(self.zones_btn)
        
        self.stats_btn = QPushButton('Stats')
        self.stats_btn.clicked.connect(self.show_stats)
        button_layout.addWidget(self.stats_btn)
        
        self.export_btn = QPushButton('Export')
        self.export_btn.clicked.connect(self.export_map)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Create graphics scene and view
        self.scene = GridOverlay()
        self.view = MapView(self.scene)
        self.view.setFocusPolicy(Qt.StrongFocus)
        main_layout.addWidget(self.view)
        
        self.show()
    
    def load_template(self):
        """Load a template image and display it in the scene."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Template Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "Error", "Could not load image.")
                return
            
            # Clear the scene
            self.scene.clear()
            self.current_pixmap = pixmap
            
            # Add pixmap to scene
            self.scene.addPixmap(pixmap)
            
            # Set scene rect to match the image
            self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
            
            # Enable grid overlay
            self.scene.show_grid = True
            
            # Reset view and fit to window
            self.view.resetTransform()
            self.view.current_zoom = 1.0  # Reset zoom level tracking
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            
            # Update scene to show grid
            self.scene.update()
            
            # Set focus to the view so keyboard input works immediately
            self.view.setFocus()
    
    def show_systems(self):
        """Placeholder for Systems functionality."""
        QMessageBox.information(
            self,
            "Systems",
            "Systems editor coming soon!\n\n"
            "This will allow you to add and edit star systems on the map."
        )
    
    def show_routes(self):
        """Placeholder for Routes functionality."""
        QMessageBox.information(
            self,
            "Routes",
            "Routes editor coming soon!\n\n"
            "This will allow you to create hyperlane routes between systems."
        )
    
    def show_zones(self):
        """Placeholder for Zones functionality."""
        QMessageBox.information(
            self,
            "Zones",
            "Zones editor coming soon!\n\n"
            "This will allow you to define territorial zones and regions."
        )
    
    def show_stats(self):
        """Placeholder for Stats functionality."""
        QMessageBox.information(
            self,
            "Stats",
            "Stats viewer coming soon!\n\n"
            "This will display statistics about your map."
        )
    
    def export_map(self):
        """Export the map data to a JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Map",
            "map.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            map_data = {
                "mapName": self.map_name,
                "systems": [],
                "routes": [],
                "zones": [],
                "stats": {}
            }
            
            try:
                with open(file_path, 'w') as f:
                    json.dump(map_data, f, indent=2)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Map exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Could not export map:\n{str(e)}"
                )
