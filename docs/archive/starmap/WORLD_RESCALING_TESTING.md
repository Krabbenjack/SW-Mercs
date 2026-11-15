# World Rescaling Feature - Testing Guide

This document describes how to manually test the new World Rescaling and SceneRect auto-expansion features.

## Prerequisites

1. Run the application:
   ```bash
   cd star-map-editor
   python main.py
   ```

2. Have at least one template image ready to load (any PNG/JPG image will work)

## Test 1: SceneRect Auto-Expansion with Multiple Templates

**Goal:** Verify that scrolling works when multiple templates are placed far apart.

**Steps:**
1. Start a new project (File → New Project)
2. Switch to Template Mode
3. Load a template (Load Template button)
4. Move the template to position (0, 0) approximately
5. Load a second template
6. Move the second template far away (e.g., drag it to the far right/bottom)
7. Try scrolling/panning to both templates using WASD keys or middle-mouse drag

**Expected Result:**
- You should be able to scroll to both templates without the camera "stopping"
- The scrollable area should automatically expand to include both templates

## Test 2: World Rescaling with Factor < 1 (Shrink)

**Goal:** Verify that rescaling makes the world smaller and reduces travel times.

**Steps:**
1. Create a project with:
   - At least 2 systems placed far apart (e.g., 1000 units apart)
   - At least 1 route connecting them
2. Go to Stats mode and note the travel time for the route
3. Open World → Scale...
4. Set Scale Factor to 0.5
5. Keep "Scale templates too" checked
6. Keep anchor as "Keep center (centroid)"
7. Click OK
8. Go back to Stats mode and check the travel time

**Expected Result:**
- All systems should be closer together (distance halved)
- Travel time should be approximately half of the original
- If templates were enabled, they should also be repositioned and scaled down
- Camera should stay in the same position (not auto-center)
- You should still be able to scroll to all content

## Test 3: World Rescaling with Factor > 1 (Expand)

**Goal:** Verify that rescaling makes the world larger and increases travel times.

**Steps:**
1. Create a project with:
   - At least 2 systems placed close together
   - At least 1 route connecting them
2. Note the travel time in Stats mode
3. Open World → Scale...
4. Set Scale Factor to 2.0
5. Keep "Scale templates too" checked
6. Keep anchor as "Keep center (centroid)"
7. Click OK
8. Check the travel time in Stats mode

**Expected Result:**
- All systems should be farther apart (distance doubled)
- Travel time should be approximately double the original
- Templates should be repositioned and scaled up
- Scrolling should work to reach all content (no camera stops)

## Test 4: Anchor Mode - Origin vs Centroid

**Goal:** Verify that anchor modes work correctly.

**Steps:**

### Part A: Origin Anchor
1. Create a project with a system at position (100, 100)
2. Open World → Scale...
3. Set Scale Factor to 2.0
4. Select "Origin (0, 0)" anchor
5. Click OK
6. Inspect the system position (should be at 200, 200)

### Part B: Centroid Anchor
1. Create a project with two systems:
   - System A at (100, 100)
   - System B at (300, 300)
   - Centroid is at (200, 200)
2. Open World → Scale...
3. Set Scale Factor to 2.0
4. Select "Keep center (centroid)" anchor
5. Click OK
6. Inspect system positions:
   - System A should be at (0, 0): 200 + (100 - 200) * 2 = 0
   - System B should be at (400, 400): 200 + (300 - 200) * 2 = 400

**Expected Result:**
- Origin anchor: scales from (0, 0)
- Centroid anchor: scales from the center of all systems

## Test 5: Templates Checkbox

**Goal:** Verify that templates are only affected when the checkbox is enabled.

**Steps:**
1. Create a project with:
   - 1 template at position (100, 100) with scale 1.0
   - 1 system at position (100, 100)
2. Open World → Scale...
3. Set Scale Factor to 2.0
4. **Uncheck** "Scale templates too"
5. Select "Origin (0, 0)" anchor
6. Click OK
7. Check positions:
   - System should be at (200, 200)
   - Template should still be at (100, 100) with scale 1.0

**Expected Result:**
- When unchecked: templates position and scale are not affected
- When checked: templates are scaled along with everything else

## Test 6: Route Geometry Preservation

**Goal:** Verify that route control points are scaled correctly.

**Steps:**
1. Create a project with:
   - System A at (0, 0)
   - System B at (100, 100)
   - A route between them with a control point at (50, 25)
2. Open World → Scale...
3. Set Scale Factor to 2.0
4. Select "Origin (0, 0)" anchor
5. Click OK
6. The route should maintain its shape, with:
   - System A at (0, 0)
   - System B at (200, 200)
   - Control point at (100, 50)

**Expected Result:**
- Route shape is preserved proportionally
- Route still connects the systems correctly
- Route curve is maintained

## Test 7: No Regression - Existing Features

**Goal:** Verify that existing features still work after implementing rescaling.

**Steps:**
1. Test the following existing features:
   - Template loading and positioning
   - System placement
   - Route creation
   - Zoom with mouse wheel
   - Pan with WASD keys
   - Save/Load project
   - Export map data
   - Stats display

**Expected Result:**
- All existing features work as before
- No crashes or errors
- No visual glitches

## Test 8: Project Modified State

**Goal:** Verify that rescaling marks the project as modified.

**Steps:**
1. Open or create a project and save it
2. Open World → Scale... and apply any rescaling
3. Try to close the application or open a new project

**Expected Result:**
- You should be prompted to save changes
- The window title should show an asterisk (*) indicating unsaved changes

## Automated Tests

The following automated tests are available:

```bash
cd star-map-editor
python tests/test_world_rescale.py
```

This runs:
- System position scaling tests (origin and centroid anchors)
- Route control point scaling tests
- Template position and scale tests
- Centroid fallback tests

All tests should pass with a ✅ success message.
