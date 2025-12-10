"""JSON data loader for system stats.

This module loads external JSON data files for goods, facilities, and population levels.
All JSON data is cached in memory after first load.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class DataLoader:
    """Loader for external JSON data files.
    
    Loads and caches data from:
    - /data/goods/goods.json
    - /data/goods/production_chains.json
    - /data/facilities/facility_flags.json
    - /data/population/population_levels.json
    
    All data is loaded relative to the project root directory.
    """
    
    def __init__(self):
        """Initialize the data loader."""
        self._goods: Optional[List[Dict[str, Any]]] = None
        self._production_chains: Optional[List[Dict[str, Any]]] = None
        self._facility_categories: Optional[Dict[str, List[str]]] = None
        self._population_levels: Optional[List[Dict[str, Any]]] = None
        self._data_dir: Optional[Path] = None
    
    def _find_data_directory(self) -> Path:
        """Find the data directory relative to project root.
        
        Returns:
            Path to the data directory
            
        Raises:
            FileNotFoundError: If data directory cannot be found
        """
        if self._data_dir is not None:
            return self._data_dir
        
        # Start from this file's directory and search upwards
        current_dir = Path(__file__).parent
        
        # Try going up from core/ to star-map-editor/ to project root
        for _ in range(3):
            data_path = current_dir / "data"
            if data_path.exists() and data_path.is_dir():
                self._data_dir = data_path
                return data_path
            current_dir = current_dir.parent
        
        # If not found, raise error
        raise FileNotFoundError("Could not locate /data directory in project")
    
    def _load_json_safe(self, file_path: Path) -> Any:
        """Load JSON file safely.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON data, or empty structure if file missing/malformed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: JSON file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Malformed JSON in {file_path}: {e}")
            return {}
        except Exception as e:
            print(f"Warning: Error loading {file_path}: {e}")
            return {}
    
    def load_all(self) -> None:
        """Load all JSON data files.
        
        This method loads all data files and caches them in memory.
        Safe to call multiple times (will only load once).
        """
        try:
            data_dir = self._find_data_directory()
            
            # Load goods
            if self._goods is None:
                goods_file = data_dir / "goods" / "goods.json"
                goods_data = self._load_json_safe(goods_file)
                self._goods = goods_data.get("goods", [])
            
            # Load production chains
            if self._production_chains is None:
                chains_file = data_dir / "goods" / "production_chains.json"
                chains_data = self._load_json_safe(chains_file)
                self._production_chains = chains_data.get("production_chains", [])
            
            # Load facility categories
            if self._facility_categories is None:
                facilities_file = data_dir / "facilities" / "facility_flags.json"
                facilities_data = self._load_json_safe(facilities_file)
                self._facility_categories = facilities_data.get("categories", {})
            
            # Load population levels
            if self._population_levels is None:
                population_file = data_dir / "population" / "population_levels.json"
                population_data = self._load_json_safe(population_file)
                self._population_levels = population_data.get("population_levels", [])
        
        except Exception as e:
            print(f"Error in load_all: {e}")
            # Ensure we have empty structures even on error
            if self._goods is None:
                self._goods = []
            if self._production_chains is None:
                self._production_chains = []
            if self._facility_categories is None:
                self._facility_categories = {}
            if self._population_levels is None:
                self._population_levels = []
    
    def get_goods(self) -> List[Dict[str, Any]]:
        """Get list of all goods.
        
        Returns:
            List of goods dictionaries with keys: id, name, tier, cu
        """
        if self._goods is None:
            self.load_all()
        return self._goods or []
    
    def get_facility_categories(self) -> Dict[str, List[str]]:
        """Get facility categories.
        
        Returns:
            Dictionary mapping category names to lists of facility IDs
        """
        if self._facility_categories is None:
            self.load_all()
        return self._facility_categories or {}
    
    def get_population_levels(self) -> List[Dict[str, Any]]:
        """Get population levels.
        
        Returns:
            List of population level dictionaries with keys: id, label, min, max
        """
        if self._population_levels is None:
            self.load_all()
        return self._population_levels or []


# Global singleton instance
_data_loader = None


def get_data_loader() -> DataLoader:
    """Get the global DataLoader instance.
    
    Returns:
        The singleton DataLoader instance
    """
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
    return _data_loader
