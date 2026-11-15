# Testing Instructions for Route Control Point Editing System

## Overview
This document provides step-by-step instructions for testing the new route control point editing system.

## Prerequisites
- Python 3.10+
- PySide6 installed (`pip install -r requirements.txt`)
- A test image for the background (any PNG/JPG)

## Running the Application
```bash
cd star-map-editor
python main.py
```

## Test Scenarios

### Test 1: Create a Basic Route
**Objective**: Verify routes are created without automatic control points

1. Launch the application
2. Click "Template Mode" and load a background image
3. Switch to "Systems Mode"
4. Place at least 2 systems on the map (left-click to place, enter names)
5. Switch to "Routes" mode
6. Click on first system, then click on second system
7. **Expected**: Route appears as a straight line connecting the two systems
8. **Expected**: Status bar shows "Routes mode: Click systems to create routes..."

✅ **Pass Criteria**: Route is a straight line with no automatic control points

---

### Test 2: Add Control Points with P + Click
**Objective**: Verify P + Click inserts control points at the correct position

1. Continue from Test 1 with a route created
2. Press and hold the **P** key
3. While holding P, click on the route near the middle
4. **Expected**: A control point is inserted at that position
5. **Expected**: The route curves to pass through the control point
6. Release P key
7. Press P again and click near 25% along the route
8. **Expected**: A second control point is inserted before the first one
9. Press P again and click near 75% along the route
10. **Expected**: A third control point is inserted after the first two

✅ **Pass Criteria**: Control points are inserted at click positions in the correct order

---

### Test 3: Drag Control Point Handles
**Objective**: Verify handles are draggable and update the route

1. Continue from Test 2 with a route containing control points
2. Click on the route to select it
3. **Expected**: Orange circular handles appear at each control point
4. **Expected**: Handles have white borders and are clearly visible
5. Click and drag one of the handles to a new position
6. **Expected**: The handle moves smoothly with the mouse
7. **Expected**: The route updates in real-time as you drag
8. Release the mouse button
9. **Expected**: The control point stays at the new position
10. **Expected**: The route remains curved through the new position
11. Try dragging each handle
12. **Expected**: All handles are draggable

✅ **Pass Criteria**: Handles are draggable and route updates correctly

---

### Test 4: Handle Visibility on Selection
**Objective**: Verify handles appear/disappear correctly

1. Continue from Test 3
2. Click on empty space to deselect the route
3. **Expected**: All handles disappear
4. Click on the route again
5. **Expected**: All handles reappear at control point positions
6. Create a second route between different systems
7. Click on the first route
8. **Expected**: Only first route's handles are visible
9. Click on the second route
10. **Expected**: First route's handles disappear, second route's handles appear

✅ **Pass Criteria**: Handles are visible only when route is selected

---

### Test 5: Multiple Control Points
**Objective**: Verify complex routes with many control points

1. Create a new route
2. Add 5-7 control points using P + Click
3. **Expected**: All control points are inserted correctly
4. Select the route
5. **Expected**: All handles appear
6. Try dragging various handles
7. **Expected**: Route maintains smooth curves through all points
8. Verify the spline passes through all control points

✅ **Pass Criteria**: Routes with many control points render and edit correctly

---

### Test 6: Unsaved Changes Tracking
**Objective**: Verify changes mark project as modified

1. Create and save a project with routes
2. Select a route and drag a control point handle
3. **Expected**: Window title shows asterisk (*) indicating unsaved changes
4. Press Ctrl+S to save
5. **Expected**: Asterisk disappears
6. Add a new control point with P + Click
7. **Expected**: Asterisk reappears
8. Save again
9. **Expected**: Asterisk disappears

✅ **Pass Criteria**: All control point changes mark project as unsaved

---

### Test 7: Project Persistence
**Objective**: Verify control points are saved and loaded correctly

1. Create a route with 3-4 control points
2. Position them in a distinctive curve
3. Save the project (Ctrl+S or File → Save Project As)
4. Close the application
5. Reopen the application
6. Open the saved project (File → Open Project)
7. **Expected**: Route appears with all control points in correct positions
8. **Expected**: Route has the same curve as before
9. Select the route
10. **Expected**: Handles appear at saved control point positions

✅ **Pass Criteria**: Control points persist across save/load cycles

---

### Test 8: Compatibility with Existing Features
**Objective**: Verify other features still work

1. **Template Mode**: Load, move, scale, and lock templates
   - **Expected**: All template operations work as before
2. **Systems Mode**: Place, edit, move, and delete systems
   - **Expected**: All system operations work as before
3. **Camera Controls**: Use mouse wheel zoom, WASD panning
   - **Expected**: All navigation works as before
4. **Route Grouping**: Ctrl+Click routes to select for grouping
   - **Expected**: Route grouping still works
5. **Route Context Menu**: Right-click on route to rename
   - **Expected**: Context menu appears and renaming works
6. **Route Deletion**: Select route and press Delete key
   - **Expected**: Route is deleted with confirmation

✅ **Pass Criteria**: All existing features work without regression

---

### Test 9: Edge Cases
**Objective**: Verify system handles edge cases gracefully

1. **No Control Points**: Create a route without adding any control points
   - **Expected**: Route displays as straight line
   - **Expected**: Selecting route shows no handles
   
2. **One Control Point**: Add exactly one control point
   - **Expected**: Route uses quadratic curve through the point
   - **Expected**: One handle appears when selected
   
3. **P Key Without Route**: Hold P and click on empty space
   - **Expected**: Nothing happens (no errors)
   
4. **Click Handle Without P**: Click on a handle without holding P
   - **Expected**: Handle is selected and can be dragged
   
5. **Route Selection Priority**: Click on route while P is held
   - **Expected**: Control point is inserted (P + Click takes priority)

✅ **Pass Criteria**: All edge cases handled without errors

---

### Test 10: Visual Quality
**Objective**: Verify visual appearance meets standards

1. Select a route with multiple control points
2. **Expected**: Handles are clearly visible (bright orange)
3. **Expected**: Handles have white borders
4. **Expected**: Handles are on top of the route (not obscured)
5. Hover mouse over a handle
6. **Expected**: Handle color changes to vivid orange (hover state)
7. Verify route curves are smooth (Catmull-Rom spline)
8. **Expected**: No sharp corners or discontinuities
9. Zoom in and out
10. **Expected**: Handles and routes scale appropriately

✅ **Pass Criteria**: Visual appearance is clean and professional

---

## Known Behaviors

### By Design
- New routes are created as straight lines (no automatic control points)
- Control points must be added manually using P + Click
- Control points are inserted at the closest segment to the click position
- Routes use Catmull-Rom spline interpolation
- Handles are visible only when route is selected

### Keyboard Shortcuts
- **P + Click on route**: Insert control point
- **Ctrl + Click on route**: Toggle route for group selection
- **Delete**: Delete selected route
- **Right-click on route**: Rename route

---

## Reporting Issues

If you encounter any issues during testing, please report:

1. **What you did**: Steps to reproduce
2. **What happened**: Actual behavior
3. **What you expected**: Expected behavior
4. **Environment**: OS, Python version, PySide6 version
5. **Screenshots**: If applicable

---

## Summary Checklist

- [ ] Test 1: Create basic route (straight line)
- [ ] Test 2: Add control points with P + Click
- [ ] Test 3: Drag control point handles
- [ ] Test 4: Handle visibility on selection
- [ ] Test 5: Multiple control points
- [ ] Test 6: Unsaved changes tracking
- [ ] Test 7: Project persistence
- [ ] Test 8: Compatibility with existing features
- [ ] Test 9: Edge cases
- [ ] Test 10: Visual quality

✅ **All tests passed**: System is ready for use
