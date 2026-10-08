import random
import sys
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel


class LiquidBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bubbles = []
        for _ in range(6):
            self.bubbles.append({
                "x": random.uniform(0.1, 0.9),
                "y": random.uniform(0.1, 0.9),
                "vx": random.uniform(-0.0002, 0.0002),
                "vy": random.uniform(-0.0002, 0.0002),
                "r": random.uniform(180, 320),
                "color": random.choice([
                    QColor(0, 122, 255, 50),
                    QColor(175, 82, 222, 40),
                    QColor(88, 86, 214, 45),
                    QColor(50, 215, 75, 30),
                ]),
            })
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_bubbles)
        self.timer.start(30)

    def update_bubbles(self):
        for b in self.bubbles:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            if b["x"] < -0.2 or b["x"] > 1.2:
                b["vx"] *= -1
            if b["y"] < -0.2 or b["y"] > 1.2:
                b["vy"] *= -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_max = self.window().isMaximized() if self.window() else False
        radius = 0 if is_max else 18

        path = QPainterPath()
        path.addRoundedRect(
            float(self.rect().x()), float(self.rect().y()),
            float(self.rect().width()), float(self.rect().height()),
            radius, radius,
        )
        painter.setClipPath(path)

        bg_gradient = QLinearGradient(0, 0, self.width(), self.height())
        bg_gradient.setColorAt(0.0, QColor(12, 12, 16))
        bg_gradient.setColorAt(0.5, QColor(16, 16, 22))
        bg_gradient.setColorAt(1.0, QColor(8, 8, 12))
        painter.fillRect(self.rect(), bg_gradient)

        for b in self.bubbles:
            bx = b["x"] * self.width()
            by = b["y"] * self.height()
            grad = QLinearGradient(bx, by - b["r"], bx, by + b["r"])
            c1 = b["color"]
            c2 = QColor(c1.red(), c1.green(), c1.blue(), 0)
            grad.setColorAt(0.0, c1)
            grad.setColorAt(1.0, c2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(grad)
            painter.drawEllipse(QPointF(bx, by), b["r"], b["r"])

        if not is_max:
            painter.setPen(QPen(QColor(255, 255, 255, 25), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), radius, radius)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(900, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_widget = LiquidBackground(self)
        bg_layout = QVBoxLayout(self.bg_widget)
        label = QLabel("Шаг 2: + LiquidBackground (анимированный фон)")
        label.setStyleSheet("color: white; background: transparent; padding: 20px;")
        bg_layout.addWidget(label)

        main_layout.addWidget(self.bg_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
