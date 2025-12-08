#!/usr/bin/env python3
"""
Test script for route editing functionality.
Tests the core logic without GUI dependencies.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock PySide6 modules for testing - must be done before any imports
class MockQPointF:
    def __init__(self, x=0, y=0):
        self._x = x
        self._y = y
    
    def x(self):
        return self._x
    
    def y(self):
        return self._y

class MockQt:
    pass

# Create mock modules
pyside6_module = type(sys)('PySide6')
qtcore_module = type(sys)('PySide6.QtCore')
qtwidgets_module = type(sys)('PySide6.QtWidgets')
qtgui_module = type(sys)('PySide6.QtGui')

# Add mock classes
qtcore_module.QPointF = MockQPointF
qtcore_module.Qt = MockQt
qtcore_module.Signal = lambda *a: None
qtcore_module.QRectF = object
qtcore_module.QTimer = object

qtwidgets_module.QGraphicsEllipseItem = object
qtwidgets_module.QGraphicsTextItem = object
qtwidgets_module.QDialog = object
qtwidgets_module.QVBoxLayout = object
qtwidgets_module.QHBoxLayout = object
qtwidgets_module.QLineEdit = object
qtwidgets_module.QPushButton = object
qtwidgets_module.QLabel = object
qtwidgets_module.QGraphicsPathItem = object
qtwidgets_module.QGraphicsPixmapItem = object

qtgui_module.QColor = lambda *a, **k: None
qtgui_module.QPen = lambda *a, **k: None
qtgui_module.QBrush = lambda *a, **k: None
qtgui_module.QFont = lambda *a, **k: None
qtgui_module.QPainterPath = type('QPainterPath', (), {'moveTo': lambda *a: None, 'lineTo': lambda *a: None})
qtgui_module.QPixmap = object
qtgui_module.QPainter = object
qtgui_module.QTransform = object

# Install mocks
sys.modules['PySide6'] = pyside6_module
sys.modules['PySide6.QtCore'] = qtcore_module
sys.modules['PySide6.QtWidgets'] = qtwidgets_module
sys.modules['PySide6.QtGui'] = qtgui_module

# Now import our modules
from core.routes import RouteData

def test_system_chain_basic():
    """Test basic system chain functionality."""
    print("Test 1: Basic system chain")
    
    # Create a simple route
    route = RouteData.create_new("Test Route", "sys1", "sys2")
    
    # Check default chain
    chain = route.get_system_chain()
    assert chain == ["sys1", "sys2"], f"Expected ['sys1', 'sys2'], got {chain}"
    print("✓ Default chain works")
    
    # Set a custom chain
    route.set_system_chain(["sys1", "sys2", "sys3"])
    chain = route.get_system_chain()
    assert chain == ["sys1", "sys2", "sys3"], f"Expected ['sys1', 'sys2', 'sys3'], got {chain}"
    assert route.start_system_id == "sys1"
    assert route.end_system_id == "sys3"
    print("✓ Setting system chain works")
    
    print("✅ Test 1 passed\n")

def test_insert_system():
    """Test inserting systems into route."""
    print("Test 2: Insert system into route")
    
    route = RouteData.create_new("Test Route", "sys1", "sys2")
    
    # Insert at beginning
    route.insert_system_at(0, "sys0")
    chain = route.get_system_chain()
    assert chain == ["sys0", "sys1", "sys2"], f"Expected ['sys0', 'sys1', 'sys2'], got {chain}"
    print("✓ Insert at beginning works")
    
    # Insert in middle
    route.insert_system_at(2, "sys1.5")
    chain = route.get_system_chain()
    assert chain == ["sys0", "sys1", "sys1.5", "sys2"], f"Expected ['sys0', 'sys1', 'sys1.5', 'sys2'], got {chain}"
    print("✓ Insert in middle works")
    
    # Insert at end
    route.insert_system_at(4, "sys3")
    chain = route.get_system_chain()
    assert chain == ["sys0", "sys1", "sys1.5", "sys2", "sys3"], f"Expected 5 systems, got {chain}"
    print("✓ Insert at end works")
    
    print("✅ Test 2 passed\n")

def test_remove_system():
    """Test removing systems from route."""
    print("Test 3: Remove system from route")
    
    route = RouteData.create_new("Test Route", "sys1", "sys2")
    route.set_system_chain(["sys1", "sys2", "sys3", "sys4"])
    
    # Remove from middle
    route.remove_system_at(1)
    chain = route.get_system_chain()
    assert chain == ["sys1", "sys3", "sys4"], f"Expected ['sys1', 'sys3', 'sys4'], got {chain}"
    print("✓ Remove from middle works")
    
    # Remove by ID
    route.remove_system_by_id("sys3")
    chain = route.get_system_chain()
    assert chain == ["sys1", "sys4"], f"Expected ['sys1', 'sys4'], got {chain}"
    print("✓ Remove by ID works")
    
    # Try to remove when only 2 systems (should fail)
    try:
        route.remove_system_at(0)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✓ Correctly prevents removal when route would be too short")
    
    print("✅ Test 3 passed\n")

def test_split_route():
    """Test splitting routes."""
    print("Test 4: Split route")
    
    route = RouteData.create_new("Main Route", "sys1", "sys5")
    route.set_system_chain(["sys1", "sys2", "sys3", "sys4", "sys5"])
    
    # Split at sys3
    new_route = route.split_at_system("sys3")
    
    # Check original route
    chain1 = route.get_system_chain()
    assert chain1 == ["sys1", "sys2", "sys3"], f"Expected ['sys1', 'sys2', 'sys3'], got {chain1}"
    print("✓ Original route correctly shortened")
    
    # Check new route
    chain2 = new_route.get_system_chain()
    assert chain2 == ["sys3", "sys4", "sys5"], f"Expected ['sys3', 'sys4', 'sys5'], got {chain2}"
    print("✓ New route correctly created")
    
    # Try to split at edges (should fail)
    route2 = RouteData.create_new("Test", "a", "c")
    route2.set_system_chain(["a", "b", "c"])
    
    result = route2.split_at_system("a")
    assert result is None, "Should not split at first system"
    
    result = route2.split_at_system("c")
    assert result is None, "Should not split at last system"
    print("✓ Correctly prevents splitting at edges")
    
    print("✅ Test 4 passed\n")

def test_merge_routes():
    """Test merging routes."""
    print("Test 5: Merge routes")
    
    # Test end-to-start merge
    route1 = RouteData.create_new("Route 1", "sys1", "sys3")
    route1.set_system_chain(["sys1", "sys2", "sys3"])
    
    route2 = RouteData.create_new("Route 2", "sys3", "sys5")
    route2.set_system_chain(["sys3", "sys4", "sys5"])
    
    merged = RouteData.merge_routes(route1, route2)
    assert merged is not None, "Should be able to merge"
    chain = merged.get_system_chain()
    assert chain == ["sys1", "sys2", "sys3", "sys4", "sys5"], f"Expected 5 systems, got {chain}"
    print("✓ End-to-start merge works")
    
    # Test end-to-end merge
    route3 = RouteData.create_new("Route 3", "sys10", "sys12")
    route3.set_system_chain(["sys10", "sys11", "sys12"])
    
    route4 = RouteData.create_new("Route 4", "sys14", "sys12")
    route4.set_system_chain(["sys14", "sys13", "sys12"])
    
    merged2 = RouteData.merge_routes(route3, route4)
    assert merged2 is not None, "Should be able to merge end-to-end"
    chain2 = merged2.get_system_chain()
    # Should be: route3 + reversed(route4 without last)
    assert chain2 == ["sys10", "sys11", "sys12", "sys13", "sys14"], f"Expected specific order, got {chain2}"
    print("✓ End-to-end merge works")
    
    # Test incompatible routes (should fail)
    route5 = RouteData.create_new("Route 5", "sysA", "sysB")
    route6 = RouteData.create_new("Route 6", "sysC", "sysD")
    
    merged3 = RouteData.merge_routes(route5, route6)
    assert merged3 is None, "Should not be able to merge incompatible routes"
    print("✓ Correctly rejects incompatible merges")
    
    print("✅ Test 5 passed\n")

def test_system_queries():
    """Test system query methods."""
    print("Test 6: System query methods")
    
    route = RouteData.create_new("Test Route", "sys1", "sys5")
    route.set_system_chain(["sys1", "sys2", "sys3", "sys4", "sys5"])
    
    # Test contains_system
    assert route.contains_system("sys1")
    assert route.contains_system("sys3")
    assert route.contains_system("sys5")
    assert not route.contains_system("sys99")
    print("✓ contains_system works")
    
    # Test get_system_index
    assert route.get_system_index("sys1") == 0
    assert route.get_system_index("sys3") == 2
    assert route.get_system_index("sys5") == 4
    assert route.get_system_index("sys99") == -1
    print("✓ get_system_index works")
    
    print("✅ Test 6 passed\n")

def main():
    """Run all tests."""
    print("=" * 60)
    print("ROUTE EDITING FUNCTIONALITY TESTS")
    print("=" * 60)
    print()
    
    try:
        test_system_chain_basic()
        test_insert_system()
        test_remove_system()
        test_split_route()
        test_merge_routes()
        test_system_queries()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
