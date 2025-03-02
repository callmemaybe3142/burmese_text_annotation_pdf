"""
Annotation classes for the Burmese PDF annotation tool.
This module contains the TextAnnotation and ImageAnnotation classes.
"""

import io
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtCore import QRect, QPoint, QByteArray
from PyQt5.QtGui import QImage

class TextAnnotation:
    """Class to represent a text annotation on the PDF"""
    def __init__(self, text, x, y, font_size=13, color="red", font_path="pyidaungsu.ttf", 
                rotation=0, bold=False, italic=False, underline=False, background=None):
        self.text = text
        # Store the original PDF coordinates (unscaled)
        self.pdf_x = float(x)
        self.pdf_y = float(y)
        # For screen display (will be updated with zoom)
        self.x = int(x)
        self.y = int(y)
        self.font_size = font_size
        self.color = color
        self.font_path = font_path
        self.rotation = rotation
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.background = background
        self.img = None
        self.rect = None
        self.selected = False
        self.scale_factor = 1.0  # Current scale factor for rendering
        self.render_image()
    
    def render_image(self, scale_factor=None):
        """Render the text as an image
        
        Args:
            scale_factor: Scale factor for rendering (zoom level)
        """
        if scale_factor is not None:
            self.scale_factor = scale_factor
            
        # Determine size needed - this is approximate and may need adjustment
        sample_img = Image.new("RGBA", (500, 100), (255, 255, 255, 0))
        sample_draw = ImageDraw.Draw(sample_img)
        
        # Scale font size by the current scale factor
        actual_font_size = int(self.font_size * self.scale_factor)
        font = ImageFont.truetype(self.font_path, actual_font_size)
        
        # Get text dimensions to create appropriate sized image
        text_bbox = sample_draw.textbbox((0, 0), self.text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Add padding (also scaled)
        padding = int(10 * self.scale_factor)
        width = text_width + (padding * 2)
        height = text_height + (padding * 2)
        
        # Create image with transparent background
        self.img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(self.img)
        
        # Draw background if specified
        if self.background:
            draw.rectangle([0, 0, width, height], fill=self.background)
        
        # Draw text
        draw.text((padding, padding), self.text, font=font, fill=self.color)
        
        # Apply rotation if needed
        if self.rotation != 0:
            self.img = self.img.rotate(self.rotation, expand=True)
        
        # Update screen coordinates based on PDF coordinates and scale factor
        self.x = int(self.pdf_x * self.scale_factor)
        self.y = int(self.pdf_y * self.scale_factor)
        
        # Update rect in screen coordinates
        self.rect = QRect(self.x, self.y, self.img.width, self.img.height)
    
    def contains_point(self, point):
        """Check if the given point is within this annotation"""
        if self.rect:
            return self.rect.contains(point)
        return False
    
    def move(self, dx, dy):
        """Move the annotation by the given delta in screen coordinates
        
        Args:
            dx: Delta x in screen coordinates
            dy: Delta y in screen coordinates
        """
        # Update screen coordinates
        self.x += dx
        self.y += dy
        
        # Update PDF coordinates based on scale factor
        self.pdf_x = float(self.x) / self.scale_factor
        self.pdf_y = float(self.y) / self.scale_factor
        
        # Update the rectangle
        self.rect.moveTopLeft(QPoint(self.x, self.y))
    
    def to_dict(self):
        """Convert annotation to dictionary for serialization"""
        return {
            "type": "text",
            "text": self.text,
            "x": self.pdf_x,  # Store PDF coordinates, not screen coordinates
            "y": self.pdf_y,
            "font_size": self.font_size,
            "color": self.color,
            "font_path": self.font_path,
            "rotation": self.rotation,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "background": self.background
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create annotation from dictionary"""
        return cls(
            text=data["text"],
            x=data["x"],
            y=data["y"],
            font_size=data["font_size"],
            color=data["color"],
            font_path=data.get("font_path", "pyidaungsu.ttf"),
            rotation=data.get("rotation", 0),
            bold=data.get("bold", False),
            italic=data.get("italic", False),
            underline=data.get("underline", False),
            background=data.get("background", None)
        )

    def get_qimage(self):
        """Convert PIL image to QImage for rendering"""
        data = io.BytesIO()
        self.img.save(data, format='PNG')
        img_data = data.getvalue()
        return QImage.fromData(QByteArray(img_data))
        
    def update_scale(self, scale_factor):
        """Update the scale factor and recalculate screen coordinates"""
        self.scale_factor = scale_factor
        
        # Update screen coordinates based on PDF coordinates
        self.x = int(self.pdf_x * scale_factor)
        self.y = int(self.pdf_y * scale_factor)
        
        # Update screen dimensions
        new_width = int(self.pdf_width * scale_factor)
        new_height = int(self.pdf_height * scale_factor)
        
        # Only resize if dimensions have changed significantly
        if abs(self.width - new_width) > 2 or abs(self.height - new_height) > 2:
            self.width = new_width
            self.height = new_height
            self.img = self.img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        # Update rectangle - ensure all values are integers
        self.rect = QRect(self.x, self.y, self.width, self.height)


class ImageAnnotation:
    """Class to represent an image annotation on the PDF"""
    def __init__(self, image_path, x, y, width=None, height=None):
        self.image_path = image_path
        # Store the original PDF coordinates (unscaled)
        self.pdf_x = float(x)
        self.pdf_y = float(y)
        # For screen display (will be updated with zoom)
        self.x = int(x)
        self.y = int(y)
        
        # Load the image
        self.img = Image.open(image_path)
        
        # Resize large images to a reasonable size to prevent crashes
        MAX_SIZE = 500  # Maximum dimension (width or height) in pixels
        
        # Calculate the resize factor if the image is too large
        orig_width, orig_height = self.img.size
        resize_factor = 1.0
        
        if orig_width > MAX_SIZE or orig_height > MAX_SIZE:
            # Determine the resize factor based on the largest dimension
            if orig_width >= orig_height:
                resize_factor = MAX_SIZE / orig_width
            else:
                resize_factor = MAX_SIZE / orig_height
            
            # Resize the image while maintaining aspect ratio
            new_width = int(orig_width * resize_factor)
            new_height = int(orig_height * resize_factor)
            self.img = self.img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Store original dimensions for PDF (potentially resized)
        if width is None or height is None:
            self.pdf_width = float(self.img.width)
            self.pdf_height = float(self.img.height)
        else:
            self.pdf_width = float(width)
            self.pdf_height = float(height)
            # Resize if explicit dimensions provided
            self.img = self.img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        
        self.width = int(self.img.width)
        self.height = int(self.img.height)
        self.rect = QRect(self.x, self.y, self.width, self.height)
        self.selected = False
        self.resize_handle = None
        self.scale_factor = 1.0  # Current scale factor for rendering
    
    def contains_point(self, point):
        """Check if the given point is within this annotation"""
        if self.rect:
            return self.rect.contains(point)
        return False
    
    def is_on_resize_handle(self, point):
        """Check if the point is on a resize handle"""
        # Bottom-right corner is the resize handle
        handle_size = 10
        handle_rect = QRect(
            int(self.x + self.width - handle_size),
            int(self.y + self.height - handle_size),
            handle_size, 
            handle_size
        )
        return handle_rect.contains(point)
    
    def move(self, dx, dy):
        """Move the annotation by the given delta in screen coordinates"""
        # Update screen coordinates
        self.x += dx
        self.y += dy
        
        # Update PDF coordinates based on scale factor
        self.pdf_x = self.x / self.scale_factor
        self.pdf_y = self.y / self.scale_factor
        
        # Update the rectangle
        self.rect.moveTopLeft(QPoint(self.x, self.y))
    
    def resize(self, width, height):
        """Resize the image annotation in screen coordinates"""
        # Update screen dimensions
        self.width = max(20, width)  # Minimum width
        self.height = max(20, height)  # Minimum height
        
        # Update PDF dimensions
        self.pdf_width = self.width / self.scale_factor
        self.pdf_height = self.height / self.scale_factor
        
        # Resize the image
        self.img = self.img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        # Update rectangle
        self.rect = QRect(self.x, self.y, self.width, self.height)
    
    def to_dict(self):
        """Convert annotation to dictionary for serialization"""
        return {
            "type": "image",
            "image_path": self.image_path,
            "x": self.pdf_x,  # Store PDF coordinates, not screen coordinates
            "y": self.pdf_y,
            "width": self.pdf_width,  # Store PDF dimensions
            "height": self.pdf_height
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create annotation from dictionary"""
        return cls(
            image_path=data["image_path"],
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"]
        )

    def get_qimage(self):
        """Convert PIL image to QImage for rendering"""
        data = io.BytesIO()
        self.img.save(data, format='PNG')
        img_data = data.getvalue()
        return QImage.fromData(QByteArray(img_data))
    
    def update_scale(self, scale_factor):
        """Update the scale factor and recalculate screen coordinates"""
        self.scale_factor = scale_factor
        
        # Update screen coordinates based on PDF coordinates
        self.x = int(self.pdf_x * scale_factor)
        self.y = int(self.pdf_y * scale_factor)
        
        # Update screen dimensions
        new_width = int(self.pdf_width * scale_factor)
        new_height = int(self.pdf_height * scale_factor)
        
        # Only resize if dimensions have changed significantly
        if abs(self.width - new_width) > 2 or abs(self.height - new_height) > 2:
            self.width = new_width
            self.height = new_height
            self.img = self.img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        # Update rectangle - ensure all values are integers
        self.rect = QRect(self.x, self.y, self.width, self.height)