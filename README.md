# SW-Mercs

SW-Mercs is a desktop toolkit for galactic maps, ship databases and economic simulation. The Star Map Editor is the first working module.

## SW-Mercs Launcher (new)

From the **repository root**, double-click `swmercs.bat` on Windows or run `python swmercs.py` in a terminal. If PySide6 is missing or too old, the launcher offers to install dependencies into a local virtual environment (`.venv`). Internet access is required for the first installation. Subsequent launches reuse the environment automatically.

The launcher shows **Play** (not yet implemented) and **Editor**. The Editor Command Center opens the Star Map Editor and Starship Editor. Industry and the Fleet Manager are planned.

### Starship Editor

The Starship Database lists ships, stations and cargo containers by their stable master IDs. Each class has its own editable JSON file. Search, create, edit, save, import and export individual records or batches. Category-aware optional fields keep small craft forms compact without losing data. Ships and stations have an editable FFG silhouette rating (3–10 and higher for exceptional objects). The Component Database manages reusable weapons, which can be assigned through a searchable drag-and-drop equipment popup with count, firing direction and optional ammunition capacity. Six weapon size classes and editable hull limits prevent incompatible equipment, including on import; the question-mark buttons explain the classes.

Sensors and weapons share five FFG-inspired range bands (Close, Short, Medium, Long, Extreme). Weapon tracking and ship/station maneuverability use integer ratings from 0–10. Distance thresholds and combat mechanics will be defined later; each field has in-editor help.

Unknown fields are blank (JSON `null`); zero, false and empty lists are distinct explicit values. Imports validate IDs and references, preserve omitted fields and ask before updating existing records. See [Starship catalog](docs/STARSHIP_CATALOG.md) for the data format.

The launcher and Star Map Editor use the shared SW-Mercs dark-blue UI theme. Module-specific styles live in `resources/styles/`; the map's own light/dark rendering remains independently selectable.

The existing `python star-map-editor/main.py` command remains supported as a legacy direct entry point. Existing map projects need no format conversion; their original locations remain accessible. The launcher creates `saves/starmaps/` and `saves/shipsets/` on startup. New star maps default to `saves/starmaps/`; the shipsets folder is reserved for whole-database saves. Exports default to the root `exports/` directory. Personal saves are ignored by Git; curated examples can be versioned in the respective `examples/` subfolders.


### In-system map (initial implementation in PR #30)

In **Stats**, select a star system and click **Open System Map...**. A separate, static system grid opens without replacing the galactic view. **Right-click** an existing planet, moon or system-authorized facility in the left list to pick it up, then **left-click** the grid to place it (Esc cancels). Drag & drop remains an alternative. Planet symbols are colored by type (desert yellow, temperate green, ice light blue, gas giant violet), moons grey, and constructed facilities triangles: **red for military**, **blue for civilian/non-military** (provisional classification; the military science lab is also red). A facility represents a future package of installations/capabilities, not necessarily one building; package composition and capability accounting are not yet implemented. The star is at (0,0); the physical grid scale is editable in AU per cell and saved per system. Habitable-zone inner/outer radii are also editable. Objects use provisional circle icons.

A facility dropped onto a planet or moon icon prompts for surface or orbit (subject to the allowed modes in `data/facilities/facility_placements.json`); a drop on empty space creates a deep-space facility only when permitted. The original facility IDs and system-level selections remain unchanged. The spatial map is stored as optional `system_map` data within each system in `.swmproj`; old saves without it remain valid.

**Known limitations of this initial increment:** placed icons are not yet individually draggable for repositioning, object removal is currently last-placement-only, the habitable zone is a configurable guide rather than stellar-physics-derived, and tactical/facility detail editors are not implemented. The dialog's Save commits its working copy to the project model; save the overall project to write the `.swmproj` file.

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
├── saves/                      # Standard save directories (created on startup)
│   ├── starmaps/               # Star map projects (.swmproj)
│   └── shipsets/               # Reserved for complete ship databases
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

## System Statistics

In Stats mode, select a star system to edit its population, facilities,
imports and exports in the right-hand sidebar. The population label also shows
the estimated numeric population (midpoint of the selected population category).
Uninhabited is explicitly 0; an unspecified category is unknown.

- Add, rename and delete planets, each with its own stable ID and optional type:
  Desert, Ice, Temperate or Gas Giant.
- Select a planet to add, rename or delete its moons. Deleting a planet requires
  confirmation and removes its moons from that system as well.
- Enter a system description (up to 500 characters) with a live character count.

The new fields are included in map saves and game JSON exports. Older maps load
without modification; missing planets, planet types and descriptions remain
unspecified/empty. Edits mark the project as unsaved.

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

