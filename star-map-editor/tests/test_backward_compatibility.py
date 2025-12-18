#!/usr/bin/env python3
"""Integration test to verify backward compatibility with old features."""

import sys
from pathlib import Path
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import QPointF
from core.systems import SystemData
from core.routes import RouteData
from core.project_model import MapProject, TemplateData
from core.project_io import save_project, load_project


def test_complete_backward_compatibility():
    """Test that all old features still work with new fields present."""
    print("Testing Complete Backward Compatibility...")
    print("=" * 60)
    
    # Create a project with old-style data
    project = MapProject()
    project.metadata["name"] = "Backward Compatibility Test"
    
    # Add a template
    template = TemplateData.create_new("/path/to/image.png", (0, 0))
    project.templates.append(template)
    print("✓ Template added")
    
    # Add systems with only old fields (no planets, no fluff_text)
    system1 = SystemData.create_new("System 1", QPointF(100, 100))
    system1.population_id = "mid"
    system1.imports = ["goods-001", "goods-002"]
    system1.exports = ["goods-003"]
    system1.facilities = ["facility-001"]
    project.systems[system1.id] = system1
    print("✓ System 1 added with population, imports, exports, facilities")
    
    system2 = SystemData.create_new("System 2", QPointF(200, 200))
    system2.population_id = "low"
    project.systems[system2.id] = system2
    print("✓ System 2 added")
    
    # Add a route
    route = RouteData.create_new(
        name="Route 1",
        start_system_id=system1.id,
        end_system_id=system2.id
    )
    route.control_points = [(150, 150)]
    route.route_class = 2
    route.travel_type = "fast"
    route.hazards = ["pirates"]
    project.routes[route.id] = route
    print("✓ Route added with control points and stats")
    
    # Save the project
    with tempfile.NamedTemporaryFile(suffix='.swmproj', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Save
        assert save_project(project, temp_path), "Save failed"
        print("✓ Project saved successfully")
        
        # Load
        loaded = load_project(temp_path)
        assert loaded is not None, "Load failed"
        print("✓ Project loaded successfully")
        
        # Verify metadata
        assert loaded.metadata["name"] == "Backward Compatibility Test"
        print("✓ Metadata preserved")
        
        # Verify template
        assert len(loaded.templates) == 1
        assert loaded.templates[0].filepath == "/path/to/image.png"
        print("✓ Template preserved")
        
        # Verify systems
        assert len(loaded.systems) == 2
        s1 = loaded.systems[system1.id]
        assert s1.name == "System 1"
        assert s1.population_id == "mid"
        assert s1.imports == ["goods-001", "goods-002"]
        assert s1.exports == ["goods-003"]
        assert s1.facilities == ["facility-001"]
        # Verify new fields have default values
        assert len(s1.planets) == 0
        assert s1.fluff_text == ""
        print("✓ System 1 preserved with all old fields + new field defaults")
        
        s2 = loaded.systems[system2.id]
        assert s2.name == "System 2"
        assert s2.population_id == "low"
        assert len(s2.planets) == 0
        assert s2.fluff_text == ""
        print("✓ System 2 preserved with new field defaults")
        
        # Verify route
        assert len(loaded.routes) == 1
        r = loaded.routes[route.id]
        assert r.name == "Route 1"
        assert r.start_system_id == system1.id
        assert r.end_system_id == system2.id
        assert r.control_points == [(150, 150)]
        assert r.route_class == 2
        assert r.travel_type == "fast"
        assert r.hazards == ["pirates"]
        print("✓ Route preserved with all stats")
        
        print("\n" + "=" * 60)
        print("✅ ALL BACKWARD COMPATIBILITY TESTS PASSED!")
        print("=" * 60)
        return True
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_mixed_old_new_data():
    """Test mixing old and new features in the same project."""
    print("\nTesting Mixed Old and New Data...")
    print("=" * 60)
    
    project = MapProject()
    
    # System with only old data
    old_system = SystemData.create_new("Old System", QPointF(100, 100))
    old_system.population_id = "mid"
    old_system.imports = ["goods-001"]
    project.systems[old_system.id] = old_system
    print("✓ Old-style system added")
    
    # System with new data
    new_system = SystemData.create_new("New System", QPointF(200, 200))
    new_system.population_id = "established"
    new_system.fluff_text = "A system with new features."
    
    from core.systems import PlanetData, MoonData
    planet = PlanetData.create_new("New Planet")
    planet.moons.append(MoonData.create_new("New Moon"))
    new_system.planets.append(planet)
    project.systems[new_system.id] = new_system
    print("✓ New-style system added with planets and fluff text")
    
    # Save and load
    with tempfile.NamedTemporaryFile(suffix='.swmproj', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        assert save_project(project, temp_path), "Save failed"
        print("✓ Mixed project saved")
        
        loaded = load_project(temp_path)
        assert loaded is not None, "Load failed"
        print("✓ Mixed project loaded")
        
        # Verify old system
        old = loaded.systems[old_system.id]
        assert old.name == "Old System"
        assert len(old.planets) == 0
        assert old.fluff_text == ""
        print("✓ Old system preserved correctly")
        
        # Verify new system
        new = loaded.systems[new_system.id]
        assert new.name == "New System"
        assert new.fluff_text == "A system with new features."
        assert len(new.planets) == 1
        assert new.planets[0].name == "New Planet"
        assert len(new.planets[0].moons) == 1
        assert new.planets[0].moons[0].name == "New Moon"
        print("✓ New system preserved correctly")
        
        print("\n" + "=" * 60)
        print("✅ MIXED DATA TEST PASSED!")
        print("=" * 60)
        return True
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("BACKWARD COMPATIBILITY INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_complete_backward_compatibility()
        test_mixed_old_new_data()
        
        print("\n" + "=" * 60)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
