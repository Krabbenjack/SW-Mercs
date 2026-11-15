# SW-Mercs UI Design System v1

The common SW-Mercs visual identity is a dark, navy/steel-blue technical console with readable contrast. Qt/PySide6 uses QSS rather than browser CSS.

## Palette

| Token | Hex | Purpose |
| --- | --- | --- |
| Background | `#101923` | Window background |
| Panel | `#1B2C3B` | Menus, lists, panels |
| Elevated | `#273F54` | Selected tabs, elevated surfaces |
| Button | `#22384C` | Interactive controls |
| Accent | `#9CCCF2` | Titles and highlights |
| Accent border | `#75B6E4` | Focus and hover |
| Border | `#3B5366` | Separators and borders |
| Primary text | `#E6EDF5` | Main labels |
| Secondary text | `#B3C4D2` | Secondary labels |
| Success | `#81C8A4` | Validated/ready |
| Warning | `#E2BF83` | Pending/caution |

The shared stylesheet is `resources/styles/swmercs.qss`. The helper `app/shared/theme.py` loads it before the module-specific stylesheet (`launcher.qss` or `starmap.qss`) on the window, so separate tools do not overwrite each other's appearance. Future editors can use the same helper with their own stylesheet (e.g. `starships.qss`). Small UI icons live in `resources/icons/ui/`.

The Star Map Editor now uses this common design for its menus, controls, dialogs, statistics sidebar, and zoom/status displays. Its View → Dark/Light Mode actions still switch the map scene colors, independent of the dark application chrome. Do not apply theme colors to the star-map scene, route classes, hazards, system markers, or other semantically color-coded graphics without separate review.

## Navigation and planned modules

1. Main menu: **Play** (disabled for now) and **Editor**.
2. Editor Command Center: **Star Map Editor**, **Starship Editor**, **Industry Editor**.
3. Starship Editor: ship class database first; Fleet Manager later for fleet composition, upkeep and maintenance testing.
4. Industry Editor: goods, production and economic simulation in one module.
5. Modules can eventually be open at the same time, sharing master IDs and catalog data.

The main menu, command center, Star Map Editor and Starship Editor are operational. The Starship Editor uses the shared stylesheet plus `starships.qss`. Play and Industry remain disabled placeholders.

## Manual visual QA

- Start from the repository root with `python swmercs.py` or double-click `swmercs.bat` on Windows.
- Check main menu/toolbar, sidebar, tabs, tables, dialogs and scrollbars for readable contrast.
- Verify existing map layers and route colors remain distinguishable.
- Check keyboard focus, disabled controls, input selection and dropdown visibility.
- Run existing regression tests before merging.
