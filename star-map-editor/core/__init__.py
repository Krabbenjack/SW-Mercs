"""Core logic module for Star Map Editor.

This package contains all non-GUI business logic including:
- Project data models
- System and template management
- Project file I/O operations
"""

from .project_model import MapProject, TemplateData
from .systems import SystemData, SystemItem, SystemDialog
from .templates import TemplateItem

__all__ = [
    'MapProject',
    'TemplateData',
    'SystemData',
    'SystemItem',
    'SystemDialog',
    'TemplateItem',
]
