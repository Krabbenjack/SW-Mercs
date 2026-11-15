# Stats Tab Implementation - Manual Testing Guide

This document provides step-by-step instructions for manually testing the new Stats Tab feature.

## Prerequisites
- The application should be running (`python main.py`)
- Load or create a project with at least one system

## Test 1: Stats Tab Activation

### Steps:
1. Launch the application
2. Load a template (Template Mode → Load Template)
3. Switch to Systems Mode and create at least one system
4. Click the "Stats" button in the top toolbar

### Expected Results:
- ✓ Stats button becomes highlighted (green background)
- ✓ Stats tab widget appears below the map view
- ✓ If no system is selected: shows "No system selected" message
- ✓ Map view remains visible and functional

## Test 2: System Selection in Stats Tab

### Steps:
1. Ensure Stats tab is active
2. Click on a system in the map view to select it

### Expected Results:
- ✓ Stats widget updates to show the selected system
- ✓ System name is displayed at the top
- ✓ Population dropdown shows current value (or "No population")
- ✓ Facilities summary shows "0 facilities" or current count
- ✓ Imports summary shows "0 goods" or current count
- ✓ Exports summary shows "0 goods" or current count

## Test 3: Population Selection

### Steps:
1. Select a system in Stats tab
2. Click the Population dropdown
3. Select a population level (e.g., "Mittel" or "Niedrig")
4. Switch to another system and back

### Expected Results:
- ✓ Dropdown shows all population levels from population_levels.json
- ✓ Selection updates immediately
- ✓ Population persists when switching between systems
- ✓ Population persists when saving/loading project

## Test 4: Facilities Editor

### Steps:
1. Select a system in Stats tab
2. Click "Edit Facilities..." button
3. Observe the tabbed dialog that opens
4. Switch between different tabs (Industry, Space Ops, Military, etc.)
5. Check several facility checkboxes
6. Click "OK"

### Expected Results:
- ✓ Dialog opens with multiple tabs (one per category)
- ✓ Each tab contains checkboxes for facilities in that category
- ✓ Facility names are readable (e.g., "Mining Facility" not "mining_facility")
- ✓ Checked facilities persist when reopening dialog
- ✓ Facilities count updates in summary label
- ✓ Cancel button discards changes
- ✓ OK button saves changes

## Test 5: Imports Editor

### Steps:
1. Select a system in Stats tab
2. Click "Edit Imports..." button
3. Observe the goods selection dialog
4. Try typing in the search box to filter goods
5. Select multiple goods using Ctrl+Click or Shift+Click
6. Click "OK"

### Expected Results:
- ✓ Dialog opens titled "Edit Imports"
- ✓ Shows list of all goods with tier information
- ✓ Search box filters goods by name
- ✓ Multi-select works (Ctrl+Click)
- ✓ Selected goods persist when reopening dialog
- ✓ Imports count updates in summary label
- ✓ Cancel button discards changes
- ✓ OK button saves changes

## Test 6: Exports Editor

### Steps:
1. Select a system in Stats tab
2. Click "Edit Exports..." button
3. Follow similar steps as Test 5

### Expected Results:
- ✓ Dialog opens titled "Edit Exports"
- ✓ Same functionality as Imports editor
- ✓ Separate from imports (can have different selections)

## Test 7: Mode Switching

### Steps:
1. Configure stats for a system
2. Switch to Template Mode
3. Switch back to Stats tab
4. Select the same system

### Expected Results:
- ✓ Stats tab hides when switching to Template Mode
- ✓ Stats tab reappears when clicking Stats button
- ✓ All configured stats are preserved

## Test 8: Save and Load Project

### Steps:
1. Create a system with:
   - Population: "Mittel"
   - Facilities: "Mining Facility", "Refinery"
   - Imports: "Ore", "Gas"
   - Exports: "Metal Bars"
2. Save the project (File → Save Project)
3. Close the application
4. Restart and load the project
5. Switch to Stats tab and select the system

### Expected Results:
- ✓ Project saves without errors
- ✓ Project loads without errors
- ✓ All stats are preserved:
  - Population is correct
  - All facilities are checked
  - All imports are selected
  - All exports are selected

## Test 9: Backward Compatibility

### Steps:
1. Load a project file created before the stats feature
2. Switch to Stats tab
3. Select a system

### Expected Results:
- ✓ Old project loads without errors or warnings
- ✓ Systems show default empty stats:
  - Population: "(No population)"
  - Facilities: "0 facilities"
  - Imports: "0 goods"
  - Exports: "0 goods"

## Test 10: Export Map Data

### Steps:
1. Configure stats for at least one system
2. Export map data (File → Export Map Data)
3. Open the exported JSON file in a text editor

### Expected Results:
- ✓ Export succeeds without errors
- ✓ Exported JSON includes stat fields for systems:
  ```json
  {
    "id": "system-001",
    "name": "Test System",
    "x": 100.0,
    "y": 200.0,
    "population_id": "mid",
    "imports": ["ore", "gas"],
    "exports": ["metal_bars"],
    "facilities": ["mining_facility", "refinery"]
  }
  ```

## Test 11: Regression Testing

### Steps:
1. Test Template Mode:
   - Load templates
   - Move/scale/rotate templates
   - Adjust opacity
2. Test Systems Mode:
   - Create new systems
   - Edit system names
   - Delete systems
   - Move systems
3. Test Routes Mode:
   - Create routes between systems
   - Edit routes
   - Delete routes

### Expected Results:
- ✓ All existing features work as before
- ✓ No new UI elements appear in Systems Mode
- ✓ No crashes or errors
- ✓ Stats remain independent of these operations

## Common Issues to Check

1. **Empty State Handling**
   - Stats tab with no selection
   - System with no stats configured
   - Empty dropdowns/lists

2. **Data Validation**
   - Very long facility/goods lists
   - Special characters in system names
   - Edge case population levels

3. **UI Responsiveness**
   - Large numbers of systems
   - Rapid mode switching
   - Dialog open/close cycling

4. **Cross-Feature Integration**
   - Stats persist when system is renamed
   - Stats persist when system is moved
   - Stats cleared when system is deleted

## Reporting Issues

When reporting issues, please include:
- Steps to reproduce
- Expected vs. actual behavior
- Screenshots if UI-related
- Project file if possible
- Console output/errors
