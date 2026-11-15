"""Compose the shared SW-Mercs QSS with a module's own styling."""
import logging

from app.shared.paths import RESOURCES_DIR


def apply_theme(window, module):
    """Keep styles scoped to the window so other tools remain independent."""
    styles = RESOURCES_DIR / "styles"
    parts = []
    for name in ("swmercs.qss", f"{module}.qss"):
        try:
            qss = (styles / name).read_text(encoding="utf-8")
            parts.append(qss.replace("@icons/", (RESOURCES_DIR / "icons" / "ui").as_posix() + "/"))
        except (OSError, UnicodeError) as exc:
            logging.warning("Cannot load theme %s: %s", name, exc)
    window.setStyleSheet("\n".join(parts))
