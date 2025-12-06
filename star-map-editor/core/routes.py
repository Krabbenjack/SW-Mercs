"""Route management for the Star Map Editor - Ghost-Line System.

This module handles route data structures and graphics representation for
creating curved routes between star systems using a ghost-line drawing approach.
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QPen, QColor


@dataclass
class RouteData:
    """Data model for a hyperlane route between systems.
    
    Routes are paths connecting two star systems. The shape is defined by
    intermediate points that can be drawn freehand using a ghost-line gesture.
    
    Attributes:
        id: Unique identifier for the route (UUID string)
        name: Display name of the route
        start_system_id: ID of the starting system
        end_system_id: ID of the ending system
        control_points: List of intermediate points defining the route's shape
                       (excluding start/end system positions which are added at render time)
                       Renamed from old system but repurposed for ghost-line points
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
            control_points: Optional list of intermediate shape points
            
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


class RouteItem(QGraphicsPathItem):
    """Graphics representation of a route between systems.
    
    Displays as a path (straight line or curved based on shape_points).
    Shape can be modified by drawing a ghost-line with G/Shift + drag.
    """
    
    # Visual configuration
    LINE_WIDTH = 3
    NORMAL_COLOR = QColor(100, 200, 255)  # Light blue
    SELECTED_COLOR = QColor(255, 255, 100)  # Yellow
    GROUP_SELECTION_COLOR = QColor(255, 150, 255)  # Magenta
    
    def __init__(self, route_data: RouteData, system_items_dict: Dict[str, 'SystemItem']):
        """Initialize the route graphics item.
        
        Args:
            route_data: The RouteData object this item represents
            system_items_dict: Dictionary mapping system IDs to SystemItem instances
        """
        super().__init__()
        self.route_data = route_data
        self.system_items = system_items_dict
        self.is_group_selected = False
        
        # Configure appearance
        self.setPen(QPen(self.NORMAL_COLOR, self.LINE_WIDTH, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Enable interaction
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsPathItem.ItemSendsGeometryChanges, True)
        
        # Z-order: routes below systems but above templates
        self.setZValue(5)
        
        # Initial path computation
        self.recompute_path()
    
    def get_start_position(self) -> Optional[QPointF]:
        """Get the current position of the start system."""
        if self.route_data.start_system_id in self.system_items:
            return self.system_items[self.route_data.start_system_id].pos()
        return None
    
    def get_end_position(self) -> Optional[QPointF]:
        """Get the current position of the end system."""
        if self.route_data.end_system_id in self.system_items:
            return self.system_items[self.route_data.end_system_id].pos()
        return None
    
    def recompute_path(self):
        """Recompute the route path based on current system positions and shape points."""
        start_pos = self.get_start_position()
        end_pos = self.get_end_position()
        
        if start_pos is None or end_pos is None:
            self.setPath(QPainterPath())
            return
        
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # If no shape points, draw straight line
        if not self.route_data.control_points:
            path.lineTo(end_pos)
        else:
            # Draw through intermediate points
            for x, y in self.route_data.control_points:
                path.lineTo(QPointF(x, y))
            # Connect to end
            path.lineTo(end_pos)
        
        self.setPath(path)
    
    def set_shape_from_stroke(self, stroke_points: List[QPointF], decimate: bool = True, smooth: bool = True):
        """Set the route's shape from a ghost-line stroke.
        
        Args:
            stroke_points: Raw list of points from user's mouse drag
            decimate: Whether to reduce the number of points
            smooth: Whether to apply smoothing
        """
        if len(stroke_points) < 2:
            # Not enough points, reset to straight line
            self.route_data.control_points = []
            self.recompute_path()
            return
        
        # Start with the stroke points
        points = stroke_points.copy()
        
        # Snap first and last to systems
        start_pos = self.get_start_position()
        end_pos = self.get_end_position()
        if start_pos:
            points[0] = start_pos
        if end_pos:
            points[-1] = end_pos
        
        # Decimate: keep every Nth point to reduce complexity
        if decimate and len(points) > 10:
            step = max(1, len(points) // 20)  # Keep ~20 points
            decimated = [points[i] for i in range(0, len(points), step)]
            # Always include the last point
            if points[-1] not in decimated:
                decimated.append(points[-1])
            points = decimated
        
        # Simple smoothing: moving average
        if smooth and len(points) > 3:
            smoothed = [points[0]]  # Keep first point
            for i in range(1, len(points) - 1):
                # Average with neighbors
                prev = points[i - 1]
                curr = points[i]
                next_p = points[i + 1]
                avg_x = (prev.x() + curr.x() + next_p.x()) / 3.0
                avg_y = (prev.y() + curr.y() + next_p.y()) / 3.0
                smoothed.append(QPointF(avg_x, avg_y))
            smoothed.append(points[-1])  # Keep last point
            points = smoothed
        
        # Store as shape points (excluding start/end which come from systems)
        # Skip first and last point since they're system positions
        self.route_data.control_points = [(p.x(), p.y()) for p in points[1:-1]]
        
        # Recompute the visual path
        self.recompute_path()
    
    def reset_to_straight_line(self):
        """Reset the route to a straight line between systems."""
        self.route_data.control_points = []
        self.recompute_path()
    
    def itemChange(self, change, value):
        """Handle item changes, particularly selection."""
        if change == QGraphicsPathItem.ItemSelectedHasChanged:
            self.update_visual_state()
        return super().itemChange(change, value)
    
    def get_route_data(self) -> RouteData:
        """Get the underlying route data."""
        return self.route_data
    
    def update_from_system_movement(self):
        """Update the route path when connected systems have moved."""
        self.recompute_path()
    
    def update_name(self, name: str):
        """Update the route name."""
        self.route_data.name = name
    
    def set_group_selection(self, selected: bool):
        """Set group selection state and update visual appearance."""
        self.is_group_selected = selected
        self.update_visual_state()
    
    def update_visual_state(self):
        """Update visual appearance based on selection state."""
        if self.is_group_selected:
            self.setPen(QPen(self.GROUP_SELECTION_COLOR, self.LINE_WIDTH + 1, 
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        elif self.isSelected():
            self.setPen(QPen(self.SELECTED_COLOR, self.LINE_WIDTH, 
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        else:
            self.setPen(QPen(self.NORMAL_COLOR, self.LINE_WIDTH,
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
