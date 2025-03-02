"""
Text properties widget for the Burmese PDF annotation tool.
"""

from PyQt5.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QSpinBox, QPushButton, 
                            QColorDialog, QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt

class TextPropertiesWidget(QDockWidget):
    """Dock widget for text properties"""
    def __init__(self, parent=None):
        super().__init__("Text Properties", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.text_color = "red"
        self.bg_color = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI elements"""
        text_widget = QWidget()
        layout = QVBoxLayout()
        
        # Text input
        layout.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        layout.addWidget(self.text_input)
        
        # Font size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Font Size:"))
        self.font_size_input = QSpinBox()
        self.font_size_input.setRange(6, 72)
        self.font_size_input.setValue(13)  # Default font size
        size_layout.addWidget(self.font_size_input)
        layout.addLayout(size_layout)
        
        # Text color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Text Color:"))
        self.color_btn = QPushButton()
        self.color_btn.setStyleSheet("background-color: red;")  # Default color
        self.color_btn.clicked.connect(self.choose_text_color)
        color_layout.addWidget(self.color_btn)
        layout.addLayout(color_layout)
        
        # Background color
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background:"))
        self.bg_btn = QPushButton("None")
        self.bg_btn.clicked.connect(self.choose_bg_color)
        bg_layout.addWidget(self.bg_btn)
        layout.addLayout(bg_layout)
        
        # Text rotation
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("Rotation:"))
        self.rotation_input = QSpinBox()
        self.rotation_input.setRange(0, 360)
        self.rotation_input.setValue(0)
        rotation_layout.addWidget(self.rotation_input)
        layout.addLayout(rotation_layout)
        
        # Text formatting
        format_group = QGroupBox("Text Formatting")
        format_layout = QHBoxLayout()
        
        self.bold_check = QCheckBox("Bold")
        self.italic_check = QCheckBox("Italic")
        self.underline_check = QCheckBox("Underline")
        
        format_layout.addWidget(self.bold_check)
        format_layout.addWidget(self.italic_check)
        format_layout.addWidget(self.underline_check)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Add some spacing
        layout.addStretch()
        
        text_widget.setLayout(layout)
        self.setWidget(text_widget)
    
    def get_text(self):
        """Get the text from the input field"""
        return self.text_input.text()
    
    def get_font_size(self):
        """Get the font size"""
        return self.font_size_input.value()
    
    def get_text_color(self):
        """Get the text color"""
        return self.text_color
    
    def get_background_color(self):
        """Get the background color"""
        return self.bg_color
    
    def get_rotation(self):
        """Get the rotation angle"""
        return self.rotation_input.value()
    
    def get_bold(self):
        """Get bold state"""
        return self.bold_check.isChecked()
    
    def get_italic(self):
        """Get italic state"""
        return self.italic_check.isChecked()
    
    def get_underline(self):
        """Get underline state"""
        return self.underline_check.isChecked()
    
    def choose_text_color(self):
        """Open color dialog for text color"""
        color = QColorDialog.getColor()
        
        if color.isValid():
            self.text_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.text_color};")
    
    def choose_bg_color(self):
        """Open color dialog for background color"""
        color = QColorDialog.getColor()
        
        if color.isValid():
            self.bg_color = color.name()
            self.bg_btn.setText("")
            self.bg_btn.setStyleSheet(f"background-color: {self.bg_color};")
        else:
            self.bg_color = None
            self.bg_btn.setText("None")
            self.bg_btn.setStyleSheet("")