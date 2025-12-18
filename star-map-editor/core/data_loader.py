"""Data loader module for JSON game data.

This module handles loading and caching of JSON data files from the /data/ directory.
Provides a centralized interface for accessing goods, facilities, and population data.
"""

import json
from pathlib import Path
from typing import Optional


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
            
        # Start from this file's directory and search upward
        current = Path(__file__).resolve().parent
        
        # Try going up to find the data directory
        for _ in range(5):  # Limit search depth
            data_path = current.parent / "data"
            if data_path.exists() and data_path.is_dir():
                self._data_dir = data_path
                return self._data_dir
            current = current.parent
        
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
        """Get the numeric population value for a given population ID.
        
        Uses the average of min and max for the population level.
        
        Args:
            population_id: The population level ID (from population_levels.json)
            
        Returns:
            The average population value, or None if not found or if uninhabited
        """
        if population_id is None:
            return None
        
        population_levels = self.get_population_levels()
        for level in population_levels:
            if level.get("id") == population_id:
                min_val = level.get("min", 0)
                max_val = level.get("max", 0)
                # Return average of min and max
                return (min_val + max_val) // 2
        
        return None


def format_population(value: int | None) -> str:
    """Format a population value in a human-readable way.
    
    Examples:
        1_200_000_000 -> "1.2B"
        500_000_000 -> "500M"
        1_000_000 -> "1M"
        50_000 -> "50K"
    
    Args:
        value: The population value to format
        
    Returns:
        Formatted string (e.g., "1.2B") or empty string if value is None
    """
    if value is None or value == 0:
        return ""
    
    def format_with_suffix(num, suffix):
        """Format number with suffix, removing unnecessary decimals."""
        formatted = f"{num:.1f}"
        # Remove trailing zeros and decimal point if not needed
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return formatted + suffix
    
    if value >= 1_000_000_000_000:  # Trillion
        return format_with_suffix(value / 1_000_000_000_000, 'T')
    elif value >= 1_000_000_000:  # Billion
        return format_with_suffix(value / 1_000_000_000, 'B')
    elif value >= 1_000_000:  # Million
        return format_with_suffix(value / 1_000_000, 'M')
    elif value >= 1_000:  # Thousand
        return format_with_suffix(value / 1_000, 'K')
    else:
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
