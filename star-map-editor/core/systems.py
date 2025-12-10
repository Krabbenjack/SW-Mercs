"""System placement and management module.

This module handles star system data structures and graphics representation
for the Star Map Editor.
"""

import uuid
from dataclasses import dataclass, field
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsTextItem, QDialog, 
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QComboBox, QTabWidget, QWidget, QCheckBox, QListWidget,
    QAbstractItemView, QScrollArea, QGroupBox
)
from PySide6.QtGui import QColor, QPen, QBrush, QFont

from .data_loader import get_data_loader


@dataclass
class SystemData:
    """Data model for a star system.
    
    WORLD SPACE: System positions are in HSU (Hyperspace Units) coordinates.
    These coordinates are fixed and never affected by:
    - View zoom level
    - Template scaling
    - Icon size changes
    
    Attributes:
        id: Unique identifier for the system (UUID string)
        name: Display name of the system
        position: Position in WORLD SPACE (HSU coordinates as QPointF)
        population_id: Population level ID (from population_levels.json)
        imports: List of imported goods IDs (from goods.json)
        exports: List of exported goods IDs (from goods.json)
        facilities: List of facility IDs (from facility_flags.json)
    """
    id: str
    name: str
    position: QPointF
    population_id: str | None = None
    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    facilities: list[str] = field(default_factory=list)
    
    @classmethod
    def create_new(cls, name: str, position: QPointF):
        """Create a new system with a generated UUID.
        
        Args:
            name: Display name for the system
            position: Position in WORLD SPACE (HSU coordinates)
        """
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            position=position
        )


class SystemItem(QGraphicsEllipseItem):
    """Graphics representation of a star system.
    
    UI SPACE ARCHITECTURE:
    - Icon radius is a visual property in UI space
    - Changing icon size does NOT affect system position (WORLD SPACE)
    - Hitboxes scale with icon size for consistent interaction
    - Label positioning adjusts to icon size
    
    Displays as a colored circle with the system name as a label.
    Supports selection, dragging, and position updates.
    """
    
    # Visual configuration (UI SPACE)
    # Class variable for global icon size setting
    RADIUS = 10  # Default circle radius in scene units
    ICON_SIZE_SMALL = 8
    ICON_SIZE_MEDIUM = 10
    ICON_SIZE_LARGE = 15
    
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
        
        # Use current global radius setting
        self.current_radius = SystemItem.RADIUS
        
        # Set up the circle (UI SPACE: visual size only)
        self.setRect(-self.current_radius, -self.current_radius, 
                     self.current_radius * 2, self.current_radius * 2)
        # WORLD SPACE: position stays in HSU coordinates
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
        self.update_label_position()
        
        # Make label non-interactive
        self.label.setFlag(QGraphicsTextItem.ItemIsMovable, False)
        self.label.setFlag(QGraphicsTextItem.ItemIsSelectable, False)
    
    def set_icon_size(self, radius: float):
        """Update the icon size (UI SPACE only).
        
        Changes visual appearance without affecting world coordinates.
        
        Args:
            radius: New radius for the icon
        """
        self.current_radius = radius
        # Update the ellipse rect (UI SPACE)
        self.setRect(-radius, -radius, radius * 2, radius * 2)
        # Update label position to match new size
        self.update_label_position()
    
    def update_label_position(self):
        """Update label position based on current icon size."""
        self.label.setPos(self.current_radius + 5, -self.current_radius)
    
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
        
        # Stats section
        stats_group = QGroupBox("System Stats")
        stats_layout = QVBoxLayout()
        
        # Population dropdown
        pop_layout = QHBoxLayout()
        pop_label = QLabel("Population:")
        self.population_combo = QComboBox()
        self.population_combo.addItem("-- None --", None)
        
        # Load population levels from JSON
        data_loader = get_data_loader()
        pop_levels = data_loader.get_population_levels()
        for level in pop_levels:
            self.population_combo.addItem(level.get("label", level["id"]), level["id"])
        
        # Set current value
        if system_data and system_data.population_id:
            index = self.population_combo.findData(system_data.population_id)
            if index >= 0:
                self.population_combo.setCurrentIndex(index)
        
        pop_layout.addWidget(pop_label)
        pop_layout.addWidget(self.population_combo)
        stats_layout.addLayout(pop_layout)
        
        # Imports/Exports buttons
        trade_layout = QHBoxLayout()
        
        self.imports_btn = QPushButton("Edit Imports...")
        self.imports_btn.clicked.connect(self.on_edit_imports)
        trade_layout.addWidget(self.imports_btn)
        
        self.exports_btn = QPushButton("Edit Exports...")
        self.exports_btn.clicked.connect(self.on_edit_exports)
        trade_layout.addWidget(self.exports_btn)
        
        stats_layout.addLayout(trade_layout)
        
        # Facilities button
        self.facilities_btn = QPushButton("Edit Facilities...")
        self.facilities_btn.clicked.connect(self.on_edit_facilities)
        stats_layout.addWidget(self.facilities_btn)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
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
        
        # Update system data with stats
        if self.system_data:
            self.system_data.population_id = self.population_combo.currentData()
        
        self.result_action = 'save'
        self.accept()
    
    def on_edit_imports(self):
        """Handle Edit Imports button click."""
        current_imports = self.system_data.imports if self.system_data else []
        dialog = GoodsPopup(current_imports, "Select Imports", self)
        if dialog.exec():
            selected_goods = dialog.get_selected_goods()
            if self.system_data:
                self.system_data.imports = selected_goods
    
    def on_edit_exports(self):
        """Handle Edit Exports button click."""
        current_exports = self.system_data.exports if self.system_data else []
        dialog = GoodsPopup(current_exports, "Select Exports", self)
        if dialog.exec():
            selected_goods = dialog.get_selected_goods()
            if self.system_data:
                self.system_data.exports = selected_goods
    
    def on_edit_facilities(self):
        """Handle Edit Facilities button click."""
        current_facilities = self.system_data.facilities if self.system_data else []
        dialog = FacilityPopup(current_facilities, self)
        if dialog.exec():
            selected_facilities = dialog.get_selected_facilities()
            if self.system_data:
                self.system_data.facilities = selected_facilities
    
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


class GoodsPopup(QDialog):
    """Dialog for selecting goods (imports or exports).
    
    Provides a multi-select list of goods loaded from goods.json.
    """
    
    def __init__(self, selected_goods: list[str], title: str = "Select Goods", parent=None):
        """Initialize the goods selection dialog.
        
        Args:
            selected_goods: List of currently selected goods IDs
            title: Dialog window title
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Search bar (optional but nice to have)
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter goods...")
        self.search_input.textChanged.connect(self._filter_goods)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Goods list
        self.goods_list = QListWidget()
        self.goods_list.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # Load goods from JSON
        data_loader = get_data_loader()
        self.all_goods = data_loader.get_goods()
        
        # Populate list - store goods ID as item data
        for good in self.all_goods:
            item_text = f"{good.get('name', good['id'])} (Tier {good.get('tier', '?')})"
            item = self.goods_list.addItem(item_text)
            # Get the item we just added
            list_item = self.goods_list.item(self.goods_list.count() - 1)
            # Store the goods ID as user data for reliable retrieval
            list_item.setData(Qt.UserRole, good['id'])
            
            # Select if in selected_goods
            if good['id'] in selected_goods:
                list_item.setSelected(True)
        
        layout.addWidget(self.goods_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _filter_goods(self, search_text: str):
        """Filter goods list based on search text.
        
        Args:
            search_text: Text to search for
        """
        search_lower = search_text.lower()
        
        for i in range(self.goods_list.count()):
            item = self.goods_list.item(i)
            item_text = item.text().lower()
            # Show item if search text is in item text, or if search is empty
            item.setHidden(search_lower not in item_text and search_lower != "")
    
    def get_selected_goods(self) -> list[str]:
        """Get the list of selected goods IDs.
        
        Returns:
            List of selected goods IDs
        """
        selected_ids = []
        for item in self.goods_list.selectedItems():
            # Get goods ID from item's user data
            goods_id = item.data(Qt.UserRole)
            if goods_id:
                selected_ids.append(goods_id)
        
        return selected_ids


class FacilityPopup(QDialog):
    """Dialog for selecting facilities.
    
    Provides a tabbed interface with one tab per category,
    each containing checkboxes for facilities.
    """
    
    def __init__(self, selected_facilities: list[str], parent=None):
        """Initialize the facility selection dialog.
        
        Args:
            selected_facilities: List of currently selected facility IDs
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Facilities")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Load facility categories from JSON
        data_loader = get_data_loader()
        categories = data_loader.get_facility_categories()
        
        # Store checkboxes for retrieval
        self.facility_checkboxes = {}
        
        # Create one tab per category
        for category_name, facility_ids in categories.items():
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            
            # Create scrollable area for checkboxes
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            
            # Add checkbox for each facility
            for facility_id in facility_ids:
                # Convert facility_id to readable label
                label = facility_id.replace('_', ' ').title()
                checkbox = QCheckBox(label)
                checkbox.setChecked(facility_id in selected_facilities)
                
                # Store checkbox with facility_id as key
                self.facility_checkboxes[facility_id] = checkbox
                
                scroll_layout.addWidget(checkbox)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            tab_layout.addWidget(scroll)
            
            # Add tab with readable name
            tab_title = category_name.replace('_', ' ').title()
            self.tab_widget.addTab(tab, tab_title)
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def get_selected_facilities(self) -> list[str]:
        """Get the list of selected facility IDs.
        
        Returns:
            List of selected facility IDs
        """
        selected_ids = []
        for facility_id, checkbox in self.facility_checkboxes.items():
            if checkbox.isChecked():
                selected_ids.append(facility_id)
        
        return selected_ids
