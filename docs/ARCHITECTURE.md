# SW-Mercs application architecture

The root entry point `swmercs.py` delegates to `app.launcher.window.main()`, which creates a single QApplication and shows the main menu. Editor opens the command center. Star Map Editor creates a separate window in the same Qt application; it checks for unsaved changes before closing. Play, Starship Editor and Industry Editor are disabled until implemented.

## Modules

- `app/launcher/`: navigation and launcher-specific styling.
- `app/editors/starmap/`: existing map editor, system and route graphics, templates, models, project I/O and data loader.
- `app/editors/starships/`: reserved for the ship database and fleet tooling.
- `app/editors/industry/`: reserved for goods and production tools.
- `app/simulation/`: reserved for simulation logic.
- `app/shared/paths.py`: canonical root-relative data, resources, saves and exports directories.

Data and resource paths are resolved from the repository, never the current working directory. Existing master data and the map save/export schemas remain unchanged. Existing user saves are not relocated; the Open dialog also recognizes legacy save directories.

## Verification

From the root run `python tools/verify_installation.py`. It compiles the application and runs all regression scripts in isolated processes using real PySide6, including launcher navigation and map persistence.

Previous architecture and implementation records are preserved under [archive/](archive/). They describe earlier versions and may contain obsolete paths or behavior.
