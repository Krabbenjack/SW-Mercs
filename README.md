# SW-Mercs

SW-Mercs is a desktop toolkit for galactic maps, ship databases and economic simulation. The Star Map Editor is the first working module.

## SW-Mercs Launcher (new)

From the **repository root**, double-click `swmercs.bat` on Windows or run `python swmercs.py` in a terminal. If PySide6 is missing or too old, the launcher offers to install dependencies into a local virtual environment (`.venv`). Internet access is required for the first installation. Subsequent launches reuse the environment automatically.

The launcher shows **Play** (not yet implemented) and **Editor**. The Editor Command Center opens the Star Map Editor and Starship Editor. Industry and the Fleet Manager are planned.

### Starship Editor

The Starship Database lists ships, stations and cargo containers by their stable master IDs. Each class has its own editable JSON file. Search, create, edit, save, import and export individual records or batches. Category-aware optional fields keep small craft forms compact without losing data. The Component Database manages reusable weapons, which can be assigned through a searchable drag-and-drop equipment popup with count, firing direction and optional ammunition capacity. Six weapon size classes and editable hull limits prevent incompatible equipment, including on import; the question-mark buttons explain the classes.

Unknown fields are blank (JSON `null`); zero, false and empty lists are distinct explicit values. Imports validate IDs and references, preserve omitted fields and ask before updating existing records. See [Starship catalog](docs/STARSHIP_CATALOG.md) for the data format.

The launcher and Star Map Editor use the shared SW-Mercs dark-blue UI theme. Module-specific styles live in `resources/styles/`; the map's own light/dark rendering remains independently selectable.

The existing `python star-map-editor/main.py` command remains supported as a legacy direct entry point. Existing map projects need no format conversion; their original locations remain accessible. New saves and exports default to the root `saves/` and `exports/` directories.

## Quick Start

### Installation

1. **Install Python 3.10+**
2. **Double-click `swmercs.bat`** (Windows) or run `python swmercs.py` from a terminal.
3. **Confirm the first-run setup if prompted** with Y or J. The launcher installs dependencies and opens the application when finished. No changes to system Python are needed.

### Running the Application

```bash
python swmercs.py
```

### Verifying Installation

```bash
python tools/verify_installation.py
```

If the launcher created a virtual environment, use `.venv\Scripts\python.exe tools/verify_installation.py` on Windows (or `.venv/bin/python tools/verify_installation.py` on Linux/macOS).

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - Current application layout
- **[Project knowledge base](docs/README.md)** - Design decisions and game data
- **[Star Map Editor documentation (archive)](docs/archive/starmap/README.md)** - Historical feature documentation
- **[Manual testing reference](docs/archive/starmap/TESTING.md)** - Historical manual testing procedures
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Development guidelines for contributors

## Project Structure

```
SW-Mercs/
├── swmercs.bat                 # Windows launcher
├── swmercs.py                  # Python entry point
├── requirements.txt
├── app/
│   ├── launcher/               # Main menu and command center
│   ├── editors/
│   │   ├── starmap/            # Working map editor and models
│   │   ├── starships/          # Ship and weapon catalogs; fleet tools planned
│   │   └── industry/           # Planned production and goods tools
│   ├── simulation/             # Reserved for game simulation
│   └── shared/                 # Central application paths
├── data/                       # Master JSON data
├── resources/                  # QSS, icons and templates
├── saves/                      # Local projects, created on demand
├── exports/                    # Local exports, created on demand
├── tests/                      # Automated regression tests
├── tools/                      # Installation verifier
├── docs/                       # Design and historical documentation
└── star-map-editor/            # Legacy entry point only
```

## Key Features

- 🗺️ **Template-based Map Creation**: Load background images as reference
- ⭐ **Star System Placement**: Add and position star systems on your map
- 🛣️ **Route Creation**: Connect systems with curved hyperlane routes
- 🔍 **Advanced Navigation**: Smooth zoom and pan controls
- 🌍 **World Rescaling**: Adjust world scale to fix travel time issues
- 💾 **Project Management**: Save/load projects with full state
- 📤 **Export**: Generate game-ready JSON data

## World Menu

The **World** menu provides tools for adjusting the global scale and geometry of your map:

### World → Scale...

The **Scale** feature allows you to rescale the entire world geometry to fix travel time issues or adjust the overall map scale.

**What it does:**
- Scales all system positions by a given factor
- Scales all route control points (geometry)
- Optionally scales template positions and sizes

**Parameters:**
- **Scale Factor** (0.01 - 100.0): The multiplier to apply to all coordinates
  - Values < 1.0: Shrink the world (shorter travel times)
  - Values > 1.0: Expand the world (longer travel times)
- **Scale templates too**: When checked, templates are also scaled and repositioned
- **Anchor Point**: Choose the fixed point around which scaling occurs
  - **Keep center (centroid)**: Scale around the center of all systems (default)
  - **Origin (0, 0)**: Scale from the coordinate origin

**Use cases:**
- **Fix travel times**: If newly created projects have unrealistic travel times due to incorrect world scale, use this to rescale everything proportionally
- **Match reference scale**: Scale your map to match a specific reference or measurement
- **Combine maps**: Adjust scale when merging content from different sources

**Scene expansion:** The scrollable scene area automatically expands after rescaling to ensure all content remains accessible.

## Route Classes & Travel Speed

The Star Map Editor includes a comprehensive route statistics system that affects travel time calculations. Route Classes allow you to differentiate between fast trade lanes and slow dangerous routes.

### Route Class System (1-5)

Routes are categorized into five classes that significantly affect travel speed:

- **Class 1**: Super-fast trade lane (10x base speed, ≈ 4000 HSU/h)
- **Class 2**: Fast main route (4x base speed, ≈ 1600 HSU/h)
- **Class 3**: Standard route (1x base speed, ≈ 400 HSU/h) - Default
- **Class 4**: Slow / indirect route (0.5x base speed, ≈ 200 HSU/h)
- **Class 5**: Very slow / dangerous route (0.25x base speed, ≈ 100 HSU/h)

### Travel Time Calculation

The editor uses a calibrated formula to calculate realistic travel times:

**Base Calibration**: `BASE_HSU_PER_HOUR = 400`
- This applies to Route Class 3, normal travel type, no hazards, with a x1 hyperdrive

**Formula**:
```
effective_hsu_per_hour = BASE_HSU_PER_HOUR × route_class_multiplier × travel_type_multiplier × hazard_multiplier
travel_time_hours = (route_length_hsu / effective_hsu_per_hour) × hyperdrive_rating
```

### Factors Affecting Travel Time

1. **Route Class**: Primary speed factor (see multipliers above)
2. **Travel Type**: Route condition modifiers
   - Normal: 1.0x (standard)
   - Express Lane: 1.2x (well-maintained)
   - Ancient Hyperlane: 0.8x (degraded)
   - Backwater: 0.6x (poorly maintained)
3. **Hazards**: Each hazard reduces speed (stacks multiplicatively)
   - Nebula: 0.8x (20% slower)
   - Hypershadow: 0.7x (30% slower)
   - Quasar: 0.6x (40% slower)
   - Minefield: 0.85x (15% slower)
   - Pirate Activity: 0.9x (10% slower)
4. **Hyperdrive Rating**: Ship capability
   - x1: Fastest (1.0x time)
   - x2: 2x travel time
   - x3: 3x travel time
   - x4: Slowest (4x travel time)

### Using Route Stats

1. Select a route on the map
2. Switch to "Route" tab in the Stats panel (or it switches automatically)
3. Adjust Route Class, Travel Type, and Hazards
4. Switch to "Calculator" tab to see travel time estimates
5. Select different hyperdrive ratings to compare ship performance

The Travel Calculator updates automatically when you change route parameters.

## Technology Stack

- **Python 3.10+**
- **PySide6** (Qt for Python)
- **Architecture**: Model-View-Graphics Item pattern with Qt Graphics View Framework

## Testing

Currently, testing is done manually. Run the application and follow procedures in:
- `docs/archive/starmap/TESTING.md`

Future: Add automated unit and integration tests.

## Development

See [.github/copilot-instructions.md](.github/copilot-instructions.md) for:
- Coding guidelines
- Architecture patterns
- Development workflow
- PR standards

## License

See [LICENSE](LICENSE) file for details.

