# GitHub Copilot Instructions for Star Map Editor

## Project Overview

This repository contains **Star Map Editor**, a Python desktop application for creating and editing Star Wars-inspired galactic maps.

- **Technology Stack**: Python 3.10+, PyQt5
- **Application Type**: Desktop GUI application
- **Main Entry Point**: `src/main.py`
- **Primary GUI Module**: `src/gui.py`

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

- **`src/main.py`**: Minimal application startup and window creation only
- **`src/gui.py`**: All PyQt5 UI logic (windows, widgets, views, dialogs)
- **`src/models.py`**: Data structures (systems, routes, zones, companies, etc.)
- **`src/io.py`**: JSON import/export functionality
- **`src/simulation/`**: Future economy and convoy simulation logic

### Separation of Concerns

- Keep GUI code separate from business logic
- Domain logic should not depend on PyQt5
- UI components should consume domain models, not define them
- Use clear interfaces between layers

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

## PyQt5 Guidelines

### Map View Architecture

Use the Graphics View Framework for the map display:

- **`QGraphicsView`**: Viewport for viewing the scene (subclass as `MapView`)
- **`QGraphicsScene`**: Container for all graphical items
- **Custom `QGraphicsItem`**: Implement grid overlay, systems, routes as items

### Zoom and Pan Implementation

Implement in a custom `QGraphicsView` subclass (e.g., `MapView`):

- **Zoom**: Override `wheelEvent` to scale the view
- **Pan**: Implement WASD key handling in `keyPressEvent`
- Consider adding drag-to-pan with middle mouse button

### Grid Overlay

- Implement as a custom `QGraphicsItem` overlay
- Do NOT draw grid directly in the scene
- Make grid semi-transparent
- Update grid when view transforms change

### Loading Images

Follow this sequence when loading a background image:

1. Clear the scene (`scene.clear()`)
2. Add the pixmap to the scene (`scene.addPixmap()`)
3. Add the grid overlay item
4. Set scene rectangle to image bounds (`setSceneRect()`)
5. Reset view transform
6. Fit view to scene (`fitInView()`)

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
- Prefer standard library and PyQt5 built-ins when possible

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
# In models.py
@dataclass
class System:
    id: str
    name: str
    x: float
    y: float
    type: str = "standard"
    population: int = 0
    notes: str = ""

# In gui.py (MapView)
class SystemItem(QGraphicsItem):
    def __init__(self, system: System):
        super().__init__()
        self.system = system
        self.setPos(system.x, system.y)
    
    def paint(self, painter, option, widget):
        # Draw system representation
        pass
```

### Handling File Operations

```python
# In io.py
import json
from pathlib import Path
from typing import Dict, Any

def export_map(data: Dict[str, Any], file_path: Path) -> bool:
    """Export map data to JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error exporting map: {e}")
        return False

def import_map(file_path: Path) -> Dict[str, Any] | None:
    """Import map data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error importing map: {e}")
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

## Summary

When working on this project:

- ✅ Make small, focused changes
- ✅ Keep architecture clean (separate GUI from logic)
- ✅ Use PyQt5 Graphics View Framework properly
- ✅ Follow Python best practices
- ✅ Maintain stable JSON schema
- ✅ Test changes by running the application
- ✅ Write clear PR descriptions
- ❌ Don't make large rewrites
- ❌ Don't add unnecessary dependencies
- ❌ Don't hardcode absolute paths
- ❌ Don't break existing features
