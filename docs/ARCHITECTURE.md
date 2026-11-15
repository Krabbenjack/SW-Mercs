# SW-Mercs application architecture

The root entry point `swmercs.py` checks dependencies via `app.launcher.bootstrap.main()` before starting `app.launcher.window.main()`, which creates a single QApplication and shows the main menu. Editor opens the command center. Star Map Editor and Starship Editor create separate windows in the same Qt application; both check for unsaved changes before closing. Play and Industry Editor are disabled until implemented.

## Modules

- `app/launcher/`: navigation and launcher-specific styling.
- `app/editors/starmap/`: existing map editor, system and route graphics, templates, models, project I/O and data loader.
- `app/editors/starships/`: class and weapon catalogs, field schema, validated JSON persistence and Qt editor; fleet tooling planned.
- `app/editors/industry/`: reserved for goods and production tools.
- `app/simulation/`: reserved for simulation logic.
- `app/shared/paths.py`: canonical root-relative data, resources, saves and exports directories.
- `app/shared/theme.py`: combines the common QSS and per-window stylesheet. See [UI design system](UI_DESIGN_SYSTEM.md).

Data and resource paths are resolved from the repository, never the current working directory. Existing master data and the map save/export schemas remain unchanged. The launcher ensures `saves/starmaps/` and `saves/shipsets/` exist; new maps use the former, and the latter is reserved for whole-database persistence. Existing user saves are not relocated; the Open dialog also recognizes the former root `saves/` and legacy save directories. The standard folders are tracked via their README files, with personal saves ignored and curated examples allowed in their `examples/` subdirectories.

## Verification

From the root run `python tools/verify_installation.py`. It compiles the application and runs all regression scripts in isolated processes using real PySide6, including launcher navigation and map persistence.

Previous architecture and implementation records are preserved under [archive/](archive/). They describe earlier versions and may contain obsolete paths or behavior.
