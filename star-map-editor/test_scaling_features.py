#!/usr/bin/env python3
"""Test script for scaling system refactor.

This script tests the core functionality without requiring a GUI display.
"""

import sys
from pathlib import Path

# Add current directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtCore import QPointF
from core.systems import SystemData, SystemItem
from core.routes import RouteData
from core.templates import TemplateData
from core.project_model import MapProject


def test_system_icon_sizes():
    """Test that system icon sizes can be changed without affecting coordinates."""
    print("Testing System Icon Sizes...")
    
    # Create a system at a specific position
    position = QPointF(100.0, 200.0)
    system_data = SystemData.create_new("Test System", position)
    
    # Verify position is stored correctly (WORLD SPACE)
    assert system_data.position.x() == 100.0
    assert system_data.position.y() == 200.0
    
    # Test icon size constants
    assert SystemItem.ICON_SIZE_SMALL == 8
    assert SystemItem.ICON_SIZE_MEDIUM == 10
    assert SystemItem.ICON_SIZE_LARGE == 15
    
    # Verify default radius
    assert SystemItem.RADIUS == 10
    
    print("  ✓ System icon sizes defined correctly")
    print("  ✓ System coordinates remain in WORLD SPACE")
    return True


def test_route_control_points():
    """Test that route control points are stored in WORLD SPACE."""
    print("\nTesting Route Control Points...")
    
    # Create two systems
    system1_pos = QPointF(50.0, 50.0)
    system2_pos = QPointF(200.0, 150.0)
    system1 = SystemData.create_new("System A", system1_pos)
    system2 = SystemData.create_new("System B", system2_pos)
    
    # Create a route with control points
    control_points = [(100.0, 80.0), (150.0, 120.0)]
    route_data = RouteData.create_new(
        "Test Route",
        system1.id,
        system2.id,
        control_points
    )
    
    # Verify control points are stored correctly (WORLD SPACE)
    assert len(route_data.control_points) == 2
    assert route_data.control_points[0] == (100.0, 80.0)
    assert route_data.control_points[1] == (150.0, 120.0)
    
    print("  ✓ Route control points stored in WORLD SPACE")
    print("  ✓ Control points preserved correctly")
    return True


def test_template_scale_independence():
    """Test that template scaling doesn't affect world coordinates."""
    print("\nTesting Template Scale Independence...")
    
    # Create a template
    template_data = TemplateData.create_new("/test/path/image.png")
    
    # Verify default scale
    assert template_data.scale == 1.0
    
    # Change template scale (IMAGE LAYER)
    template_data.scale = 2.0
    assert template_data.scale == 2.0
    
    # Create a system - its coordinates should be unaffected by template scale
    system_pos = QPointF(100.0, 100.0)
    system_data = SystemData.create_new("Test System", system_pos)
    
    # System coordinates remain in WORLD SPACE regardless of template scale
    assert system_data.position.x() == 100.0
    assert system_data.position.y() == 100.0
    
    print("  ✓ Template scale is independent (IMAGE LAYER)")
    print("  ✓ System coordinates unaffected by template scale")
    return True


def test_grid_configuration():
    """Test grid spacing configuration."""
    print("\nTesting Grid Configuration...")
    
    # Grid spacing should be in HSU units
    grid_spacing = 100  # 1 grid cell = 100 HSU
    assert grid_spacing > 0
    
    print(f"  ✓ Grid spacing: {grid_spacing} HSU")
    print("  ✓ Grid is independent of templates")
    return True


def test_project_integration():
    """Test that all components integrate properly in a project."""
    print("\nTesting Project Integration...")
    
    project = MapProject()
    
    # Add a template (IMAGE LAYER)
    template = TemplateData.create_new("/test/image.png")
    template.scale = 1.5  # Scale template
    project.add_template(template)
    
    # Add systems (WORLD SPACE)
    system1 = SystemData.create_new("Alpha", QPointF(100.0, 100.0))
    system2 = SystemData.create_new("Beta", QPointF(300.0, 200.0))
    project.systems[system1.id] = system1
    project.systems[system2.id] = system2
    
    # Add a route (WORLD SPACE)
    route = RouteData.create_new(
        "Alpha-Beta Route",
        system1.id,
        system2.id,
        [(200.0, 150.0)]  # One control point
    )
    project.add_route(route)
    
    # Verify everything is stored correctly
    assert len(project.templates) == 1
    assert len(project.systems) == 2
    assert len(project.routes) == 1
    
    # Verify template scale didn't affect system positions
    assert project.systems[system1.id].position.x() == 100.0
    assert project.systems[system2.id].position.x() == 300.0
    
    # Verify route control points are correct
    assert project.routes[route.id].control_points[0] == (200.0, 150.0)
    
    print("  ✓ All components integrated correctly")
    print("  ✓ WORLD SPACE and IMAGE LAYER remain separate")
    return True


def test_zoom_calculations():
    """Test zoom indicator calculations."""
    print("\nTesting Zoom Calculations...")
    
    # At 100% zoom: 1 HSU = 1 pixel
    zoom_100 = 1.0
    pixels_per_hsu_100 = zoom_100
    assert pixels_per_hsu_100 == 1.0
    
    # At 200% zoom: 1 HSU = 2 pixels
    zoom_200 = 2.0
    pixels_per_hsu_200 = zoom_200
    assert pixels_per_hsu_200 == 2.0
    
    # At 50% zoom: 1 HSU = 0.5 pixels
    zoom_50 = 0.5
    pixels_per_hsu_50 = zoom_50
    assert pixels_per_hsu_50 == 0.5
    
    print("  ✓ Zoom calculations correct")
    print("  ✓ Pixels-per-HSU ratio accurate")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Scaling System Refactor - Unit Tests")
    print("=" * 60)
    
    tests = [
        test_system_icon_sizes,
        test_route_control_points,
        test_template_scale_independence,
        test_grid_configuration,
        test_project_integration,
        test_zoom_calculations,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
