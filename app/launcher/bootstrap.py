"""First-run setup without importing Qt until dependencies are available."""
import os
import subprocess
import sys
from pathlib import Path

from app.shared.paths import ROOT


def qt_ready():
    """Check the version and imports needed by the launcher and map editor."""
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
        if tuple(map(int, QtCore.__version__.split(".")[:2])) < (6, 6):
            return False, "PySide6 6.6 or newer is required."
    except (ImportError, OSError, ValueError) as exc:
        return False, str(exc)
    return True, ""


def launch_checked():
    """Launch without offering installation again (used after setup)."""
    ready, reason = qt_ready()
    if not ready:
        print(f"PySide6 could not be loaded: {reason}", file=sys.stderr)
        return 1
    from app.launcher.window import main as launch
    return launch()


def environment_python(environment):
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run_in_environment(python):
    # Use the installed interpreter, without entering the setup flow again.
    return subprocess.call(
        [str(python), "-c",
         "from app.launcher.bootstrap import launch_checked; raise SystemExit(launch_checked())",
         *sys.argv[1:]], cwd=ROOT,
    )


def main():
    if sys.version_info < (3, 10):
        print("SW-Mercs requires Python 3.10 or newer.", file=sys.stderr)
        return 1

    ready, reason = qt_ready()
    if ready:
        return launch_checked()

    environment = ROOT / ".venv"
    python = environment_python(environment)
    # Direct Python launches should also reuse an existing local environment.
    if Path(sys.prefix).resolve() != environment.resolve() and python.is_file():
        try:
            probe = subprocess.run(
                [str(python), "-c",
                 "from app.launcher.bootstrap import qt_ready; raise SystemExit(not qt_ready()[0])"],
                cwd=ROOT,
            )
            if probe.returncode == 0:
                return run_in_environment(python)
        except OSError as exc:
            print(f"Could not reuse the local environment: {exc}", file=sys.stderr)

    print("\nSW-Mercs | First-time setup", flush=True)
    print(f"Required GUI library is missing or unavailable: {reason}")
    print("This installs the requirements into a local .venv folder, without")
    print("changing your system Python. Internet access is required.")
    try:
        answer = input("Install now? [Y/N, J/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = ""
    if answer not in {"y", "yes", "j", "ja"}:
        print("Setup cancelled. Start SW-Mercs again when you are ready.")
        return 0

    try:
        if not python.is_file():
            subprocess.run([sys.executable, "-m", "venv", str(environment)],
                           cwd=ROOT, check=True)
        subprocess.run(
            [str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
            cwd=ROOT, check=True,
        )
        print("Setup complete. Starting SW-Mercs...", flush=True)
        return run_in_environment(python)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        print("Check your internet connection and Python installation, then retry.",
              file=sys.stderr)
        return 1
