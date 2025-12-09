# Route System Testing Guide

## Overview
This document provides comprehensive testing procedures for the polyline route creation system with visual feedback and enhanced context menu features.

---

## Test Suite

### 1. Route Creation with Visual Feedback

**Test 1.1: Basic Route Creation**
1. Switch to Routes mode
2. Click on System A
3. **Expected**: Status bar shows "Route drawing: Click intermediate points, then click end system..."
4. Click 2-3 points in empty space
5. **Expected**: Blue dashed line appears, growing from System A through each clicked point
6. Click on System B
7. **Expected**: 
   - Blue dashed preview disappears
   - Solid route appears connecting A → points → B
   - Route is automatically selected
   - Status bar shows "Routes mode: Click system to start route."

**Test 1.2: Route Without Intermediate Points**
1. Click System A
2. Immediately click System B (no intermediate points)
3. **Expected**: Straight line route from A to B

**Test 1.3: Route With Many Intermediate Points**
1. Click System A
2. Click 10+ intermediate points
3. **Expected**: Preview updates smoothly with each click
4. Click System B
5. **Expected**: Route follows all clicked points exactly

**Test 1.4: Cancel Route Drawing (ESC)**
1. Click System A
2. Click 2-3 intermediate points
3. **Expected**: Blue dashed preview visible
4. Press ESC key
5. **Expected**:
   - Preview disappears completely
   - No route is created
   - Status bar shows "Routes mode: Click system to start route."

**Test 1.5: Cancel Route Drawing (Right-Click)**
1. Click System A
2. Click 2-3 intermediate points
3. **Expected**: Blue dashed preview visible
4. Right-click anywhere
5. **Expected**: Same as Test 1.4

**Test 1.6: Click on System Label**
1. Click on System A's text label (not the circle)
2. **Expected**: Route drawing starts (same as clicking circle)
3. Click intermediate points
4. Click on System B's text label
5. **Expected**: Route finishes correctly

### 2. Route Context Menu

**Test 2.1: Rename Route**
1. Create a route
2. Right-click the route
3. **Expected**: Context menu shows "Rename Route" and "Delete Route"
4. Click "Rename Route"
5. **Expected**: Dialog appears with current route name
6. Enter new name "Test Route"
7. Click OK
8. **Expected**: 
   - Route name is updated in project data
   - Unsaved changes marker appears

**Test 2.2: Delete Route (Single)**
1. Create a route
2. Right-click the route
3. Click "Delete Route"
4. **Expected**: Confirmation dialog appears
5. Click Yes
6. **Expected**:
   - Route is removed from scene
   - Route is removed from project
   - Status bar shows "Route deleted."
   - Unsaved changes marker appears

**Test 2.3: Delete Route (Cancel)**
1. Create a route
2. Right-click the route
3. Click "Delete Route"
4. Click No in confirmation dialog
5. **Expected**: Route remains unchanged

**Test 2.4: Delete Route in Group**
1. Create 3 routes
2. Group them (Ctrl+Click all, "Create Route Group")
3. **Expected**: Group label appears
4. Right-click one route
5. Delete it
6. **Expected**:
   - Route removed
   - Group still exists with 2 routes
   - Group label position may update

**Test 2.5: Delete Route Leaving Empty Group**
1. Create 1 route
2. Group it (creates a group with 1 route)
3. **Expected**: Group label appears
4. Delete the route
5. **Expected**:
   - Route removed
   - Group is automatically deleted
   - Group label is removed

### 3. Route Grouping Integration

**Test 3.1: Create Group After Route Drawing**
1. Create 2-3 routes with visual feedback
2. Ctrl+Click to select all routes
3. Click "Create Route Group"
4. Enter group name
5. **Expected**:
   - Group created
   - Group label appears at averaged midpoint
   - Routes remain selectable individually

**Test 3.2: Delete Multiple Routes in Group**
1. Create 4 routes
2. Group them
3. Delete 2 routes (one at a time)
4. **Expected**: 
   - Each deletion updates the group
   - Group label position updates
   - Group persists with remaining routes

### 4. System Movement with Routes

**Test 4.1: Move Start System**
1. Create route with intermediate points
2. Switch to Systems mode
3. Drag the start system to new position
4. **Expected**: Route follows system, first segment updates

**Test 4.2: Move End System**
1. Create route with intermediate points
2. Switch to Systems mode
3. Drag the end system
4. **Expected**: Route follows system, last segment updates

**Test 4.3: Move Both Systems**
1. Create route
2. Move start system
3. Move end system
4. **Expected**: 
   - Route stays connected to both systems
   - Intermediate points remain at their original positions

### 5. Duplicate Prevention

**Test 5.1: Duplicate Route Prevention**
1. Create route from System A to System B
2. Try to create another route from A to B
3. **Expected**: Warning dialog "A route already exists between these systems."

**Test 5.2: Reverse Route Prevention**
1. Create route from System A to System B
2. Try to create route from System B to System A
3. **Expected**: Same warning as Test 5.1

**Test 5.3: Same System Prevention**
1. Click System A to start route
2. Click intermediate points
3. Try to click System A again to finish
4. **Expected**: Route drawing cancelled, no route created

### 6. Persistence

**Test 6.1: Save and Load Routes**
1. Create 3 routes with various intermediate points
2. Save project
3. Close and reopen application
4. Load project
5. **Expected**: All routes appear exactly as created

**Test 6.2: Save and Load Groups**
1. Create routes
2. Create groups with labels
3. Save project
4. Reload
5. **Expected**:
   - Groups restored
   - Labels appear at correct positions

### 7. Mode Switching Regression Tests

**Test 7.1: Template Mode**
1. Switch to Template mode
2. Load, move, resize templates
3. **Expected**: No interference from route system

**Test 7.2: Systems Mode**
1. Switch to Systems mode
2. Create, move, delete systems
3. **Expected**: Normal system behavior, routes update on system movement

**Test 7.3: Return to Routes Mode**
1. Create routes in Routes mode
2. Switch to Systems mode
3. Switch back to Routes mode
4. **Expected**: Existing routes visible, can create new routes

### 8. Edge Cases

**Test 8.1: Click Very Close to System**
1. Start route drawing
2. Click intermediate point very close to a system (but not on it)
3. **Expected**: Point is added at clicked location, doesn't snap to system

**Test 8.2: Many Routes Between Systems**
1. Place 10+ systems
2. Create routes between various pairs
3. **Expected**: All routes render correctly, no performance issues

**Test 8.3: Long Route Path**
1. Create route with 20+ intermediate points
2. **Expected**: 
   - Preview handles all points
   - Final route displays correctly
   - No performance degradation

**Test 8.4: Zoom While Drawing**
1. Start route drawing
2. Add some intermediate points
3. Zoom in/out with mouse wheel
4. Continue adding points
5. **Expected**: Preview remains visible and correct

**Test 8.5: Pan While Drawing**
1. Start route drawing
2. Add some intermediate points
3. Pan the view (WASD or middle-mouse drag)
4. Continue adding points
5. **Expected**: Preview follows view, coordinates correct

### 9. Visual Quality

**Test 9.1: Preview Appearance**
1. Create route with preview visible
2. **Expected**:
   - Blue dashed line (matches description)
   - Line is visible but distinguishable from final routes
   - Z-order correct (doesn't obscure systems)

**Test 9.2: Context Menu Appearance**
1. Right-click route
2. **Expected**:
   - Both "Rename Route" and "Delete Route" visible
   - Menu readable and properly formatted

### 10. Error Recovery

**Test 10.1: Delete While Drawing**
1. Start route drawing
2. Delete the start system (switch to Systems mode first)
3. Return to Routes mode
4. Try to finish route
5. **Expected**: Graceful handling (route cancelled or error message)

**Test 10.2: Delete End System While Drawing**
1. Start route drawing
2. Add intermediate points
3. Delete the target system before finishing
4. **Expected**: Can't finish route, or gracefully handled

---

## Quick Smoke Test (5 minutes)

For rapid verification:

1. **Create Route**: System A → 2 clicks → System B (see blue preview)
2. **Rename Route**: Right-click → Rename → Change name
3. **Delete Route**: Right-click → Delete → Confirm
4. **Cancel Drawing**: Start route → ESC (preview disappears)
5. **Group Routes**: Create 2 routes → Ctrl+Click both → Create Group
6. **Save/Load**: Save project → Reload → Verify all routes present

---

## Known Issues / Expected Behavior

1. **Preview Color**: Blue dashed line (#6496FF, 2px width)
2. **Confirmation Dialogs**: All deletions require confirmation
3. **Empty Groups**: Automatically removed when last route deleted
4. **System Labels**: Clicking label or circle both work for route creation
5. **Z-Order**: Preview appears below systems and other items

---

## Success Criteria

✅ All 50+ test cases pass
✅ No console errors during testing
✅ Smooth visual feedback during route creation
✅ Context menu fully functional (rename + delete)
✅ No regressions in Template or System modes
✅ Routes persist correctly in save/load
✅ Groups update correctly on route deletion

---

## Reporting Issues

When reporting issues, include:
- Test case number and name
- Expected behavior
- Actual behavior
- Steps to reproduce
- Screenshots if applicable
- Console errors if any
