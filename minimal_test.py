import sys
from PyQt6.QtWidgets import QApplication, QLabel

app = QApplication(sys.argv)
label = QLabel("Если ты видишь это окно — PyQt6 работает нормально")
label.resize(400, 100)
label.show()
sys.exit(app.exec())
