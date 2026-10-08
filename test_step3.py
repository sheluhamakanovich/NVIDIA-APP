import random
import sys
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)


class LiquidBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bubbles = []
        for _ in range(6):
            self.bubbles.append({
                "x": random.uniform(0.1, 0.9), "y": random.uniform(0.1, 0.9),
                "vx": random.uniform(-0.0002, 0.0002), "vy": random.uniform(-0.0002, 0.0002),
                "r": random.uniform(180, 320),
                "color": random.choice([
                    QColor(0, 122, 255, 50), QColor(175, 82, 222, 40),
                    QColor(88, 86, 214, 45), QColor(50, 215, 75, 30),
                ]),
            })
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_bubbles)
        self.timer.start(30)

    def update_bubbles(self):
        for b in self.bubbles:
            b["x"] += b["vx"]; b["y"] += b["vy"]
            if b["x"] < -0.2 or b["x"] > 1.2: b["vx"] *= -1
            if b["y"] < -0.2 or b["y"] > 1.2: b["vy"] *= -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_max = self.window().isMaximized() if self.window() else False
        radius = 0 if is_max else 18
        path = QPainterPath()
        path.addRoundedRect(float(self.rect().x()), float(self.rect().y()),
                             float(self.rect().width()), float(self.rect().height()), radius, radius)
        painter.setClipPath(path)
        bg = QLinearGradient(0, 0, self.width(), self.height())
        bg.setColorAt(0.0, QColor(12, 12, 16)); bg.setColorAt(0.5, QColor(16, 16, 22)); bg.setColorAt(1.0, QColor(8, 8, 12))
        painter.fillRect(self.rect(), bg)
        for b in self.bubbles:
            bx = b["x"] * self.width(); by = b["y"] * self.height()
            grad = QLinearGradient(bx, by - b["r"], bx, by + b["r"])
            c1 = b["color"]; c2 = QColor(c1.red(), c1.green(), c1.blue(), 0)
            grad.setColorAt(0.0, c1); grad.setColorAt(1.0, c2)
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(grad)
            painter.drawEllipse(QPointF(bx, by), b["r"], b["r"])
        if not is_max:
            painter.setPen(QPen(QColor(255, 255, 255, 25), 1)); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), radius, radius)


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 8, 0)
        self.title = QLabel("Шаг 3: + TitleBar (drag/resize мышью)")
        self.title.setStyleSheet("color: #a1a1aa; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(self.title)
        layout.addStretch()

        btn_min = QPushButton("—")
        self.btn_max = QPushButton("▢")
        btn_close = QPushButton("✕")
        for btn in (btn_min, self.btn_max, btn_close):
            btn.setFixedSize(42, 32)
            btn.setStyleSheet("QPushButton{background:transparent;color:#a1a1aa;border:none;} QPushButton:hover{background:rgba(255,255,255,20);color:white;}")
        btn_min.clicked.connect(self.parent.showMinimized)
        self.btn_max.clicked.connect(self.toggle_max_restore)
        btn_close.clicked.connect(self.parent.close)
        layout.addWidget(btn_min); layout.addWidget(self.btn_max); layout.addWidget(btn_close)

        self.dragging = False
        self.offset = QPoint()

    def toggle_max_restore(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()
        self.parent.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.parent.isMaximized():
                self.parent.showNormal()
                self.parent.update()
                gp = event.globalPosition().toPoint()
                self.parent.move(gp.x() - self.parent.width() // 2, gp.y() - 15)
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def mouseDoubleClickEvent(self, event):
        self.toggle_max_restore()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.edge_margin = 10
        self.resize_dir = None
        self.drag_pos = QPoint()

        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(900, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.bg_widget = LiquidBackground(self)
        bg_layout = QVBoxLayout(self.bg_widget)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        bg_layout.addWidget(self.title_bar)
        bg_layout.addStretch()

        main_layout.addWidget(self.bg_widget)

    def _get_resize_direction(self, pos):
        if self.isMaximized():
            return None
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        m = self.edge_margin
        left, right, top, bottom = x < m, x >= w - m, y < m, y >= h - m
        if top and left: return "top_left"
        if top and right: return "top_right"
        if bottom and left: return "bottom_left"
        if bottom and right: return "bottom_right"
        if left: return "left"
        if right: return "right"
        if top: return "top"
        if bottom: return "bottom"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resize_dir = self._get_resize_direction(event.position().toPoint())
            if self.resize_dir:
                self.drag_pos = event.globalPosition().toPoint()
                self.grabMouse()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        direction = self._get_resize_direction(pos)
        if not self.isMaximized():
            if direction in ("left", "right"): self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif direction in ("top", "bottom"): self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif direction in ("top_left", "bottom_right"): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif direction in ("top_right", "bottom_left"): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else: self.setCursor(Qt.CursorShape.ArrowCursor)

        if event.buttons() & Qt.MouseButton.LeftButton and self.resize_dir and not self.isMaximized():
            gp = event.globalPosition().toPoint()
            diff = gp - self.drag_pos
            self.drag_pos = gp
            geo = self.geometry()
            if "left" in self.resize_dir: geo.setLeft(geo.left() + diff.x())
            if "right" in self.resize_dir: geo.setRight(geo.right() + diff.x())
            if "top" in self.resize_dir: geo.setTop(geo.top() + diff.y())
            if "bottom" in self.resize_dir: geo.setBottom(geo.bottom() + diff.y())
            self.setGeometry(geo)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.resize_dir:
            self.releaseMouse()
        self.resize_dir = None
        super().mouseReleaseEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
