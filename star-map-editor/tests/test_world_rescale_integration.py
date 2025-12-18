#!/usr/bin/env python3
"""Integration test for world rescaling feature.

This script creates a test project, applies rescaling, and verifies the results.
"""

import sys
from pathlib import Path

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import QPointF
from core.systems import SystemData
from core.routes import RouteData
from core.templates import TemplateData
from core.project_model import MapProject


def create_test_project():
    """Create a test project with systems, routes, and templates."""
    project = MapProject()
    project.metadata["name"] = "Test World Rescaling Project"
    
    # Create systems
    system_a = SystemData.create_new("Alpha Station", QPointF(100.0, 100.0))
    system_b = SystemData.create_new("Beta Outpost", QPointF(300.0, 300.0))
    system_c = SystemData.create_new("Gamma Colony", QPointF(500.0, 100.0))
    
    project.systems[system_a.id] = system_a
    project.systems[system_b.id] = system_b
    project.systems[system_c.id] = system_c
    
    # Create routes with control points
    route1 = RouteData.create_new(
        "Alpha-Beta Lane",
        system_a.id,
        system_b.id,
        control_points=[(150.0, 150.0), (250.0, 250.0)]
    )
    
    route2 = RouteData.create_new(
        "Beta-Gamma Lane",
        system_b.id,
        system_c.id,
        control_points=[(400.0, 200.0)]
    )
    
    project.routes[route1.id] = route1
    project.routes[route2.id] = route2
    
    # Create templates
    template1 = TemplateData.create_new("/tmp/background.png", position=(0.0, 0.0))
    template1.scale = 1.0
    
    template2 = TemplateData.create_new("/tmp/overlay.png", position=(400.0, 400.0))
    template2.scale = 0.5
    
    project.templates.append(template1)
    project.templates.append(template2)
    
    return project


def verify_project_state(project, expected_state):
    """Verify that project state matches expected values."""
    systems = list(project.systems.values())
    routes = list(project.routes.values())
    templates = project.templates
    
    # Check system positions
    for i, system in enumerate(systems):
        expected_pos = expected_state['systems'][i]
        actual_x = round(system.position.x(), 2)
        actual_y = round(system.position.y(), 2)
        assert actual_x == expected_pos[0], f"System {i} X: expected {expected_pos[0]}, got {actual_x}"
        assert actual_y == expected_pos[1], f"System {i} Y: expected {expected_pos[1]}, got {actual_y}"
    
    # Check route control points
    for i, route in enumerate(routes):
        expected_points = expected_state['routes'][i]
        assert len(route.control_points) == len(expected_points), f"Route {i}: expected {len(expected_points)} points, got {len(route.control_points)}"
        for j, point in enumerate(route.control_points):
            actual_x = round(point[0], 2)
            actual_y = round(point[1], 2)
            assert actual_x == expected_points[j][0], f"Route {i} point {j} X: expected {expected_points[j][0]}, got {actual_x}"
            assert actual_y == expected_points[j][1], f"Route {i} point {j} Y: expected {expected_points[j][1]}, got {actual_y}"
    
    # Check template positions and scales
    for i, template in enumerate(templates):
        expected_template = expected_state['templates'][i]
        actual_x = round(template.position[0], 2)
        actual_y = round(template.position[1], 2)
        actual_scale = round(template.scale, 2)
        assert actual_x == expected_template['position'][0], f"Template {i} X: expected {expected_template['position'][0]}, got {actual_x}"
        assert actual_y == expected_template['position'][1], f"Template {i} Y: expected {expected_template['position'][1]}, got {actual_y}"
        assert actual_scale == expected_template['scale'], f"Template {i} scale: expected {expected_template['scale']}, got {actual_scale}"


def test_rescale_by_2_with_origin():
    """Test rescaling by factor 2.0 with origin anchor."""
    print("\nTest: Rescale by 2.0 with origin anchor, templates enabled")
    print("-" * 60)
    
    project = create_test_project()
    
    # Apply rescaling
    project.rescale_world(2.0, scale_templates=True, anchor_mode="origin")
    
    # Expected state after rescaling
    expected = {
        'systems': [
            (200.0, 200.0),  # Alpha: (100, 100) * 2
            (600.0, 600.0),  # Beta: (300, 300) * 2
            (1000.0, 200.0), # Gamma: (500, 100) * 2
        ],
        'routes': [
            [(300.0, 300.0), (500.0, 500.0)],  # Route1 control points * 2
            [(800.0, 400.0)],                   # Route2 control points * 2
        ],
        'templates': [
            {'position': (0.0, 0.0), 'scale': 2.0},    # Template1: (0, 0) * 2, scale 1.0 * 2
            {'position': (800.0, 800.0), 'scale': 1.0}, # Template2: (400, 400) * 2, scale 0.5 * 2
        ]
    }
    
    verify_project_state(project, expected)
    print("✓ All positions and scales correct")


def test_rescale_by_half_with_centroid():
    """Test rescaling by factor 0.5 with centroid anchor."""
    print("\nTest: Rescale by 0.5 with centroid anchor, templates disabled")
    print("-" * 60)
    
    project = create_test_project()
    
    # Centroid of systems: ((100+300+500)/3, (100+300+100)/3) = (300, 166.67)
    # Formula: p' = anchor + (p - anchor) * factor
    # Alpha: (300, 166.67) + ((100, 100) - (300, 166.67)) * 0.5
    #      = (300, 166.67) + (-200, -66.67) * 0.5
    #      = (300, 166.67) + (-100, -33.33)
    #      = (200, 133.34)
    
    project.rescale_world(0.5, scale_templates=False, anchor_mode="centroid")
    
    expected = {
        'systems': [
            (200.0, 133.33),   # Alpha
            (300.0, 233.33),   # Beta: (300, 166.67) + ((300, 300) - (300, 166.67)) * 0.5
            (400.0, 133.33),   # Gamma: (300, 166.67) + ((500, 100) - (300, 166.67)) * 0.5
        ],
        'routes': [
            # Route1 control points
            # (150, 150): (300, 166.67) + ((150, 150) - (300, 166.67)) * 0.5 = (225, 158.33)
            # (250, 250): (300, 166.67) + ((250, 250) - (300, 166.67)) * 0.5 = (275, 208.33)
            [(225.0, 158.33), (275.0, 208.33)],
            # Route2 control points
            # (400, 200): (300, 166.67) + ((400, 200) - (300, 166.67)) * 0.5 = (350, 183.33)
            [(350.0, 183.33)],
        ],
        'templates': [
            # Templates not affected when scale_templates=False
            {'position': (0.0, 0.0), 'scale': 1.0},
            {'position': (400.0, 400.0), 'scale': 0.5},
        ]
    }
    
    verify_project_state(project, expected)
    print("✓ All positions correct, templates unchanged")


def test_rescale_empty_project():
    """Test rescaling an empty project (should not crash)."""
    print("\nTest: Rescale empty project")
    print("-" * 60)
    
    project = MapProject()
    
    # Should not raise any errors
    project.rescale_world(2.0, scale_templates=True, anchor_mode="centroid")
    
    assert len(project.systems) == 0
    assert len(project.routes) == 0
    assert len(project.templates) == 0
    
    print("✓ Empty project handles rescaling gracefully")


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("World Rescaling Integration Tests")
    print("=" * 60)
    
    try:
        test_rescale_by_2_with_origin()
        test_rescale_by_half_with_centroid()
        test_rescale_empty_project()
        
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
