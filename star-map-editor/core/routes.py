"""Route management for the Star Map Editor.

This module handles route data structures and graphics representation for
creating curved routes between star systems.
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtWidgets import (
    QGraphicsPathItem, QGraphicsEllipseItem, QGraphicsItem
)
from PySide6.QtGui import QPainterPath, QPen, QColor, QBrush, QPainter


@dataclass
class RouteData:
    """Data model for a hyperlane route between systems.
    
    Routes are curved paths connecting two star systems, with intermediate
    control points that can be adjusted to bend the route.
    
    Attributes:
        id: Unique identifier for the route (UUID string)
        name: Display name of the route (optional, can be auto-generated)
        start_system_id: ID of the starting system
        end_system_id: ID of the ending system
        control_points: List of intermediate control points in scene coordinates
                       Used to bend the spline path between start and end
    """
    id: str
    name: str
    start_system_id: str
    end_system_id: str
    control_points: List[tuple[float, float]] = field(default_factory=list)
    
    @classmethod
    def create_new(cls, name: str, start_system_id: str, end_system_id: str,
                   control_points: Optional[List[tuple[float, float]]] = None):
        """Create a new route with a generated UUID.
        
        Args:
            name: Display name for the route
            start_system_id: ID of the starting system
            end_system_id: ID of the ending system
            control_points: Optional list of control points
            
        Returns:
            New RouteData instance
        """
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            start_system_id=start_system_id,
            end_system_id=end_system_id,
            control_points=control_points or []
        )


class RouteHandleItem(QGraphicsEllipseItem):
    """Draggable control point handle for route editing.
    
    Displays as a small circle that can be dragged to adjust the route curve.
    """
    
    RADIUS = 6  # Handle radius in scene units
    NORMAL_COLOR = QColor(255, 200, 100)  # Orange for normal state
    HOVER_COLOR = QColor(255, 150, 50)  # Brighter orange for hover
    
    def __init__(self, index: int, position: QPointF, parent: 'RouteItem'):
        """Initialize the handle item.
        
        Args:
            index: Index of this control point in the route's control_points list
            position: Initial position in scene coordinates
            parent: The parent RouteItem this handle belongs to
        """
        super().__init__(parent)
        self.control_point_index = index
        self.route_item = parent
        
        # Set up the circle
        self.setRect(-self.RADIUS, -self.RADIUS, 
                     self.RADIUS * 2, self.RADIUS * 2)
        self.setPos(position)
        
        # Configure appearance
        self.setPen(QPen(Qt.white, 2))
        self.setBrush(QBrush(self.NORMAL_COLOR))
        
        # Enable interaction
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        # Higher z-value so handles are on top of the route
        self.setZValue(100)
    
    def hoverEnterEvent(self, event):
        """Handle mouse hover enter."""
        self.setBrush(QBrush(self.HOVER_COLOR))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle mouse hover leave."""
        self.setBrush(QBrush(self.NORMAL_COLOR))
        super().hoverLeaveEvent(event)
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position updates.
        
        Args:
            change: The type of change
            value: The new value
            
        Returns:
            The processed value
        """
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            # Notify parent route that this handle moved
            self.route_item.handle_moved(self.control_point_index, self.pos())
        
        return super().itemChange(change, value)


class RouteItem(QGraphicsPathItem):
    """Graphics representation of a route between systems.
    
    Displays as a curved spline path with optional control point handles
    for editing the curve shape.
    """
    
    # Visual configuration
    LINE_WIDTH = 3
    NORMAL_COLOR = QColor(100, 200, 255)  # Light blue for normal state
    SELECTED_COLOR = QColor(255, 255, 100)  # Yellow for selected state
    
    def __init__(self, route_data: RouteData, system_items_dict: Dict[str, 'SystemItem']):
        """Initialize the route graphics item.
        
        Args:
            route_data: The RouteData object this item represents
            system_items_dict: Dictionary mapping system IDs to SystemItem instances
                              Used to get current system positions
        """
        super().__init__()
        self.route_data = route_data
        self.system_items = system_items_dict
        self.handles: List[RouteHandleItem] = []
        
        # Configure appearance
        self.setPen(QPen(self.NORMAL_COLOR, self.LINE_WIDTH, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Enable interaction
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsPathItem.ItemSendsGeometryChanges, True)
        
        # Lower z-value so routes are below systems but above templates
        self.setZValue(5)
        
        # Initial path computation
        self.recompute_path()
    
    def get_start_position(self) -> Optional[QPointF]:
        """Get the current position of the start system.
        
        Returns:
            Position of start system, or None if system not found
        """
        if self.route_data.start_system_id in self.system_items:
            return self.system_items[self.route_data.start_system_id].pos()
        return None
    
    def get_end_position(self) -> Optional[QPointF]:
        """Get the current position of the end system.
        
        Returns:
            Position of end system, or None if system not found
        """
        if self.route_data.end_system_id in self.system_items:
            return self.system_items[self.route_data.end_system_id].pos()
        return None
    
    def recompute_path(self):
        """Recompute the spline path based on current system positions and control points."""
        start_pos = self.get_start_position()
        end_pos = self.get_end_position()
        
        if start_pos is None or end_pos is None:
            # Can't draw path without both endpoints
            self.setPath(QPainterPath())
            return
        
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # If no control points, draw a straight line
        if not self.route_data.control_points:
            path.lineTo(end_pos)
        else:
            # Draw a smooth curve through control points using cubic splines
            # Convert control points to QPointF
            control_qpoints = [QPointF(cp[0], cp[1]) for cp in self.route_data.control_points]
            
            if len(control_qpoints) == 1:
                # With one control point, use quadratic curve
                path.quadTo(control_qpoints[0], end_pos)
            else:
                # With multiple control points, use cubic curves
                # Create smooth path through all points
                all_points = [start_pos] + control_qpoints + [end_pos]
                
                # Use cubic bezier curves to create smooth path
                for i in range(len(all_points) - 1):
                    if i == 0:
                        # First segment
                        p0 = all_points[i]
                        p1 = all_points[i + 1]
                        # Control point 1/3 of the way
                        c1 = QPointF(p0.x() + (p1.x() - p0.x()) / 3, 
                                    p0.y() + (p1.y() - p0.y()) / 3)
                        # Control point 2/3 of the way
                        c2 = QPointF(p0.x() + 2 * (p1.x() - p0.x()) / 3,
                                    p0.y() + 2 * (p1.y() - p0.y()) / 3)
                        path.cubicTo(c1, c2, p1)
                    else:
                        # Subsequent segments
                        p1 = all_points[i + 1]
                        path.lineTo(p1)
        
        self.setPath(path)
    
    def handle_moved(self, index: int, position: QPointF):
        """Called when a control point handle is moved.
        
        Args:
            index: Index of the control point that moved
            position: New position of the handle
        """
        # Update the control point in the data model
        self.route_data.control_points[index] = (position.x(), position.y())
        # Recompute the path
        self.recompute_path()
    
    def show_handles(self):
        """Show control point handles for editing."""
        # Remove existing handles
        self.hide_handles()
        
        # Create handles for each control point
        for i, (x, y) in enumerate(self.route_data.control_points):
            handle = RouteHandleItem(i, QPointF(x, y), self)
            self.handles.append(handle)
    
    def hide_handles(self):
        """Hide control point handles."""
        for handle in self.handles:
            self.scene().removeItem(handle)
        self.handles.clear()
    
    def itemChange(self, change, value):
        """Handle item changes, particularly selection.
        
        Args:
            change: The type of change
            value: The new value
            
        Returns:
            The processed value
        """
        if change == QGraphicsPathItem.ItemSelectedHasChanged:
            # Update visual appearance when selection changes
            if self.isSelected():
                self.setPen(QPen(self.SELECTED_COLOR, self.LINE_WIDTH, 
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                self.show_handles()
            else:
                self.setPen(QPen(self.NORMAL_COLOR, self.LINE_WIDTH,
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                self.hide_handles()
        
        return super().itemChange(change, value)
    
    def get_route_data(self) -> RouteData:
        """Get the underlying route data.
        
        Returns:
            The RouteData object for this item
        """
        return self.route_data
    
    def update_from_system_movement(self):
        """Update the route path when connected systems have moved."""
        self.recompute_path()
        # Update handle positions if they're visible
        if self.handles:
            for i, handle in enumerate(self.handles):
                x, y = self.route_data.control_points[i]
                handle.setPos(QPointF(x, y))
