# Star Map Editor

A PySide6-based desktop application for creating and editing Star Wars-inspired galactic maps.

## Requirements

- Python 3.10+
- PySide6 6.6+

## Installation

It's recommended to use a virtual environment:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

Run the application from the star-map-editor directory:

```bash
python main.py
```

## Project Structure

```
star-map-editor/
│
├─ main.py              # Application entry point
├─ gui.py               # PySide6 GUI implementation
│
├─ core/                # Non-GUI business logic
│   ├─ project_model.py # MapProject and TemplateData data structures
│   ├─ project_io.py    # Save/load/export functionality
│   ├─ systems.py       # System data and graphics
│   ├─ templates.py     # Template graphics management
│   └─ __init__.py
│
├─ Saves/               # Default location for .swmproj project files
├─ Exports/             # Default location for exported map data
│
└─ resources/           # Application resources
    ├─ icons/           # Toolbar and UI icons
    └─ example_templates/  # Sample template images
```

## Features

### File Menu

The application includes a full File menu for project management:

- **New Project** (Ctrl+N): Create a new blank project
- **Open Project** (Ctrl+O): Load a `.swmproj` project file from the `Saves/` directory
- **Save Project** (Ctrl+S): Save the current project
- **Save Project As** (Ctrl+Shift+S): Save with a new filename
- **Export Map Data** (Ctrl+E): Export game-readable JSON data to `Exports/`
- **Quit** (Ctrl+Q): Exit the application (prompts to save unsaved changes)

### Navigation & View

- **Mouse Wheel Zoom**: Smooth zoom (0.1x-10x) anchored under cursor position with limits
- **Keyboard Panning**: 
  - WASD/Arrow keys for continuous panning at 30 FPS
  - Pan speed scales with zoom level for consistent control
- **Mouse Drag Panning**: Middle mouse or Space+left mouse for intuitive map navigation
- **Semi-transparent Grid Overlay**: Light green 100px grid overlay for precise alignment

### Template Mode

Template Mode allows you to load and manage multiple background images (sketches, reference maps, etc.) with full control over positioning, scaling, and appearance.

#### Activating Template Mode

Click the **"Template Mode"** button in the mode bar. When active, the button turns green and a workspace toolbar appears below the mode buttons.

**Status bar message**: *"Template mode active: Click to select template, drag to move, Ctrl+wheel to scale."*

#### Workspace Toolbar

The workspace toolbar provides the following controls (visible only in Template Mode):

- **Load Template**: Opens a file dialog to load a new template image (PNG, JPG, BMP)
  - Multiple templates can be loaded
  - Each template is independent with its own transformations
  
- **Delete Template**: Removes the currently selected template

- **Reset Transform**: Resets the selected template's position and scale to defaults

- **Lock/Unlock Template**: Toggle to prevent/allow moving or scaling the template

- **Opacity Slider**: Adjusts the selected template's opacity (0-100%)

#### Template Interaction

- **Select**: Click on a template to select it (workspace controls operate on the selected template)
- **Move**: Click and drag a template to reposition it
- **Scale**: Hold **Ctrl** and use the **mouse wheel** while hovering over a template to scale it
  - Scaling is centered under the cursor
  - Scale range: 10% to 1000%
- **Lock**: Locked templates cannot be moved or scaled

#### Multiple Templates

You can load multiple template images, each with:
- Independent position
- Independent scale
- Independent opacity
- Independent lock state
- Layer order (z-order)

All template data is saved in the project file and restored when you load the project.

### System Placement Mode

System Mode allows you to place and manage star systems on your map.

#### Activating Systems Mode

Click the **"Systems Mode"** button in the mode bar. When active, the button turns green.

**Status bar message**: *"Mode: System placement – left-click to place a system, right-click to edit"*

#### System Operations

- **Place System**: Left-click on empty space to place a new star system
  - Opens a dialog to enter the system name
  - Systems appear as blue circles with white labels
  - Each system gets a unique UUID identifier

- **Edit System**: Right-click on an existing system to edit or delete it
  - Modify the system name
  - Delete the system

- **Move System**: Click and drag a system to reposition it
  - Works smoothly at all zoom levels
  - Position updates automatically in the project data

- **Visual Feedback**:
  - Normal systems: Blue circles
  - Selected systems: Orange/yellow circles
  - System names displayed as labels

### Routes Mode (Coming Soon)

Placeholder for creating hyperlane routes between systems.

### Zones Mode (Coming Soon)

Placeholder for defining territorial regions and special areas.

### Statistics

View map statistics including:
- Number of templates
- Number of systems
- Number of routes (future)
- Number of zones (future)

## Project File Format

Projects are saved as `.swmproj` files in JSON format, containing:

```json
{
  "metadata": {
    "name": "My Galactic Map",
    "version": "1.0"
  },
  "templates": [
    {
      "id": "uuid-string",
      "filepath": "path/to/template.png",
      "position": [0.0, 0.0],
      "scale": 1.0,
      "opacity": 1.0,
      "locked": false,
      "z_order": 0
    }
  ],
  "systems": [
    {
      "id": "uuid-string",
      "name": "Coruscant",
      "x": 1000.0,
      "y": 750.0
    }
  ],
  "routes": [],
  "zones": []
}
```

### Workflow

1. **Start a new project** or open an existing one from the File menu
2. **Enter Template Mode** and load one or more template images
3. **Adjust templates** as needed (position, scale, opacity)
4. **Switch to Systems Mode** and place star systems
5. **Save your project** frequently (Ctrl+S)
6. **Export map data** when ready for use in your game/simulation

### Export Format

Exported map data (for game use) is saved as clean JSON:

```json
{
  "mapName": "My Galactic Map",
  "systems": [
    {
      "id": "uuid-string",
      "name": "Coruscant",
      "x": 1000.0,
      "y": 750.0
    }
  ],
  "routes": [],
  "zones": [],
  "stats": {
    "totalSystems": 1,
    "totalRoutes": 0,
    "totalZones": 0,
    "version": "1.0"
  }
}
```

Note: Export data excludes editor-specific information (templates, etc.) for clean game integration.

## High-level Design

This editor is part of a larger space trading and combat simulation framework:

### 1. Map Layers

The system supports multiple map types at different scales:
- **Galactic maps**: Systems connected by hyperlanes
- **Inner system maps**: Planets, stations, asteroid belts within a star system
- **Tactical battle maps**: Future support for combat encounters

### 2. Economy System

A detailed economic model with:
- **Planets**: Characterized by type, population, climate, and industry level
- **Companies**: Own industrial facilities with defined requirements and outputs
- **Industrial Facilities**: Process resources with specific "requires", "produces", and "capacity" parameters

### 3. Trade & Supply Simulation

Dynamic trade simulation featuring:
- Resource need determination based on production requirements
- Supplier identification and matching
- Communication delay simulation for realistic information propagation
- Convoy generation for resource transport
- Event-driven convoy travel (pirate attacks, imperial inspections, etc.)
- Resource delivery affecting production chains

### 4. Factions & Ship Movements

Multiple faction types with distinct behaviors:
- **Civilian convoys**: Trade routes and commercial shipping
- **Pirate activity**: Raids and interdictions
- **Imperial patrols**: Law enforcement and security
- **Blockades**: Strategic control points

### 5. Encounter Generator

Dynamic battle setup based on context:
- Location-based ship proximity calculations
- Faction presence probability modeling
- Fleet composition generation (pirates, empire, neutral traders)
- Cargo manifest generation for encountered ships

### 6. Data Flow

Clear separation between design-time and run-time data:
- **Editor generates**: Systems, routes, zones, companies, industries, resource definitions
- **Simulation generates**: Convoys, events, fleet movements, market dynamics

### 7. Future Extensions

Planned features for expanded gameplay:
- **Diplomacy**: Faction relations and treaties
- **Black markets and smuggling**: Illicit trade networks
- **Espionage and fog of war**: Information warfare mechanics
- **Event cards**: Random narrative events affecting the game state
- **AI-driven factions**: Autonomous faction behavior and decision-making

## Development Notes

### Architecture

- **Separation of Concerns**: GUI code (`gui.py`) is separate from business logic (`core/`)
- **Data Models**: All data structures are in `core/project_model.py`
- **Graphics Items**: `TemplateItem` and `SystemItem` handle visual representation
- **I/O Operations**: `core/project_io.py` handles all file operations

### Code Organization

- **`main.py`**: Minimal application startup
- **`gui.py`**: All PySide6 UI components
- **`core/`**: Non-GUI logic
  - `project_model.py`: Data structures
  - `systems.py`: System data and graphics
  - `templates.py`: Template graphics
  - `project_io.py`: File I/O

### Design Principles

- **Type hints** for better code clarity
- **Dataclasses** for simple data structures
- **Clear naming** following PEP 8
- **Modular design** for easy extension
- **PyQt Graphics View Framework** for scalable scene management

## Keyboard Shortcuts

- **Ctrl+N**: New Project
- **Ctrl+O**: Open Project
- **Ctrl+S**: Save Project
- **Ctrl+Shift+S**: Save Project As
- **Ctrl+E**: Export Map Data
- **Ctrl+Q**: Quit
- **WASD / Arrow Keys**: Pan the view
- **Mouse Wheel**: Zoom in/out
- **Ctrl+Mouse Wheel** (Template Mode): Scale selected template
- **Space+Drag**: Pan the view

## Tips

- Use the grid overlay to align systems precisely
- Lock templates after positioning to prevent accidental changes
- Adjust template opacity to see systems more clearly
- Save your project frequently
- Use multiple templates to layer different reference images

## Troubleshooting

### Templates won't load
- Ensure the image file exists and is a supported format (PNG, JPG, BMP)
- Check file permissions

### Systems aren't selectable
- Make sure you're in Systems Mode (green button)
- Check that you're not in Template Mode

### Can't move a template
- Check if the template is locked (unlock it in the workspace toolbar)
- Make sure you're in Template Mode

## Coming Soon

- **Routes Mode**: Create hyperlane connections between systems
- **Zones Mode**: Define territorial regions and special areas
- **Enhanced Export**: More export format options
- **Undo/Redo**: Full undo/redo support
- **Layers Panel**: Better template management
- **Keyboard Shortcuts**: Customizable shortcuts
