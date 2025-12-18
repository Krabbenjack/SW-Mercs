#!/usr/bin/env python3
"""Test script for new system stats features (planets, moons, fluff text)."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import QPointF
from core.systems import SystemData, PlanetData, MoonData
from core.project_model import MapProject
from core.project_io import save_project, load_project
from core.data_loader import get_data_loader, format_population
import tempfile


def test_planet_moon_creation():
    """Test creating planets and moons."""
    print("Testing Planet and Moon Creation...")
    
    # Create a planet with moons
    planet = PlanetData.create_new("Coruscant Prime")
    assert planet.id is not None
    assert planet.name == "Coruscant Prime"
    assert len(planet.moons) == 0
    
    # Add moons
    moon1 = MoonData.create_new("Hesperidium")
    moon2 = MoonData.create_new("Centax-1")
    planet.moons.extend([moon1, moon2])
    
    assert len(planet.moons) == 2
    assert planet.moons[0].name == "Hesperidium"
    assert planet.moons[1].name == "Centax-1"
    
    print("  ✓ Planets and moons created successfully")
    return True


def test_system_with_planets():
    """Test creating a system with planets."""
    print("\nTesting System with Planets...")
    
    # Create a system
    system = SystemData.create_new("Coruscant", QPointF(100, 200))
    
    # Add planets
    planet1 = PlanetData.create_new("Coruscant Prime")
    planet1.moons.append(MoonData.create_new("Hesperidium"))
    planet1.moons.append(MoonData.create_new("Centax-1"))
    
    planet2 = PlanetData.create_new("Coruscant Minor")
    
    system.planets.extend([planet1, planet2])
    
    assert len(system.planets) == 2
    assert system.planets[0].name == "Coruscant Prime"
    assert len(system.planets[0].moons) == 2
    assert system.planets[1].name == "Coruscant Minor"
    assert len(system.planets[1].moons) == 0
    
    print("  ✓ System with planets created successfully")
    return True


def test_fluff_text():
    """Test fluff text field."""
    print("\nTesting Fluff Text...")
    
    system = SystemData.create_new("Tatooine", QPointF(50, 75))
    
    # Set fluff text
    fluff = "A harsh desert world in the Outer Rim, home to moisture farmers and scoundrels."
    system.fluff_text = fluff
    
    assert system.fluff_text == fluff
    assert len(system.fluff_text) < 500
    
    print("  ✓ Fluff text set successfully")
    return True


def test_save_load_roundtrip():
    """Test saving and loading a project with new features."""
    print("\nTesting Save/Load Roundtrip...")
    
    # Create a project with systems containing planets
    project = MapProject()
    
    # System 1: Coruscant with multiple planets and moons
    system1 = SystemData.create_new("Coruscant", QPointF(100, 100))
    system1.population_id = "galactic_capital"
    system1.fluff_text = "Capital of the Galactic Republic and later the Empire."
    
    planet1 = PlanetData.create_new("Coruscant Prime")
    planet1.moons.append(MoonData.create_new("Hesperidium"))
    planet1.moons.append(MoonData.create_new("Centax-1"))
    
    planet2 = PlanetData.create_new("Coruscant Minor")
    planet2.moons.append(MoonData.create_new("Centax-2"))
    
    system1.planets.extend([planet1, planet2])
    project.systems[system1.id] = system1
    
    # System 2: Simple system with no planets
    system2 = SystemData.create_new("Tatooine", QPointF(200, 150))
    system2.population_id = "low"
    system2.fluff_text = "Desert world in the Outer Rim."
    project.systems[system2.id] = system2
    
    # System 3: System with planets but no moons
    system3 = SystemData.create_new("Naboo", QPointF(150, 50))
    system3.population_id = "established"
    planet3 = PlanetData.create_new("Naboo")
    system3.planets.append(planet3)
    project.systems[system3.id] = system3
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.swmproj', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Save
        result = save_project(project, temp_path)
        assert result, "Save failed"
        print("  ✓ Project saved successfully")
        
        # Load
        loaded_project = load_project(temp_path)
        assert loaded_project is not None, "Load failed"
        print("  ✓ Project loaded successfully")
        
        # Verify systems
        assert len(loaded_project.systems) == 3
        print("  ✓ Correct number of systems loaded")
        
        # Verify System 1 (Coruscant)
        loaded_system1 = loaded_project.systems[system1.id]
        assert loaded_system1.name == "Coruscant"
        assert loaded_system1.population_id == "galactic_capital"
        assert loaded_system1.fluff_text == "Capital of the Galactic Republic and later the Empire."
        assert len(loaded_system1.planets) == 2
        assert loaded_system1.planets[0].name == "Coruscant Prime"
        assert len(loaded_system1.planets[0].moons) == 2
        assert loaded_system1.planets[0].moons[0].name == "Hesperidium"
        assert loaded_system1.planets[1].name == "Coruscant Minor"
        assert len(loaded_system1.planets[1].moons) == 1
        print("  ✓ System 1 (Coruscant) verified with all planets and moons")
        
        # Verify System 2 (Tatooine)
        loaded_system2 = loaded_project.systems[system2.id]
        assert loaded_system2.name == "Tatooine"
        assert loaded_system2.population_id == "low"
        assert loaded_system2.fluff_text == "Desert world in the Outer Rim."
        assert len(loaded_system2.planets) == 0
        print("  ✓ System 2 (Tatooine) verified with no planets")
        
        # Verify System 3 (Naboo)
        loaded_system3 = loaded_project.systems[system3.id]
        assert loaded_system3.name == "Naboo"
        assert len(loaded_system3.planets) == 1
        assert loaded_system3.planets[0].name == "Naboo"
        assert len(loaded_system3.planets[0].moons) == 0
        print("  ✓ System 3 (Naboo) verified with planet but no moons")
        
        return True
        
    finally:
        # Clean up
        if temp_path.exists():
            temp_path.unlink()


def test_backward_compatibility():
    """Test loading old project files without new fields."""
    print("\nTesting Backward Compatibility...")
    
    # Create an old-style project JSON (without planets and fluff_text)
    old_project_json = """{
        "metadata": {"name": "Old Map", "version": "1.0"},
        "templates": [],
        "systems": [
            {
                "id": "system-001",
                "name": "Old System",
                "x": 100,
                "y": 200,
                "population_id": "mid"
            }
        ],
        "routes": [],
        "route_groups": [],
        "zones": []
    }"""
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.swmproj', delete=False, mode='w') as f:
        f.write(old_project_json)
        temp_path = Path(f.name)
    
    try:
        # Load the old project
        loaded_project = load_project(temp_path)
        assert loaded_project is not None, "Failed to load old project"
        print("  ✓ Old project loaded successfully")
        
        # Verify system loaded with default values for new fields
        assert len(loaded_project.systems) == 1
        system = list(loaded_project.systems.values())[0]
        assert system.name == "Old System"
        assert system.population_id == "mid"
        assert len(system.planets) == 0, "Old project should have empty planets list"
        assert system.fluff_text == "", "Old project should have empty fluff_text"
        print("  ✓ Old project has correct default values for new fields")
        
        return True
        
    finally:
        # Clean up
        if temp_path.exists():
            temp_path.unlink()


def test_population_formatting():
    """Test population value formatting."""
    print("\nTesting Population Formatting...")
    
    assert format_population(None) == ""
    assert format_population(0) == ""
    assert format_population(1234) == "1.2K"
    assert format_population(50_000) == "50K"
    assert format_population(1_000_000) == "1M"
    assert format_population(500_000_000) == "500M"
    assert format_population(1_200_000_000) == "1.2B"
    assert format_population(50_000_000_000) == "50B"
    assert format_population(1_500_000_000_000) == "1.5T"
    
    print("  ✓ Population formatting works correctly")
    return True


def test_population_value_retrieval():
    """Test retrieving population values from data loader."""
    print("\nTesting Population Value Retrieval...")
    
    data_loader = get_data_loader()
    
    # Test uninhabited
    value = data_loader.get_population_value("uninhabited")
    assert value == 0 or value is None
    print(f"  ✓ Uninhabited: {value}")
    
    # Test galactic capital (should be very large)
    value = data_loader.get_population_value("galactic_capital")
    assert value is not None
    assert value > 1_000_000_000_000
    print(f"  ✓ Galactic capital: {format_population(value)}")
    
    # Test mid population
    value = data_loader.get_population_value("mid")
    assert value is not None
    assert 500_000_000 <= value <= 1_000_000_000
    print(f"  ✓ Mid population: {format_population(value)}")
    
    # Test None
    value = data_loader.get_population_value(None)
    assert value is None
    print("  ✓ None returns None")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing New System Stats Features")
    print("=" * 60)
    
    tests = [
        test_planet_moon_creation,
        test_system_with_planets,
        test_fluff_text,
        test_population_formatting,
        test_population_value_retrieval,
        test_save_load_roundtrip,
        test_backward_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
