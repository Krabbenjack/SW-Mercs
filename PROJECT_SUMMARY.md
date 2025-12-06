# Star Map Editor - Project Summary

## Architecture Overview

The Star Map Editor is a desktop application built with Python 3.10+ and PySide6 (Qt for Python). It enables users to create 2D galactic maps by loading background template images, placing star systems, creating hyperlane routes between them, and exporting the data for use in games or simulations.

The application follows a clean **Model-View-Graphics Item** architecture built on Qt's Graphics View Framework. Data models define the structure of map entities (systems, routes, templates, projects). Graphics items provide visual representations that are added to a Qt scene. The view manages navigation (zoom/pan) and coordinates user interaction with the models.

A key design decision is the separation of map data (stored in `MapProject`) from editor state (stored in the main window). This allows clean serialization of projects while keeping UI concerns separate. The application supports both full project files (.swmproj) for editing and lightweight export files (.json) for game consumption.

## Key Files and Modules

### Application Entry & Main Window

**`star-map-editor/main.py`** (18 lines)
- Application entry point
- Creates QApplication and main window
- Starts Qt event loop

**`star-map-editor/gui.py`** (1,324 lines)
- **StarMapEditor(QMainWindow)**: Main application window with file menu, mode buttons, workspace toolbar, and state management
- **MapView(QGraphicsView)**: Custom view with zoom (0.1x-10x), pan (WASD/mouse), and mode-specific interactions
- **GridOverlay(QGraphicsScene)**: Custom scene that draws semi-transparent grid overlay in foreground
- Handles all user interaction, mode switching, and orchestration between data and graphics

### Data Models & Core Logic

**`star-map-editor/core/project_model.py`** (157 lines)
- **MapProject**: Master container holding all map data (templates, systems, routes, zones, metadata)
- **TemplateData**: Data model for background template images with position, scale, opacity, lock state

**`star-map-editor/core/systems.py`** (221 lines)
- **SystemData**: Data model for star systems (id, name, position)
- **SystemItem(QGraphicsEllipseItem)**: Visual representation as blue circle with name label
- **SystemDialog(QDialog)**: Modal dialog for creating/editing systems

**`star-map-editor/core/routes.py`** (302 lines)
- **RouteData**: Data model for routes with control points for curved paths
- **RouteItem(QGraphicsPathItem)**: Visual representation as curved spline between systems
- **RouteHandleItem(QGraphicsEllipseItem)**: Draggable control point handles for adjusting curves

**`star-map-editor/core/templates.py`** (139 lines)
- **TemplateItem(QGraphicsPixmapItem)**: Visual representation of template images with transform support

**`star-map-editor/core/project_io.py`** (193 lines)
- **save_project()**: Serialize MapProject to .swmproj JSON file
- **load_project()**: Deserialize .swmproj file to MapProject
- **export_map_data()**: Export game-ready JSON (systems/routes only, no templates)

**`star-map-editor/core/__init__.py`** (26 lines)
- Public API exports for core module

### Resources & Documentation

**`star-map-editor/resources/`**
- `example_templates/`: Sample galaxy background images
- `icons/`: UI toolbar icons (planned)

**Documentation Files:**
- `ARCHITECTURE.md`: Complete technical architecture documentation (this file)
- `star-map-editor/README.md`: Full feature documentation and usage guide
- `star-map-editor/QUICKSTART.md`: 5-minute getting started guide
- `star-map-editor/TESTING.md`: Comprehensive manual test procedures
- `star-map-editor/IMPLEMENTATION.md`: Development implementation notes
- `.github/copilot-instructions.md`: Coding guidelines and patterns for contributors

### Configuration & Verification

**`star-map-editor/requirements.txt`**
- PySide6>=6.6 (only dependency)

**`star-map-editor/verify_installation.py`** (4,554 bytes)
- Verifies directory structure
- Checks Python file syntax
- Tests module imports
- Reports installation status

## Running the Application

### Install Dependencies

```bash
cd star-map-editor
pip install -r requirements.txt
```

Recommended: Use a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Application

```bash
cd star-map-editor
python main.py
```

### Verify Installation

```bash
cd star-map-editor
python verify_installation.py
```

Expected output:
- ✅ Directory structure checks (Saves/, Exports/ may be missing initially - created on first save)
- ✅ Required Python files
- ✅ Python syntax validation
- ⚠️ GUI import may fail in headless environments (this is normal)

## Running Tests

Currently, the application uses **manual testing only**. There are no automated tests.

### Manual Testing Procedure

1. **Run the application**:
   ```bash
   cd star-map-editor
   python main.py
   ```

2. **Follow test procedures** documented in `star-map-editor/TESTING.md`:
   - File menu operations (New, Open, Save, Export)
   - Template mode features (Load, Move, Scale, Lock, Opacity)
   - Systems mode (Place, Edit, Move, Delete)
   - Routes mode (Create, Edit curves, Select, Delete)
   - Navigation (Zoom, Pan with mouse/keyboard)
   - Mode switching and UI interactions

3. **Test checklist** (high-level):
   - ✅ Create a new project
   - ✅ Load a template image
   - ✅ Place multiple star systems
   - ✅ Create routes between systems
   - ✅ Save the project as .swmproj
   - ✅ Close and reopen the project
   - ✅ Export map data as .json
   - ✅ Verify all data persists correctly

### Future Testing Plans

Planned improvements:
- **Unit tests** for data models (SystemData, RouteData, TemplateData, MapProject)
- **Unit tests** for I/O operations (save_project, load_project, export_map_data)
- **Integration tests** for complete user workflows
- **GUI automation tests** using PyQt Test Framework

Test infrastructure would be organized as:
```
star-map-editor/
└── tests/
    ├── test_models.py          # Data model tests
    ├── test_project_io.py      # File I/O tests
    ├── test_integration.py     # Workflow tests
    └── test_gui.py            # GUI automation tests
```

## Project Statistics

**Total Python Code**: ~2,335 lines (excluding comments/blanks)

**Code Distribution**:
- GUI Layer (`gui.py`): 1,324 lines (56.7%)
- Core Logic (`core/`): 1,011 lines (43.3%)
  - routes.py: 302 lines
  - systems.py: 221 lines
  - project_io.py: 193 lines
  - project_model.py: 157 lines
  - templates.py: 139 lines

**Documentation**: ~30 pages across 5 markdown files

**External Dependencies**: 1 (PySide6 only)

## Key Features Summary

✅ **Template-based Map Creation**: Load background images as alignment references
✅ **Star System Placement**: Add and position systems with names
✅ **Route Creation**: Connect systems with curved hyperlane routes using Bezier splines
✅ **Multiple Editing Modes**: Template, Systems, Routes, Zones (planned)
✅ **Advanced Navigation**: Mouse wheel zoom (0.1x-10x), WASD/arrow pan, drag pan
✅ **Visual Feedback**: Semi-transparent grid, color-coded selection, status messages
✅ **Project Management**: Save/load full editor state as .swmproj files
✅ **Data Export**: Generate game-ready JSON without editor metadata
✅ **Unsaved Changes Tracking**: Prompts before losing work
✅ **Keyboard Shortcuts**: Full keyboard support for all operations

## Next Steps for Development

Based on the issue requirements, the setup is now complete:

1. ✅ **Repository analysis complete**: Architecture documented
2. ✅ **Code structure identified**: All modules and responsibilities mapped
3. ✅ **Documentation created**: ARCHITECTURE.md with detailed overview
4. ✅ **Copilot instructions updated**: Correct paths and framework
5. ✅ **Commands documented**: Clear instructions to run and test
6. ✅ **Structure cleaned**: No dead code, clear organization

The repository is now **clean, coherent, and ready for future feature work** such as:
- Statistics dashboard expansion
- Route optimization algorithms
- Zone/territory system implementation
- System property expansion (population, economy, factions)
- Automated testing infrastructure
- Additional export formats
- Economy/convoy simulation features

All documentation is consistent, accurate, and up-to-date with the actual codebase.
