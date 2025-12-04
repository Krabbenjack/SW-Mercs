# Testing Guide for Star Map Editor

This document describes how to test the new features of the Star Map Editor.

## Prerequisites

- Python 3.10+
- PySide6 installed
- Desktop environment with display

## Installation for Testing

```bash
cd star-map-editor
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## Test Plan

### 1. File Menu Tests

#### Test 1.1: New Project
1. Launch the application
2. Click File → New Project (or Ctrl+N)
3. **Expected**: Scene clears, no templates or systems visible
4. **Expected**: Title bar shows "Star Map Editor - Untitled"
5. **Expected**: No unsaved changes indicator

#### Test 1.2: Save Project As
1. Create a new project (File → New)
2. Load a template (Template Mode → Load Template)
3. Click File → Save Project As (or Ctrl+Shift+S)
4. **Expected**: File dialog opens in Saves/ directory
5. Save as "test_project.swmproj"
6. **Expected**: Success message appears
7. **Expected**: Title bar shows "Star Map Editor - test_project.swmproj"
8. **Expected**: No asterisk in title (changes saved)

#### Test 1.3: Save Project
1. With test_project.swmproj open, make a change (move a template)
2. **Expected**: Title bar shows asterisk: "... test_project.swmproj *"
3. Click File → Save Project (or Ctrl+S)
4. **Expected**: Status message "Project saved successfully"
5. **Expected**: Asterisk removed from title

#### Test 1.4: Open Project
1. Click File → New Project
2. Click File → Open Project (or Ctrl+O)
3. **Expected**: File dialog opens in Saves/ directory
4. Select test_project.swmproj
5. **Expected**: Template loads with correct position, scale, opacity
6. **Expected**: Systems load at correct positions
7. **Expected**: Title shows correct filename

#### Test 1.5: Unsaved Changes Warning
1. Create a new project
2. Add a template
3. Click File → New Project
4. **Expected**: Dialog asks "You have unsaved changes. Do you want to save?"
5. Test all three options: Save, Discard, Cancel
6. **Expected**: Save saves the project, Discard continues, Cancel returns

#### Test 1.6: Export Map Data
1. Open a project with systems
2. Click File → Export Map Data (or Ctrl+E)
3. **Expected**: File dialog opens in Exports/ directory
4. Save as "exported_map.json"
5. **Expected**: Success message
6. Open exported_map.json
7. **Expected**: Contains systems array, routes, zones, stats
8. **Expected**: Does NOT contain template data

#### Test 1.7: Quit
1. Make some changes to a project
2. Click File → Quit (or Ctrl+Q)
3. **Expected**: Warning about unsaved changes
4. Choose Cancel
5. **Expected**: Application remains open
6. Try Quit again and choose Discard
7. **Expected**: Application closes

### 2. Template Mode Tests

#### Test 2.1: Activate Template Mode
1. Launch application
2. Click "Template Mode" button
3. **Expected**: Button turns green
4. **Expected**: Workspace toolbar appears below mode buttons
5. **Expected**: Status bar: "Template mode active: Click to select template, drag to move, Ctrl+wheel to scale."

#### Test 2.2: Load Single Template
1. Enter Template Mode
2. Click "Load Template" in workspace
3. Select a PNG/JPG image
4. **Expected**: Image loads in scene at origin
5. **Expected**: Grid overlay appears
6. **Expected**: View fits to show entire image

#### Test 2.3: Load Multiple Templates
1. In Template Mode, load first template
2. Click "Load Template" again
3. Select a different image
4. **Expected**: Second template loads
5. **Expected**: Both templates visible
6. **Expected**: Can select either by clicking

#### Test 2.4: Select Template
1. Load 2+ templates
2. Click on first template
3. **Expected**: Template becomes selected (check by workspace controls enabling)
4. Click on second template
5. **Expected**: Selection moves to second template
6. **Expected**: Workspace controls update (opacity slider, lock state)

#### Test 2.5: Move Template
1. Load a template
2. Click and drag the template
3. **Expected**: Template moves smoothly
4. **Expected**: Position updates in data model
5. Release mouse
6. **Expected**: Template stays at new position

#### Test 2.6: Scale Template (Ctrl+Wheel)
1. Load a template
2. Select it by clicking
3. Hover mouse over template
4. Hold Ctrl and scroll mouse wheel up
5. **Expected**: Template scales up
6. Scroll wheel down (with Ctrl held)
7. **Expected**: Template scales down
8. **Expected**: Scaling centered under cursor

#### Test 2.7: Opacity Slider
1. Select a template
2. Move opacity slider to 50%
3. **Expected**: Template becomes semi-transparent
4. **Expected**: Opacity label shows "50%"
5. Move to 0%
6. **Expected**: Template invisible (but still present)
7. Move to 100%
8. **Expected**: Template fully opaque

#### Test 2.8: Lock Template
1. Select a template
2. Click "Lock Template" button
3. **Expected**: Button changes to "Unlock Template"
4. **Expected**: Button appears pressed/checked
5. Try to drag the template
6. **Expected**: Template does NOT move
7. Try Ctrl+wheel scaling
8. **Expected**: Template does NOT scale
9. Click "Unlock Template"
10. **Expected**: Can move and scale again

#### Test 2.9: Reset Transform
1. Load a template
2. Move it to a different position
3. Scale it to 2x
4. Click "Reset Transform"
5. **Expected**: Template returns to position (0, 0)
6. **Expected**: Scale returns to 1.0 (100%)

#### Test 2.10: Delete Template
1. Load 2 templates
2. Select one
3. Click "Delete Template"
4. **Expected**: Selected template removed from scene
5. **Expected**: Other template remains
6. **Expected**: Workspace controls disabled (no selection)

### 3. Navigation Tests (Regression)

#### Test 3.1: Mouse Wheel Zoom
1. Load a template
2. Position cursor over center of image
3. Scroll wheel up
4. **Expected**: View zooms in, centered on cursor position
5. Scroll wheel down
6. **Expected**: View zooms out
7. Try to zoom beyond 10x (max)
8. **Expected**: Zoom stops at limit
9. Try to zoom below 0.1x (min)
10. **Expected**: Zoom stops at limit

#### Test 3.2: WASD Panning
1. Load a template and zoom in
2. Press and hold W key
3. **Expected**: View pans up continuously
4. Release W, press S
5. **Expected**: View pans down
6. Press A
7. **Expected**: View pans left
8. Press D
9. **Expected**: View pans right
10. Try holding multiple keys (W+D)
11. **Expected**: Pans diagonally

#### Test 3.3: Arrow Key Panning
1. Repeat Test 3.2 using arrow keys instead of WASD
2. **Expected**: Same behavior

#### Test 3.4: Middle Mouse Drag Pan
1. Load a template
2. Click and hold middle mouse button
3. Drag mouse
4. **Expected**: Cursor changes to closed hand
5. **Expected**: View pans following mouse movement
6. Release middle button
7. **Expected**: Cursor returns to normal

#### Test 3.5: Space+Drag Pan
1. Load a template
2. Press and hold Space bar
3. Click and hold left mouse button
4. Drag mouse
5. **Expected**: Cursor changes to closed hand
6. **Expected**: View pans following mouse movement
7. Release mouse and Space
8. **Expected**: Cursor returns to normal

#### Test 3.6: Grid Overlay
1. Load a template
2. **Expected**: Light green grid appears
3. **Expected**: Grid lines spaced 100 pixels apart
4. Zoom in
5. **Expected**: Grid scales with view
6. Pan around
7. **Expected**: Grid moves with view

### 4. Systems Mode Tests (Regression)

#### Test 4.1: Activate Systems Mode
1. Load a template
2. Click "Systems Mode" button
3. **Expected**: Button turns green
4. **Expected**: Status bar: "Mode: System placement – left-click to place a system, right-click to edit"

#### Test 4.2: Place System
1. In Systems Mode, left-click on empty area
2. **Expected**: Dialog opens for system name
3. Enter "Coruscant"
4. Click Save
5. **Expected**: Blue circle appears at clicked position
6. **Expected**: White label "Coruscant" appears next to circle

#### Test 4.3: Place Multiple Systems
1. Place 5 systems at different locations
2. **Expected**: All systems appear correctly
3. **Expected**: Each has unique position
4. **Expected**: Labels don't overlap circles

#### Test 4.4: Edit System Name
1. Right-click on a system
2. **Expected**: Edit dialog opens with current name
3. Change name to "Coruscant Prime"
4. Click Save
5. **Expected**: Label updates to new name
6. **Expected**: System stays at same position

#### Test 4.5: Delete System
1. Right-click on a system
2. Click Delete button in dialog
3. **Expected**: System removed from map
4. **Expected**: No errors

#### Test 4.6: Drag System
1. Place a system
2. Click and drag the system
3. **Expected**: System moves smoothly
4. **Expected**: Label moves with system
5. Release mouse
6. **Expected**: System stays at new position

#### Test 4.7: Select System
1. Place a system
2. Click on it
3. **Expected**: Circle color changes to orange/yellow
4. Click elsewhere
5. **Expected**: Circle returns to blue

### 5. Project Persistence Tests

#### Test 5.1: Save and Load Templates
1. Create new project
2. Load 2 templates
3. Move first template to (500, 300)
4. Scale second template to 1.5x
5. Set first template opacity to 70%
6. Lock second template
7. Save project as "persistence_test.swmproj"
8. File → New Project
9. File → Open → persistence_test.swmproj
10. **Expected**: Both templates load
11. **Expected**: First template at (500, 300), opacity 70%
12. **Expected**: Second template scale 1.5x, locked
13. **Expected**: Can't move locked template

#### Test 5.2: Save and Load Systems
1. Load template
2. Place 3 systems: "Alpha", "Beta", "Gamma"
3. Move them to distinct positions
4. Save project
5. Close and reopen project
6. **Expected**: All 3 systems present
7. **Expected**: Correct names and positions
8. **Expected**: Can edit and move them

#### Test 5.3: Mixed Content Save/Load
1. Load 2 templates
2. Place 5 systems
3. Adjust template opacity, lock states
4. Save project
5. Close and reopen
6. **Expected**: All templates load correctly
7. **Expected**: All systems load correctly
8. **Expected**: All properties preserved

### 6. Mode Switching Tests

#### Test 6.1: Template to Systems Mode
1. Enter Template Mode
2. Load a template
3. Switch to Systems Mode
4. **Expected**: Workspace toolbar disappears
5. **Expected**: Can place systems
6. **Expected**: Cannot move templates

#### Test 6.2: Systems to Template Mode
1. Enter Systems Mode
2. Place a system
3. Switch to Template Mode
4. **Expected**: Workspace toolbar appears
5. **Expected**: Can select and move templates
6. **Expected**: Cannot place systems

#### Test 6.3: Deactivate Mode
1. Enter Template Mode
2. Click Template Mode button again
3. **Expected**: Mode deactivates
4. **Expected**: Button no longer green
5. **Expected**: Workspace toolbar disappears
6. **Expected**: Status bar: "Ready"

### 7. Edge Cases and Error Handling

#### Test 7.1: Load Invalid Image
1. Template Mode → Load Template
2. Select a non-image file (e.g., .txt)
3. **Expected**: Gray placeholder or error message
4. **Expected**: Application doesn't crash

#### Test 7.2: Load Missing Image (project)
1. Save project with template
2. Manually delete the template image file
3. Open project
4. **Expected**: Gray placeholder shown
5. **Expected**: Application doesn't crash

#### Test 7.3: Delete Last Template
1. Load one template
2. Delete it
3. **Expected**: Scene becomes empty
4. **Expected**: Grid disappears
5. **Expected**: No errors

#### Test 7.4: No Template Selected
1. Load template
2. Click on empty area to deselect
3. **Expected**: Workspace controls disabled
4. **Expected**: Clicking them has no effect

#### Test 7.5: System Placement Without Template
1. New project (no template)
2. Enter Systems Mode
3. Try to place a system
4. **Expected**: Can place system
5. **Expected**: System appears on empty scene

### 8. Integration Tests

#### Test 8.1: Full Workflow
1. Start application
2. Create new project
3. Load background template
4. Position and scale template
5. Set opacity to 60%
6. Lock template
7. Switch to Systems Mode
8. Place 10 systems with names
9. Move some systems around
10. Save project as "galaxy_map.swmproj"
11. Export map data as "galaxy_map.json"
12. Close application
13. Reopen application
14. Open galaxy_map.swmproj
15. **Expected**: Everything loads exactly as left
16. **Expected**: Template still locked at 60% opacity
17. **Expected**: All 10 systems in correct positions

#### Test 8.2: Multiple Sessions
1. Create and save a project in session 1
2. Close application
3. Open application again
4. Open the project
5. Make changes and save
6. Close application
7. Open application again
8. Open the project
9. **Expected**: Latest changes present
10. **Expected**: No data corruption

## Performance Tests

### Test P.1: Many Templates
1. Load 10 templates
2. **Expected**: All load successfully
3. **Expected**: Can select and manipulate each
4. **Expected**: No significant lag

### Test P.2: Many Systems
1. Place 100 systems
2. **Expected**: All render correctly
3. **Expected**: Zoom/pan still smooth
4. **Expected**: Can select and move individual systems

### Test P.3: Large Template Image
1. Load a very large image (e.g., 4000x4000)
2. **Expected**: Loads successfully
3. **Expected**: Zoom and pan work smoothly

## Success Criteria

All tests should pass with:
- ✅ No crashes or errors
- ✅ Expected behavior matches actual behavior
- ✅ Data persistence works correctly
- ✅ All existing features still work (regression tests pass)
- ✅ New features work as specified
- ✅ UI is responsive and intuitive

## Known Limitations

- Application requires a desktop environment (no headless mode)
- Template images must be in supported formats (PNG, JPG, BMP)
- Very large projects may have performance implications
- Undo/Redo not yet implemented (coming soon)
