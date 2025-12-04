# Quick Start Guide

Get started with the Star Map Editor in 5 minutes!

## Installation

### 1. Install Python

Make sure you have Python 3.10 or newer:
```bash
python --version
```

### 2. Set Up Virtual Environment

```bash
cd star-map-editor
python -m venv .venv
```

### 3. Activate Virtual Environment

**On Linux/macOS:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Verify Installation

```bash
python verify_installation.py
```

You should see all checks pass (except GUI import in headless environments).

## Running the Application

```bash
python main.py
```

## Your First Map

### 1. Create a Project

- Click **File → New Project** (or press Ctrl+N)
- This starts with a blank canvas

### 2. Load a Template

- Click the **Template Mode** button (it turns green)
- Click **Load Template** in the toolbar below
- Select an image file (PNG, JPG, or BMP)
- The image loads and the grid appears

### 3. Adjust the Template

- **Move**: Click and drag the template
- **Scale**: Hold Ctrl and scroll mouse wheel
- **Opacity**: Use the slider to make it semi-transparent
- **Lock**: Click "Lock Template" when positioned correctly

### 4. Place Star Systems

- Click the **Systems Mode** button
- Left-click on the map where you want a system
- Enter a name (e.g., "Coruscant")
- Click Save
- Repeat to add more systems

### 5. Save Your Work

- Click **File → Save Project** (or press Ctrl+S)
- Choose a name (e.g., "my_galaxy.swmproj")
- The file saves to the `Saves/` directory

### 6. Export for Your Game

- Click **File → Export Map Data** (or press Ctrl+E)
- Choose a name (e.g., "galaxy_map.json")
- The file exports to the `Exports/` directory
- This contains only the systems data (no templates)

## Navigation

| Action | How To |
|--------|--------|
| Zoom In/Out | Mouse wheel |
| Pan View | WASD or Arrow keys |
| Drag Pan | Middle mouse button + drag |
| Drag Pan | Space + Left mouse + drag |
| Select Item | Left click |
| Edit System | Right click (in Systems Mode) |

## Template Mode Tools

| Tool | Function |
|------|----------|
| Load Template | Add a new background image |
| Delete Template | Remove the selected template |
| Reset Transform | Reset position and scale to defaults |
| Lock/Unlock | Prevent/allow moving and scaling |
| Opacity Slider | Adjust transparency (0-100%) |

**Remember**: In Template Mode, hold **Ctrl** while using the mouse wheel to scale templates!

## Tips

✨ **Use multiple templates** to layer different reference images

🔒 **Lock templates** after positioning to prevent accidental changes

👁️ **Adjust opacity** to see systems clearly through templates

💾 **Save often** - use Ctrl+S frequently

📏 **Use the grid** to align systems precisely

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Project |
| Ctrl+O | Open Project |
| Ctrl+S | Save Project |
| Ctrl+Shift+S | Save Project As |
| Ctrl+E | Export Map Data |
| Ctrl+Q | Quit |
| WASD / Arrows | Pan view |
| Mouse Wheel | Zoom |
| Ctrl+Wheel | Scale template (in Template Mode) |

## Common Tasks

### Load Multiple Templates
1. Enter Template Mode
2. Load first template
3. Click Load Template again
4. Load second template
5. Use opacity to blend them

### Move a System
1. Enter Systems Mode
2. Click and drag the system
3. Release to drop it

### Edit a System Name
1. Enter Systems Mode
2. Right-click the system
3. Change the name
4. Click Save

### Delete a System
1. Enter Systems Mode
2. Right-click the system
3. Click Delete

## Troubleshooting

**Can't see the template?**
- Check the opacity slider - it might be at 0%
- Try zooming out (scroll mouse wheel)

**Can't move the template?**
- Make sure you're in Template Mode (button is green)
- Check if the template is locked (unlock it)

**Can't place systems?**
- Make sure you're in Systems Mode (button is green)
- Don't click on existing systems - click empty space

**Changes aren't saving?**
- Look for the asterisk (*) in the title bar
- Press Ctrl+S to save

## Need Help?

- **README.md** - Complete feature documentation
- **TESTING.md** - Detailed test procedures
- **IMPLEMENTATION.md** - Technical details for developers

## What's Next?

After creating your map:

1. **Export the data** (Ctrl+E) for use in your game
2. **Keep the .swmproj file** so you can make changes later
3. **Add more systems** as your galaxy grows
4. **Share your map** with others

Happy mapping! 🚀✨
