# Route Control Point Quick Reference

## Keyboard Shortcuts

### General
- **WASD** or **Arrow Keys**: Pan the view
- **Mouse Wheel**: Zoom in/out
- **Space + Left Mouse**: Pan by dragging
- **Middle Mouse**: Pan by dragging

### Route Mode
- **P + Click on route**: Add control point at clicked position
- **Ctrl + Click on route**: Toggle route for group selection
- **Delete** or **Backspace**: Delete selected control point handle
- **Delete** (route selected): Delete entire route (with confirmation)

## Mouse Actions

### Creating Routes
1. Click **Routes** button
2. Click first system (start)
3. Click second system (end)
4. Route created as straight line

### Adding Control Points
1. Select route (optional)
2. Hold **P** key
3. Click on route where you want the point
4. Control point added at closest segment

### Moving Control Points
1. Select route (handles appear)
2. Click and drag any orange handle
3. Route updates in real-time
4. Release to finalize

### Deleting Control Points
1. Select route (handles appear)
2. Click handle to select it (turns red)
3. Press **Delete** or **Backspace**
4. Control point removed

## Visual Indicators

### Handle Colors
- **Orange**: Normal state (can be dragged)
- **Vivid Orange**: Mouse hovering over handle
- **Red**: Handle selected (press Delete/Backspace to remove)

### Route Colors
- **Light Blue**: Normal route
- **Yellow**: Selected route
- **Magenta**: Route selected for grouping (Ctrl+Click)

## Tips

- Control points are inserted at the closest segment to your click
- You can add control points without selecting the route first
- Handles only appear when route is selected
- Handles are always on top (z-value 100) for easy clicking
- All changes mark the project as unsaved (*)
- Control points persist across save/load

## Common Workflows

### Create a Curved Route
1. Enter Routes mode
2. Click two systems to create route
3. Hold P and click on route multiple times
4. Route curves through all control points

### Edit an Existing Route
1. Click on route to select it
2. Drag handles to adjust curve
3. Add more control points with P + Click
4. Delete unwanted points by selecting and pressing Delete

### Clean Up a Route
1. Select route
2. Select each unwanted handle (turns red)
3. Press Delete to remove
4. Route simplifies as points are removed

## Troubleshooting

**Handles won't drag:**
- Ensure you're in Routes mode
- Click handle first to ensure it's active
- Try selecting the route again

**Can't delete control point:**
- Click handle to select it first (must turn red)
- Then press Delete or Backspace
- Route must be selected to see handles

**Control point added in wrong place:**
- P + Click adds at closest segment
- You can immediately drag the handle to correct position
- Or delete it and try again

**Route disappears when deleting:**
- If you delete the route itself (not a handle), confirmation dialog appears
- To delete a control point, select the handle first (turns red)

## Related Features

### Route Grouping
1. Ctrl + Click multiple routes (turn magenta)
2. Click "Create Route Group" button
3. Enter group name
4. Routes grouped, label appears

### Route Renaming
1. Right-click on route
2. Select "Rename Route"
3. Enter new name

### Project Management
- **Ctrl + S**: Save project
- **Ctrl + O**: Open project
- **Ctrl + N**: New project
- **Ctrl + E**: Export map data

---

For detailed testing instructions, see TESTING_GUIDE.md
For implementation details, see FINAL_IMPLEMENTATION_SUMMARY.md
