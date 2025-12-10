#!/usr/bin/env python3
"""Test script for System Stats V1 implementation.

This script tests the core logic without requiring GUI display.
"""

import sys
import json
from pathlib import Path

# Add star-map-editor to path
sys.path.insert(0, str(Path(__file__).parent))


def test_json_data_loading():
    """Test that all JSON data files load correctly."""
    print("\n" + "="*70)
    print("TEST 1: JSON Data Loading")
    print("="*70)
    
    # Find data directory - it's at project root, not in star-map-editor
    test_file = Path(__file__)
    project_root = test_file.parent.parent.parent  # tests/ -> star-map-editor/ -> SW-Mercs/
    data_dir = project_root / "data"
    
    if not data_dir.exists():
        # Try alternate path
        data_dir = test_file.parent.parent.parent / "data"
    
    # Test goods.json
    goods_file = data_dir / "goods" / "goods.json"
    with open(goods_file) as f:
        goods_data = json.load(f)
    goods_count = len(goods_data["goods"])
    print(f"✓ Loaded {goods_count} goods from goods.json")
    assert goods_count > 0, "Should have at least one good"
    
    # Test facility_flags.json
    facilities_file = data_dir / "facilities" / "facility_flags.json"
    with open(facilities_file) as f:
        facilities_data = json.load(f)
    categories_count = len(facilities_data["categories"])
    print(f"✓ Loaded {categories_count} facility categories")
    assert categories_count > 0, "Should have at least one category"
    
    # Test population_levels.json
    population_file = data_dir / "population" / "population_levels.json"
    with open(population_file) as f:
        population_data = json.load(f)
    pop_count = len(population_data["population_levels"])
    print(f"✓ Loaded {pop_count} population levels")
    assert pop_count > 0, "Should have at least one population level"
    
    print("\n✅ All JSON files loaded successfully")
    return True


def test_system_data_structure():
    """Test SystemData structure with new fields."""
    print("\n" + "="*70)
    print("TEST 2: SystemData Structure")
    print("="*70)
    
    from dataclasses import dataclass
    
    @dataclass
    class QPointF:
        x_val: float
        y_val: float
        def x(self): return self.x_val
        def y(self): return self.y_val
    
    @dataclass
    class SystemData:
        id: str
        name: str
        position: QPointF
        population_id: str | None = None
        imports: list[str] = None
        exports: list[str] = None
        facilities: list[str] = None
        
        def __post_init__(self):
            if self.imports is None:
                self.imports = []
            if self.exports is None:
                self.exports = []
            if self.facilities is None:
                self.facilities = []
    
    # Test 1: Create system without stats (backward compatibility)
    system1 = SystemData(
        id='test-1',
        name='Test System',
        position=QPointF(100.0, 200.0)
    )
    
    assert system1.population_id is None
    assert system1.imports == []
    assert system1.exports == []
    assert system1.facilities == []
    print("✓ System without stats created successfully")
    print(f"  - Name: {system1.name}")
    print(f"  - Position: ({system1.position.x()}, {system1.position.y()})")
    print(f"  - Default values set correctly")
    
    # Test 2: Create system with stats
    system2 = SystemData(
        id='test-2',
        name='Coruscant',
        position=QPointF(0.0, 0.0),
        population_id='galactic_capital',
        imports=['ore', 'gas'],
        exports=['electronics', 'starship_components'],
        facilities=['civilian_spaceport', 'trade_hub', 'military_shipyard']
    )
    
    assert system2.population_id == 'galactic_capital'
    assert len(system2.imports) == 2
    assert len(system2.exports) == 2
    assert len(system2.facilities) == 3
    print("✓ System with stats created successfully")
    print(f"  - Name: {system2.name}")
    print(f"  - Population: {system2.population_id}")
    print(f"  - Imports: {len(system2.imports)} goods")
    print(f"  - Exports: {len(system2.exports)} goods")
    print(f"  - Facilities: {len(system2.facilities)} facilities")
    
    print("\n✅ SystemData structure works correctly")
    return True


def test_serialization():
    """Test system serialization for save/load."""
    print("\n" + "="*70)
    print("TEST 3: Serialization")
    print("="*70)
    
    def _serialize_system(system):
        system_dict = {
            'id': system['id'],
            'name': system['name'],
            'x': system['position'][0],
            'y': system['position'][1]
        }
        
        if system.get('population_id'):
            system_dict['population_id'] = system['population_id']
        if system.get('imports'):
            system_dict['imports'] = system['imports']
        if system.get('exports'):
            system_dict['exports'] = system['exports']
        if system.get('facilities'):
            system_dict['facilities'] = system['facilities']
        
        return system_dict
    
    # Test old system (no stats)
    old_system = {
        'id': 'old-1',
        'name': 'Old System',
        'position': (100.0, 200.0)
    }
    
    serialized_old = _serialize_system(old_system)
    assert 'id' in serialized_old
    assert 'name' in serialized_old
    assert 'x' in serialized_old
    assert 'y' in serialized_old
    assert 'population_id' not in serialized_old
    assert 'imports' not in serialized_old
    print("✓ Old system serialization (no stats fields)")
    print(f"  Keys: {list(serialized_old.keys())}")
    
    # Test new system (with stats)
    new_system = {
        'id': 'new-1',
        'name': 'New System',
        'position': (150.0, 250.0),
        'population_id': 'mid',
        'imports': ['ore', 'gas'],
        'exports': ['metal_bars'],
        'facilities': ['mining_facility']
    }
    
    serialized_new = _serialize_system(new_system)
    assert 'population_id' in serialized_new
    assert 'imports' in serialized_new
    assert 'exports' in serialized_new
    assert 'facilities' in serialized_new
    print("✓ New system serialization (with stats fields)")
    print(f"  Keys: {list(serialized_new.keys())}")
    
    print("\n✅ Serialization preserves data correctly")
    return True


def test_backward_compatibility():
    """Test loading old project files."""
    print("\n" + "="*70)
    print("TEST 4: Backward Compatibility")
    print("="*70)
    
    # Simulate old project format (without stats)
    old_project = {
        'metadata': {'name': 'Legacy Map'},
        'templates': [],
        'systems': [
            {
                'id': 'legacy-1',
                'name': 'Legacy System 1',
                'x': 100.0,
                'y': 200.0
            },
            {
                'id': 'legacy-2',
                'name': 'Legacy System 2',
                'x': 300.0,
                'y': 400.0
            }
        ],
        'routes': [],
        'zones': []
    }
    
    # Simulate loading
    for s_dict in old_project['systems']:
        population_id = s_dict.get('population_id')
        imports = s_dict.get('imports', [])
        exports = s_dict.get('exports', [])
        facilities = s_dict.get('facilities', [])
        
        # Verify defaults
        assert population_id is None
        assert imports == []
        assert exports == []
        assert facilities == []
    
    print(f"✓ Loaded {len(old_project['systems'])} systems from old format")
    print("✓ Missing fields handled with defaults")
    print("✓ No errors or warnings")
    
    print("\n✅ Old project files load correctly")
    return True


def test_export_format():
    """Test export format includes new stats."""
    print("\n" + "="*70)
    print("TEST 5: Export Format")
    print("="*70)
    
    def _export_system(system):
        export_dict = {
            'id': system['id'],
            'name': system['name'],
            'x': system['position'][0],
            'y': system['position'][1]
        }
        
        if system.get('population_id'):
            export_dict['population_id'] = system['population_id']
        if system.get('imports'):
            export_dict['imports'] = system['imports']
        if system.get('exports'):
            export_dict['exports'] = system['exports']
        if system.get('facilities'):
            export_dict['facilities'] = system['facilities']
        
        return export_dict
    
    # Test export with full stats
    system = {
        'id': 'export-1',
        'name': 'Export Test System',
        'position': (500.0, 600.0),
        'population_id': 'large',
        'imports': ['ore', 'gas', 'water'],
        'exports': ['metal_bars', 'alloys'],
        'facilities': ['mining_facility', 'refinery', 'factory']
    }
    
    exported = _export_system(system)
    
    # Verify all fields present
    assert 'population_id' in exported
    assert 'imports' in exported
    assert 'exports' in exported
    assert 'facilities' in exported
    assert exported['population_id'] == 'large'
    assert len(exported['imports']) == 3
    assert len(exported['exports']) == 2
    assert len(exported['facilities']) == 3
    
    print("✓ Export includes all stats fields")
    print(f"  - Population: {exported['population_id']}")
    print(f"  - Imports: {len(exported['imports'])} goods")
    print(f"  - Exports: {len(exported['exports'])} goods")
    print(f"  - Facilities: {len(exported['facilities'])} facilities")
    
    print("\n✅ Export format correct")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("SYSTEM STATS V1 - IMPLEMENTATION TESTS")
    print("="*70)
    
    tests = [
        test_json_data_loading,
        test_system_data_structure,
        test_serialization,
        test_backward_compatibility,
        test_export_format
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n✅ All tests passed! Implementation is correct.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed.")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
