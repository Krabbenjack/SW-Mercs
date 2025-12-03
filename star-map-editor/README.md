# Star Map Editor

A PyQt5-based desktop application for creating and editing Star Wars-inspired galactic maps.

## Requirements

- Python 3.10+
- PyQt5 5.15.0+

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
- **`src/gui.py`**: PyQt5 GUI implementation containing:
  - `StarMapEditor`: Main window class
  - `MapView`: Custom QGraphicsView with zoom and pan controls
  - `GridOverlay`: Custom QGraphicsScene with semi-transparent grid rendering

## Current Features

- **PyQt5 Desktop GUI**: Modern graphical interface with button toolbar
- **Load Template**: Import PNG/JPG/BMP images as map backgrounds
- **Semi-transparent Grid Overlay**: 100px grid overlay for precise alignment
- **Mouse Wheel Zoom**: Zoom in/out anchored under cursor position
- **WASD Panning**: Keyboard navigation for moving around the map
- **JSON Export**: Save map data structure with the following format:
  ```json
  {
    "mapName": "Unnamed Map",
    "systems": [],
    "routes": [],
    "zones": [],
    "stats": {}
  }
  ```
- **Placeholder Buttons**: Systems, Routes, Zones, and Stats (coming soon)

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
