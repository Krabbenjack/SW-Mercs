"""Core logic module for Star Map Editor.

This package contains all non-GUI business logic including:
- Project data models
- System and template management
- Route management
- Project file I/O operations
"""

from .project_model import MapProject, TemplateData
from .systems import SystemData, SystemItem, SystemDialog, PlanetData, MoonData
from .templates import TemplateItem
from .routes import RouteData, RouteItem

__all__ = [
    'MapProject',
    'TemplateData',
    'SystemData',
    'SystemItem',
    'SystemDialog',
    'PlanetData',
    'MoonData',
    'TemplateItem',
    'RouteData',
    'RouteItem',
]

