"""Template management for the Star Map Editor.

This module handles template graphics representation and interaction.
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtWidgets import QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QPainter

from .project_model import TemplateData


class TemplateItem(QGraphicsPixmapItem):
    """Graphics representation of a template image.
    
    Displays a template image with support for:
    - Position and scale transformations
    - Opacity adjustment
    - Lock state (prevents movement/scaling)
    - Selection for editing
    """
    
    def __init__(self, template_data: TemplateData, parent=None):
        """Initialize the template graphics item.
        
        Args:
            template_data: The TemplateData object this item represents
            parent: Optional parent graphics item
        """
        super().__init__(parent)
        self.template_data = template_data
        
        # Load the pixmap
        pixmap = QPixmap(template_data.filepath)
        if pixmap.isNull():
            # Create a placeholder if image can't be loaded
            pixmap = QPixmap(100, 100)
            pixmap.fill(Qt.gray)
        
        self.setPixmap(pixmap)
        
        # Apply stored transformations
        self.setPos(template_data.position[0], template_data.position[1])
        self.setScale(template_data.scale)
        self.setOpacity(template_data.opacity)
        self.setZValue(template_data.z_order)
        
        # Configure interaction based on lock state
        self.update_lock_state()
        
        # Enable selection
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsPixmapItem.ItemSendsGeometryChanges, True)
        
        # Set transform origin to center for scaling
        self.setTransformOriginPoint(self.boundingRect().center())
    
    def update_lock_state(self):
        """Update interaction flags based on lock state."""
        is_locked = self.template_data.locked
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, not is_locked)
    
    def update_position(self):
        """Update data model with current position."""
        pos = self.pos()
        self.template_data.position = (pos.x(), pos.y())
    
    def update_scale_data(self):
        """Update data model with current scale."""
        self.template_data.scale = self.scale()
    
    def update_opacity_data(self):
        """Update data model with current opacity."""
        self.template_data.opacity = self.opacity()
    
    def set_template_opacity(self, opacity: float):
        """Set the template opacity.
        
        Args:
            opacity: Opacity value (0.0 = transparent, 1.0 = opaque)
        """
        self.setOpacity(opacity)
        self.template_data.opacity = opacity
    
    def set_locked(self, locked: bool):
        """Set the template lock state.
        
        Args:
            locked: Whether the template should be locked
        """
        self.template_data.locked = locked
        self.update_lock_state()
    
    def reset_transform(self):
        """Reset position and scale to defaults."""
        self.setPos(0, 0)
        self.setScale(1.0)
        self.template_data.position = (0.0, 0.0)
        self.template_data.scale = 1.0
    
    def scale_relative(self, factor: float):
        """Scale the template by a relative factor.
        
        Args:
            factor: Scale multiplier
        """
        if self.template_data.locked:
            return
        
        new_scale = self.scale() * factor
        # Clamp scale to reasonable limits
        new_scale = max(0.1, min(10.0, new_scale))
        self.setScale(new_scale)
        self.template_data.scale = new_scale
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position updates.
        
        Args:
            change: The type of change
            value: The new value
            
        Returns:
            The processed value
        """
        if change == QGraphicsPixmapItem.ItemPositionHasChanged:
            # Update the data model when position changes
            self.update_position()
        
        return super().itemChange(change, value)
    
    def get_template_data(self) -> TemplateData:
        """Get the underlying template data.
        
        Returns:
            The TemplateData object for this item
        """
        return self.template_data
