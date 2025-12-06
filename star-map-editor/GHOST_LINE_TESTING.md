# Ghost-Line Route System - Testing Checklist

## Test Environment Setup

```bash
cd star-map-editor
python main.py
```

---

## Test 1: Route Creation ✓

**Objective**: Verify basic route creation

1. Load a template (Template Mode → Load Template)
2. Place System A (Systems Mode → Left-click)
3. Place System B (Systems Mode → Left-click again)
4. Enter Routes mode
5. Click System A
6. Click System B

**Expected**:
- Route created between systems
- Route is a straight line
- Route automatically selected (yellow)
- Route name is "System A - System B"

---

## Test 2: Ghost-Line Drawing ✓

**Objective**: Verify ghost-line shaping works

1. Continue from Test 1 with a route created
2. Ensure route is selected (click it if not)
3. Hold **G** key
4. Click and drag mouse on/near the route
5. Draw a curved path between start and end
6. Release mouse button
7. Release **G** key

**Expected**:
- While dragging: cursor changes to crosshair
- On release: route redraws with curved shape
- Route follows the general path you drew
- Route starts at System A and ends at System B
- Shape is smoothed and decimated (~20 points)

---

## Test 3: Re-shaping Routes ✓

**Objective**: Verify routes can be re-shaped

1. Select an existing curved route
2. Hold **G** and drag a different path
3. Release

**Expected**:
- Old shape completely replaced by new shape
- No remnants of previous curve
- Route still connects to same systems

---

## Test 4: Reset to Straight Line ✓

**Objective**: Verify reset functionality

1. Select a curved route
2. Right-click on the route
3. Select "Reset to Straight Line"

**Expected**:
- Context menu appears with options
- Route becomes straight between systems
- All shape points removed

---

## Test 5: System Movement with Routes ✓

**Objective**: Verify routes update when systems move

1. Create a curved route
2. Switch to Systems Mode
3. Drag one of the connected systems to a new position

**Expected**:
- Route endpoint follows the moved system
- Inner curve shape remains consistent
- Route still properly shaped

---

## Test 6: Route Grouping - Creation ✓

**Objective**: Verify route groups can be created

1. Create 3-4 routes
2. Enter Routes mode
3. Hold **Ctrl** and click each route

**Expected**:
- Routes turn magenta/pink when Ctrl+clicked
- Routes become slightly thicker

4. Click "Create Route Group" button
5. Enter group name (e.g., "Trade Lane Alpha")
6. Click OK

**Expected**:
- Group created successfully
- Routes return to normal color
- **No QGraphicsTextItem errors** in console
- Group label appears on map (if implemented)

---

## Test 7: Route Grouping - Labels ✓

**Objective**: Verify group labels display correctly

1. Create a route group from Test 6
2. Observe the map

**Expected**:
- Group name label visible near center of routes
- Label is readable
- Label does not interfere with route interaction
- **No runtime errors related to QGraphicsTextItem**

---

## Test 8: Route Grouping - Renaming ✓

**Objective**: Verify group names can be changed

1. Create a route group
2. (If rename UI exists) Rename the group
3. Verify name updates everywhere

**Expected**:
- Name changes correctly
- No errors during rename
- Label updates if shown

---

## Test 9: Route Grouping - Deletion ✓

**Objective**: Verify groups can be deleted safely

1. Create a route group
2. Delete the group (if UI exists)

**Expected**:
- Group deleted successfully
- Routes remain on map
- No crashes or errors
- Labels removed cleanly

---

## Test 10: Template Mode Regression ✓

**Objective**: Verify template operations unchanged

1. Switch to Template Mode
2. Load a new template
3. Select template
4. Drag to move it
5. Ctrl + Mouse wheel to scale
6. Adjust opacity slider
7. Lock/unlock template
8. Delete template

**Expected**:
- All template operations work normally
- No interference from route system changes
- Zoom/pan work correctly

---

## Test 11: System Mode Regression ✓

**Objective**: Verify system operations unchanged

1. Switch to Systems Mode
2. Place new system (left-click)
3. Right-click to edit existing system
4. Drag system to move it
5. Delete system from edit dialog

**Expected**:
- All system operations work normally
- Routes update when systems move
- System selection/dragging smooth

---

## Test 12: Route Selection and Interaction ✓

**Objective**: Verify route selection works

1. Create multiple routes
2. Click on different routes
3. Use Ctrl+Click for group selection
4. Right-click for context menu

**Expected**:
- Routes select correctly (turn yellow)
- Only one route selected at a time (unless Ctrl)
- Context menu works
- Rename works
- No selection issues

---

## Test 13: Console Error Check ✓

**Objective**: Verify no errors during normal use

1. Perform all operations above
2. Monitor terminal/console output

**Expected**:
- **No Python exceptions**
- **No QGraphicsTextItem errors**
- **No AttributeError for RouteHandleItem**
- **No errors about control_points or handles**

---

## Test 14: Project Save/Load ✓

**Objective**: Verify shaped routes persist

1. Create routes with various shapes (G + drag)
2. Save project (Ctrl+S)
3. Close application
4. Reopen application
5. Load saved project (Ctrl+O)

**Expected**:
- Routes load with shapes intact
- Shapes match what was saved
- No errors during load
- Routes still editable

---

## Test 15: Export Functionality ✓

**Objective**: Verify export still works

1. Create project with shaped routes
2. Export map data (Ctrl+E)
3. Check exported JSON file

**Expected**:
- Export succeeds
- control_points field contains shape data
- Systems and routes properly linked
- Valid JSON format

---

## Summary Checklist

- [ ] Test 1: Route Creation
- [ ] Test 2: Ghost-Line Drawing  
- [ ] Test 3: Re-shaping Routes
- [ ] Test 4: Reset to Straight Line
- [ ] Test 5: System Movement with Routes
- [ ] Test 6: Route Grouping - Creation
- [ ] Test 7: Route Grouping - Labels
- [ ] Test 8: Route Grouping - Renaming
- [ ] Test 9: Route Grouping - Deletion
- [ ] Test 10: Template Mode Regression
- [ ] Test 11: System Mode Regression
- [ ] Test 12: Route Selection and Interaction
- [ ] Test 13: Console Error Check
- [ ] Test 14: Project Save/Load
- [ ] Test 15: Export Functionality

---

## Known Issues to Watch For

~~1. QGraphicsTextItem not defined~~ - FIXED in commit 1a68531
~~2. RouteHandleItem errors~~ - REMOVED in new system
~~3. Control point insertion errors~~ - REMOVED in new system

## Success Criteria

✅ All 15 tests pass
✅ No console errors
✅ Template and System modes work normally
✅ Routes can be shaped with G + drag
✅ Route grouping works without errors
✅ Projects save and load correctly

---

## How to Run Tests

**Quick Test (5 min)**:
1. Create 2 systems, 1 route
2. Hold G and drag on route → should curve
3. Right-click → Reset to Straight Line → should straighten
4. Ctrl+Click routes → Create group → should work without errors

**Full Test (20 min)**:
Complete all 15 test scenarios above.

---

## Reporting Issues

If any test fails, report:
- Test number and name
- Steps to reproduce
- Expected vs actual behavior
- Console output (copy all errors)
- Screenshots if applicable
