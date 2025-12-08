# Route Editing Guide

## Overview

The Route Editing system allows you to modify existing routes by adding, removing, and rearranging systems within route chains. Routes can now pass through multiple systems, not just connect two endpoints.

## Features

### 1. Route System Chains

Routes can now contain multiple systems in sequence:
- **Simple Route**: System A → System B (traditional 2-system route)
- **Chain Route**: System A → System B → System C → System D (multi-system route)

### 2. Route Editing Mode

Route Editing Mode is **automatically activated** when you:
1. Switch to Routes mode (toolbar button)
2. Select a route on the map

The route editing sidebar will appear showing:
- Current selected route name
- List of systems in the route chain (read-only)
- Action buttons for editing operations

### 3. Inserting Systems into Routes

#### Via Sidebar Button
1. Select a route
2. Select a system (not already in the route)
3. Click "Insert System" button
4. Choose where to insert the system in the chain

#### Via Context Menu (Right-click)
- Right-click on a **route segment** (line between two systems)
- Select "Insert System into Route Here"
- Must have a system selected that's not already in the route

### 4. Removing Systems from Routes

#### Via Sidebar Button
1. Select a route
2. Select a system that's in the route
3. Click "Remove System" button
4. Confirm the removal

#### Via Context Menu (Right-click)
- Right-click on a **system** (while in Route Editing Mode)
- Select "Remove '[System Name]' from Route"

**Constraints:**
- Routes must have at least 2 systems
- Cannot remove if it would leave only 1 system

### 5. Splitting Routes

Split a route into two separate routes at any intermediate system.

#### Via Sidebar Button
1. Select a route
2. Select a system in the middle of the route (not first or last)
3. Click "Split Route" button
4. Confirm the split

#### Via Context Menu (Right-click)
- Right-click on a **system** in a route
- Select "Split Route at '[System Name]'"

**Result:**
- Original route: Start → ... → Split Point
- New route: Split Point → ... → End

**Constraints:**
- Cannot split at the first or last system

### 6. Merging Routes

Combine two routes into a single route if they share a common endpoint.

#### Via Sidebar Button
1. Select two routes using CTRL+click
2. Click "Merge Routes" button
3. Confirm the merge

**Valid Merge Configurations:**
- End of Route 1 → Start of Route 2
- End of Route 1 → End of Route 2 (Route 2 reversed)
- Start of Route 1 ← End of Route 2
- Start of Route 1 ← Start of Route 2 (Route 2 reversed)

The system automatically detects the valid configuration.

## Context Menu Reference

### System Context Menu (in Route Editing Mode)
- **Remove from Route**: Remove this system from the selected route
- **Split Route Here**: Split the route at this system (if not at ends)
- **Insert into Route**: Insert this system into the selected route

### Route Segment Context Menu (in Route Editing Mode)
- **Insert System into Route Here**: Insert the selected system at this position
- **Split Route Here**: Split the route between these two systems

## Workflow Examples

### Example 1: Create a Trade Route Chain
1. Create route: Coruscant → Corellia
2. Select the route
3. Select Kuat system
4. Right-click on the route segment between Coruscant and Corellia
5. Choose "Insert System into Route Here"
6. Result: Coruscant → Kuat → Corellia

### Example 2: Remove a Waypoint
1. Select a multi-system route
2. Right-click on a middle system
3. Select "Remove from Route"
4. The route is automatically recalculated

### Example 3: Split a Long Route
1. Select a route: A → B → C → D → E
2. Right-click on system C
3. Select "Split Route at C"
4. Result: Two routes:
   - Route 1: A → B → C
   - Route 2: C → D → E

### Example 4: Merge Two Routes
1. CTRL+click two routes that share an endpoint
2. Click "Merge Routes" button
3. Confirm the merge
4. Routes are combined into one continuous route

## Tips and Best Practices

1. **Visual Feedback**: Selected routes are highlighted in yellow, routes selected for grouping in magenta
2. **System List**: The sidebar shows all systems in the selected route in order
3. **Button States**: Action buttons are enabled/disabled based on context
4. **Undo Support**: Changes can be undone (if undo system is implemented)
5. **Save Often**: Complex route edits should be saved regularly

## Keyboard Shortcuts

- **CTRL+Click Route**: Select route for grouping/merging
- **ESC**: Cancel route creation
- **Right-click**: Context menu for editing operations

## Compatibility

- Route editing preserves control points for simple 2-system routes
- Chain routes connect systems directly (no intermediate control points)
- Existing projects load correctly with backward compatibility
- System_chain field is optional in save files

## Known Limitations

1. Cannot reorder systems by drag-and-drop (use remove+insert instead)
2. Control points are cleared when converting to chain routes
3. Cannot set specific start/end points (use split+remove instead)
4. Route editing requires Routes mode to be active

## Technical Details

### Data Model
- Routes store a `system_chain` field (ordered list of system IDs)
- Backward compatible with `start_system_id` and `end_system_id`
- Control points preserved for simple 2-system routes

### Rendering
- Chain routes draw straight lines between consecutive systems
- Simple routes with control points use polyline rendering
- Routes update automatically when systems are moved

## Troubleshooting

**Q: Why can't I see the editing buttons?**
A: Make sure you're in Routes mode and have a route selected.

**Q: Why is "Insert System" disabled?**
A: The selected system might already be in the route, or no system is selected.

**Q: Why can't I remove a system?**
A: The route must have at least 2 systems. Delete the route instead if needed.

**Q: Why can't I merge two routes?**
A: The routes don't share a common endpoint. They must connect at one of their ends.

**Q: Context menu not showing?**
A: Ensure you're right-clicking directly on a system or route segment, and that Route Editing Mode is active (route selected).
