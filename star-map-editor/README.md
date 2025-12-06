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

## Testing

The application currently uses manual testing procedures. To test the application:

1. **Run the application**: `python main.py`
2. **Follow test procedures**: See [TESTING.md](TESTING.md) for comprehensive test cases
3. **Verify installation**: Run `python verify_installation.py` to check setup

**Note**: Automated tests are planned for future development. Current testing focuses on:
- File operations (New, Open, Save, Export)
- Template management (Load, Move, Scale, Lock, Opacity)
- System placement and editing
- Route creation and editing
- Navigation controls (Zoom, Pan)
- Mode switching and UI interactions

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
- **Pan Sensitivity Slider**: Adjusts how fast the camera pans when using keyboard controls (0.5x-5.0x)
  - Located below the mode buttons, always visible
  - Default: 1.0x (normal speed)
  - Lower values: Slower, more precise camera movement
  - Higher values: Faster camera navigation
  - Applies to WASD and arrow key panning
  - Pan speed still scales appropriately with zoom level

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

- **Scale Sensitivity Slider**: Adjusts how sensitive template scaling is to mouse wheel input (0.1x-3.0x)
  - Default: 1.0x (normal sensitivity)
  - Lower values: Finer, more precise scaling control
  - Higher values: Faster scaling adjustments
  - Only affects Ctrl+wheel scaling in Template Mode

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

### Routes Mode

Routes Mode allows you to create curved hyperlane routes between star systems with adjustable control points, name them, and organize them into groups.

#### Activating Routes Mode

Click the **"Routes"** button in the mode bar. When active, the button turns green and a workspace toolbar appears below the mode buttons.

**Status bar message**: *"Routes mode: Click a start system, then an end system. Select a route to show control points and edit the curve."*

#### Workspace Toolbar

The workspace toolbar provides the following controls (visible only in Routes Mode):

- **Create Route Group**: Create a named group from currently selected routes (see Route Groups below)
- **Info**: Instructions for using CTRL+click to select routes for grouping

#### Creating Routes

1. **Select Start System**: Click on any system to designate it as the route's starting point
   - The system must be clicked directly (or within a small snap radius)
   - Status updates to indicate start system is selected

2. **Select End System**: Click on another system to complete the route
   - Cannot create routes to the same system
   - Duplicate routes between the same systems are prevented
   - Route is automatically created and named (e.g., "System A - System B")
   - **The route is automatically selected**, showing control handles immediately

#### Route Labels

Each route displays its name as a label near the midpoint of the route:

- **Auto-generated names**: By default, routes are named "System A - System B"
- **Label positioning**: Labels automatically update when systems move or routes change
- **Rename routes**: Right-click on any route and select "Rename Route" to change its name
- **Label visibility**: Labels are always visible and saved with your project

#### Editing Routes

- **Select Route**: Click on a route path to select it
  - Selected routes turn yellow
  - Control point handles appear as draggable bright orange circles (larger and more visible than before)
  - Handles are now easier to see and grab for precise curve editing

- **Adjust Curve**: Drag the orange control point handles to bend the route
  - Control points can be positioned anywhere
  - The spline path updates in real-time as you drag
  - Multiple control points create smooth curves through all points
  - Route labels update position automatically

- **Route Follows Systems**: When you move a system (in Systems Mode), all connected routes automatically update to follow the new position
  - Route endpoints remain attached to their systems
  - Control points maintain their positions
  - Labels update to reflect new positions

#### Route Groups

Route Groups allow you to organize multiple route segments under a common name, useful for defining trade lanes, patrol routes, or strategic corridors.

##### Creating Route Groups

1. **Select Routes for Grouping**: In Routes Mode, hold **CTRL** and click on routes to toggle selection
   - Selected routes turn magenta and become slightly thicker
   - You can select as many routes as needed
   - CTRL+click again on a selected route to deselect it

2. **Create Group**: Click the **"Create Route Group"** button in the workspace toolbar
   - A dialog appears asking for the group name
   - Enter a meaningful name (e.g., "Corellian Trade Spine", "Outer Rim Patrol Route")
   - The group is created with all selected routes
   - Selection highlight is cleared after group creation

##### Managing Route Groups

- Route groups are saved with your project
- Group data is stored in the `.swmproj` file and persists across sessions
- View group count in the Stats dialog
- Future updates will add visualization and management features for groups

#### Deleting Routes

- **Delete Key**: Select a route and press the **Delete** key
  - A confirmation dialog appears
  - Route and all its handles are removed

#### Route Visualization

- **Normal routes**: Light blue curved lines with labels
- **Selected routes**: Yellow curved lines with visible control handles
- **Group-selected routes**: Magenta (pink) routes with thicker lines
- **Control handles**: Bright orange circles (8 pixels radius) that light up on hover
- **Routes layer below systems** but above templates

#### Notes

- Routes are saved with your project and restored when you load
- Initial routes are straight lines (no control points)
- Add curvature by selecting a route and dragging its handles
- Routes can pass over/under each other freely
- Route names and groups are fully customizable
- Handle visibility and colors have been improved for better usability

### Zones Mode (Coming Soon)

Placeholder for defining territorial regions and special areas.

### Statistics

View map statistics including:
- Number of templates
- Number of systems
- Number of routes
- Number of route groups
- Number of zones

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
  "routes": [
    {
      "id": "uuid-string",
      "name": "Corellian Run",
      "start_system_id": "system-uuid-1",
      "end_system_id": "system-uuid-2",
      "control_points": [[1500.0, 800.0], [2000.0, 900.0]]
    }
  ],
  "route_groups": [
    {
      "id": "uuid-string",
      "name": "Trade Lane Alpha",
      "route_ids": ["route-uuid-1", "route-uuid-2"]
    }
  ],
  "zones": []
}
```

### Workflow

1. **Start a new project** or open an existing one from the File menu
2. **Enter Template Mode** and load one or more template images
3. **Adjust templates** as needed (position, scale, opacity)
4. **Switch to Systems Mode** and place star systems
5. **Switch to Routes Mode** and create routes between systems
6. **Select routes to edit** and drag control points to adjust curves
7. **Save your project** frequently (Ctrl+S)
8. **Export map data** when ready for use in your game/simulation

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
  "routes": [
    {
      "id": "uuid-string",
      "name": "Corellian Run",
      "start_system_id": "system-uuid-1",
      "end_system_id": "system-uuid-2",
      "control_points": [[1500.0, 800.0], [2000.0, 900.0]]
    }
  ],
  "zones": [],
  "stats": {
    "totalSystems": 1,
    "totalRoutes": 1,
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
- **Ctrl+Click** (Routes Mode): Toggle route selection for grouping
- **Space+Drag**: Pan the view
- **Delete** (Routes Mode): Delete selected route

## Tips

- Use the grid overlay to align systems precisely
- Lock templates after positioning to prevent accidental changes
- Adjust template opacity to see systems more clearly
- Save your project frequently
- Use multiple templates to layer different reference images
- Lower the Scale Sensitivity slider for precise template scaling adjustments
- Increase the Pan Sensitivity slider for faster map navigation when working on large maps
- Adjust sensitivity sliders to match your workflow preference and input device characteristics
- Create systems first, then add routes between them
- Routes automatically update when you move connected systems
- Select a route and drag its control handles to create curved paths
- Right-click routes to rename them with meaningful names
- Use CTRL+click to select multiple routes for grouping
- Create route groups to organize trade lanes, patrol routes, or strategic corridors
- Use the Delete key to remove selected routes
- Newly created routes are automatically selected, showing handles immediately for editing

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

### Routes won't snap to systems
- Make sure you're clicking directly on the system (or very close to it)
- Systems have a snap radius of about 20 pixels
- Check that you're in Routes Mode

### Can't see route control handles
- Make sure the route is selected (click on it)
- Control handles only appear when a route is selected
- Handles are now larger and brighter orange circles (8 pixels) for better visibility
- Newly created routes are automatically selected with visible handles

### Route labels not visible
- Route labels are automatically displayed near the midpoint of each route
- Labels update position when systems move or routes are edited
- Right-click a route and select "Rename Route" to change the label text

### Can't select routes with CTRL+click
- Make sure you're in Routes Mode
- CTRL+click directly on the route path (not on systems or empty space)
- Selected routes turn magenta/pink with thicker lines
- CTRL+click again to deselect

## Coming Soon

- **Zones Mode**: Define territorial regions and special areas
- **Route Group Management**: View, edit, and delete route groups
- **Route Properties**: Edit route colors and visual styles
- **Enhanced Export**: More export format options
- **Undo/Redo**: Full undo/redo support
- **Layers Panel**: Better template management
- **Keyboard Shortcuts**: Customizable shortcuts
