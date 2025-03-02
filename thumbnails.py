"""
Thumbnail navigation widget for the Burmese PDF annotation tool.
"""

import fitz
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSignal

class PDFThumbnailWidget(QListWidget):
    """Widget to display PDF page thumbnails"""
    page_selected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(100, 140))  # Adjust the thumbnail size
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setWrapping(True)  # Enable wrapping
        self.setFlow(QListWidget.TopToBottom)  # Vertical flow
        self.setMovement(QListWidget.Static)
        self.setSpacing(10)  # Add space between thumbnails
        
        # Set fixed width for the widget to ensure vertical layout
        self.setMaximumWidth(150)
        self.setMinimumWidth(120)
        
        # Styling
        self.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #c2d2e9;
                border: 1px solid #99b0d1;
            }
        """)
        
        self.doc = None
        self.itemClicked.connect(self.on_thumbnail_clicked)
    
    def load_document(self, doc):
        """Load document and generate thumbnails"""
        self.clear()
        self.doc = doc
        
        for i in range(len(doc)):
            page = doc[i]
            
            # Use a smaller scale factor for thumbnails
            pix = page.get_pixmap(matrix=fitz.Matrix(0.15, 0.15))
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            
            # Create list widget item
            item = QListWidgetItem(f"Page {i+1}")
            item.setIcon(QIcon(pixmap))
            item.setData(Qt.UserRole, i)
            
            # Set size hint to ensure consistent thumbnail size
            item.setSizeHint(QSize(100, 160))
            
            # Center text under the icon
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            
            self.addItem(item)
    
    def on_thumbnail_clicked(self, item):
        """Handle thumbnail click"""
        page_num = item.data(Qt.UserRole)
        self.page_selected.emit(page_num)