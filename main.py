"""
Burmese PDF Annotation Tool main application.
This is the entry point of the application.
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                           QToolBar, QAction, QFileDialog, QMessageBox,
                           QSplitter, QLabel, QDialog, QVBoxLayout, QActionGroup)
from PyQt5.QtCore import Qt

from thumbnails import PDFThumbnailWidget
from pdf_viewer import PDFViewerWidget
from text_properties import TextPropertiesWidget
from templates import TemplateDialog

class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Burmese PDF Annotation Tool")
        self.resize(1200, 800)
        
        # Initialize central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        # Create split view
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # Create left panel with thumbnails
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add a label above thumbnails
        thumbnail_label = QLabel("Pages")
        thumbnail_label.setAlignment(Qt.AlignCenter)
        thumbnail_label.setStyleSheet("font-weight: bold; padding: 5px;")
        left_layout.addWidget(thumbnail_label)
        
        # Create vertical thumbnails
        self.thumbnails = PDFThumbnailWidget()
        self.thumbnails.page_selected.connect(self.on_thumbnail_selected)
        left_layout.addWidget(self.thumbnails)
        
        # Create text properties widget
        self.text_properties = TextPropertiesWidget(self)
        
        # Create viewer widget
        self.viewer = PDFViewerWidget(self)
        
        # Add to splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.viewer)
        
        # Set initial splitter sizes
        self.splitter.setSizes([150, 1050])
        
        # Create toolbar
        self.create_toolbar()
        
        # Add text properties dock
        self.addDockWidget(Qt.RightDockWidgetArea, self.text_properties)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
    
    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = QToolBar("Tools")
        self.addToolBar(toolbar)
        
        # Open action
        open_action = QAction("Open PDF", self)
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)
        
        # Save action
        save_action = QAction("Save PDF", self)
        save_action.triggered.connect(self.save_pdf)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Tool selection
        self.tool_action_group = QActionGroup(self)
        self.tool_action_group.setExclusive(True)
        
        # Select tool
        self.select_action = QAction("Select", self)
        self.select_action.setCheckable(True)
        self.select_action.setChecked(True)  # Select is the default tool
        self.select_action.triggered.connect(lambda: self.set_tool("select"))
        self.tool_action_group.addAction(self.select_action)
        toolbar.addAction(self.select_action)
        
        # Add Text tool
        self.text_action = QAction("Add Text", self)
        self.text_action.setCheckable(True)
        self.text_action.triggered.connect(lambda: self.set_tool("text"))
        self.tool_action_group.addAction(self.text_action)
        toolbar.addAction(self.text_action)
        
        # Add Image tool
        self.image_action = QAction("Add Image", self)
        self.image_action.setCheckable(True)
        self.image_action.triggered.connect(lambda: self.set_tool("image"))
        self.tool_action_group.addAction(self.image_action)
        toolbar.addAction(self.image_action)
        
        toolbar.addSeparator()
        
        # Template actions
        template_action = QAction("Templates", self)
        template_action.triggered.connect(self.show_templates)
        toolbar.addAction(template_action)
        
        # Zoom actions
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        # Apply stylesheet for button highlighting
        toolbar.setStyleSheet("""
            QToolButton:checked {
                background-color: #c2d2e9;
                border: 1px solid #99b0d1;
                border-radius: 2px;
            }
        """)
    
    def open_pdf(self):
        """Open a PDF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)"
        )
        
        if file_path:
            if self.viewer.load_document(file_path):
                self.thumbnails.load_document(self.viewer.doc)
                self.statusBar().showMessage(f"Loaded: {file_path}")
    
    def save_pdf(self):
        """Save the annotated PDF"""
        if not self.viewer.doc:
            QMessageBox.warning(self, "Warning", "No document loaded.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "", "PDF Files (*.pdf)"
        )
        
        if file_path:
            if self.viewer.save_annotations_to_pdf(file_path):
                self.statusBar().showMessage(f"Saved: {file_path}")
    
    def set_tool(self, tool):
        """Set the current tool"""
        self.viewer.current_tool = tool
        
        # Update action checked states
        if tool == "select":
            self.select_action.setChecked(True)
        elif tool == "text":
            self.text_action.setChecked(True)
        elif tool == "image":
            self.image_action.setChecked(True)
            
        self.statusBar().showMessage(f"Active tool: {tool}")
    
    def on_thumbnail_selected(self, page_num):
        """Handle thumbnail selection"""
        self.viewer.go_to_page(page_num)
    
    def show_templates(self):
        """Show template management dialog"""
        dialog = TemplateDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            templates = dialog.apply_template()
            if templates:
                self.viewer.apply_templates(templates)
                self.statusBar().showMessage(f"Applied {len(templates)} annotation(s) from template")
    
    def zoom_in(self):
        """Zoom in"""
        self.viewer.scale_factor *= 1.2
        self.viewer.update_page_display()
    
    def zoom_out(self):
        """Zoom out"""
        self.viewer.scale_factor /= 1.2
        self.viewer.update_page_display()
    
    def get_current_annotations(self):
        """Get current page annotations"""
        return self.viewer.get_current_annotations()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())