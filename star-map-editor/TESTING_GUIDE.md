# Comprehensive Testing Guide - Route Control Point System

## Overview
This document provides step-by-step instructions for testing all route control point features, including the newly implemented control point deletion and improved handle interaction.

## Setup

### Prerequisites
- Python 3.10+
- PySide6 installed (`pip install -r requirements.txt`)
- A test image for background (any PNG/JPG)

### Running the Application
```bash
cd star-map-editor
python main.py
```

---

## Test Suite

### Test 1: Basic Application Launch
**Objective**: Verify application launches without errors

1. Launch the application with `python main.py`
2. **Expected**: Application window opens
3. **Expected**: No error messages in console
4. **Expected**: Dark mode is active by default
5. **Expected**: Status bar shows "Ready"

✅ **Pass Criteria**: Application launches cleanly

---

### Test 2: Create Basic Route
**Objective**: Verify routes are created as straight lines

1. Click "Template Mode" and load a background image
2. Switch to "Systems Mode"
3. Place 2 systems on the map (left-click, enter names)
4. Switch to "Routes" mode
5. Click first system, then click second system
6. **Expected**: Route appears as straight line connecting systems
7. **Expected**: Route is light blue color
8. **Expected**: No control points are added automatically

✅ **Pass Criteria**: Route is straight line, no automatic control points

---

### Test 3: Add Control Points with P + Click
**Objective**: Verify P + Click inserts control points correctly

1. Continue from Test 2 with a route
2. Press and hold **P** key
3. While holding P, click near the middle of the route
4. **Expected**: Orange control point handle appears at click position
5. **Expected**: Route curves to pass through the control point
6. Release P key
7. Press P again and click near 25% along the route
8. **Expected**: Second control point inserted before first one
9. **Expected**: Route curves smoothly through both points

✅ **Pass Criteria**: Control points inserted at correct positions

---

### Test 4: Drag Control Point Handles
**Objective**: Verify handles are draggable

1. Select the route (click on it)
2. **Expected**: Orange handles appear at each control point
3. **Expected**: Handles have white borders
4. **Expected**: Handles are clearly visible, not obscured
5. Click and drag one handle to a new position
6. **Expected**: Handle moves smoothly
7. **Expected**: Route updates in real-time during drag
8. Release mouse
9. **Expected**: Control point stays at new position
10. **Expected**: Route maintains smooth curve
11. **Expected**: Window title shows asterisk (*) for unsaved changes

✅ **Pass Criteria**: Handles drag smoothly, route updates correctly

---

### Test 5: Select Control Point Handles
**Objective**: Verify handles can be selected independently

1. Select a route with control points
2. Click on one of the orange handles
3. **Expected**: Handle turns RED when selected
4. **Expected**: Only the clicked handle changes color
5. Click on another handle
6. **Expected**: Previous handle returns to orange
7. **Expected**: New handle turns red
8. Click on empty space
9. **Expected**: All handles return to orange

✅ **Pass Criteria**: Handle selection works, visual feedback is clear

---

### Test 6: Delete Control Point with Delete Key
**Objective**: Verify control point deletion works

1. Select a route with multiple control points
2. Click on one control point handle to select it (turns red)
3. Press **Delete** key
4. **Expected**: Selected control point is removed
5. **Expected**: Remaining handles renumber correctly
6. **Expected**: Route recalculates without the deleted point
7. **Expected**: Window title shows asterisk (*) for unsaved changes

✅ **Pass Criteria**: Control point deleted, route updates correctly

---

### Test 7: Delete Control Point with Backspace Key
**Objective**: Verify Backspace also deletes control points

1. Select a route with control points
2. Click on a control point handle to select it
3. Press **Backspace** key
4. **Expected**: Same behavior as Delete key
5. **Expected**: Control point removed, route updates

✅ **Pass Criteria**: Backspace works same as Delete

---

### Test 8: Delete Last Control Point
**Objective**: Verify edge case of deleting all control points

1. Create a route with only one control point
2. Select the route
3. Click the single handle to select it
4. Press Delete
5. **Expected**: Control point removed
6. **Expected**: Route returns to straight line
7. **Expected**: No handles remain (since no control points)

✅ **Pass Criteria**: Route reverts to straight line when no control points

---

### Test 9: Handle Visibility on Selection
**Objective**: Verify handles appear/disappear correctly

1. Create route with control points
2. Click on route to select it
3. **Expected**: Handles appear at all control points
4. Click on empty space
5. **Expected**: Handles disappear
6. Click on route again
7. **Expected**: Handles reappear
8. Create second route with control points
9. Click first route
10. **Expected**: Only first route's handles visible
11. Click second route
12. **Expected**: First route handles disappear, second route handles appear

✅ **Pass Criteria**: Handles visible only when route selected

---

### Test 10: Control Point Hover Behavior
**Objective**: Verify handle hover states work correctly

1. Select route with control points
2. Hover mouse over a handle (without clicking)
3. **Expected**: Handle color changes to vivid orange (hover state)
4. Move mouse away from handle
5. **Expected**: Handle returns to normal orange
6. Click handle to select it
7. **Expected**: Handle turns red
8. Hover over the selected handle
9. **Expected**: Handle stays red (selection overrides hover)

✅ **Pass Criteria**: Hover feedback works, selection takes priority

---

### Test 11: Multiple Control Points
**Objective**: Verify system works with many control points

1. Create a route
2. Add 7-10 control points using P + Click
3. **Expected**: All control points inserted correctly
4. Select the route
5. **Expected**: All handles appear
6. Try dragging various handles
7. **Expected**: Route maintains smooth curves
8. Verify spline passes through all control points
9. Try deleting several control points
10. **Expected**: Each deletion works correctly

✅ **Pass Criteria**: System handles many control points gracefully

---

### Test 12: Project Save and Load
**Objective**: Verify control points persist correctly

1. Create routes with control points
2. Drag handles to create distinctive curves
3. Save project (Ctrl+S)
4. Close application
5. Reopen application
6. Open saved project
7. **Expected**: Routes appear with all control points
8. **Expected**: Curves match saved state
9. Select route
10. **Expected**: Handles appear at correct positions
11. Try dragging a handle
12. **Expected**: Dragging works on loaded project

✅ **Pass Criteria**: Control points persist across save/load

---

### Test 13: Route Grouping
**Objective**: Verify route grouping still works

1. Create 3-4 routes
2. Hold Ctrl and click each route
3. **Expected**: Each clicked route turns magenta (group selection)
4. **Expected**: Previously selected routes stay magenta
5. Click "Create Route Group" button
6. Enter group name
7. **Expected**: Dialog appears, accepts name
8. **Expected**: Group label appears on map
9. **Expected**: Routes return to normal color
10. **Expected**: No "QGraphicsTextItem" errors in console

✅ **Pass Criteria**: Grouping works, no text item errors

---

### Test 14: Route Group Label Visibility
**Objective**: Verify route group labels display correctly

1. Create a route group from Test 13
2. **Expected**: Group name label appears near center of routes
3. **Expected**: Label is readable (light blue in dark mode, dark blue in light mode)
4. **Expected**: Label is non-selectable
5. **Expected**: Label is non-movable
6. Move one of the systems in the group
7. **Expected**: Routes update
8. **Expected**: Group label repositions to new center

✅ **Pass Criteria**: Group labels work correctly

---

### Test 15: Route Context Menu
**Objective**: Verify route renaming works

1. Right-click on a route
2. **Expected**: Context menu appears with "Rename Route" option
3. Click "Rename Route"
4. **Expected**: Dialog appears with current name
5. Enter new name and click OK
6. **Expected**: Route name updates
7. **Expected**: Window shows unsaved changes (*)

✅ **Pass Criteria**: Route renaming works

---

### Test 16: Route Deletion
**Objective**: Verify entire route can be deleted

1. Create a route with control points
2. Select the route (not a handle)
3. Press Delete key
4. **Expected**: Confirmation dialog appears
5. Click Yes
6. **Expected**: Route and all handles removed from scene
7. **Expected**: Window shows unsaved changes (*)

✅ **Pass Criteria**: Route deletion works

---

### Test 17: System Movement Updates Routes
**Objective**: Verify routes update when systems move

1. Create route with control points
2. Switch to Systems Mode
3. Drag one of the connected systems
4. **Expected**: Route endpoint follows system
5. **Expected**: Control points remain in place
6. **Expected**: Route curve updates smoothly
7. **Expected**: If handles visible, they stay at control points

✅ **Pass Criteria**: Routes update correctly with system movement

---

### Test 18: Camera Controls
**Objective**: Verify zoom and pan still work

1. Use mouse wheel to zoom in
2. **Expected**: View zooms smoothly
3. Use mouse wheel to zoom out
4. **Expected**: View zooms smoothly
5. Press WASD keys
6. **Expected**: View pans continuously
7. Press Space + drag mouse
8. **Expected**: View pans with mouse
9. Middle-click and drag
10. **Expected**: View pans with mouse
11. Verify routes and handles remain properly positioned

✅ **Pass Criteria**: All camera controls work, no regression

---

### Test 19: Template Mode Compatibility
**Objective**: Verify template operations still work

1. Switch to Template Mode
2. Load a template
3. Drag template
4. **Expected**: Template moves
5. Ctrl + wheel to scale
6. **Expected**: Template scales
7. Adjust opacity slider
8. **Expected**: Template opacity changes
9. Lock/unlock template
10. **Expected**: Lock state toggles correctly

✅ **Pass Criteria**: Template mode works, no regression

---

### Test 20: Systems Mode Compatibility
**Objective**: Verify system operations still work

1. Switch to Systems Mode
2. Left-click to place new system
3. **Expected**: System placement dialog appears
4. Enter name and save
5. **Expected**: System appears on map
6. Right-click existing system
7. **Expected**: Edit dialog appears
8. Drag system
9. **Expected**: System moves, routes update

✅ **Pass Criteria**: Systems mode works, no regression

---

### Test 21: Dark/Light Mode Toggle
**Objective**: Verify theme switching works with all elements

1. From View menu, select Light Mode
2. **Expected**: Background becomes light gray
3. **Expected**: Routes become darker blue
4. **Expected**: System labels become black
5. **Expected**: Group labels become dark blue
6. Switch back to Dark Mode
7. **Expected**: Background becomes dark
8. **Expected**: All colors revert to dark mode palette
9. Create route and add control points
10. **Expected**: Handles remain visible in both modes

✅ **Pass Criteria**: Theme switching works for all elements

---

### Test 22: P Key State Management
**Objective**: Verify P key tracking works correctly

1. In Routes mode, press P key
2. Move mouse over route
3. **Expected**: No visual change (P alone doesn't do anything)
4. Click on route while holding P
5. **Expected**: Control point inserted
6. Release P key
7. Click on route (without P)
8. **Expected**: Route selects (no control point added)

✅ **Pass Criteria**: P key state tracked correctly

---

### Test 23: Edge Case - No Control Points
**Objective**: Verify route with no control points

1. Create route (straight line)
2. Click to select it
3. **Expected**: No handles appear (since no control points)
4. **Expected**: Route displays as straight line
5. Try pressing Delete
6. **Expected**: Route deletion confirmation (not control point deletion)

✅ **Pass Criteria**: Routes without control points handled correctly

---

### Test 24: Edge Case - Single Control Point
**Objective**: Verify route with one control point

1. Create route
2. Add exactly one control point with P + Click
3. **Expected**: Route uses quadratic curve through the point
4. Select route
5. **Expected**: One handle appears
6. Drag the handle
7. **Expected**: Curve updates
8. Select and delete the handle
9. **Expected**: Route returns to straight line

✅ **Pass Criteria**: Single control point works correctly

---

### Test 25: Console Error Check
**Objective**: Verify no errors appear during normal operation

1. Perform various operations:
   - Create routes
   - Add control points
   - Drag handles
   - Delete control points
   - Create route groups
   - Rename routes
   - Save and load project
2. Monitor console output throughout
3. **Expected**: No error messages
4. **Expected**: No warnings about QGraphicsTextItem
5. **Expected**: No Python exceptions

✅ **Pass Criteria**: No errors or warnings in console

---

## Summary Checklist

Use this checklist to track testing progress:

- [ ] Test 1: Basic application launch
- [ ] Test 2: Create basic route
- [ ] Test 3: Add control points with P + Click
- [ ] Test 4: Drag control point handles
- [ ] Test 5: Select control point handles
- [ ] Test 6: Delete with Delete key
- [ ] Test 7: Delete with Backspace key
- [ ] Test 8: Delete last control point
- [ ] Test 9: Handle visibility on selection
- [ ] Test 10: Control point hover behavior
- [ ] Test 11: Multiple control points
- [ ] Test 12: Project save and load
- [ ] Test 13: Route grouping
- [ ] Test 14: Route group label visibility
- [ ] Test 15: Route context menu
- [ ] Test 16: Route deletion
- [ ] Test 17: System movement updates routes
- [ ] Test 18: Camera controls
- [ ] Test 19: Template mode compatibility
- [ ] Test 20: Systems mode compatibility
- [ ] Test 21: Dark/light mode toggle
- [ ] Test 22: P key state management
- [ ] Test 23: Edge case - no control points
- [ ] Test 24: Edge case - single control point
- [ ] Test 25: Console error check

---

## Known Issues to Watch For

Based on the problem statement, verify these are fixed:

1. ✅ Handle dragging should work (not blocked by MapView)
2. ✅ Control point deletion should work (Delete/Backspace)
3. ✅ No "QGraphicsTextItem not defined" errors
4. ✅ Handles should be selectable and focusable
5. ✅ Z-order should prioritize handles (always on top)

---

## Reporting Issues

If you encounter any issues, report:

1. **Test number** that failed
2. **Steps to reproduce**
3. **Expected behavior**
4. **Actual behavior**
5. **Console output** (if any errors)
6. **Screenshots** (if visual issue)

---

## Success Criteria

All 25 tests must pass for the system to be considered fully functional and ready for production use.

✅ **All tests passed**: System is ready for use
❌ **Any test failed**: Review and fix before release
