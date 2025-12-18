"""Project data model for the Star Map Editor.

This module defines the core data structures for representing
a complete map project including templates, systems, routes, and zones.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from PySide6.QtCore import QPointF


@dataclass
class TemplateData:
    """Data model for a template image layer.
    
    Templates are background images that can be independently positioned,
    scaled, and adjusted for opacity. Multiple templates can be loaded
    and layered.
    
    Attributes:
        id: Unique identifier for the template (UUID string)
        filepath: Path to the template image file
        position: Position in scene coordinates (x, y tuple)
        scale: Scale factor (1.0 = 100%)
        opacity: Opacity value (0.0 = transparent, 1.0 = opaque)
        locked: Whether the template can be moved/scaled
        z_order: Layer ordering (higher values = on top)
    """
    id: str
    filepath: str
    position: tuple[float, float] = (0.0, 0.0)
    scale: float = 1.0
    opacity: float = 1.0
    locked: bool = False
    z_order: int = 0
    
    @classmethod
    def create_new(cls, filepath: str, position: tuple[float, float] = (0.0, 0.0)):
        """Create a new template with a generated UUID.
        
        Args:
            filepath: Path to the template image
            position: Initial position (default: origin)
            
        Returns:
            New TemplateData instance
        """
        return cls(
            id=str(uuid.uuid4()),
            filepath=filepath,
            position=position
        )


@dataclass
class RouteGroup:
    """Data model for a named group of routes.
    
    Route groups allow organizing multiple route segments under a common name,
    which can be useful for defining trade lanes, patrol routes, etc.
    
    Attributes:
        id: Unique identifier for the group (UUID string)
        name: Display name of the group
        route_ids: List of route IDs that belong to this group
    """
    id: str
    name: str
    route_ids: List[str] = field(default_factory=list)
    
    @classmethod
    def create_new(cls, name: str, route_ids: Optional[List[str]] = None):
        """Create a new route group with a generated UUID.
        
        Args:
            name: Display name for the group
            route_ids: Optional list of route IDs to include
            
        Returns:
            New RouteGroup instance
        """
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            route_ids=route_ids or []
        )


@dataclass
class MapProject:
    """Master data container for a complete map project.
    
    This represents all the data that makes up a map project,
    including templates, systems, routes, zones, and metadata.
    
    Attributes:
        templates: List of template image data
        systems: Dictionary mapping system ID to SystemData
        routes: Dictionary mapping route ID to RouteData
        route_groups: Dictionary mapping route group ID to RouteGroup
        zones: List of zone data (future implementation)
        metadata: Optional project metadata (name, version, etc.)
    """
    templates: List[TemplateData] = field(default_factory=list)
    systems: Dict[str, 'SystemData'] = field(default_factory=dict)
    routes: Dict[str, 'RouteData'] = field(default_factory=dict)
    route_groups: Dict[str, RouteGroup] = field(default_factory=dict)
    zones: List = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata with defaults if not provided."""
        if not self.metadata:
            self.metadata = {
                "name": "Unnamed Map",
                "version": "1.0"
            }
    
    def add_template(self, template: TemplateData):
        """Add a template to the project.
        
        Args:
            template: TemplateData to add
        """
        self.templates.append(template)
    
    def remove_template(self, template_id: str):
        """Remove a template from the project.
        
        Args:
            template_id: ID of the template to remove
        """
        self.templates = [t for t in self.templates if t.id != template_id]
    
    def get_template(self, template_id: str) -> Optional[TemplateData]:
        """Get a template by ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            TemplateData if found, None otherwise
        """
        for template in self.templates:
            if template.id == template_id:
                return template
        return None
    
    def add_route(self, route: 'RouteData'):
        """Add a route to the project.
        
        Args:
            route: RouteData to add
        """
        self.routes[route.id] = route
    
    def remove_route(self, route_id: str):
        """Remove a route from the project.
        
        Args:
            route_id: ID of the route to remove
        """
        if route_id in self.routes:
            del self.routes[route_id]
    
    def get_route(self, route_id: str) -> Optional['RouteData']:
        """Get a route by ID.
        
        Args:
            route_id: ID of the route to retrieve
            
        Returns:
            RouteData if found, None otherwise
        """
        return self.routes.get(route_id)
    
    def add_route_group(self, route_group: RouteGroup):
        """Add a route group to the project.
        
        Args:
            route_group: RouteGroup to add
        """
        self.route_groups[route_group.id] = route_group
    
    def remove_route_group(self, group_id: str):
        """Remove a route group from the project.
        
        Args:
            group_id: ID of the route group to remove
        """
        if group_id in self.route_groups:
            del self.route_groups[group_id]
    
    def get_route_group(self, group_id: str) -> Optional[RouteGroup]:
        """Get a route group by ID.
        
        Args:
            group_id: ID of the route group to retrieve
            
        Returns:
            RouteGroup if found, None otherwise
        """
        return self.route_groups.get(group_id)
    
    def clear(self):
        """Clear all project data."""
        self.templates.clear()
        self.systems.clear()
        self.routes.clear()
        self.route_groups.clear()
        self.zones.clear()
        self.metadata = {
            "name": "Unnamed Map",
            "version": "1.0"
        }
    
    def rescale_world(self, factor: float, scale_templates: bool = True, 
                     anchor_mode: str = "centroid") -> None:
        """Rescale all world geometry by the given factor.
        
        This method scales:
        - System positions
        - Route control points
        - Template positions and scales (if scale_templates is True)
        
        Args:
            factor: Scale factor to apply (e.g., 0.5 = half size, 2.0 = double size)
            scale_templates: Whether to scale templates as well
            anchor_mode: Either "centroid" (default) or "origin"
                - "centroid": Scale around the center of all systems
                - "origin": Scale around (0, 0)
        """
        # Determine anchor point
        if anchor_mode == "origin":
            anchor = QPointF(0.0, 0.0)
        else:  # "centroid"
            # Calculate centroid of all systems
            if self.systems:
                sum_x = sum(system.position.x() for system in self.systems.values())
                sum_y = sum(system.position.y() for system in self.systems.values())
                count = len(self.systems)
                anchor = QPointF(sum_x / count, sum_y / count)
            else:
                # Fallback to (0, 0) if no systems
                anchor = QPointF(0.0, 0.0)
        
        # Scale system positions: p' = anchor + (p - anchor) * factor
        for system in self.systems.values():
            old_pos = system.position
            new_x = anchor.x() + (old_pos.x() - anchor.x()) * factor
            new_y = anchor.y() + (old_pos.y() - anchor.y()) * factor
            system.position = QPointF(new_x, new_y)
        
        # Scale route control points
        for route in self.routes.values():
            scaled_points = []
            for px, py in route.control_points:
                new_x = anchor.x() + (px - anchor.x()) * factor
                new_y = anchor.y() + (py - anchor.y()) * factor
                scaled_points.append((new_x, new_y))
            route.control_points = scaled_points
        
        # Scale templates if requested
        if scale_templates:
            for template in self.templates:
                # Scale template position
                old_x, old_y = template.position
                new_x = anchor.x() + (old_x - anchor.x()) * factor
                new_y = anchor.y() + (old_y - anchor.y()) * factor
                template.position = (new_x, new_y)
                
                # Scale template scale factor
                template.scale *= factor

# Import SystemData and RouteData here to avoid circular imports
# These are defined in systems.py and routes.py
from .systems import SystemData
from .routes import RouteData
