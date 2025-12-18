# SW-Mercs

Star Map Editor for creating and editing Star Wars-inspired galactic maps.

## Quick Start

### Installation

1. **Install Python 3.10+**
2. **Navigate to the application directory:**
   ```bash
   cd star-map-editor
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

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

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete architecture overview and technical details
- **[star-map-editor/README.md](star-map-editor/README.md)** - Full feature documentation
- **[star-map-editor/QUICKSTART.md](star-map-editor/QUICKSTART.md)** - 5-minute getting started guide
- **[star-map-editor/TESTING.md](star-map-editor/TESTING.md)** - Manual testing procedures
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Development guidelines for contributors

## Project Structure

```
SW-Mercs/
├── ARCHITECTURE.md              # Architecture documentation
├── star-map-editor/            # Main application directory
│   ├── main.py                 # Application entry point
│   ├── gui.py                  # PySide6 GUI implementation
│   ├── core/                   # Business logic and data models
│   │   ├── project_model.py    # MapProject, TemplateData
│   │   ├── systems.py          # SystemData, SystemItem
│   │   ├── routes.py           # RouteData, RouteItem
│   │   ├── templates.py        # TemplateItem
│   │   └── project_io.py       # Save/load/export
│   ├── resources/              # Application resources
│   ├── Saves/                  # Project files (.swmproj)
│   └── Exports/                # Exported map data (.json)
└── .github/
    └── copilot-instructions.md # Development guidelines
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

The Star Map Editor provides comprehensive system management through the **Stats** tab in the right sidebar. When a system is selected, you can configure:

### Population

Select from predefined population levels (from uninhabited to galactic capitals). The editor displays both the population category label and an approximate numeric value:

- **Uninhabited** — No permanent inhabitants
- **Mikrosiedlung** — ≈ 50K inhabitants
- **Sehr niedrig** — ≈ 550K inhabitants
- **Niedrig** — ≈ 25M inhabitants
- **Mittel-niedrig** — ≈ 275M inhabitants
- **Mittel** — ≈ 750M inhabitants
- **Etabliert** — ≈ 3B inhabitants
- **Groß** — ≈ 7.5B inhabitants
- **Sehr groß** — ≈ 30B inhabitants
- **Hyperurbanisiert** — ≈ 125B inhabitants
- **Megacity-Planet** — ≈ 550B inhabitants
- **Galaktische Hauptstadt** — ≈ 1.5T inhabitants

### Planets and Moons

Each system can contain multiple planets, and each planet can have multiple moons:

- **Add Planet**: Create a new planet in the system
- **Rename**: Change the name of a selected planet
- **Delete**: Remove a planet (and all its moons) from the system

When a planet is selected, you can manage its moons:

- **Add Moon**: Create a new moon orbiting the selected planet
- **Rename**: Change the name of a selected moon
- **Delete**: Remove a moon from the planet

**Example**: A Coruscant-style multi-planet system might have:
- Planet: **Coruscant Prime**
  - Moon: **Hesperidium**
  - Moon: **Centax-1**
  - Moon: **Centax-2**
- Planet: **Coruscant Minor**
  - Moon: **Centax-3**

### Facilities

Configure what industrial and commercial facilities are present in the system (mining, manufacturing, trade hubs, etc.).

### Imports and Exports

Define which goods the system imports and exports for trade route planning.

### Lore / Description

Add custom flavor text describing the system's history, culture, or strategic importance. The lore field has a 500 character limit with a live character counter.

**Example**: "Capital of the Galactic Republic and later the Empire. A sprawling ecumenopolis covering the entire planet, Coruscant serves as the political, economic, and cultural heart of the galaxy."

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
- `star-map-editor/TESTING.md`

Future: Add automated unit and integration tests.

## Development

See [.github/copilot-instructions.md](.github/copilot-instructions.md) for:
- Coding guidelines
- Architecture patterns
- Development workflow
- PR standards

## License

See [LICENSE](LICENSE) file for details.
