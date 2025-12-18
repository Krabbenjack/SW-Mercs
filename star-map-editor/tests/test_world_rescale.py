#!/usr/bin/env python3
"""Test script for world rescaling feature.

This script tests the rescale_world functionality without requiring a GUI display.
"""

import sys
from pathlib import Path

# Add parent directory to path for core imports (star-map-editor/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import QPointF
from core.systems import SystemData
from core.routes import RouteData
from core.templates import TemplateData
from core.project_model import MapProject


def test_rescale_systems():
    """Test that system positions are scaled correctly."""
    print("Testing System Position Rescaling...")
    
    # Create a project with two systems
    project = MapProject()
    
    system1 = SystemData.create_new("System A", QPointF(100.0, 100.0))
    system2 = SystemData.create_new("System B", QPointF(200.0, 200.0))
    
    project.systems[system1.id] = system1
    project.systems[system2.id] = system2
    
    # Test scaling by 2.0 with origin anchor
    project.rescale_world(2.0, scale_templates=False, anchor_mode="origin")
    
    assert system1.position.x() == 200.0, f"Expected 200.0, got {system1.position.x()}"
    assert system1.position.y() == 200.0, f"Expected 200.0, got {system1.position.y()}"
    assert system2.position.x() == 400.0, f"Expected 400.0, got {system2.position.x()}"
    assert system2.position.y() == 400.0, f"Expected 400.0, got {system2.position.y()}"
    
    print("  ✓ Systems scaled correctly with origin anchor")
    
    # Test scaling by 0.5 with centroid anchor
    project.rescale_world(0.5, scale_templates=False, anchor_mode="centroid")
    
    # Centroid is at (300, 300)
    # system1 was at (200, 200), after scaling: 300 + (200 - 300) * 0.5 = 250
    # system2 was at (400, 400), after scaling: 300 + (400 - 300) * 0.5 = 350
    assert abs(system1.position.x() - 250.0) < 0.01, f"Expected 250.0, got {system1.position.x()}"
    assert abs(system1.position.y() - 250.0) < 0.01, f"Expected 250.0, got {system1.position.y()}"
    assert abs(system2.position.x() - 350.0) < 0.01, f"Expected 350.0, got {system2.position.x()}"
    assert abs(system2.position.y() - 350.0) < 0.01, f"Expected 350.0, got {system2.position.y()}"
    
    print("  ✓ Systems scaled correctly with centroid anchor")
    return True


def test_rescale_routes():
    """Test that route control points are scaled correctly."""
    print("\nTesting Route Control Point Rescaling...")
    
    project = MapProject()
    
    # Create systems
    system1 = SystemData.create_new("System A", QPointF(0.0, 0.0))
    system2 = SystemData.create_new("System B", QPointF(100.0, 100.0))
    
    project.systems[system1.id] = system1
    project.systems[system2.id] = system2
    
    # Create a route with control points
    route = RouteData.create_new(
        "Route 1",
        system1.id,
        system2.id,
        control_points=[(50.0, 25.0), (75.0, 75.0)]
    )
    project.routes[route.id] = route
    
    # Scale by 2.0 with origin
    project.rescale_world(2.0, scale_templates=False, anchor_mode="origin")
    
    assert route.control_points[0] == (100.0, 50.0), f"Expected (100.0, 50.0), got {route.control_points[0]}"
    assert route.control_points[1] == (150.0, 150.0), f"Expected (150.0, 150.0), got {route.control_points[1]}"
    
    print("  ✓ Route control points scaled correctly")
    return True


def test_rescale_templates():
    """Test that template positions and scales are adjusted correctly."""
    print("\nTesting Template Rescaling...")
    
    project = MapProject()
    
    # Create a template
    template = TemplateData.create_new("/tmp/test.png", position=(100.0, 100.0))
    template.scale = 1.0
    project.templates.append(template)
    
    # Scale by 2.0 with origin, with templates enabled
    project.rescale_world(2.0, scale_templates=True, anchor_mode="origin")
    
    assert template.position == (200.0, 200.0), f"Expected (200.0, 200.0), got {template.position}"
    assert template.scale == 2.0, f"Expected 2.0, got {template.scale}"
    
    print("  ✓ Template position and scale adjusted correctly")
    
    # Test with templates disabled
    project.rescale_world(0.5, scale_templates=False, anchor_mode="origin")
    
    # Position should not change, scale should not change
    assert template.position == (200.0, 200.0), f"Expected (200.0, 200.0), got {template.position}"
    assert template.scale == 2.0, f"Expected 2.0, got {template.scale}"
    
    print("  ✓ Templates not affected when scale_templates=False")
    return True


def test_centroid_calculation():
    """Test that centroid is calculated correctly when no systems exist."""
    print("\nTesting Centroid Fallback...")
    
    project = MapProject()
    
    # Add a template but no systems
    template = TemplateData.create_new("/tmp/test.png", position=(50.0, 50.0))
    template.scale = 1.0
    project.templates.append(template)
    
    # Scale with centroid mode (should fall back to origin since no systems)
    project.rescale_world(2.0, scale_templates=True, anchor_mode="centroid")
    
    assert template.position == (100.0, 100.0), f"Expected (100.0, 100.0), got {template.position}"
    
    print("  ✓ Centroid falls back to origin when no systems exist")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("World Rescaling Feature Tests")
    print("=" * 60)
    
    try:
        test_rescale_systems()
        test_rescale_routes()
        test_rescale_templates()
        test_centroid_calculation()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
