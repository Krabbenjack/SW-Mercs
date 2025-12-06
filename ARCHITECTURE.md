# Star Map Editor - Architecture Overview

## High-Level Architecture

The Star Map Editor is a desktop application built with Python and PySide6 (Qt for Python). It follows a clean separation between UI logic, business logic, and data persistence.

### Core Architecture Pattern

The application uses a **Model-View-Graphics Item** pattern built on Qt's Graphics View Framework:

1. **Data Models** (`core/` modules): Define the structure and behavior of map entities (systems, routes, templates, projects)
2. **Graphics Items** (`core/` modules): Provide visual representation of data models in the Qt scene
3. **View/Scene** (`gui.py`): Manage the viewport, user interaction, and coordinate between models and items
4. **Main Window** (`gui.py`): Orchestrate modes, file operations, and application state

### Key Design Decisions

- **Graphics items live in core/**: While traditionally UI code, `SystemItem`, `RouteItem`, and `TemplateItem` are tightly coupled with their respective data models and are therefore colocated in `core/` modules for maintainability
- **Separation of editor state from map data**: The `MapProject` contains only map data (systems, routes, templates), while editor-specific state (selected items, modes, UI settings) lives in the main window
- **PySide6 Qt types in data models**: `QPointF` is used in data models because it provides the precise 2D coordinate behavior needed for graphics

## Module Responsibilities

### `star-map-editor/main.py`
**Role**: Application entry point

- Creates QApplication instance
- Instantiates and shows the main window
- Enters Qt event loop

**Lines of code**: ~18 lines

### `star-map-editor/gui.py`
**Role**: All UI implementation - main window, view, scene, mode management

Key classes:
- **`StarMapEditor(QMainWindow)`**: Main application window
  - File menu and project management (New, Open, Save, Export)
  - Mode buttons and mode switching (Template, Systems, Routes, Zones, Stats)
  - Workspace toolbar for template mode
  - Orchestrates interaction between view and data models
  - Manages project state and unsaved changes tracking

- **`MapView(QGraphicsView)`**: Custom graphics view for map navigation
  - Mouse wheel zoom (0.1x-10x) centered on cursor
  - Keyboard panning (WASD/Arrow keys) with continuous movement
  - Mouse drag panning (middle button or Space+left click)
  - Mode-specific interaction handling (system placement, route creation, template scaling)
  - Emits signals for user actions (system clicks, route clicks, item modifications)

- **`GridOverlay(QGraphicsScene)`**: Custom scene with semi-transparent grid
  - Draws grid in `drawForeground()` on top of all items
  - 100-pixel grid spacing
  - Light green semi-transparent color (144, 238, 144, 128)
  - Toggleable visibility

**Lines of code**: ~1,324 lines

### `star-map-editor/core/project_model.py`
**Role**: Core data structures for the entire map project

Key classes:
- **`MapProject`**: Master container for all map data
  - `templates: List[TemplateData]` - Background image layers
  - `systems: Dict[str, SystemData]` - Star systems by ID
  - `routes: Dict[str, RouteData]` - Hyperlane routes by ID
  - `zones: List` - Territory zones (future feature)
  - `metadata: Dict` - Project name, version, etc.
  
- **`TemplateData`**: Data model for a background template image
  - Stores filepath, position, scale, opacity, locked state, z-order
  - Supports multiple layered templates

**Lines of code**: ~157 lines

### `star-map-editor/core/systems.py`
**Role**: Star system data and graphics

Key classes:
- **`SystemData`**: Data model for a star system
  - Properties: id (UUID), name, position (QPointF)
  - Factory method: `create_new()` generates UUID

- **`SystemItem(QGraphicsEllipseItem)`**: Graphics representation
  - Blue circle (orange when selected)
  - White border
  - Text label with system name
  - Movable and selectable
  - Updates data model when moved

- **`SystemDialog(QDialog)`**: Modal dialog for creating/editing systems
  - Name input field
  - Save/Delete/Cancel buttons
  - Returns action result

**Lines of code**: ~221 lines

### `star-map-editor/core/routes.py`
**Role**: Hyperlane route data and graphics

Key classes:
- **`RouteData`**: Data model for a route between two systems
  - Properties: id, name, start_system_id, end_system_id, control_points
  - Control points allow curved paths (Bezier splines)

- **`RouteItem(QGraphicsPathItem)`**: Graphics representation
  - Light blue curved line (yellow when selected)
  - Spline path through control points
  - Shows/hides control handles when selected
  - Updates path when systems move

- **`RouteHandleItem(QGraphicsEllipseItem)`**: Draggable control point handle
  - Orange circle that can be dragged
  - Notifies parent route when moved
  - Used to adjust route curves

**Lines of code**: ~302 lines

### `star-map-editor/core/templates.py`
**Role**: Template image graphics

Key classes:
- **`TemplateItem(QGraphicsPixmapItem)`**: Graphics representation of a template
  - Displays image at specified position and scale
  - Supports opacity adjustment
  - Lock state prevents movement/scaling
  - Transform origin at center for proper scaling

**Lines of code**: ~139 lines

### `star-map-editor/core/project_io.py`
**Role**: File I/O operations

Key functions:
- **`save_project(project, file_path)`**: Save project as .swmproj JSON file
  - Serializes MapProject to JSON
  - Stores all templates, systems, routes with their properties

- **`load_project(file_path)`**: Load project from .swmproj file
  - Deserializes JSON to MapProject
  - Reconstructs all data models and relationships
  - Validates that route endpoints exist

- **`export_map_data(project, file_path)`**: Export game-ready JSON
  - Exports only game data (systems, routes, zones)
  - Excludes editor-specific data (templates, UI state)
  - Includes statistics

**Lines of code**: ~193 lines

### `star-map-editor/core/__init__.py`
**Role**: Core module public interface

Exports:
- `MapProject`, `TemplateData` from project_model
- `SystemData`, `SystemItem`, `SystemDialog` from systems
- `TemplateItem` from templates
- `RouteData`, `RouteItem`, `RouteHandleItem` from routes

**Lines of code**: ~26 lines

## Data Flow

### Application Startup
1. `main.py` creates `QApplication`
2. `StarMapEditor` window is instantiated
3. `GridOverlay` scene and `MapView` are created
4. Mode buttons and UI controls are initialized
5. Window is shown and event loop starts

### Loading a Template
1. User clicks "Load Template" in Template Mode
2. File dialog prompts for image selection
3. `TemplateData.create_new()` creates data model with UUID
4. `MapProject.add_template()` stores the data
5. `TemplateItem` is created from data and added to scene
6. Scene rect is set, grid is enabled, view fits to template

### Placing a System
1. User clicks in Systems Mode
2. `MapView` emits `system_click` signal with position
3. `StarMapEditor.create_system_at()` creates temporary `SystemData`
4. `SystemItem` preview is added to scene
5. `SystemDialog` is shown for name input
6. On save: data is stored in `MapProject.systems`, preview becomes permanent
7. On cancel: preview is removed

### Creating a Route
1. User clicks first system in Routes Mode
2. Start system ID is stored
3. User clicks second system
4. `RouteData.create_new()` creates route between systems
5. `MapProject.add_route()` stores the data
6. `RouteItem` is created and added to scene
7. Route computes spline path between system positions

### Saving a Project
1. User clicks File → Save (or Ctrl+S)
2. File dialog prompts for .swmproj file location
3. `save_project()` serializes `MapProject` to JSON
4. All templates, systems, routes are written to file
5. Unsaved changes flag is cleared

## User Interaction Modes

The application has several operational modes:

### None (Default Mode)
- View navigation only (zoom, pan)
- No editing interactions
- Items can be viewed but not modified

### Template Mode
- Select and move template images
- Ctrl+Wheel to scale selected template
- Workspace toolbar visible with:
  - Load/Delete template buttons
  - Reset Transform button
  - Lock/Unlock toggle
  - Opacity slider
  - Scale sensitivity slider

### Systems Mode
- Left-click empty space: Place new system
- Right-click system: Edit existing system
- Drag system: Move system (updates routes automatically)
- Delete key: Not used (delete via right-click dialog)

### Routes Mode
- Click first system to select start
- Click second system to complete route
- Click empty space to cancel
- Click route to select (shows control handles)
- Drag control handles to adjust curve
- Delete key: Delete selected route

### Zones Mode (Placeholder)
- Not yet implemented
- Button shows "coming soon" message

## Rendering Pipeline

### Scene Graph Hierarchy
```
QGraphicsScene (GridOverlay)
├─ Grid (drawn in drawForeground)
├─ TemplateItem (z=0) - Background images
│  └─ Each pixmap at specified position/scale
├─ RouteItem (z=5) - Routes between systems
│  ├─ QPainterPath - The curved line
│  └─ RouteHandleItem (z=100) - Control point handles
└─ SystemItem (z=default) - Star systems
   ├─ QGraphicsEllipseItem - The circle
   └─ QGraphicsTextItem - The name label
```

### View Transformations
- **Zoom**: Scaling transform on the view (0.1x to 10x)
- **Pan**: Scrollbar adjustments (WASD keys) or view translation (mouse drag)
- **Grid**: Drawn in scene coordinates, automatically scales with view

### Paint Order
1. Scene background (none)
2. Templates (lowest z-value)
3. Routes (z=5)
4. Systems (default z)
5. Control handles (z=100)
6. Grid overlay (drawn in foreground)

## Navigation & Input

### Mouse Input
- **Wheel**: Zoom view (or scale template with Ctrl in Template Mode)
- **Left Click**: Mode-specific action (place system, select item, etc.)
- **Right Click**: Edit action (edit system in Systems Mode)
- **Middle Button Drag**: Pan view
- **Space + Left Drag**: Pan view

### Keyboard Input
- **W/↑**: Pan up
- **S/↓**: Pan down
- **A/←**: Pan left
- **D/→**: Pan right
- **Delete**: Delete selected route (in Routes Mode)
- **Ctrl+N**: New Project
- **Ctrl+O**: Open Project
- **Ctrl+S**: Save Project
- **Ctrl+Shift+S**: Save Project As
- **Ctrl+E**: Export Map Data
- **Ctrl+Q**: Quit

### Continuous Panning
- QTimer runs at 33ms intervals (~30 FPS) when keys are pressed
- Pan speed scales inversely with zoom level
- Pan sensitivity slider provides 0.5x-5.0x multiplier

## File Formats

### Project File (.swmproj)
JSON format with complete editor state:
```json
{
  "metadata": {
    "name": "My Galaxy Map",
    "version": "1.0"
  },
  "templates": [
    {
      "id": "uuid",
      "filepath": "path/to/image.png",
      "position": [x, y],
      "scale": 1.0,
      "opacity": 0.5,
      "locked": false,
      "z_order": 0
    }
  ],
  "systems": [
    {
      "id": "uuid",
      "name": "Coruscant",
      "x": 100.0,
      "y": 150.0
    }
  ],
  "routes": [
    {
      "id": "uuid",
      "name": "Corellian Run",
      "start_system_id": "uuid1",
      "end_system_id": "uuid2",
      "control_points": [[x1, y1], [x2, y2]]
    }
  ],
  "zones": []
}
```

### Export File (.json)
Game-ready format without editor data:
```json
{
  "mapName": "My Galaxy Map",
  "systems": [...],
  "routes": [...],
  "zones": [...],
  "stats": {
    "totalSystems": 42,
    "totalRoutes": 89,
    "totalZones": 5,
    "version": "1.0"
  }
}
```

## Extension Points

The architecture is designed for future expansion:

### Planned Features
- **Zones/Territories**: Visual regions grouping systems (data model exists, UI pending)
- **Statistics Dashboard**: Detailed analytics on map structure
- **Route Optimization**: Path-finding and distance calculations
- **System Properties**: Population, economy type, faction ownership
- **Company/Faction Management**: Trade companies and political entities
- **Economy Simulation**: Trade flow and economic modeling
- **Convoy/Fleet Simulation**: Ship movement along routes

### Adding New Features
1. **Data Model**: Add classes to appropriate `core/` module
2. **Graphics Item**: Create visualization (if needed) in same module
3. **UI Integration**: Add mode/controls to `gui.py`
4. **File I/O**: Update `project_io.py` serialization
5. **Dialog/Forms**: Create user input dialogs in `gui.py` or separate module

## Code Statistics

**Total Lines (excluding comments/blanks)**: ~2,335 lines

**Distribution**:
- `gui.py`: ~1,324 lines (56.7%)
- `core/` modules: ~1,011 lines (43.3%)
  - `routes.py`: ~302 lines
  - `systems.py`: ~221 lines
  - `project_io.py`: ~193 lines
  - `project_model.py`: ~157 lines
  - `templates.py`: ~139 lines

**Characteristics**:
- Well-documented with docstrings
- Type hints used throughout
- Clean separation of concerns
- Minimal external dependencies (only PySide6)

## Testing Strategy

**Current State**: Manual testing only

Manual test procedures are documented in `star-map-editor/TESTING.md` covering:
- File operations (New, Open, Save, Export)
- Template management
- System placement and editing
- Route creation and editing
- Navigation controls
- Mode switching
- Edge cases and error handling

**Future Improvements**:
- Unit tests for data models (`MapProject`, `SystemData`, `RouteData`, `TemplateData`)
- Unit tests for I/O operations (`project_io.py`)
- Integration tests for user workflows
- GUI automation tests (PyQt Test Framework)

## Development Commands

### Running the Application
```bash
cd star-map-editor
python main.py
```

### Verifying Installation
```bash
cd star-map-editor
python verify_installation.py
```

### Installing Dependencies
```bash
cd star-map-editor
pip install -r requirements.txt
```

## Summary

The Star Map Editor is a well-architected desktop application with:
- ✅ Clean separation between data, graphics, and UI logic
- ✅ Extensible design ready for new features
- ✅ Comprehensive file I/O with both editor and game formats
- ✅ Rich user interaction with multiple editing modes
- ✅ Professional Qt-based UI with smooth navigation
- ✅ Minimal dependencies and clear code structure

The codebase is ready for future feature development while maintaining stability and usability.
