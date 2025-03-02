"""
Utility functions for the Burmese PDF annotation tool.
"""

import os
import json
import fitz
from PIL import Image, ImageDraw, ImageFont
import io

def render_burmese_text_to_image(text, font_path, font_size, color="black", 
                                background=None, rotation=0):
    """
    Render Burmese text to an image using PIL.
    
    Args:
        text (str): Text to render
        font_path (str): Path to font file
        font_size (int): Font size
        color (str): Text color
        background (str, optional): Background color
        rotation (int, optional): Rotation angle
        
    Returns:
        PIL.Image: Rendered text as image
    """
    # Determine size needed
    sample_img = Image.new("RGBA", (500, 100), (255, 255, 255, 0))
    sample_draw = ImageDraw.Draw(sample_img)
    font = ImageFont.truetype(font_path, font_size)
    
    # Get text dimensions
    text_bbox = sample_draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Add padding
    width = text_width + 20
    height = text_height + 20
    
    # Create image with transparent background
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw background if specified
    if background:
        draw.rectangle([0, 0, width, height], fill=background)
    
    # Draw text
    draw.text((10, 10), text, font=font, fill=color)
    
    # Apply rotation if needed
    if rotation != 0:
        img = img.rotate(rotation, expand=True)
    
    return img

def add_burmese_text_to_pdf_page(page, text, x, y, font_path, font_size, 
                                color="black", background=None, rotation=0):
    """
    Add Burmese text to a PDF page using the image method.
    
    Args:
        page (fitz.Page): PDF page
        text (str): Text to add
        x (int): X coordinate
        y (int): Y coordinate
        font_path (str): Path to font file
        font_size (int): Font size
        color (str): Text color
        background (str, optional): Background color
        rotation (int, optional): Rotation angle
        
    Returns:
        None
    """
    # Render text to image
    img = render_burmese_text_to_image(
        text, font_path, font_size, color, background, rotation
    )
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    # Define rectangle for image placement
    rect = fitz.Rect(x, y, x + img.width, y + img.height)
    
    # Insert image
    page.insert_image(rect, stream=img_bytes)

def ensure_dir_exists(dir_path):
    """
    Ensure a directory exists, creating it if needed.
    
    Args:
        dir_path (str): Directory path
        
    Returns:
        str: Directory path
    """
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def load_json_file(file_path, default=None):
    """
    Load JSON data from a file.
    
    Args:
        file_path (str): Path to JSON file
        default (any, optional): Default value if file doesn't exist
        
    Returns:
        dict: Loaded JSON data or default
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default or {}

def save_json_file(file_path, data):
    """
    Save data to a JSON file.
    
    Args:
        file_path (str): Path to JSON file
        data (dict): Data to save
        
    Returns:
        bool: Success
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False