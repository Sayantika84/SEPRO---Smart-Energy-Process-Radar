from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QFontMetrics

class Toast(QLabel):
    """
    A non-blocking, self-hiding notification toast.
    """
    def __init__(self, parent, msg, timeout=3000):
        super().__init__(msg, parent)


        self.setStyleSheet("""
            QLabel {
                background-color: #222; 
                color: #FFFFFF; 
                padding: 10px 15px; 
                border-radius: 8px;
                border: 1px solid #FFFFFF;
                font-size: 11pt;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.WindowStaysOnTopHint)
        self.adjustSize() 

        # Positioning
        # Calculate center of parent window
        parent_rect = parent.geometry()
        parent_center_x = parent_rect.x() + parent_rect.width() // 2
        
        # Position toast at the top-center of the parent
        self.move(
            parent_center_x - (self.width() // 2), 
            parent_rect.y() + 20 # 20px from the top
        )

        self.raise_()
        self.show()

        # Timer to auto-hide 
        QTimer.singleShot(timeout, self.close)
