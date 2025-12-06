# GitHub Copilot Instructions for Star Map Editor

## Project Overview

This repository contains **Star Map Editor**, a Python desktop application for creating and editing Star Wars-inspired galactic maps.

- **Technology Stack**: Python 3.10+, PySide6
- **Application Type**: Desktop GUI application
- **Main Entry Point**: `star-map-editor/main.py`
- **Primary GUI Module**: `star-map-editor/gui.py`

## Project Vision

The Star Map Editor is a tool for creating 2D galactic maps with the following capabilities:

- Display a background image representing the galaxy
- Semi-transparent grid overlay for positioning
- Zoom functionality using mouse wheel
- Panning with WASD keys
- Place and manage star systems
- Define trade routes between systems
- Create zones and territories
- Track statistics
- Export/import map data as JSON

## Architecture Guidelines

### Module Organization

Keep the codebase well-organized and maintainable:

- **`star-map-editor/main.py`**: Minimal application startup and window creation only
- **`star-map-editor/gui.py`**: All PySide6 UI logic (windows, widgets, views, dialogs)
- **`star-map-editor/core/project_model.py`**: Core data structures (MapProject, TemplateData)
- **`star-map-editor/core/systems.py`**: System data structures and graphics (SystemData, SystemItem, SystemDialog)
- **`star-map-editor/core/routes.py`**: Route data structures and graphics (RouteData, RouteItem, RouteHandleItem)
- **`star-map-editor/core/templates.py`**: Template graphics management (TemplateItem)
- **`star-map-editor/core/project_io.py`**: Project save/load/export functionality
- **`star-map-editor/core/__init__.py`**: Core module exports

### Separation of Concerns

- Keep GUI code separate from business logic
- Domain logic should not depend on PySide6 (except for Qt types like QPointF)
- UI components should consume domain models, not define them
- Use clear interfaces between layers
- Graphics items (SystemItem, TemplateItem, RouteItem) are in core/ modules as they're tightly coupled with data models

## Coding Guidelines

### Python Best Practices

- **Target Python 3.10+**: Use modern Python features
- **Type Hints**: Use type annotations for function parameters and return values
- **Dataclasses**: Prefer dataclasses for simple data structures
- **Clear Code**: Write explicit, readable code over clever one-liners
- **Function Size**: Keep functions and methods focused and relatively short
- **Naming**: Follow PEP 8 naming conventions
  - `snake_case` for functions, methods, variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

### Documentation

- Add docstrings to classes and public methods
- Include comments for complex logic or design decisions
- Keep comments concise and up-to-date with code changes

### File Organization

- Follow existing naming and folder structure
- Group related functionality in modules
- Use `__init__.py` to expose public interfaces

## PySide6 Guidelines

### Map View Architecture

Use the Graphics View Framework for the map display:

- **`QGraphicsView`**: Viewport for viewing the scene (subclassed as `MapView` in gui.py)
- **`QGraphicsScene`**: Container for all graphical items (subclassed as `GridOverlay` in gui.py)
- **Custom `QGraphicsItem`**: Grid overlay, systems, routes, templates as items

### Zoom and Pan Implementation

Implement in a custom `QGraphicsView` subclass (e.g., `MapView`):

- **Zoom**: Override `wheelEvent` to scale the view
- **Pan**: Implement WASD key handling in `keyPressEvent`
- Consider adding drag-to-pan with middle mouse button

### Grid Overlay

- Implemented as a custom `QGraphicsScene` subclass (`GridOverlay`) that draws in `drawForeground()`
- Grid is drawn on top of all scene items
- Grid is semi-transparent light green (144, 238, 144, 128)
- Grid spacing is 100 scene units
- Grid updates automatically when view transforms change

### Loading Templates

Follow this sequence when loading a template image:

1. Create `TemplateData` object with filepath
2. Create `TemplateItem` from `TemplateData`
3. Add item to scene (`scene.addItem()`)
4. For first template: set scene rect, enable grid, fit view
5. Store item in `template_items` dictionary by ID

### Best Practices

- Use Qt signals and slots for event handling
- Leverage Qt's built-in functionality (layouts, dialogs, etc.)
- Test UI changes by running the application
- Handle edge cases (empty scenes, missing files, etc.)

## JSON Schema

### Map Data Export Format

Use this structure for exporting/importing map data:

```json
{
  "mapName": "Unnamed Map",
  "backgroundImage": "path/to/image.png",
  "systems": [
    {
      "id": "system-001",
      "name": "Coruscant",
      "x": 100.0,
      "y": 150.0,
      "type": "capital",
      "population": 1000000000,
      "notes": "Galactic capital"
    }
  ],
  "routes": [
    {
      "id": "route-001",
      "name": "Corellian Run",
      "fromSystem": "system-001",
      "toSystem": "system-002",
      "distance": 250.0,
      "type": "major"
    }
  ],
  "zones": [
    {
      "id": "zone-001",
      "name": "Core Worlds",
      "systemIds": ["system-001", "system-002"],
      "color": "#3498db"
    }
  ],
  "stats": {
    "totalSystems": 2,
    "totalRoutes": 1,
    "totalZones": 1,
    "version": "1.0"
  }
}
```

### Schema Guidelines

- Keep JSON human-readable (proper indentation)
- Use consistent naming (camelCase for JSON keys)
- Maintain backward compatibility when extending schema
- Include version information for future migrations
- Store relative paths for images, not absolute paths

## Testing and Safety

### Dependencies

- Avoid introducing external dependencies unless clearly justified
- Document why new dependencies are needed
- Prefer standard library and PySide6 built-ins when possible
- Current dependencies: PySide6>=6.6 (see requirements.txt)

### File Handling

- Do NOT hardcode absolute file system paths
- Use relative paths or user-configurable paths
- Handle file I/O errors gracefully
- Validate file formats before loading

### Error Handling

- Catch and handle exceptions appropriately
- Show user-friendly error messages in the GUI
- Log errors for debugging purposes
- Don't let the application crash from user input

### Code Safety

- Validate user input
- Check for None values
- Handle empty states (no systems, no routes, etc.)
- Test boundary conditions

## Work Style and Pull Requests

### Incremental Changes

- **Focus on one feature per PR**: Don't combine unrelated changes
- **Small, focused commits**: Each PR should have a clear scope
- **Avoid large rewrites**: Prefer incremental improvements
- **Maintain existing behavior**: Don't break working features

### PR Descriptions

Include in each PR:

- **What changed**: Brief description of modifications
- **Why**: Reason for the change (fixes bug, adds feature, refactors code)
- **Testing**: How you verified the change works
- **Screenshots**: For UI changes, include before/after screenshots

### Example PR Scopes

Good PR scopes:

- ✅ "Refactor GUI code into gui.py"
- ✅ "Add system placement interaction"
- ✅ "Implement JSON export functionality"
- ✅ "Add zoom with mouse wheel"

Too broad:

- ❌ "Complete map editor rewrite"
- ❌ "Add all features at once"

### Handling Ambiguity

When requirements are unclear:

1. Maintain existing behavior
2. Don't delete or break working features
3. Add comments explaining design decisions
4. Ask for clarification if needed

## Development Workflow

### Before Making Changes

1. Understand the existing codebase
2. Identify what needs to change
3. Plan minimal modifications
4. Consider backward compatibility

### Making Changes

1. Create/modify files as needed
2. Follow coding guidelines
3. Add appropriate comments/docstrings
4. Test changes by running the application

### After Changes

1. Run the application to verify behavior
2. Check for errors or warnings
3. Review code for quality and consistency
4. Ensure no unintended side effects

## Common Patterns

### Adding a New System to the Map

```python
# In core/systems.py
from dataclasses import dataclass
from PySide6.QtCore import QPointF

@dataclass
class SystemData:
    id: str
    name: str
    position: QPointF
    
    @classmethod
    def create_new(cls, name: str, position: QPointF):
        """Create a new system with a generated UUID."""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            position=position
        )

class SystemItem(QGraphicsEllipseItem):
    """Graphics representation of a star system."""
    def __init__(self, system_data: SystemData, parent=None):
        super().__init__(parent)
        self.system_data = system_data
        self.setPos(system_data.position)
        # ... configure appearance and interaction
```

### Handling File Operations

```python
# In core/project_io.py
import json
from pathlib import Path
from typing import Optional

def save_project(project: MapProject, file_path: Path) -> bool:
    """Save a map project to a .swmproj file."""
    try:
        project_dict = {
            "metadata": project.metadata,
            "templates": [...],
            "systems": [...],
            "routes": [...]
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(project_dict, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving project: {e}")
        return False

def load_project(file_path: Path) -> Optional[MapProject]:
    """Load a map project from a .swmproj file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            project_dict = json.load(f)
        # Reconstruct project from dict
        return project
    except Exception as e:
        print(f"Error loading project: {e}")
        return None
```

## Future Features

Keep in mind these planned features when designing:

- Multiple map layers (background, routes, systems, zones)
- Company/faction management
- Economy simulation
- Convoy/fleet simulation
- Route optimization
- Statistical analysis
- Custom map themes/styles

Design with extensibility in mind, but don't over-engineer for features that don't exist yet.

## Running the Application

To run the Star Map Editor:

```bash
cd star-map-editor
python main.py
```

To verify installation:

```bash
cd star-map-editor
python verify_installation.py
```

## Testing

Currently there are no automated tests. Testing is done manually:

1. Run the application (`python main.py`)
2. Follow test procedures in `star-map-editor/TESTING.md`
3. Verify each feature works as documented

Future improvement: Add automated tests for core data models and I/O operations.

## Summary

When working on this project:

- ✅ Make small, focused changes
- ✅ Keep architecture clean (separate GUI from logic)
- ✅ Use PySide6 Graphics View Framework properly
- ✅ Follow Python best practices
- ✅ Maintain stable JSON schema
- ✅ Test changes by running the application
- ✅ Write clear PR descriptions
- ❌ Don't make large rewrites
- ❌ Don't add unnecessary dependencies
- ❌ Don't hardcode absolute paths
- ❌ Don't break existing features
