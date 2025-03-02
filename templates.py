"""
Template management for the Burmese PDF annotation tool.
"""

import os
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLabel, QPushButton, QMessageBox, QInputDialog, 
                             QFileDialog)
from PyQt5.QtCore import Qt


class TemplateDialog(QDialog):
    """Dialog for managing templates"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Annotation Templates")
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Instructions label
        instructions = QLabel("Select one or more templates to apply (use Ctrl/Shift to select multiple)")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Template list
        self.template_list = QListWidget()
        self.template_list.setSelectionMode(QListWidget.ExtendedSelection)  # Allow multiple selection
        self.load_templates()
        layout.addWidget(QLabel("Available Templates:"))
        layout.addWidget(self.template_list)
        
        # Template preview
        self.preview_label = QLabel("Select a template to see preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(100)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.preview_label)
        
        # Connect single click for preview
        self.template_list.itemClicked.connect(self.preview_template)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_apply = QPushButton("Apply Selected Templates")
        self.btn_save = QPushButton("Save Current as Template")
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_export = QPushButton("Export Templates")
        self.btn_import = QPushButton("Import Templates")
        
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        
        export_import_layout = QHBoxLayout()
        export_import_layout.addWidget(self.btn_export)
        export_import_layout.addWidget(self.btn_import)
        
        layout.addLayout(btn_layout)
        layout.addLayout(export_import_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.btn_apply.clicked.connect(self.apply_template)
        self.btn_save.clicked.connect(self.save_template)
        self.btn_delete.clicked.connect(self.delete_template)
        self.btn_export.clicked.connect(self.export_templates)
        self.btn_import.clicked.connect(self.import_templates)
    
    def load_templates(self):
        """Load saved templates"""
        self.template_list.clear()
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        for file in os.listdir(template_dir):
            if file.endswith(".json"):
                self.template_list.addItem(file.replace(".json", ""))
    
    def preview_template(self, item):
        """Show a preview of the template"""
        template_name = item.text()
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "templates", f"{template_name}.json")
        
        try:
            with open(template_path, 'r') as f:
                template = json.load(f)
            
            # Create a simple text preview
            if template:
                preview_text = f"Template: {template_name}\n"
                text_count = sum(1 for item in template if item.get("type") == "text")
                image_count = sum(1 for item in template if item.get("type") == "image")
                
                preview_text += f"Contains {len(template)} annotations:\n"
                preview_text += f"- {text_count} text annotations\n"
                preview_text += f"- {image_count} image annotations"
                
                self.preview_label.setText(preview_text)
            else:
                self.preview_label.setText("Empty template")
        except Exception:
            self.preview_label.setText("Error loading template preview")
    
    def apply_template(self):
        """Apply the selected templates"""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No templates selected.")
            return
        
        combined_templates = []
        
        for item in selected_items:
            template_name = item.text()
            template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "templates", f"{template_name}.json")
            
            try:
                with open(template_path, 'r') as f:
                    template = json.load(f)
                
                combined_templates.extend(template)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load template '{template_name}': {str(e)}")
                return None
        
        if combined_templates:
            self.accept()
            return combined_templates
        
        return None
    
    def save_template(self):
        """Save current annotations as a template"""
        name, ok = QInputDialog.getText(self, "Save Template", "Template Name:")
        
        if ok and name:
            annotations = self.parent().get_current_annotations()
            if not annotations:
                QMessageBox.warning(self, "Warning", "No annotations to save.")
                return
            
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
            os.makedirs(template_dir, exist_ok=True)
            
            template_path = os.path.join(template_dir, f"{name}.json")
            
            try:
                with open(template_path, 'w') as f:
                    json.dump(annotations, f)
                self.load_templates()
                QMessageBox.information(self, "Success", "Template saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save template: {str(e)}")
    
    def delete_template(self):
        """Delete the selected templates"""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No templates selected.")
            return
        
        # Build confirmation message based on number of selected templates
        if len(selected_items) == 1:
            confirm_message = f"Are you sure you want to delete '{selected_items[0].text()}'?"
        else:
            confirm_message = f"Are you sure you want to delete {len(selected_items)} templates?"
        
        confirm = QMessageBox.question(self, "Confirm Delete", confirm_message)
        
        if confirm == QMessageBox.Yes:
            for item in selected_items:
                template_name = item.text()
                template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                            "templates", f"{template_name}.json")
                
                try:
                    os.remove(template_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not delete template '{template_name}': {str(e)}")
            
            self.load_templates()
    
    def export_templates(self):
        """Export all templates to a file"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Templates", 
                                                "templates.json", "JSON Files (*.json)")
        
        if not file_path:
            return
        
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        templates = {}
        
        try:
            for file in os.listdir(template_dir):
                if file.endswith(".json"):
                    template_name = file.replace(".json", "")
                    with open(os.path.join(template_dir, file), 'r') as f:
                        templates[template_name] = json.load(f)
            
            with open(file_path, 'w') as f:
                json.dump(templates, f)
            
            QMessageBox.information(self, "Success", "Templates exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not export templates: {str(e)}")
    
    def import_templates(self):
        """Import templates from a file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Templates", 
                                                 "", "JSON Files (*.json)")
        
        if not file_path:
            return
        
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        try:
            with open(file_path, 'r') as f:
                templates = json.load(f)
            
            for name, template in templates.items():
                template_path = os.path.join(template_dir, f"{name}.json")
                with open(template_path, 'w') as f:
                    json.dump(template, f)
            
            self.load_templates()
            QMessageBox.information(self, "Success", "Templates imported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not import templates: {str(e)}")