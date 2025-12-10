"""Project file I/O operations for the Star Map Editor.

This module handles saving and loading .swmproj project files,
as well as exporting map data in game-readable formats.
"""

import json
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QPointF

from .project_model import MapProject, TemplateData, RouteGroup
from .systems import SystemData
from .routes import RouteData


def _serialize_system(system: SystemData) -> dict:
    """Serialize a SystemData object to a dictionary.
    
    Args:
        system: The SystemData to serialize
        
    Returns:
        Dictionary with system data
    """
    system_dict = {
        "id": system.id,
        "name": system.name,
        "x": system.position.x(),
        "y": system.position.y()
    }
    
    # Add stats fields only if they have values
    if system.population_id:
        system_dict["population_id"] = system.population_id
    if system.imports:
        system_dict["imports"] = system.imports
    if system.exports:
        system_dict["exports"] = system.exports
    if system.facilities:
        system_dict["facilities"] = system.facilities
    
    return system_dict


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
                _serialize_system(s)
                for s in project.systems.values()
            ],
            "routes": [
                {
                    "id": r.id,
                    "name": r.name,
                    "start_system_id": r.start_system_id,
                    "end_system_id": r.end_system_id,
                    "control_points": r.control_points,
                    "system_chain": r.system_chain
                }
                for r in project.routes.values()
            ],
            "route_groups": [
                {
                    "id": g.id,
                    "name": g.name,
                    "route_ids": g.route_ids
                }
                for g in project.route_groups.values()
            ],
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
                position=QPointF(s_dict["x"], s_dict["y"]),
                population_id=s_dict.get("population_id"),
                imports=s_dict.get("imports", []),
                exports=s_dict.get("exports", []),
                facilities=s_dict.get("facilities", [])
            )
            project.systems[system.id] = system
        
        # Load routes
        for r_dict in project_dict.get("routes", []):
            # Only load routes if both start and end systems exist
            if (r_dict.get("start_system_id") in project.systems and
                r_dict.get("end_system_id") in project.systems):
                route = RouteData(
                    id=r_dict["id"],
                    name=r_dict["name"],
                    start_system_id=r_dict["start_system_id"],
                    end_system_id=r_dict["end_system_id"],
                    control_points=[tuple(cp) for cp in r_dict.get("control_points", [])],
                    system_chain=r_dict.get("system_chain")  # Load system chain if present
                )
                project.routes[route.id] = route
        
        # Load route groups
        for g_dict in project_dict.get("route_groups", []):
            route_group = RouteGroup(
                id=g_dict["id"],
                name=g_dict["name"],
                route_ids=g_dict.get("route_ids", [])
            )
            project.route_groups[route_group.id] = route_group
        
        # Load zones (for future use)
        project.zones = project_dict.get("zones", [])
        
        return project
    except Exception as e:
        print(f"Error loading project: {e}")
        return None


def _export_system(system: SystemData) -> dict:
    """Export a SystemData object for game use.
    
    Args:
        system: The SystemData to export
        
    Returns:
        Dictionary with system data for game export
    """
    export_dict = {
        "id": system.id,
        "name": system.name,
        "x": system.position.x(),
        "y": system.position.y()
    }
    
    # Include stats fields
    if system.population_id:
        export_dict["population_id"] = system.population_id
    if system.imports:
        export_dict["imports"] = system.imports
    if system.exports:
        export_dict["exports"] = system.exports
    if system.facilities:
        export_dict["facilities"] = system.facilities
    
    return export_dict


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
                _export_system(s)
                for s in project.systems.values()
            ],
            "routes": [
                {
                    "id": r.id,
                    "name": r.name,
                    "start_system_id": r.start_system_id,
                    "end_system_id": r.end_system_id,
                    "control_points": r.control_points,
                    "system_chain": r.system_chain
                }
                for r in project.routes.values()
            ],
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
