"""Check dependencies, compile application code and run all regression scripts."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    import PySide6
    print("PySide6", PySide6.__version__, flush=True)
    paths = [ROOT / "swmercs.py", *ROOT.glob("app/**/*.py"), *ROOT.glob("tests/*.py")]
    for path in paths:
        compile(path.read_bytes(), str(path), "exec")
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    failed = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        print(f"\n=== {path.name} ===", flush=True)
        result = subprocess.run([sys.executable, str(path)], cwd=ROOT, env=env, timeout=60)
        if result.returncode != 0:
            failed.append(path.name)
    print("Failed:", ", ".join(failed) if failed else "none")
    return int(bool(failed))

if __name__ == "__main__":
    raise SystemExit(main())

