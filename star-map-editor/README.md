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
python -m src.main
```

Or alternatively:

```bash
cd src
python main.py
```

## Project Structure

- **`src/main.py`**: Application entry point - creates QApplication and launches the main window
- **`src/gui.py`**: PySide6 GUI implementation containing:
  - `StarMapEditor`: Main window class with mode management
  - `MapView`: Custom QGraphicsView with zoom, pan controls, and system placement
  - `GridOverlay`: Custom QGraphicsScene with semi-transparent grid rendering
- **`src/systems.py`**: System placement and management module containing:
  - `SystemData`: Data model for star systems
  - `SystemItem`: Graphics representation of systems
  - `SystemDialog`: Dialog for creating/editing systems

## Current Features

### Navigation & View
- **PySide6 Desktop GUI**: Modern graphical interface with mode-based toolbar
- **Load Template**: Import PNG/JPG/BMP images as map backgrounds
- **Semi-transparent Grid Overlay**: Light green 100px grid overlay for precise alignment
- **Mouse Wheel Zoom**: Smooth zoom (0.1x-10x) anchored under cursor position with limits
- **Keyboard Panning**: 
  - WASD/Arrow keys for continuous panning at 30 FPS
  - Pan speed scales with zoom level for consistent control
- **Mouse Drag Panning**: Middle mouse or Space+left mouse for intuitive map navigation

### System Placement Mode
- **Mode Selection**: Click the Systems button to enter placement mode (button turns green)
- **Place Systems**: Left-click on the map to place a new star system
  - Opens a dialog to enter the system name
  - Systems appear as blue circles with white labels
  - Each system gets a unique UUID identifier
- **Edit Systems**: Right-click on an existing system to edit or delete it
- **Drag Systems**: Click and drag systems to reposition them
  - Works smoothly at all zoom levels
  - Position updates automatically in the data model
- **Visual Feedback**: 
  - Normal systems: Blue circles
  - Selected systems: Orange/yellow circles
  - System names displayed as labels

### Data Management
- **JSON Export**: Save complete map data with systems:
  ```json
  {
    "mapName": "Unnamed Map",
    "systems": [
      {
        "id": "uuid-string",
        "name": "System Name",
        "x": 1000.0,
        "y": 750.0
      }
    ],
    "routes": [],
    "zones": [],
    "stats": {
      "totalSystems": 5,
      "totalRoutes": 0,
      "totalZones": 0
    }
  }
  ```

### Coming Soon
- **Routes Mode**: Create hyperlane connections between systems
- **Zones Mode**: Define territorial regions and special areas
- **Stats Viewer**: Display map statistics and analytics

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
