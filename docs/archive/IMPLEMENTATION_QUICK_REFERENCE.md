# World Rescaling Feature - Quick Reference

## For Users

### How to Use World → Scale...

1. **Open the dialog**: Menu bar → World → Scale...
2. **Set parameters**:
   - **Scale Factor**: Enter value (e.g., 2.0 to double, 0.5 to halve)
   - **Scale templates too**: Check to scale templates, uncheck to keep them fixed
   - **Anchor**: Choose centroid (center of systems) or origin (0,0)
3. **Click OK**: Changes applied immediately

### When to Use

- **Fix travel times**: If distances seem wrong, rescale to adjust
- **Match reference**: Scale to match a specific measurement
- **Combine maps**: Adjust scale when merging content

## For Developers

### Key Methods

#### Data Layer (`project_model.py`)
```python
project.rescale_world(
    factor=2.0,              # Scale factor
    scale_templates=True,    # Whether to scale templates
    anchor_mode="centroid"   # "centroid" or "origin"
)
```

#### UI Layer (`gui.py`)
```python
# Refresh all graphics from data
self.refresh_all_items()

# Recompute scrollable area
self.recompute_scene_rect(padding=1000.0)
```

### Testing

```bash
# Run unit tests
python tests/test_world_rescale.py

# Run integration tests
python tests/test_world_rescale_integration.py

# Run existing tests (verify no regression)
python tests/test_scaling_features.py
```

### Architecture

```
User clicks World → Scale...
    ↓
WorldScaleDialog shows
    ↓
User confirms
    ↓
project.rescale_world() [Data Layer]
    - Scales system positions
    - Scales route control points
    - Scales template positions/scales (optional)
    ↓
refresh_all_items() [UI Layer]
    - Updates SystemItem positions
    - Updates RouteItem paths
    - Updates TemplateItem positions/scales
    ↓
recompute_scene_rect() [UI Layer]
    - Expands scrollable area
    ↓
Project marked as modified
```

## Files Changed

- `star-map-editor/core/project_model.py` - Rescaling logic
- `star-map-editor/core/gui.py` - Dialog and UI integration
- `README.md` - User documentation

## Files Added

- `star-map-editor/tests/test_world_rescale.py` - Unit tests
- `star-map-editor/tests/test_world_rescale_integration.py` - Integration tests
- `star-map-editor/WORLD_RESCALING_TESTING.md` - Testing guide
- `star-map-editor/WORLD_RESCALING_IMPLEMENTATION.md` - Full summary
