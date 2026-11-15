# Scaling System Refactor - Testing Guide

This document describes how to test the new scaling features implemented in the Star Map Editor.

## Testing Summary

The scaling system refactor introduces several new features:

1. **Infinite Grid System** - Grid is now independent of templates and extends dynamically
2. **Zoom Indicator** - Shows current zoom percentage and pixels-per-HSU ratio
3. **System Icon Sizing** - Small/Medium/Large icon size controls
4. **Template Scaling** - Slider control for template visual scaling
5. **Enhanced Documentation** - Clear separation of WORLD/VIEW/UI spaces

## Architecture Overview

The scaling system is based on three distinct spaces:

### WORLD SPACE (HSU Coordinates)
- **What**: Hyperspace Units - the fundamental coordinate system
- **Contains**: System positions, route paths, control points
- **Properties**: 
  - Never changes due to zoom, template scale, or icon size
  - Maintains perfect coordinate precision
  - 1 grid cell = 100 HSU (configurable)

### VIEW SPACE (Camera)
- **What**: Zoom and pan transformations
- **Contains**: Zoom level, pan position, view transformations
- **Properties**:
  - Only affects pixels-per-HSU ratio
  - Does not modify world coordinates
  - Zoom range: 10% to 1000%

### UI SPACE (Visual Properties)
- **What**: Visual appearance properties
- **Contains**: Icon radius, line width, template pixmap scale
- **Properties**:
  - Affects appearance only, not coordinates
  - Icon sizes: Small (8), Medium (10), Large (15)
  - Template scale: 10% to 500%

## Manual Testing Instructions

### 1. Grid System Tests

#### Test 1.1: Grid Appears on Load
1. Start the application
2. Enter Template Mode
3. Load a template image
4. **Expected**: 
   - Grid appears as semi-transparent green lines
   - Grid spacing is consistent (100 HSU per cell)
   - Grid covers entire visible area

#### Test 1.2: Grid Extends Infinitely
1. Load a template
2. Pan around the map (WASD or drag)
3. **Expected**:
   - Grid continues beyond template boundaries
   - Grid lines remain aligned to HSU coordinates
   - No gaps or discontinuities

#### Test 1.3: Grid Independent of Template
1. Load a small template (e.g., 500x500px)
2. Pan far outside the template area
3. **Expected**:
   - Grid still visible and functional
   - Grid spacing unchanged
   - Can place systems outside template area

### 2. Zoom Indicator Tests

#### Test 2.1: Zoom Indicator Visible
1. Load a template
2. Look at bottom-right corner of map view
3. **Expected**:
   - Black semi-transparent overlay visible
   - Shows "Zoom: 100%"
   - Shows "1 HSU = 1.0 px"

#### Test 2.2: Zoom Indicator Updates
1. Scroll mouse wheel to zoom in
2. Observe zoom indicator
3. **Expected**:
   - Zoom percentage increases (e.g., "Zoom: 143%")
   - Pixels-per-HSU increases (e.g., "1 HSU = 1.4 px")

4. Scroll mouse wheel to zoom out
5. **Expected**:
   - Zoom percentage decreases
   - Pixels-per-HSU decreases proportionally

#### Test 2.3: Zoom Indicator Precision
1. Zoom to various levels
2. **Expected**:
   - At 100% zoom: 1 HSU = 1.0 px
   - At 200% zoom: 1 HSU = 2.0 px
   - At 50% zoom: 1 HSU = 0.5 px
   - Values are accurate and update smoothly

### 3. System Icon Sizing Tests

#### Test 3.1: Icon Size Controls Visible
1. Start the application
2. Look at the top toolbar
3. **Expected**:
   - "System Icon Size:" label visible
   - Three buttons: Small, Medium, Large
   - Medium is selected by default

#### Test 3.2: Change Icon Size to Small
1. Place 3 systems on the map
2. Click "Small" button
3. **Expected**:
   - All system icons shrink to radius 8
   - System positions remain unchanged
   - Labels adjust position to stay next to icons
   - Hitboxes match new icon size

#### Test 3.3: Change Icon Size to Large
1. With systems on map
2. Click "Large" button
3. **Expected**:
   - All system icons grow to radius 15
   - System positions remain unchanged
   - Labels move outward with icons
   - Can still click icons to select/drag

#### Test 3.4: Icon Size Persists for New Systems
1. Set icon size to "Large"
2. Enter Systems Mode
3. Place a new system
4. **Expected**:
   - New system appears at Large size
   - Consistent with existing systems

#### Test 3.5: Icon Size at Different Zoom Levels
1. Set icon size to Medium
2. Place 3 systems
3. Zoom in to 200%
4. **Expected**:
   - Icons appear larger on screen (VIEW SPACE effect)
   - System coordinates unchanged (WORLD SPACE preserved)
   - Can still interact with all systems

5. Zoom out to 50%
6. **Expected**:
   - Icons appear smaller on screen
   - System coordinates still unchanged
   - All systems still clickable

### 4. Template Scaling Tests

#### Test 4.1: Template Scale Control Visible
1. Enter Template Mode
2. Load a template
3. Select the template
4. **Expected**:
   - Workspace toolbar shows "Template Scale:" slider
   - Slider is enabled when template selected
   - Default value is 100%

#### Test 4.2: Scale Template Up
1. Select a template
2. Move "Template Scale" slider to 200%
3. **Expected**:
   - Template image grows to 2x size
   - Template remains centered on its origin
   - Grid remains unchanged
   - Systems remain at same positions

#### Test 4.3: Scale Template Down
1. Select a template
2. Move "Template Scale" slider to 50%
3. **Expected**:
   - Template image shrinks to 0.5x size
   - Grid spacing unchanged
   - Systems still at same world coordinates

#### Test 4.4: Extreme Template Scales
1. Move slider to 10% (minimum)
2. **Expected**: Template very small but still visible

3. Move slider to 500% (maximum)
4. **Expected**: Template very large but still functional

5. Return to 100%
6. **Expected**: Template returns to original size

#### Test 4.5: Template Scale vs Ctrl+Wheel
1. Select a template
2. Hold Ctrl and scroll mouse wheel
3. **Expected**:
   - Template scales interactively (old behavior)
   - Slider updates to match scale
   - Both methods work consistently

4. Use slider to set scale to 150%
5. Use Ctrl+Wheel to adjust further
6. **Expected**: Both methods control the same scale value

#### Test 4.6: Systems on Scaled Template
1. Load a template at 100% scale
2. Place 5 systems on the template
3. Note system positions
4. Scale template to 200%
5. **Expected**:
   - Systems remain at exact same coordinates
   - Can still click and select systems
   - Systems don't move with template scaling

6. Scale template to 50%
7. **Expected**: Systems still at same positions

### 5. Coordinate Preservation Tests

#### Test 5.1: System Position Precision
1. Place a system at a specific location
2. Right-click to edit, note position
3. Change icon size to Large
4. Zoom to 200%
5. Load and scale a template
6. **Expected**:
   - System position unchanged
   - No coordinate drift or rounding
   - Perfect precision maintained

#### Test 5.2: Route Control Points Precision
1. Create a route with 3 control points
2. Note control point positions
3. Change icon sizes
4. Zoom in and out multiple times
5. Scale templates
6. **Expected**:
   - Route path unchanged
   - Control points at exact same positions
   - No geometry corruption

#### Test 5.3: Save and Load Precision
1. Place systems with precise coordinates (e.g., 123.456, 789.012)
2. Set various icon sizes and template scales
3. Save project
4. Close and reopen project
5. **Expected**:
   - All coordinates perfectly preserved
   - Icon sizes restored
   - Template scales restored
   - No data loss or precision loss

### 6. Integration Tests

#### Test 6.1: Full Workflow - Map Creation
1. Start new project
2. Load a background template
3. Enable grid (should auto-enable)
4. Scale template to 75%
5. Set opacity to 50%
6. Set icon size to Large
7. Place 10 systems
8. Create 5 routes with control points
9. Change icon size to Medium
10. Zoom in and out
11. Pan around
12. **Expected**:
    - All features work together harmoniously
    - No conflicts or visual glitches
    - Smooth performance

#### Test 6.2: Full Workflow - Editing
1. Open existing project with systems and routes
2. Change icon size multiple times
3. Scale templates up and down
4. Zoom to various levels
5. Move systems around
6. **Expected**:
    - Routes update correctly when systems move
    - All visual settings work independently
    - No crashes or errors

#### Test 6.3: Multi-Template Scenario
1. Load 3 different templates
2. Position them in different areas
3. Scale each to different sizes (100%, 150%, 200%)
4. Place systems across all templates
5. **Expected**:
    - Systems positioned in WORLD SPACE
    - Each template scales independently
    - Grid works across all templates
    - Systems selectable on all templates

### 7. Performance Tests

#### Test 7.1: Many Systems with Large Icons
1. Set icon size to Large
2. Place 50 systems
3. Zoom in and out
4. **Expected**:
   - Smooth rendering
   - No lag when changing icon size
   - All systems remain interactive

#### Test 7.2: Extreme Zoom Levels
1. Zoom to minimum (10%)
2. **Expected**:
   - Grid still visible (may be dense)
   - Icons still clickable
   - No rendering errors

3. Zoom to maximum (1000%)
4. **Expected**:
   - Grid cells very large
   - Icons very large but functional
   - Can still pan and interact

### 8. Regression Tests (Existing Features)

#### Test 8.1: System Placement
1. Enter Systems Mode
2. Place systems
3. **Expected**: Works exactly as before

#### Test 8.2: Route Creation
1. Enter Routes Mode
2. Click system A → add control points → click system B
3. **Expected**: Works exactly as before

#### Test 8.3: Template Opacity
1. Load template
2. Adjust opacity slider
3. **Expected**: Works exactly as before

#### Test 8.4: Template Lock
1. Load template
2. Click Lock Template
3. Try to move template
4. **Expected**: Cannot move (works as before)

#### Test 8.5: Route Grouping
1. Create multiple routes
2. Ctrl+Click routes
3. Create route group
4. **Expected**: Works exactly as before

#### Test 8.6: Dark/Light Mode
1. Switch between Dark and Light mode
2. **Expected**: All UI elements update correctly

### 9. Edge Cases

#### Test 9.1: No Template Grid
1. Start new project
2. Don't load any template
3. Enter Systems Mode
4. Place a system
5. **Expected**:
   - Grid appears (now independent of templates)
   - System placeable in world space
   - Everything works without template

#### Test 9.2: Template Scale at Extreme Zoom
1. Scale template to 500%
2. Zoom view to 1000%
3. **Expected**:
   - No overflow or rendering issues
   - Can still interact with map

#### Test 9.3: Rapid Icon Size Changes
1. Place 20 systems
2. Rapidly click Small → Medium → Large → Medium
3. **Expected**:
   - All updates happen smoothly
   - No visual glitches
   - No coordinate corruption

## Acceptance Criteria

All tests should pass with:
- ✅ No crashes or errors
- ✅ Expected behavior matches actual behavior
- ✅ WORLD SPACE coordinates never affected by VIEW/UI changes
- ✅ Perfect coordinate precision maintained
- ✅ All existing features still work (no regressions)
- ✅ New features work as specified
- ✅ UI is responsive and intuitive
- ✅ Performance is acceptable

## Known Limitations

- Grid major/minor line feature not yet implemented (optional future enhancement)
- Scale bar not yet implemented (optional future enhancement)
- No undo/redo for icon size or template scale changes (consistent with rest of app)

## Automated Tests

Run the logic tests:
```bash
cd star-map-editor
python test_scaling_logic.py
```

Expected output: All 8 tests pass ✅
