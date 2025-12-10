# Stats Widget Layout Change - Before and After

## Before (Vertical Layout)
```
┌─────────────────────────────────────────────┐
│ Main Window                                  │
├─────────────────────────────────────────────┤
│ Menu Bar & Toolbars                          │
├─────────────────────────────────────────────┤
│ Stats Widget (when visible)                  │
│ - Takes up full width                        │
│ - Reduces map height                         │
├─────────────────────────────────────────────┤
│                                              │
│ Map View                                     │
│ (Reduced vertical space when stats active)  │
│                                              │
└─────────────────────────────────────────────┘
```

## After (Horizontal Splitter Layout)
```
┌─────────────────────────────────────────────┐
│ Main Window                                  │
├─────────────────────────────────────────────┤
│ Menu Bar & Toolbars                          │
├─────────────────────────────────────────────┤
│                                 │ Stats      │
│                                 │ Widget     │
│ Map View                        │ (sidebar)  │
│ (Full vertical height)          │ 250-400px  │
│                                 │ Min-Max    │
│                                 │ Width      │
│                                 │            │
└─────────────────────────────────┴────────────┘
     75% (stretch factor 3)        25% (stretch factor 1)
```

## Key Changes

1. **Layout Structure**: Changed from `QVBoxLayout` to `QSplitter(Qt.Horizontal)`
2. **Map View**: Now uses full vertical height at all times
3. **Stats Widget**: Appears as right sidebar (250-400px wide) when in Stats mode
4. **Splitter Ratios**: Map view gets 3x stretch factor, stats gets 1x
5. **Show/Hide**: Stats widget hides when not in Stats mode, map expands to full width

## Code Changes

### Import Addition
```python
from PySide6.QtWidgets import (..., QSplitter)
```

### Layout Restructuring
```python
# Create stats widget with size constraints
self.stats_widget = StatsWidget()
self.stats_widget.hide()
self.stats_widget.setMinimumWidth(250)
self.stats_widget.setMaximumWidth(400)

# Create horizontal splitter
self.main_splitter = QSplitter(Qt.Horizontal)
self.main_splitter.addWidget(self.view)
self.main_splitter.addWidget(self.stats_widget)
self.main_splitter.setStretchFactor(0, 3)  # Map: 3x
self.main_splitter.setStretchFactor(1, 1)  # Stats: 1x

# Add splitter to main layout
main_layout.addWidget(self.main_splitter)
```

## Benefits

✅ Map maintains full vertical height
✅ Stats sidebar doesn't compress map vertically
✅ User can resize the splitter for preferred width
✅ Min/max width constraints prevent extreme sizes
✅ Same show/hide behavior as before
✅ No changes to Stats widget logic or other modes
