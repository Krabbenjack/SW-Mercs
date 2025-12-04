"""Project file I/O operations for the Star Map Editor.

This module handles saving and loading .swmproj project files,
as well as exporting map data in game-readable formats.
"""

import json
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QPointF

from .project_model import MapProject, TemplateData
from .systems import SystemData


def save_project(project: MapProject, file_path: Path) -> bool:
    """Save a map project to a .swmproj file.
    
    Args:
        project: The MapProject to save
        file_path: Path where the project should be saved
        
    Returns:
        True if save successful, False otherwise
    """
    try:
        # Convert project to JSON-serializable format
        project_dict = {
            "metadata": project.metadata,
            "templates": [
                {
                    "id": t.id,
                    "filepath": t.filepath,
                    "position": list(t.position),
                    "scale": t.scale,
                    "opacity": t.opacity,
                    "locked": t.locked,
                    "z_order": t.z_order
                }
                for t in project.templates
            ],
            "systems": [
                {
                    "id": s.id,
                    "name": s.name,
                    "x": s.position.x(),
                    "y": s.position.y()
                }
                for s in project.systems.values()
            ],
            "routes": project.routes,
            "zones": project.zones
        }
        
        # Write to file with proper formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(project_dict, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving project: {e}")
        return False


def load_project(file_path: Path) -> Optional[MapProject]:
    """Load a map project from a .swmproj file.
    
    Args:
        file_path: Path to the project file to load
        
    Returns:
        MapProject if successful, None otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            project_dict = json.load(f)
        
        # Create project instance
        project = MapProject()
        
        # Load metadata
        if "metadata" in project_dict:
            project.metadata = project_dict["metadata"]
        
        # Load templates
        for t_dict in project_dict.get("templates", []):
            template = TemplateData(
                id=t_dict["id"],
                filepath=t_dict["filepath"],
                position=tuple(t_dict["position"]),
                scale=t_dict.get("scale", 1.0),
                opacity=t_dict.get("opacity", 1.0),
                locked=t_dict.get("locked", False),
                z_order=t_dict.get("z_order", 0)
            )
            project.templates.append(template)
        
        # Load systems
        for s_dict in project_dict.get("systems", []):
            system = SystemData(
                id=s_dict["id"],
                name=s_dict["name"],
                position=QPointF(s_dict["x"], s_dict["y"])
            )
            project.systems[system.id] = system
        
        # Load routes and zones (for future use)
        project.routes = project_dict.get("routes", [])
        project.zones = project_dict.get("zones", [])
        
        return project
    except Exception as e:
        print(f"Error loading project: {e}")
        return None


def export_map_data(project: MapProject, file_path: Path) -> bool:
    """Export map data in game-readable format.
    
    This exports only the game-relevant data (systems, routes, zones),
    not the editor-specific data (templates, etc.).
    
    Args:
        project: The MapProject to export
        file_path: Path where the export should be saved
        
    Returns:
        True if export successful, False otherwise
    """
    try:
        # Convert to game-readable format
        export_dict = {
            "mapName": project.metadata.get("name", "Unnamed Map"),
            "systems": [
                {
                    "id": s.id,
                    "name": s.name,
                    "x": s.position.x(),
                    "y": s.position.y()
                }
                for s in project.systems.values()
            ],
            "routes": project.routes,
            "zones": project.zones,
            "stats": {
                "totalSystems": len(project.systems),
                "totalRoutes": len(project.routes),
                "totalZones": len(project.zones),
                "version": project.metadata.get("version", "1.0")
            }
        }
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_dict, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error exporting map data: {e}")
        return False
