"""Route management for the Star Map Editor.

This module handles route data structures and graphics representation for
creating curved routes between star systems.
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtWidgets import (
    QGraphicsPathItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsTextItem
)
from PySide6.QtGui import QPainterPath, QPen, QColor, QBrush, QPainter, QFont


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
    
    RADIUS = 8  # Handle radius in scene units (increased for better visibility)
    NORMAL_COLOR = QColor(255, 180, 0)  # Bright orange for normal state
    HOVER_COLOR = QColor(255, 100, 0)  # Vivid orange for hover
    
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
        self._is_being_dragged = False
        
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
            self._is_being_dragged = True
        
        return super().itemChange(change, value)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to notify scene of modification."""
        super().mouseReleaseEvent(event)
        if self._is_being_dragged:
            self._is_being_dragged = False
            # Notify the scene that an item was modified
            if self.scene():
                # Find the view and emit item_modified signal
                for view in self.scene().views():
                    if hasattr(view, 'item_modified'):
                        view.item_modified.emit()
                        break


class RouteItem(QGraphicsPathItem):
    """Graphics representation of a route between systems.
    
    Displays as a curved spline path with optional control point handles
    for editing the curve shape.
    """
    
    # Visual configuration
    LINE_WIDTH = 3
    NORMAL_COLOR = QColor(100, 200, 255)  # Light blue for normal state
    SELECTED_COLOR = QColor(255, 255, 100)  # Yellow for selected state
    GROUP_SELECTION_COLOR = QColor(255, 150, 255)  # Magenta for group selection
    
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
        self.is_group_selected = False  # Track if selected for grouping
        
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
        elif len(self.route_data.control_points) == 1:
            # With one control point, use quadratic curve
            cp = self.route_data.control_points[0]
            path.quadTo(QPointF(cp[0], cp[1]), end_pos)
        else:
            # With 2+ control points, create a smooth spline through all points
            # Build list of all points: start -> control points -> end
            all_points = [start_pos]
            for cp in self.route_data.control_points:
                all_points.append(QPointF(cp[0], cp[1]))
            all_points.append(end_pos)
            
            # Use a simple Catmull-Rom-like spline that passes through all control points
            # For each segment, use cubic bezier with control points derived from neighbors
            for i in range(len(all_points) - 1):
                p0 = all_points[i]
                p1 = all_points[i + 1]
                
                # Calculate tangent directions based on neighbors
                if i == 0:
                    # First segment: tangent from current to next
                    if len(all_points) > 2:
                        tangent_out = QPointF(
                            (all_points[i + 1].x() - p0.x()) * 0.5,
                            (all_points[i + 1].y() - p0.y()) * 0.5
                        )
                    else:
                        tangent_out = QPointF(
                            (p1.x() - p0.x()) * 0.3,
                            (p1.y() - p0.y()) * 0.3
                        )
                else:
                    # Use previous and next points for tangent
                    tangent_out = QPointF(
                        (p1.x() - all_points[i - 1].x()) * 0.3,
                        (p1.y() - all_points[i - 1].y()) * 0.3
                    )
                
                if i == len(all_points) - 2:
                    # Last segment: tangent to endpoint
                    if len(all_points) > 2:
                        tangent_in = QPointF(
                            (p1.x() - all_points[i].x()) * 0.5,
                            (p1.y() - all_points[i].y()) * 0.5
                        )
                    else:
                        tangent_in = QPointF(
                            (p1.x() - p0.x()) * 0.3,
                            (p1.y() - p0.y()) * 0.3
                        )
                else:
                    # Use neighbors for smooth tangent
                    tangent_in = QPointF(
                        (all_points[i + 2].x() - p0.x()) * 0.3,
                        (all_points[i + 2].y() - p0.y()) * 0.3
                    )
                
                # Create cubic bezier curve
                c1 = QPointF(p0.x() + tangent_out.x(), p0.y() + tangent_out.y())
                c2 = QPointF(p1.x() - tangent_in.x(), p1.y() - tangent_in.y())
                path.cubicTo(c1, c2, p1)
        
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
            if self.scene():
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
            self.update_visual_state()
            if self.isSelected():
                self.show_handles()
            else:
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
    
    def update_name(self, name: str):
        """Update the route name.
        
        Args:
            name: New name for the route
        """
        self.route_data.name = name
    
    def set_group_selection(self, selected: bool):
        """Set group selection state and update visual appearance.
        
        Args:
            selected: Whether this route is selected for grouping
        """
        self.is_group_selected = selected
        self.update_visual_state()
    
    def update_visual_state(self):
        """Update visual appearance based on selection state."""
        if self.is_group_selected:
            # Use group selection color with thicker line
            self.setPen(QPen(self.GROUP_SELECTION_COLOR, self.LINE_WIDTH + 1, 
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        elif self.isSelected():
            # Use normal selected color
            self.setPen(QPen(self.SELECTED_COLOR, self.LINE_WIDTH, 
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        else:
            # Use normal color
            self.setPen(QPen(self.NORMAL_COLOR, self.LINE_WIDTH,
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    
    def insert_control_point(self, scene_pos: QPointF):
        """Insert a new control point at the given scene position.
        
        Finds the best position in the control points list by determining
        which segment the point is closest to.
        
        Args:
            scene_pos: Position in scene coordinates where to insert the point
        """
        start_pos = self.get_start_position()
        end_pos = self.get_end_position()
        
        if start_pos is None or end_pos is None:
            return
        
        # Build list of all points: start -> control points -> end
        all_points = [start_pos]
        for cp in self.route_data.control_points:
            all_points.append(QPointF(cp[0], cp[1]))
        all_points.append(end_pos)
        
        # Find which segment the click is closest to
        best_segment_index = 0
        min_distance = float('inf')
        
        for i in range(len(all_points) - 1):
            p1 = all_points[i]
            p2 = all_points[i + 1]
            
            # Calculate distance from scene_pos to line segment p1-p2
            distance = self._point_to_segment_distance(scene_pos, p1, p2)
            
            if distance < min_distance:
                min_distance = distance
                best_segment_index = i
        
        # Insert the control point at the appropriate position
        # Segment 0 is between start and first control point (or end if no control points)
        # So we insert at position best_segment_index in the control_points list
        insert_index = best_segment_index
        
        self.route_data.control_points.insert(insert_index, (scene_pos.x(), scene_pos.y()))
        
        # Recompute path and handles
        self.recompute_path()
        if self.isSelected():
            self.show_handles()
    
    def _point_to_segment_distance(self, point: QPointF, seg_start: QPointF, seg_end: QPointF) -> float:
        """Calculate the distance from a point to a line segment.
        
        Args:
            point: The point to measure from
            seg_start: Start of the line segment
            seg_end: End of the line segment
            
        Returns:
            Distance from point to segment
        """
        # Vector from seg_start to seg_end
        dx = seg_end.x() - seg_start.x()
        dy = seg_end.y() - seg_start.y()
        
        # Length squared of the segment
        length_sq = dx * dx + dy * dy
        
        if length_sq == 0:
            # Segment is a point
            return ((point.x() - seg_start.x()) ** 2 + (point.y() - seg_start.y()) ** 2) ** 0.5
        
        # Calculate parameter t for the projection of point onto the line
        # t = 0 means projection is at seg_start, t = 1 means at seg_end
        t = max(0, min(1, ((point.x() - seg_start.x()) * dx + (point.y() - seg_start.y()) * dy) / length_sq))
        
        # Calculate the projection point
        proj_x = seg_start.x() + t * dx
        proj_y = seg_start.y() + t * dy
        
        # Return distance from point to projection
        return ((point.x() - proj_x) ** 2 + (point.y() - proj_y) ** 2) ** 0.5
