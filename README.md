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
- 💾 **Project Management**: Save/load projects with full state
- 📤 **Export**: Generate game-ready JSON data

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
