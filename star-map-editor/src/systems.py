"""System placement and management module.

This module handles star system data structures and graphics representation
for the Star Map Editor.
"""

import uuid
from dataclasses import dataclass
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsTextItem, QDialog, 
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
)
from PySide6.QtGui import QColor, QPen, QBrush, QFont


@dataclass
class SystemData:
    """Data model for a star system.
    
    Attributes:
        id: Unique identifier for the system (UUID string)
        name: Display name of the system
        position: Position in scene coordinates (QPointF)
    """
    id: str
    name: str
    position: QPointF
    
    @classmethod
    def create_new(cls, name: str, position: QPointF):
        """Create a new system with a generated UUID."""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            position=position
        )


class SystemItem(QGraphicsEllipseItem):
    """Graphics representation of a star system.
    
    Displays as a colored circle with the system name as a label.
    Supports selection, dragging, and position updates.
    """
    
    # Visual configuration
    RADIUS = 10  # Circle radius in scene units
    NORMAL_COLOR = QColor(100, 150, 255)  # Blue for normal state
    SELECTED_COLOR = QColor(255, 200, 100)  # Orange for selected state
    BORDER_WIDTH = 2
    
    def __init__(self, system_data: SystemData, parent=None):
        """Initialize the system graphics item.
        
        Args:
            system_data: The SystemData object this item represents
            parent: Optional parent graphics item
        """
        super().__init__(parent)
        self.system_data = system_data
        
        # Set up the circle
        self.setRect(-self.RADIUS, -self.RADIUS, 
                     self.RADIUS * 2, self.RADIUS * 2)
        self.setPos(system_data.position)
        
        # Configure appearance
        self.setPen(QPen(Qt.white, self.BORDER_WIDTH))
        self.setBrush(QBrush(self.NORMAL_COLOR))
        
        # Enable interaction
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        
        # Create name label
        self.label = QGraphicsTextItem(parent=self)
        self.label.setPlainText(system_data.name)
        self.label.setDefaultTextColor(Qt.white)
        
        # Position label to the right of the circle
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setPos(self.RADIUS + 5, -self.RADIUS)
        
        # Make label non-interactive
        self.label.setFlag(QGraphicsTextItem.ItemIsMovable, False)
        self.label.setFlag(QGraphicsTextItem.ItemIsSelectable, False)
    
    def update_name(self, name: str):
        """Update the system name and label.
        
        Args:
            name: New name for the system
        """
        self.system_data.name = name
        self.label.setPlainText(name)
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position updates.
        
        Args:
            change: The type of change
            value: The new value
            
        Returns:
            The processed value
        """
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            # Update the data model when position changes
            self.system_data.position = self.pos()
        elif change == QGraphicsEllipseItem.ItemSelectedHasChanged:
            # Update visual appearance when selection changes
            if self.isSelected():
                self.setBrush(QBrush(self.SELECTED_COLOR))
            else:
                self.setBrush(QBrush(self.NORMAL_COLOR))
        
        return super().itemChange(change, value)
    
    def get_system_data(self) -> SystemData:
        """Get the underlying system data.
        
        Returns:
            The SystemData object for this item
        """
        return self.system_data


class SystemDialog(QDialog):
    """Dialog for creating or editing a star system.
    
    Provides a form with system name input and action buttons
    (Save, Delete, Cancel).
    """
    
    def __init__(self, system_data: SystemData = None, is_new: bool = True, parent=None):
        """Initialize the system dialog.
        
        Args:
            system_data: Existing SystemData to edit, or None for new system
            is_new: Whether this is a new system or editing existing
            parent: Parent widget
        """
        super().__init__(parent)
        self.system_data = system_data
        self.is_new = is_new
        self.result_action = None  # 'save', 'delete', or None
        
        self.setWindowTitle("New System" if is_new else "Edit System")
        self.setModal(True)
        self.setMinimumWidth(300)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Name input
        name_layout = QHBoxLayout()
        name_label = QLabel("System Name:")
        self.name_input = QLineEdit()
        if system_data:
            self.name_input.setText(system_data.name)
        else:
            self.name_input.setPlaceholderText("Enter system name...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.on_save)
        button_layout.addWidget(save_btn)
        
        if not is_new:
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(self.on_delete)
            button_layout.addWidget(delete_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.on_cancel)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Focus on name input
        self.name_input.setFocus()
        self.name_input.selectAll()
    
    def on_save(self):
        """Handle Save button click."""
        name = self.name_input.text().strip()
        if not name:
            # Don't allow empty names
            return
        self.result_action = 'save'
        self.accept()
    
    def on_delete(self):
        """Handle Delete button click."""
        self.result_action = 'delete'
        self.accept()
    
    def on_cancel(self):
        """Handle Cancel button click."""
        self.result_action = None
        self.reject()
    
    def get_name(self) -> str:
        """Get the entered system name.
        
        Returns:
            The system name from the input field
        """
        return self.name_input.text().strip()
