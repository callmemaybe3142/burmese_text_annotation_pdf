"""
PDF viewer widget for the Burmese PDF annotation tool.
"""

import io
import fitz
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                           QLabel, QPushButton, QMenu, QInputDialog,
                           QMessageBox, QColorDialog, QFileDialog)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt 

from annotations import TextAnnotation, ImageAnnotation
from PIL import Image

class PDFViewerWidget(QWidget):
    """Widget to display and annotate PDF"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.doc = None
        self.current_page = 0
        self.annotations = {}  # Dictionary mapping page numbers to lists of annotations
        self.current_tool = "select"  # Default tool
        self.selected_annotation = None
        self.dragging = False
        self.resizing = False
        self.drag_start = None
        self.scale_factor = 2.0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI elements"""
        self.layout = QVBoxLayout()
        
        # PDF display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        
        self.layout.addWidget(self.scroll_area)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("< Previous")
        self.next_btn = QPushButton("Next >")
        self.page_label = QLabel("Page: 0 / 0")
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_btn)
        
        self.layout.addLayout(nav_layout)
        
        self.setLayout(self.layout)
        
        # Connect signals
        self.prev_btn.clicked.connect(self.previous_page)
        self.next_btn.clicked.connect(self.next_page)
        
        # Mouse events
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.mouse_press_event
        self.image_label.mouseMoveEvent = self.mouse_move_event
        self.image_label.mouseReleaseEvent = self.mouse_release_event
        self.image_label.contextMenuEvent = self.context_menu_event
    
    def load_document(self, file_path):
        """Load PDF document"""
        try:
            self.doc = fitz.open(file_path)
            self.current_page = 0
            self.annotations = {}
            
            # Initialize annotations dict for all pages
            for i in range(len(self.doc)):
                self.annotations[i] = []
            
            self.update_page_display()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load PDF: {str(e)}")
            return False
    
    def update_page_display(self):
        """Update the display for the current page"""
        if not self.doc:
            return
        
        # Update page label
        self.page_label.setText(f"Page: {self.current_page + 1} / {len(self.doc)}")
        
        # Render page
        page = self.doc[self.current_page]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.scale_factor, self.scale_factor))
        
        # Convert to QImage
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        
        # Create a painter to draw annotations on the pixmap
        if self.current_page in self.annotations:
            painter = QPainter(pixmap)
            
            for annotation in self.annotations[self.current_page]:
                # Update annotation scale to match current zoom
                if isinstance(annotation, TextAnnotation):
                    annotation.render_image(self.scale_factor)
                else:
                    annotation.update_scale(self.scale_factor)
                
                # Get QImage from annotation
                qimg = annotation.get_qimage()
                
                # Draw the image at the annotation position
                painter.drawImage(annotation.x, annotation.y, qimg)
                
                # Draw selection box if selected
                if annotation.selected:
                    painter.setPen(Qt.blue)
                    painter.drawRect(annotation.rect)
                    
                    # Draw resize handle for image annotations
                    if isinstance(annotation, ImageAnnotation):
                        handle_size = max(5, int(10 * self.scale_factor))
                        painter.setBrush(QColor(0, 0, 255, 128))
                        painter.drawRect(
                            annotation.x + annotation.width - handle_size,
                            annotation.y + annotation.height - handle_size,
                            handle_size,
                            handle_size
                        )
            
            painter.end()
        
        # Set the pixmap
        self.image_label.setPixmap(pixmap)
    
    def go_to_page(self, page_num):
        """Go to the specified page"""
        if self.doc and 0 <= page_num < len(self.doc):
            self.current_page = page_num
            self.update_page_display()
    
    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_display()
    
    def next_page(self):
        """Go to next page"""
        if self.doc and self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.update_page_display()
    
    def add_text_annotation(self, text, screen_x, screen_y, font_size=13, color="red", 
                          rotation=0, bold=False, italic=False, underline=False, background=None):
        """Add a text annotation to the current page
        
        Args:
            text: The text to add
            screen_x: X coordinate in screen space
            screen_y: Y coordinate in screen space
        """
        if not self.doc:
            return
        
        # First create a temporary annotation at scale factor 1.0 (PDF scale)
        temp_annotation = TextAnnotation(
            text=text,
            x=0,  # Temporary position
            y=0,
            font_size=font_size,
            color=color,
            rotation=rotation,
            bold=bold,
            italic=italic,
            underline=underline,
            background=background
        )
        
        # Render at PDF scale (1.0) to get native size
        temp_annotation.scale_factor = 1.0
        temp_annotation.render_image(1.0)
        
        # Get native PDF dimensions
        pdf_width = temp_annotation.img.width
        pdf_height = temp_annotation.img.height
        
        # Convert click point to PDF coordinates
        pdf_click_x = screen_x / self.scale_factor
        pdf_click_y = screen_y / self.scale_factor
        
        # Center in PDF coordinates
        pdf_x = pdf_click_x - (pdf_width / 2)
        pdf_y = pdf_click_y - (pdf_height / 2)
        
        # Now create the actual annotation with centered position
        annotation = TextAnnotation(
            text=text,
            x=pdf_x,  # Store as PDF coordinates
            y=pdf_y,
            font_size=font_size,
            color=color,
            rotation=rotation,
            bold=bold,
            italic=italic,
            underline=underline,
            background=background
        )
        
        # Set the current scale factor
        annotation.scale_factor = self.scale_factor
        
        # Render with the current scale factor
        annotation.render_image(self.scale_factor)
        
        # Add to annotations list
        self.annotations[self.current_page].append(annotation)
        self.update_page_display()
    
    def add_image_annotation(self, image_path, screen_x, screen_y):
        """Add an image annotation to the current page
        
        Args:
            image_path: Path to the image file
            screen_x: X coordinate in screen space
            screen_y: Y coordinate in screen space
        """
        if not self.doc:
            return
        
        try:
            # Create annotation with PDF coordinates
            # The ImageAnnotation constructor will handle resizing large images
            
            # Convert click point to PDF coordinates
            pdf_click_x = float(screen_x) / self.scale_factor
            pdf_click_y = float(screen_y) / self.scale_factor
            
            # Create the annotation - we'll adjust position after measuring
            annotation = ImageAnnotation(image_path, 0, 0)
            
            # Now center the image on the click point
            annotation.pdf_x = pdf_click_x - (annotation.pdf_width / 2)
            annotation.pdf_y = pdf_click_y - (annotation.pdf_height / 2)
            
            # Set the current scale factor
            annotation.scale_factor = self.scale_factor
            
            # Update screen coordinates based on scale
            annotation.update_scale(self.scale_factor)
            
            # Add to annotations list
            self.annotations[self.current_page].append(annotation)
            self.update_page_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not add image: {str(e)}")
    
    def find_annotation_at_position(self, pos):
        """Find annotation at the given position"""
        if self.current_page not in self.annotations:
            return None
        
        # Check in reverse order (top-most first)
        for annotation in reversed(self.annotations[self.current_page]):
            if annotation.contains_point(pos):
                return annotation
        
        return None
    
    def select_annotation(self, annotation):
        """Select the specified annotation"""
        # Deselect any current selection
        if self.selected_annotation:
            self.selected_annotation.selected = False
        
        self.selected_annotation = annotation
        
        if annotation:
            annotation.selected = True
        
        self.update_page_display()
    
    def delete_selected_annotation(self):
        """Delete the currently selected annotation"""
        if self.selected_annotation and self.current_page in self.annotations:
            self.annotations[self.current_page].remove(self.selected_annotation)
            self.selected_annotation = None
            self.update_page_display()
    
    def mouse_press_event(self, event):
        """Handle mouse press events"""
        pos = event.pos()
        
        if event.button() == Qt.LeftButton:
            if self.current_tool == "select":
                # Check if we're clicking on the resize handle of a selected image annotation
                if (self.selected_annotation and 
                    isinstance(self.selected_annotation, ImageAnnotation) and 
                    self.selected_annotation.is_on_resize_handle(pos)):
                    self.resizing = True
                    self.drag_start = pos
                else:
                    # Select annotation under cursor
                    annotation = self.find_annotation_at_position(pos)
                    self.select_annotation(annotation)
                    
                    if annotation:
                        self.dragging = True
                        self.drag_start = pos
            
            elif self.current_tool == "text":
                # Get text input from parent
                text = self.parent.text_properties.get_text()
                if text:
                    font_size = self.parent.text_properties.get_font_size()
                    color = self.parent.text_properties.get_text_color()
                    rotation = self.parent.text_properties.get_rotation()
                    bold = self.parent.text_properties.get_bold()
                    italic = self.parent.text_properties.get_italic()
                    underline = self.parent.text_properties.get_underline()
                    background = self.parent.text_properties.get_background_color()
                    
                    self.add_text_annotation(
                        text, pos.x(), pos.y(), font_size, color, 
                        rotation, bold, italic, underline, background
                    )
                    
                    # Automatically switch back to Select mode after adding text
                    self.parent.set_tool("select")
            
            elif self.current_tool == "image":
                # Show file dialog to select image
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
                )
                
                if file_path:
                    self.add_image_annotation(file_path, pos.x(), pos.y())
                    
                    # Automatically switch back to Select mode after adding image
                    self.parent.set_tool("select")
    
    def mouse_move_event(self, event):
        """Handle mouse move events"""
        pos = event.pos()
        
        if self.dragging and self.selected_annotation and self.drag_start:
            # Calculate movement delta
            dx = pos.x() - self.drag_start.x()
            dy = pos.y() - self.drag_start.y()
            
            # Move the annotation
            self.selected_annotation.move(dx, dy)
            
            # Update drag start point
            self.drag_start = pos
            
            # Update display
            self.update_page_display()
        
        elif self.resizing and self.selected_annotation and isinstance(self.selected_annotation, ImageAnnotation):
            # Calculate new dimensions
            new_width = pos.x() - self.selected_annotation.x
            new_height = pos.y() - self.selected_annotation.y
            
            # Resize the annotation
            self.selected_annotation.resize(new_width, new_height)
            
            # Update display
            self.update_page_display()
        
        # Update cursor based on context
        annotation = self.find_annotation_at_position(pos)
        
        if annotation and isinstance(annotation, ImageAnnotation) and annotation.is_on_resize_handle(pos):
            self.setCursor(Qt.SizeFDiagCursor)
        elif annotation:
            self.setCursor(Qt.OpenHandCursor if not self.dragging else Qt.ClosedHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    
    def mouse_release_event(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.drag_start = None
    
    def context_menu_event(self, event):
        """Show context menu for annotations"""
        annotation = self.find_annotation_at_position(event.pos())
        
        if annotation:
            self.select_annotation(annotation)
            
            menu = QMenu(self)
            delete_action = menu.addAction("Delete")
            
            if isinstance(annotation, TextAnnotation):
                edit_action = menu.addAction("Edit Text")
                
                # Add formatting options
                format_menu = menu.addMenu("Format")
                color_action = format_menu.addAction("Change Color")
                size_action = format_menu.addAction("Change Size")
                rotation_action = format_menu.addAction("Rotate")
                
                # Connect additional actions
                edit_action.triggered.connect(self.edit_selected_text)
                color_action.triggered.connect(self.change_text_color)
                size_action.triggered.connect(self.change_text_size)
                rotation_action.triggered.connect(self.rotate_text)
            
            # Connect common actions
            delete_action.triggered.connect(self.delete_selected_annotation)
            
            menu.exec_(event.globalPos())
    
    def edit_selected_text(self):
        """Edit the text of the selected annotation"""
        if self.selected_annotation and isinstance(self.selected_annotation, TextAnnotation):
            text, ok = QInputDialog.getText(
                self, "Edit Text", "Enter Text:", 
                text=self.selected_annotation.text
            )
            
            if ok and text:
                self.selected_annotation.text = text
                self.selected_annotation.render_image()
                self.update_page_display()
    
    def change_text_color(self):
        """Change the color of the selected text annotation"""
        if self.selected_annotation and isinstance(self.selected_annotation, TextAnnotation):
            color = QColorDialog.getColor()
            
            if color.isValid():
                self.selected_annotation.color = color.name()
                self.selected_annotation.render_image()
                self.update_page_display()
    
    def change_text_size(self):
        """Change the font size of the selected text annotation"""
        if self.selected_annotation and isinstance(self.selected_annotation, TextAnnotation):
            size, ok = QInputDialog.getInt(
                self, "Font Size", "Enter font size:", 
                value=self.selected_annotation.font_size,
                min=6, max=72
            )
            
            if ok:
                self.selected_annotation.font_size = size
                self.selected_annotation.render_image()
                self.update_page_display()
    
    def rotate_text(self):
        """Rotate the selected text annotation"""
        if self.selected_annotation and isinstance(self.selected_annotation, TextAnnotation):
            angle, ok = QInputDialog.getInt(
                self, "Rotation", "Enter rotation angle (0-360):", 
                value=self.selected_annotation.rotation,
                min=0, max=360
            )
            
            if ok:
                self.selected_annotation.rotation = angle
                self.selected_annotation.render_image()
                self.update_page_display()
    
    def save_annotations_to_pdf(self, output_path):
        """Save annotations to a new PDF file"""
        if not self.doc:
            return False
        
        # Create a copy of the original document
        out_doc = fitz.open(self.doc)
        
        # Add annotations to each page
        for page_num, annotations in self.annotations.items():
            if not annotations:
                continue
            
            page = out_doc[page_num]
            
            for annotation in annotations:
                if isinstance(annotation, TextAnnotation):
                    # For saving, create a fresh image at scale 1.0 (PDF native size)
                    annotation.render_image(1.0)  # Render at PDF scale
                    
                    # Convert PIL image to bytes
                    img_bytes = io.BytesIO()
                    annotation.img.save(img_bytes, format="PNG")
                    img_bytes.seek(0)
                    
                    # Define rectangle for image placement using PDF coordinates
                    rect = fitz.Rect(
                        annotation.pdf_x, 
                        annotation.pdf_y, 
                        annotation.pdf_x + annotation.img.width,
                        annotation.pdf_y + annotation.img.height
                    )
                    
                    # Insert image
                    page.insert_image(rect, stream=img_bytes)
                    
                    # Restore the scale to match the current view
                    annotation.render_image(self.scale_factor)
                
                elif isinstance(annotation, ImageAnnotation):
                    # Open the original image
                    original_img = Image.open(annotation.image_path)
                    
                    # Resize to the PDF dimensions
                    pdf_img = original_img.resize(
                        (int(annotation.pdf_width), int(annotation.pdf_height)), 
                        Image.Resampling.LANCZOS
                    )
                    
                    # Convert to bytes
                    img_bytes = io.BytesIO()
                    pdf_img.save(img_bytes, format="PNG")
                    img_bytes.seek(0)
                    
                    # Define rectangle for image placement using PDF coordinates
                    rect = fitz.Rect(
                        annotation.pdf_x,
                        annotation.pdf_y,
                        annotation.pdf_x + annotation.pdf_width,
                        annotation.pdf_y + annotation.pdf_height
                    )
                    
                    # Insert image from memory
                    page.insert_image(rect, stream=img_bytes)
        
        # Save the document
        try:
            out_doc.save(output_path)
            out_doc.close()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save PDF: {str(e)}")
            return False
    
    def get_current_annotations(self):
        """Get annotations on the current page as serializable dict"""
        if self.current_page not in self.annotations:
            return []
        
        return [annotation.to_dict() for annotation in self.annotations[self.current_page]]
    
    def apply_templates(self, templates_data):
        """Apply multiple templates to the current page
        
        Args:
            templates_data: List of annotation data from templates
        """
        if not self.doc:
            return
        
        # Clear current annotations if requested
        # For now, we'll just add to existing annotations
        # self.annotations[self.current_page] = []
        
        # Add template annotations
        for item in templates_data:
            if item["type"] == "text":
                annotation = TextAnnotation.from_dict(item)
                # Set the current scale factor
                annotation.scale_factor = self.scale_factor
                annotation.render_image(self.scale_factor)
                self.annotations[self.current_page].append(annotation)
            elif item["type"] == "image":
                try:
                    annotation = ImageAnnotation.from_dict(item)
                    # Set the current scale factor
                    annotation.scale_factor = self.scale_factor
                    annotation.update_scale(self.scale_factor)
                    self.annotations[self.current_page].append(annotation)
                except Exception as e:
                    QMessageBox.warning(self, "Warning", 
                                      f"Could not add image from template: {str(e)}")
        
        self.update_page_display()
    
    # Keep the legacy method for backwards compatibility
    def apply_template(self, template_data):
        """Apply a template to the current page (legacy method)"""
        return self.apply_templates(template_data)