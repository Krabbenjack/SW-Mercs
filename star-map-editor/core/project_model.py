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
class MapProject:
    """Master data container for a complete map project.
    
    This represents all the data that makes up a map project,
    including templates, systems, routes, zones, and metadata.
    
    Attributes:
        templates: List of template image data
        systems: Dictionary mapping system ID to SystemData
        routes: Dictionary mapping route ID to RouteData
        zones: List of zone data (future implementation)
        metadata: Optional project metadata (name, version, etc.)
    """
    templates: List[TemplateData] = field(default_factory=list)
    systems: Dict[str, 'SystemData'] = field(default_factory=dict)
    routes: Dict[str, 'RouteData'] = field(default_factory=dict)
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
    
    def clear(self):
        """Clear all project data."""
        self.templates.clear()
        self.systems.clear()
        self.routes.clear()
        self.zones.clear()
        self.metadata = {
            "name": "Unnamed Map",
            "version": "1.0"
        }

# Import SystemData and RouteData here to avoid circular imports
# These are defined in systems.py and routes.py
from .systems import SystemData
from .routes import RouteData
