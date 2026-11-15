"""Data loader module for JSON game data.

This module handles loading and caching of JSON data files from the /data/ directory.
Provides a centralized interface for accessing goods, facilities, and population data.
"""

import json
from pathlib import Path
from typing import Optional
from app.shared.paths import DATA_DIR


class DataLoader:
    """Loads and caches JSON game data from /data/ directory.
    
    Handles missing or corrupted files gracefully by returning empty structures.
    Data is cached in memory after first load.
    """
    
    def __init__(self):
        """Initialize the data loader."""
        self._goods = None
        self._facility_categories = None
        self._population_levels = None
        self._data_dir = None
        
    def _find_data_dir(self) -> Optional[Path]:
        """Locate the /data/ directory relative to the project root.
        
        Returns:
            Path to data directory if found, None otherwise
        """
        if self._data_dir is not None:
            return self._data_dir
            
        if DATA_DIR.is_dir():
            self._data_dir = DATA_DIR
            return self._data_dir
        return None
    
    def _load_json_file(self, relative_path: str) -> dict:
        """Load a JSON file from the data directory.
        
        Args:
            relative_path: Path relative to /data/ directory
            
        Returns:
            Parsed JSON data, or empty dict if file not found/invalid
        """
        data_dir = self._find_data_dir()
        if data_dir is None:
            print(f"Warning: Could not locate data directory for {relative_path}")
            return {}
        
        file_path = data_dir / relative_path
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Data file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {file_path}: {e}")
            return {}
        except Exception as e:
            print(f"Warning: Error loading {file_path}: {e}")
            return {}
    
    def load_all(self):
        """Load all data files at once.
        
        Call this during application startup to pre-load all data.
        """
        self.get_goods()
        self.get_facility_categories()
        self.get_population_levels()
    
    def get_goods(self) -> list[dict]:
        """Get the list of all goods.
        
        Returns:
            List of good dictionaries with keys: id, name, tier, cu
        """
        if self._goods is None:
            data = self._load_json_file("goods/goods.json")
            self._goods = data.get("goods", [])
        return self._goods
    
    def get_facility_categories(self) -> dict[str, list[str]]:
        """Get facility categories and their facility IDs.
        
        Returns:
            Dictionary mapping category names to lists of facility IDs.
            Example: {"industry": ["mining_facility", ...], ...}
        """
        if self._facility_categories is None:
            data = self._load_json_file("facilities/facility_flags.json")
            self._facility_categories = data.get("categories", {})
        return self._facility_categories
    
    def get_population_levels(self) -> list[dict]:
        """Get the list of population levels.
        
        Returns:
            List of population level dictionaries with keys: id, label, min, max
        """
        if self._population_levels is None:
            data = self._load_json_file("population/population_levels.json")
            self._population_levels = data.get("population_levels", [])
        return self._population_levels

    def get_population_value(self, population_id: str | None) -> int | None:
        """Return the midpoint of the selected population category, not a census."""
        for level in self.get_population_levels():
            if level.get("id") == population_id and population_id is not None:
                return (level["min"] + level["max"]) // 2
        return None


def format_population(value: int | None) -> str:
    """Compact population display; 0 and unknown are distinct."""
    if value is None:
        return ""
    for divisor, suffix in ((10**12, "T"), (10**9, "B"), (10**6, "M"), (10**3, "K")):
        if value >= divisor:
            return f"{value / divisor:.1f}".rstrip("0").rstrip(".") + suffix
    return str(value)


# Global singleton instance
_data_loader_instance = None


def get_data_loader() -> DataLoader:
    """Get the global DataLoader instance.
    
    Returns:
        The singleton DataLoader instance
    """
    global _data_loader_instance
    if _data_loader_instance is None:
        _data_loader_instance = DataLoader()
    return _data_loader_instance

