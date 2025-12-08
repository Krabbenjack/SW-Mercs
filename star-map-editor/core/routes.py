"""Route management for the Star Map Editor - Polyline System.

This module handles route data structures and graphics representation for
creating polyline routes between star systems by clicking control points.
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
    
    WORLD SPACE: Control points are stored in HSU coordinates.
    Route geometry is defined by system positions (HSU) and intermediate control points (HSU).
    
    Routes can be either:
    1. Simple routes: Two systems with intermediate coordinate control points
    2. Chain routes: Multiple systems in sequence (A → B → C)
    
    Attributes:
        id: Unique identifier for the route (UUID string)
        name: Display name of the route
        start_system_id: ID of the starting system (for backward compatibility)
        end_system_id: ID of the ending system (for backward compatibility)
        control_points: List of intermediate points in WORLD SPACE (HSU coordinates)
                       defining the route's shape (excluding start/end system positions
                       which are added at render time). These are the points clicked by
                       user between start and end systems.
        system_chain: Optional ordered list of system IDs that form the route path.
                     If present, overrides start/end_system_id. First system is start,
                     last is end. Intermediate systems are waypoints.
                     Format: [sys1_id, sys2_id, sys3_id, ...]
    """
    id: str
    name: str
    start_system_id: str
    end_system_id: str
    control_points: List[tuple[float, float]] = field(default_factory=list)
    system_chain: Optional[List[str]] = None
    
    @classmethod
    def create_new(cls, name: str, start_system_id: str, end_system_id: str,
                   control_points: Optional[List[tuple[float, float]]] = None):
        """Create a new route with a generated UUID.
        
        Args:
            name: Display name for the route
            start_system_id: ID of the starting system
            end_system_id: ID of the ending system
            control_points: Optional list of intermediate shape points (WORLD SPACE: HSU coordinates)
            
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
    
    def get_system_chain(self) -> List[str]:
        """Get the ordered list of system IDs in this route.
        
        Returns list from system_chain if available, otherwise [start, end].
        """
        if self.system_chain:
            return self.system_chain
        return [self.start_system_id, self.end_system_id]
    
    def set_system_chain(self, chain: List[str]):
        """Set the system chain and update start/end for compatibility.
        
        Args:
            chain: Ordered list of system IDs (must have at least 2 systems)
        """
        if len(chain) < 2:
            raise ValueError("Route must have at least 2 systems")
        self.system_chain = chain
        self.start_system_id = chain[0]
        self.end_system_id = chain[-1]
    
    def insert_system_at(self, index: int, system_id: str):
        """Insert a system into the route chain at the specified position.
        
        Args:
            index: Position to insert (0 = before first, len = after last)
            system_id: ID of the system to insert
        """
        chain = self.get_system_chain()
        chain.insert(index, system_id)
        self.set_system_chain(chain)
    
    def remove_system_at(self, index: int):
        """Remove a system from the route chain at the specified position.
        
        Args:
            index: Position to remove (0-based)
        """
        chain = self.get_system_chain()
        if len(chain) <= 2:
            raise ValueError("Cannot remove system - route must have at least 2 systems")
        chain.pop(index)
        self.set_system_chain(chain)
    
    def remove_system_by_id(self, system_id: str):
        """Remove a system from the route chain by ID.
        
        Args:
            system_id: ID of the system to remove
        """
        chain = self.get_system_chain()
        if system_id not in chain:
            return
        if len(chain) <= 2:
            raise ValueError("Cannot remove system - route must have at least 2 systems")
        chain.remove(system_id)
        self.set_system_chain(chain)
    
    def get_system_index(self, system_id: str) -> int:
        """Get the index of a system in the chain.
        
        Args:
            system_id: ID of the system
            
        Returns:
            Index of system, or -1 if not found
        """
        chain = self.get_system_chain()
        try:
            return chain.index(system_id)
        except ValueError:
            return -1
    
    def contains_system(self, system_id: str) -> bool:
        """Check if this route contains the given system.
        
        Args:
            system_id: ID of the system to check
            
        Returns:
            True if system is in the route chain
        """
        return system_id in self.get_system_chain()
    
    def split_at_system(self, system_id: str, name_prefix: str = "") -> Optional['RouteData']:
        """Split this route at the given system, creating a new route.
        
        This route will be from start to system_id (inclusive).
        Returns a new route from system_id (inclusive) to end.
        
        Args:
            system_id: ID of the system to split at
            name_prefix: Optional prefix for the new route name
            
        Returns:
            New RouteData for the second part, or None if system not found or at edges
        """
        chain = self.get_system_chain()
        try:
            index = chain.index(system_id)
        except ValueError:
            return None
        
        # Can't split at first or last system
        if index == 0 or index == len(chain) - 1:
            return None
        
        # Split the chain
        # This route: from start to split point (inclusive)
        first_chain = chain[:index + 1]
        # New route: from split point (inclusive) to end
        second_chain = chain[index:]
        
        # Update this route
        self.set_system_chain(first_chain)
        
        # Create new route for second part
        new_name = f"{name_prefix}{self.name} (2)" if name_prefix else f"{self.name} (2)"
        new_route = RouteData.create_new(
            name=new_name,
            start_system_id=second_chain[0],
            end_system_id=second_chain[-1],
            control_points=[]  # Clear control points for now
        )
        new_route.set_system_chain(second_chain)
        
        return new_route
    
    def split_at_index(self, index: int, name_prefix: str = "") -> Optional['RouteData']:
        """Split this route at the given index in the system chain.
        
        Args:
            index: Index in the chain to split at (0-based)
            name_prefix: Optional prefix for the new route name
            
        Returns:
            New RouteData for the second part, or None if invalid index
        """
        chain = self.get_system_chain()
        if index <= 0 or index >= len(chain) - 1:
            return None
        
        system_id = chain[index]
        return self.split_at_system(system_id, name_prefix)
    
    @classmethod
    def merge_routes(cls, route1: 'RouteData', route2: 'RouteData', 
                     new_name: Optional[str] = None) -> Optional['RouteData']:
        """Merge two routes into a single route.
        
        Automatically detects valid merge configurations:
        - End of route1 connects to start of route2
        - End of route1 connects to end of route2 (route2 reversed)
        - Start of route1 connects to end of route2
        - Start of route1 connects to start of route2 (route2 reversed)
        
        Args:
            route1: First route
            route2: Second route
            new_name: Optional name for merged route (defaults to route1 name)
            
        Returns:
            New merged RouteData, or None if routes can't be merged
        """
        chain1 = route1.get_system_chain()
        chain2 = route2.get_system_chain()
        
        merged_chain = None
        
        # Try end-to-start: route1 end == route2 start
        if chain1[-1] == chain2[0]:
            # Merge: chain1 + chain2[1:] (skip duplicate)
            merged_chain = chain1 + chain2[1:]
        # Try end-to-end: route1 end == route2 end
        elif chain1[-1] == chain2[-1]:
            # Merge: chain1 + reversed(chain2[:-1])
            merged_chain = chain1 + list(reversed(chain2[:-1]))
        # Try start-to-end: route1 start == route2 end
        elif chain1[0] == chain2[-1]:
            # Merge: chain2 + chain1[1:]
            merged_chain = chain2 + chain1[1:]
        # Try start-to-start: route1 start == route2 start
        elif chain1[0] == chain2[0]:
            # Merge: reversed(chain2[1:]) + chain1
            merged_chain = list(reversed(chain2[1:])) + chain1
        
        if not merged_chain:
            return None
        
        # Create new merged route
        name = new_name or f"{route1.name} + {route2.name}"
        merged = cls.create_new(
            name=name,
            start_system_id=merged_chain[0],
            end_system_id=merged_chain[-1],
            control_points=[]  # Clear control points
        )
        merged.set_system_chain(merged_chain)
        
        return merged


class RouteItem(QGraphicsPathItem):
    """Graphics representation of a route between systems.
    
    WORLD SPACE ARCHITECTURE:
    - Route control points are stored in WORLD SPACE (HSU coordinates)
    - Routes connect systems at their HSU positions
    - Visual rendering (line width) is in UI SPACE
    - Routes automatically update when systems move (HSU positions change)
    
    Displays as a polyline path through clicked control points.
    Routes are NOT editable after creation - to modify, delete and redraw.
    """
    
    # Visual configuration (UI SPACE)
    LINE_WIDTH = 3
    NORMAL_COLOR = QColor(100, 200, 255)  # Light blue
    SELECTED_COLOR = QColor(255, 255, 100)  # Yellow
    GROUP_SELECTION_COLOR = QColor(255, 150, 255)  # Magenta
    
    def __init__(self, route_data: RouteData, system_items_dict: Dict[str, 'SystemItem']):
        """Initialize the route graphics item.
        
        Args:
            route_data: The RouteData object this item represents (WORLD SPACE coordinates)
            system_items_dict: Dictionary mapping system IDs to SystemItem instances
        """
        super().__init__()
        self.route_data = route_data
        self.system_items = system_items_dict
        self.is_group_selected = False
        
        # Configure appearance (UI SPACE)
        self.setPen(QPen(self.NORMAL_COLOR, self.LINE_WIDTH, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Enable interaction
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsPathItem.ItemSendsGeometryChanges, True)
        
        # Z-order: routes below systems but above templates
        self.setZValue(5)
        
        # Initial path computation (WORLD SPACE coordinates)
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
        """Recompute the route path based on current system positions and shape points.
        
        Handles both simple routes (start -> end with control points) and 
        system chain routes (A -> B -> C -> ...).
        """
        path = QPainterPath()
        
        # Get the system chain
        system_chain = self.route_data.get_system_chain()
        
        # Get positions for all systems in chain
        positions = []
        for sys_id in system_chain:
            if sys_id in self.system_items:
                positions.append(self.system_items[sys_id].pos())
            else:
                # System not found - can't draw route
                self.setPath(QPainterPath())
                return
        
        if len(positions) < 2:
            self.setPath(QPainterPath())
            return
        
        # Start path at first system
        path.moveTo(positions[0])
        
        # For simple 2-system routes with control points, use control points
        if len(system_chain) == 2 and self.route_data.control_points:
            # Draw through intermediate control points
            for x, y in self.route_data.control_points:
                path.lineTo(QPointF(x, y))
            # Connect to end
            path.lineTo(positions[1])
        else:
            # For chain routes, just connect system to system
            for i in range(1, len(positions)):
                path.lineTo(positions[i])
        
        self.setPath(path)
    
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
    
    def get_segment_at_point(self, scene_pos: QPointF, threshold: float = 20.0) -> Optional[tuple[int, str, str]]:
        """Find which segment (pair of consecutive systems) is closest to the given point.
        
        Args:
            scene_pos: Position in scene coordinates
            threshold: Maximum distance to consider a hit
            
        Returns:
            Tuple of (segment_index, system_id_1, system_id_2) if found, None otherwise
            segment_index is the index of the first system in the pair
        """
        system_chain = self.route_data.get_system_chain()
        if len(system_chain) < 2:
            return None
        
        # Get positions for all systems
        positions = []
        for sys_id in system_chain:
            if sys_id in self.system_items:
                positions.append(self.system_items[sys_id].pos())
            else:
                return None
        
        # Find closest segment
        min_dist = float('inf')
        closest_segment = None
        
        for i in range(len(positions) - 1):
            p1 = positions[i]
            p2 = positions[i + 1]
            
            # Calculate distance from point to line segment
            dist = self._point_to_segment_distance(scene_pos, p1, p2)
            
            if dist < min_dist and dist <= threshold:
                min_dist = dist
                closest_segment = (i, system_chain[i], system_chain[i + 1])
        
        return closest_segment
    
    def _point_to_segment_distance(self, point: QPointF, seg_start: QPointF, seg_end: QPointF) -> float:
        """Calculate the shortest distance from a point to a line segment.
        
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
        
        if dx == 0 and dy == 0:
            # Segment is a point
            return ((point.x() - seg_start.x()) ** 2 + (point.y() - seg_start.y()) ** 2) ** 0.5
        
        # Parameter t represents position along the segment (0 to 1)
        t = max(0, min(1, ((point.x() - seg_start.x()) * dx + (point.y() - seg_start.y()) * dy) / (dx * dx + dy * dy)))
        
        # Closest point on segment
        closest_x = seg_start.x() + t * dx
        closest_y = seg_start.y() + t * dy
        
        # Distance from point to closest point
        return ((point.x() - closest_x) ** 2 + (point.y() - closest_y) ** 2) ** 0.5
