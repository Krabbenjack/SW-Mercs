"""Compatibility wrapper for the root installation verifier."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[2] / "tools" /
                       "verify_installation.py"), run_name="__main__")
