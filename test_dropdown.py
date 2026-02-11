"""Test instrument dropdown signal."""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt5.QtGui import QFont


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected = "piano"
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Test Dropdown")
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        self.combo = QComboBox()
        self.combo.addItems(["Piano", "Bell", "Violin", "Flute"])
        self.combo.currentTextChanged.connect(self.on_change)
        layout.addWidget(self.combo)
        
        self.label = QLabel("Selected: Piano")
        self.label.setFont(QFont("Arial", 14))
        layout.addWidget(self.label)
    
    def on_change(self, text):
        self.selected = text.lower()
        self.label.setText(f"Selected: {text}")
        print(f"Signal fired! Changed to: {self.selected}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
