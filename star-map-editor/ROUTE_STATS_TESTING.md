# Route Stats Implementation Testing Guide

This document provides comprehensive manual testing procedures for the Route Stats feature implementation.

## Overview

The Route Stats feature adds a tabbed statistics inspector in Stats Mode that allows users to:
1. View and edit system statistics (existing feature, integrated into tabs)
2. View and edit route statistics (new feature)
3. Calculate travel times based on route parameters (new feature)

## Prerequisites

Before testing:
1. Ensure PySide6 is installed: `pip install -r requirements.txt`
2. Launch the application: `python main.py`
3. Have at least one template loaded and two systems placed for route creation

## Test Cases

### 1. Stats Mode Activation

**Objective**: Verify Stats Mode can be activated and displays the tabbed interface.

**Steps**:
1. Launch the application
2. Click the "Stats" button in the mode toolbar
3. Verify the stats sidebar appears on the right
4. Verify it contains three tabs: "System", "Route", and "Calculator"

**Expected Results**:
- Stats button turns green when active
- Stats sidebar appears with fixed width (260-320px)
- Map view maintains full height
- Three tabs are visible and clickable
- Default state shows "No system selected" or "No route selected" depending on active tab

---

### 2. System Stats Tab (Existing Functionality)

**Objective**: Ensure existing system stats functionality remains unchanged.

**Steps**:
1. Activate Stats Mode
2. Place or select a system on the map
3. Verify System tab is automatically selected
4. Edit system population
5. Edit system facilities
6. Edit system imports/exports

**Expected Results**:
- System tab automatically becomes active when system is selected
- System name displays correctly
- Population dropdown works
- Facilities, imports, and exports dialogs open and save correctly
- All changes are retained in the SystemData object

---

### 3. Route Stats Tab - Basic Display

**Objective**: Verify route stats display correctly when a route is selected.

**Steps**:
1. Create a route between two systems (in Routes Mode)
2. Switch to Stats Mode
3. Select the route
4. Verify Route tab is automatically selected

**Expected Results**:
- Route tab becomes active automatically
- Route name displays correctly
- Route length (HSU) shows calculated value > 0
- Route class shows default value of 3
- Travel type shows "Normal" (default)
- All hazard checkboxes are unchecked (default)

---

### 4. Route Stats Tab - Editing Route Class

**Objective**: Verify route class can be changed and persists.

**Steps**:
1. Select a route in Stats Mode
2. Change route class spinbox from 3 to 1 (fast route)
3. Click away and re-select the route
4. Verify the route class is still 1

**Expected Results**:
- Spinbox accepts values 1-5 only
- Value changes are immediately saved to RouteData
- Changes persist when route is deselected and re-selected

---

### 5. Route Stats Tab - Editing Travel Type

**Objective**: Verify travel type can be changed.

**Steps**:
1. Select a route in Stats Mode
2. Change travel type dropdown to "Express Lane"
3. Deselect and re-select the route

**Expected Results**:
- Dropdown shows four options: Normal, Express Lane, Ancient Hyperlane, Backwater
- Selected value is saved and persists
- Display names use proper capitalization (e.g., "Express Lane" not "express_lane")

---

### 6. Route Stats Tab - Editing Hazards

**Objective**: Verify hazards can be selected and deselected.

**Steps**:
1. Select a route in Stats Mode
2. Check the "Nebula" hazard checkbox
3. Check the "Pirate Activity" hazard checkbox
4. Deselect and re-select the route
5. Uncheck "Nebula"
6. Deselect and re-select the route again

**Expected Results**:
- Five hazard checkboxes are available: Nebula, Hypershadow, Quasar, Minefield, Pirate Activity
- Multiple hazards can be selected simultaneously
- Hazard selections persist when route is deselected/re-selected
- Unchecking a hazard removes it from the route's hazard list

---

### 7. Route Length Calculation

**Objective**: Verify route length is calculated correctly.

**Steps**:
1. Create a simple route between two systems
2. Note the route length in Stats Mode
3. Move one of the systems to increase the distance
4. Re-select the route and check the length

**Expected Results**:
- Length is displayed in HSU (Hyperspace Units)
- Length value is > 0 for valid routes
- Length updates when systems are moved
- For routes with control points, length includes the curved path

---

### 8. Calculator Tab - Basic Display

**Objective**: Verify calculator displays route information correctly.

**Steps**:
1. Select a route with modified stats (class 1, type Express Lane, hazards: Nebula)
2. Switch to Calculator tab manually

**Expected Results**:
- Calculator tab shows the same route name
- Hyperdrive dropdown is set to "x1" by default
- Route Information section displays:
  - Length: Matches the value from Route tab
  - Class: Shows the set value (e.g., "1")
  - Type: Shows the set value (e.g., "Express Lane")
  - Hazards: Lists active hazards or "None"
- Estimated Travel section shows calculated values

---

### 9. Calculator Tab - Hyperdrive Selection

**Objective**: Verify changing hyperdrive rating updates calculations.

**Steps**:
1. Select a route in Calculator tab
2. Note the current travel time
3. Change hyperdrive from x1 to x2
4. Note the new travel time

**Expected Results**:
- Four hyperdrive options available: x1, x2, x3, x4
- Travel time decreases when hyperdrive rating increases
- Travel time at x2 is approximately half of x1
- Speed factor remains constant when only hyperdrive changes

---

### 10. Calculator Tab - Speed Factor Calculation

**Objective**: Verify speed factor is calculated from route parameters.

**Steps**:
1. Create a route with class 3, type Normal, no hazards
2. Note the speed factor (should be close to 1.0x)
3. Change route class to 1 in Route tab
4. Return to Calculator tab and note the new speed factor
5. Add a hazard (e.g., Nebula) in Route tab
6. Return to Calculator tab and note the speed factor again

**Expected Results**:
- Speed factor for class 3, Normal, no hazards ≈ 1.0x
- Speed factor increases when route class improves (class 1 = faster)
- Speed factor decreases when hazards are added
- Calculator updates automatically when route stats change

---

### 11. Tab Switching - Selection-Driven

**Objective**: Verify tabs switch automatically based on selection.

**Steps**:
1. In Stats Mode, select a system
2. Verify System tab is active
3. Select a route
4. Verify Route tab becomes active
5. Select a system again
6. Verify System tab becomes active

**Expected Results**:
- Tab automatically switches to match selection type
- Previous tab settings are preserved (e.g., calculator hyperdrive selection)
- Manual tab switching is still possible after auto-switch

---

### 12. No Selection State

**Objective**: Verify behavior when nothing is selected.

**Steps**:
1. In Stats Mode, deselect all items (click on empty space)
2. Check System tab
3. Check Route tab
4. Check Calculator tab

**Expected Results**:
- System tab shows "No system selected"
- Route tab shows "No route selected"
- Calculator tab shows "No route selected"
- No crash or errors when no selection exists

---

### 13. Project Save/Load - Backward Compatibility

**Objective**: Verify old projects load without errors.

**Steps**:
1. Create a test project with routes (if you have an old .swmproj file without route stats, use that)
2. Save the project
3. Close and reopen the application
4. Load the saved project
5. Select a route and check its stats

**Expected Results**:
- Old projects without route_class, travel_type, hazards fields load successfully
- Routes from old projects have default values: class=3, type="normal", hazards=[]
- No errors or crashes during load
- All other project data (systems, templates, etc.) loads correctly

---

### 14. Project Save/Load - New Fields Persist

**Objective**: Verify new route stats fields are saved and loaded.

**Steps**:
1. Create a new project
2. Create a route
3. Set route class to 2, travel type to "Express Lane", add hazards "Nebula" and "Minefield"
4. Save the project
5. Close and reopen the application
6. Load the project
7. Select the route in Stats Mode

**Expected Results**:
- Route class is 2
- Travel type is "Express Lane"
- Hazards include "Nebula" and "Minefield"
- All settings are exactly as they were before save

---

### 15. Export Map Data

**Objective**: Verify route stats are included in exported JSON.

**Steps**:
1. Create a project with systems and routes
2. Set various route stats on different routes
3. Export map data (File → Export Map Data)
4. Open the exported JSON file in a text editor
5. Inspect the "routes" array

**Expected Results**:
- Each route object contains:
  - "route_class": integer value
  - "travel_type": string value
  - "hazards": array of strings
- Values match what was set in the editor
- JSON is valid and readable

---

### 16. Stress Test - Multiple Routes

**Objective**: Verify performance with many routes selected and edited.

**Steps**:
1. Create 10+ routes on the map
2. Select different routes and edit their stats
3. Switch between System and Route tabs
4. Use the calculator on different routes

**Expected Results**:
- No lag or performance issues
- Stats update instantly when selecting different routes
- Calculator recalculates quickly
- Memory usage remains stable

---

### 17. Edge Cases - Route with Control Points

**Objective**: Verify route length calculation with control points.

**Steps**:
1. Create a route between two systems
2. Add 2-3 control points to make it curved
3. Select the route in Stats Mode
4. Note the route length

**Expected Results**:
- Route length accounts for the curved path through control points
- Length is greater than the straight-line distance between systems
- Length updates when control points are moved

---

### 18. Edge Cases - Chain Routes

**Objective**: Verify stats work with multi-system chain routes (if implemented).

**Steps**:
1. If chain routes are supported, create a route: A → B → C
2. Select the chain route in Stats Mode
3. Check the route length

**Expected Results**:
- Route length is sum of all segments (A-B + B-C)
- Route stats apply to the entire chain
- No errors when selecting chain routes

---

### 19. UI Consistency - Dark Mode

**Objective**: Verify stats inspector looks correct in both light and dark modes.

**Steps**:
1. Open Stats Mode in dark mode (default)
2. Check all three tabs for readability
3. Switch to light mode (if available)
4. Check tabs again

**Expected Results**:
- All text is readable in both modes
- Controls (spinbox, combobox, checkboxes) are styled correctly
- No visual glitches or color mismatches

---

### 20. Integration - System Stats Unchanged

**Objective**: Final verification that system stats feature still works as before.

**Steps**:
1. Create several systems with different populations
2. Add facilities, imports, and exports to different systems
3. Switch between systems in Stats Mode
4. Verify all data is retained and displayed correctly

**Expected Results**:
- System stats functionality is identical to before
- No regressions or bugs in existing features
- System tab integrates seamlessly with new Route and Calculator tabs

---

## Console Error Check

After completing all tests:
1. Check the terminal/console for any Python errors or warnings
2. Verify no Qt warnings about missing properties or signals
3. Confirm no memory leaks or resource warnings

## Known Limitations / Future Work

- Travel time calculations use placeholder formulas and should be tuned for game balance
- Fuel estimate is a placeholder and not yet calculated
- Route stats are not validated (e.g., no min/max constraints on hazards)

## Test Results Summary

Record the results of each test case:

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | Stats Mode Activation | ☐ Pass ☐ Fail | |
| 2 | System Stats Tab | ☐ Pass ☐ Fail | |
| 3 | Route Stats Display | ☐ Pass ☐ Fail | |
| 4 | Route Class Editing | ☐ Pass ☐ Fail | |
| 5 | Travel Type Editing | ☐ Pass ☐ Fail | |
| 6 | Hazard Editing | ☐ Pass ☐ Fail | |
| 7 | Route Length Calc | ☐ Pass ☐ Fail | |
| 8 | Calculator Display | ☐ Pass ☐ Fail | |
| 9 | Hyperdrive Selection | ☐ Pass ☐ Fail | |
| 10 | Speed Factor Calc | ☐ Pass ☐ Fail | |
| 11 | Tab Switching | ☐ Pass ☐ Fail | |
| 12 | No Selection State | ☐ Pass ☐ Fail | |
| 13 | Backward Compatibility | ☐ Pass ☐ Fail | |
| 14 | New Fields Persist | ☐ Pass ☐ Fail | |
| 15 | Export Map Data | ☐ Pass ☐ Fail | |
| 16 | Multiple Routes | ☐ Pass ☐ Fail | |
| 17 | Routes with Control Points | ☐ Pass ☐ Fail | |
| 18 | Chain Routes | ☐ Pass ☐ Fail | |
| 19 | UI Consistency | ☐ Pass ☐ Fail | |
| 20 | System Stats Unchanged | ☐ Pass ☐ Fail | |

---

**Testing Completed By**: _________________  
**Date**: _________________  
**Version**: _________________
