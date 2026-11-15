"""Create only missing catalog JSON records; never replace existing data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.editors.starships.store import CatalogStore

if __name__ == "__main__":
    print(f"Created {CatalogStore(seed=False).seed_missing()} missing records.")
