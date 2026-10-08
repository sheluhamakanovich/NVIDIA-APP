import math
import random
import sqlite3
import sys

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
    pyqtProperty,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QStyleOptionSlider,
    QVBoxLayout,
    QWidget,
)

IS_WINDOWS = False  # ВРЕМЕННО отключено для диагностики

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    GWL_STYLE = -16
    WS_CAPTION = 0x00C00000
    WS_THICKFRAME = 0x00040000
    WS_SYSMENU = 0x00080000
    WS_MINIMIZEBOX = 0x00020000
    WS_MAXIMIZEBOX = 0x00010000
    WS_OVERLAPPEDWINDOW = (
        WS_CAPTION | WS_SYSMENU | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
    )

    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020

    WM_NCCALCSIZE = 0x0083
    WM_NCHITTEST = 0x0084
    WM_GETMINMAXINFO = 0x0024

    HTCLIENT = 1
    HTCAPTION = 2
    HTLEFT = 10
    HTRIGHT = 11
    HTTOP = 12
    HTTOPLEFT = 13
    HTTOPRIGHT = 14
    HTBOTTOM = 15
    HTBOTTOMLEFT = 16
    HTBOTTOMRIGHT = 17

    MONITOR_DEFAULTTONEAREST = 2

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    class MINMAXINFO(ctypes.Structure):
        _fields_ = [
            ("ptReserved", POINT),
            ("ptMaxSize", POINT),
            ("ptMaxPosition", POINT),
            ("ptMinTrackSize", POINT),
            ("ptMaxTrackSize", POINT),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
        ]

    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    user32.SetWindowPos.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.MonitorFromWindow.restype = wintypes.HANDLE
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]


def init_db():
  conn = sqlite3.connect("users.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
  conn.commit()
  conn.close()


class SmoothSlider(QSlider):

  def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
    super().__init__(orientation, parent)
    self.setCursor(Qt.CursorShape.PointingHandCursor)

  def _update_value_from_mouse(self, event):
    opt = QStyleOptionSlider()
    self.initStyleOption(opt)
    style = self.style()
    groove_rect = style.subControlRect(
        style.ComplexControl.CC_Slider,
        opt,
        style.SubControl.SliderGroove,
        self,
    )

    if self.orientation() == Qt.Orientation.Horizontal:
      pos = event.position().x()
      start = groove_rect.x()
      length = groove_rect.width()
    else:
      pos = event.position().y()
      start = groove_rect.y()
      length = groove_rect.height()

    if length <= 0:
      return

    relative_pos = max(0.0, min(1.0, (pos - start) / float(length)))
    if self.orientation() == Qt.Orientation.Vertical:
      relative_pos = 1.0 - relative_pos

    new_val = self.minimum() + relative_pos * (self.maximum() - self.minimum())
    self.setValue(int(round(new_val)))

  def mousePressEvent(self, event):
    if event.button() == Qt.MouseButton.LeftButton:
      self._update_value_from_mouse(event)
      event.accept()
    super().mousePressEvent(event)

  def mouseMoveEvent(self, event):
    if event.buttons() & Qt.MouseButton.LeftButton:
      self._update_value_from_mouse(event)
      event.accept()
    super().mouseMoveEvent(event)


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

    is_max = (
        self.window().isMaximized()
        if hasattr(self, "window") and self.window()
        else False
    )
    radius = 0 if is_max else 18

    path = QPainterPath()
    path.addRoundedRect(
        float(self.rect().x()),
        float(self.rect().y()),
        float(self.rect().width()),
        float(self.rect().height()),
        radius,
        radius,
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


class IOSSwitch(QPushButton):

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setCheckable(True)
    self.setFixedSize(51, 31)
    self.setCursor(Qt.CursorShape.PointingHandCursor)
    self.setStyleSheet("background: transparent; border: none; outline: none;")
    self._circle_position = 3.0
    self.animation = QPropertyAnimation(self, b"circle_position", self)
    self.animation.setDuration(200)
    self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
    self.clicked.connect(self.start_animation)

  def get_circle_position(self):
    return self._circle_position

  def set_circle_position(self, pos):
    self._circle_position = pos
    self.update()

  circle_position = pyqtProperty(float, get_circle_position, set_circle_position)

  def start_animation(self, checked):
    self.animation.stop()
    if checked:
      self.animation.setStartValue(3.0)
      self.animation.setEndValue(23.0)
    else:
      self.animation.setStartValue(23.0)
      self.animation.setEndValue(3.0)
    self.animation.start()

  def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)

    if self.isChecked():
      painter.setBrush(QColor(48, 209, 88, 230))
    else:
      painter.setBrush(QColor(255, 255, 255, 25))
    painter.drawRoundedRect(0, 0, 51, 31, 15.5, 15.5)

    painter.setPen(QPen(QColor(255, 255, 255, 45), 1))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(0, 0, 51, 31, 15.5, 15.5)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 255, 255, 250))
    painter.drawEllipse(int(self._circle_position), 3, 25, 25)


class TitleBar(QWidget):

  def __init__(self, parent):
    super().__init__(parent)
    self.parent = parent
    self.setFixedHeight(40)
    self.setStyleSheet("background: transparent; border: none;")

    layout = QHBoxLayout(self)
    layout.setContentsMargins(18, 0, 8, 0)

    self.title = QLabel("Modern Control Panel")
    self.title.setStyleSheet(
        "color: #a1a1aa; font-size: 12px; font-weight: 500; background:"
        " transparent; border: none;"
    )
    layout.addWidget(self.title)
    layout.addStretch()

    btn_min = QPushButton("—")
    self.btn_max = QPushButton("▢")
    btn_close = QPushButton("✕")

    for btn in (btn_min, self.btn_max, btn_close):
      btn.setFixedSize(42, 32)
      btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #a1a1aa;
                    border: none;
                    font-size: 11px;
                    border-radius: 6px;
                    outline: none;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 20);
                    color: white;
                }
            """)

    btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a1a1aa;
                border: none;
                font-size: 11px;
                border-radius: 6px;
                outline: none;
            }
            QPushButton:hover {
                background: #e81123;
                color: white;
            }
        """)

    btn_min.clicked.connect(self.parent.showMinimized)
    self.btn_max.clicked.connect(self.toggle_max_restore)
    btn_close.clicked.connect(self.parent.close)

    layout.addWidget(btn_min)
    layout.addWidget(self.btn_max)
    layout.addWidget(btn_close)

    self.dragging = False
    self.offset = QPoint()

  def toggle_max_restore(self):
    if self.parent.isMaximized():
      self.parent.showNormal()
    else:
      self.parent.showMaximized()
    self.parent.update()

  # На Windows перетаскивание/даблклик заголовка отдаём нативному WM_NCHITTEST
  # (HTCAPTION) — это и даёт нормальный Aero Snap. Ручная логика ниже
  # используется только на macOS/Linux, где нативного снапинга у Qt-окна нет.

  def mousePressEvent(self, event):
    if IS_WINDOWS:
      return
    if event.button() == Qt.MouseButton.LeftButton:
      if self.parent.isMaximized():
        self.parent.showNormal()
        self.parent.update()
        global_pos = event.globalPosition().toPoint()
        new_left = global_pos.x() - self.parent.width() // 2
        new_top = global_pos.y() - 15
        self.parent.move(new_left, new_top)
      self.dragging = True
      self.offset = (
          event.globalPosition().toPoint()
          - self.parent.frameGeometry().topLeft()
      )
      event.accept()

  def mouseMoveEvent(self, event):
    if IS_WINDOWS:
      return
    if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
      self.parent.move(event.globalPosition().toPoint() - self.offset)
      event.accept()

  def mouseReleaseEvent(self, event):
    if IS_WINDOWS:
      return
    self.dragging = False

  def mouseDoubleClickEvent(self, event):
    if IS_WINDOWS:
      return
    self.toggle_max_restore()


class MainWindow(QWidget):

  def __init__(self):
    super().__init__()
    init_db()
    self.setMouseTracking(True)
    self.edge_margin = 6
    self.resize_dir = None
    self.drag_pos = QPoint()
    self.initUI()

  def initUI(self):
    if IS_WINDOWS:
      # Оставляем окно "настоящим" (с WS_CAPTION/WS_THICKFRAME), чтобы
      # работали Aero Snap, тени и Snap Layouts. Рамку/заголовок прячем
      # сами через nativeEvent (WM_NCCALCSIZE).
      self.setWindowFlags(Qt.WindowType.Window)
    else:
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
    main_layout.setSpacing(0)

    self.bg_widget = LiquidBackground(self)
    bg_layout = QVBoxLayout(self.bg_widget)
    bg_layout.setContentsMargins(0, 0, 0, 0)
    bg_layout.setSpacing(0)

    self.title_bar = TitleBar(self)
    bg_layout.addWidget(self.title_bar)

    content_wrapper = QWidget()
    content_wrapper.setStyleSheet("background: transparent; border: none;")
    content_layout = QVBoxLayout(content_wrapper)
    content_layout.setContentsMargins(16, 6, 16, 16)

    self.stack = QStackedWidget()
    self.stack.setStyleSheet("background: transparent; border: none;")
    self.auth_widget = self.create_auth_screen()
    self.dashboard_widget = self.create_dashboard_screen()

    self.stack.addWidget(self.auth_widget)
    self.stack.addWidget(self.dashboard_widget)

    content_layout.addWidget(self.stack)
    bg_layout.addWidget(content_wrapper)
    main_layout.addWidget(self.bg_widget)

    if IS_WINDOWS:
      QTimer.singleShot(0, self._setup_windows_frame)

  # ---------------------------------------------------------------
  # Нативная поддержка Windows Aero Snap
  # ---------------------------------------------------------------

  def _setup_windows_frame(self):
    hwnd = int(self.winId())
    style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
    style |= WS_OVERLAPPEDWINDOW
    user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)
    user32.SetWindowPos(
        hwnd,
        None,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
    )

  def nativeEvent(self, eventType, message):
    if IS_WINDOWS and eventType == b"windows_generic_MSG":
      msg = wintypes.MSG.from_address(int(message))

      if msg.message == WM_NCCALCSIZE:
        if msg.wParam:
          # Убираем нерабочую область (рамку/заголовок) полностью,
          # оставляя весь прямоугольник окна под клиентскую область.
          return True, 0

      elif msg.message == WM_NCHITTEST:
        hit = self._hit_test(msg.lParam)
        if hit is not None:
          return True, hit

      elif msg.message == WM_GETMINMAXINFO:
        self._fix_minmax_info(msg.lParam)
        return True, 0

    return super().nativeEvent(eventType, message)

  def _hit_test(self, lParam):
    x = ctypes.c_short(lParam & 0xFFFF).value
    y = ctypes.c_short((lParam >> 16) & 0xFFFF).value
    global_pos = QPoint(x, y)
    local_pos = self.mapFromGlobal(global_pos)

    w, h = self.width(), self.height()
    lx, ly = local_pos.x(), local_pos.y()
    m = 0 if self.isMaximized() else self.edge_margin

    if not self.isMaximized():
      left = lx < m
      right = lx >= w - m
      top = ly < m
      bottom = ly >= h - m

      if top and left:
        return HTTOPLEFT
      if top and right:
        return HTTOPRIGHT
      if bottom and left:
        return HTBOTTOMLEFT
      if bottom and right:
        return HTBOTTOMRIGHT
      if left:
        return HTLEFT
      if right:
        return HTRIGHT
      if top:
        return HTTOP
      if bottom:
        return HTBOTTOM

    # Область заголовка -> отдаём Windows под HTCAPTION (даёт снапинг и
    # даблклик-максимизацию бесплатно), но кнопки в титлбаре оставляем
    # кликабельными как HTCLIENT.
    tb_top_left = self.title_bar.mapTo(self, QPoint(0, 0))
    tb_rect = QRect(tb_top_left, self.title_bar.size())
    if tb_rect.contains(local_pos):
      child = self.title_bar.childAt(self.title_bar.mapFromGlobal(global_pos))
      if isinstance(child, QPushButton):
        return HTCLIENT
      return HTCAPTION

    return HTCLIENT

  def _fix_minmax_info(self, lParam):
    hwnd = int(self.winId())
    monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    if not monitor:
      return

    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(monitor, ctypes.byref(info))

    work = info.rcWork
    mon = info.rcMonitor

    mmi = MINMAXINFO.from_address(lParam)
    mmi.ptMaxPosition.x = work.left - mon.left
    mmi.ptMaxPosition.y = work.top - mon.top
    mmi.ptMaxSize.x = work.right - work.left
    mmi.ptMaxSize.y = work.bottom - work.top

  # ---------------------------------------------------------------
  # Ручной drag/resize — только для macOS/Linux (там нет нативного
  # снапинга в любом случае, поэтому теряем немного, но окно остаётся
  # управляемым мышью).
  # ---------------------------------------------------------------

  def _get_resize_direction(self, pos):
    if self.isMaximized():
      return None
    x, y = pos.x(), pos.y()
    w, h = self.width(), self.height()
    m = self.edge_margin

    left = x < m
    right = x >= w - m
    top = y < m
    bottom = y >= h - m

    if top and left:
      return "top_left"
    if top and right:
      return "top_right"
    if bottom and left:
      return "bottom_left"
    if bottom and right:
      return "bottom_right"
    if left:
      return "left"
    if right:
      return "right"
    if top:
      return "top"
    if bottom:
      return "bottom"
    return None

  def mousePressEvent(self, event):
    if IS_WINDOWS:
      return super().mousePressEvent(event)
    if event.button() == Qt.MouseButton.LeftButton:
      self.resize_dir = self._get_resize_direction(event.position().toPoint())
      if self.resize_dir:
        self.drag_pos = event.globalPosition().toPoint()
        event.accept()
        return
    super().mousePressEvent(event)

  def mouseMoveEvent(self, event):
    if IS_WINDOWS:
      return super().mouseMoveEvent(event)
    pos = event.position().toPoint()
    direction = self._get_resize_direction(pos)

    if not self.isMaximized():
      if direction in ("left", "right"):
        self.setCursor(Qt.CursorShape.SizeHorCursor)
      elif direction in ("top", "bottom"):
        self.setCursor(Qt.CursorShape.SizeVerCursor)
      elif direction in ("top_left", "bottom_right"):
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
      elif direction in ("top_right", "bottom_left"):
        self.setCursor(Qt.CursorShape.SizeBDiagCursor)
      else:
        self.setCursor(Qt.CursorShape.ArrowCursor)

    if (
        event.buttons() & Qt.MouseButton.LeftButton
        and self.resize_dir
        and not self.isMaximized()
    ):
      global_pos = event.globalPosition().toPoint()
      diff = global_pos - self.drag_pos
      self.drag_pos = global_pos

      geo = self.geometry()
      if "left" in self.resize_dir:
        geo.setLeft(geo.left() + diff.x())
      if "right" in self.resize_dir:
        geo.setRight(geo.right() + diff.x())
      if "top" in self.resize_dir:
        geo.setTop(geo.top() + diff.y())
      if "bottom" in self.resize_dir:
        geo.setBottom(geo.bottom() + diff.y())

      self.setGeometry(geo)
      event.accept()
      return

    super().mouseMoveEvent(event)

  def mouseReleaseEvent(self, event):
    if IS_WINDOWS:
      return super().mouseReleaseEvent(event)
    self.resize_dir = None
    super().mouseReleaseEvent(event)

  def create_auth_screen(self):
    widget = QWidget()
    widget.setStyleSheet("background: transparent; border: none;")
    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    panel = QWidget()
    panel.setFixedSize(380, 390)
    panel.setStyleSheet("""
            QWidget {
                background-color: rgba(22, 22, 30, 170);
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: 20px;
            }
        """)

    panel_layout = QVBoxLayout(panel)
    panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    panel_layout.setContentsMargins(40, 40, 40, 40)

    self.title_label = QLabel("Авторизация", panel)
    self.title_label.setStyleSheet(
        "color: #ffffff; font-size: 22px; font-weight: 600; background:"
        " transparent; border: none;"
    )
    panel_layout.addWidget(
        self.title_label, alignment=Qt.AlignmentFlag.AlignCenter
    )
    panel_layout.addSpacing(25)

    self.user_input = QLineEdit(panel)
    self.user_input.setPlaceholderText("Логин")
    self.user_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 6);
                border: 1px solid rgba(255, 255, 255, 12);
                border-radius: 12px;
                color: white;
                padding: 12px 14px;
                font-size: 14px;
                outline: none;
            }
            QLineEdit:focus {
                border: 1px solid rgba(0, 122, 255, 200);
                background: rgba(0, 122, 255, 15);
            }
        """)
    panel_layout.addWidget(self.user_input)
    panel_layout.addSpacing(12)

    self.pass_input = QLineEdit(panel)
    self.pass_input.setPlaceholderText("Пароль")
    self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
    self.pass_input.setStyleSheet(self.user_input.styleSheet())
    panel_layout.addWidget(self.pass_input)
    panel_layout.addSpacing(20)

    self.action_btn = QPushButton("Войти", panel)
    self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 132, 255, 230), stop:1 rgba(0, 102, 220, 230));
                color: white;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
                border: 1px solid rgba(255, 255, 255, 20);
                outline: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(20, 145, 255, 255), stop:1 rgba(0, 115, 235, 255)); }
            QPushButton:pressed { background-color: #004d99; }
        """)
    self.action_btn.clicked.connect(self.handle_auth_action)
    panel_layout.addWidget(self.action_btn)
    panel_layout.addSpacing(15)

    self.switch_btn = QPushButton("Нет аккаунта? Зарегистрироваться", panel)
    self.switch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.switch_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a1a1aa;
                font-size: 12px;
                border: none;
                outline: none;
            }
            QPushButton:hover { color: #ffffff; }
        """)
    self.switch_btn.clicked.connect(self.toggle_auth_mode)
    panel_layout.addWidget(
        self.switch_btn, alignment=Qt.AlignmentFlag.AlignCenter
    )

    self.status_label = QLabel("", panel)
    self.status_label.setStyleSheet(
        "color: #ff453a; font-size: 12px; background: transparent; border: none;"
    )
    panel_layout.addWidget(
        self.status_label, alignment=Qt.AlignmentFlag.AlignCenter
    )

    layout.addWidget(panel)
    self.is_register_mode = False
    return widget

  def toggle_auth_mode(self):
    self.is_register_mode = not self.is_register_mode
    if self.is_register_mode:
      self.title_label.setText("Регистрация")
      self.action_btn.setText("Зарегистрироваться")
      self.switch_btn.setText("Уже есть аккаунт? Войти")
    else:
      self.title_label.setText("Авторизация")
      self.action_btn.setText("Войти")
      self.switch_btn.setText("Нет аккаунта? Зарегистрироваться")
    self.status_label.setText("")

  def handle_auth_action(self):
    username = self.user_input.text().strip()
    password = self.pass_input.text().strip()

    if not username or not password:
      self.status_label.setText("Заполни все поля!")
      return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if self.is_register_mode:
      try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password),
        )
        conn.commit()
        self.status_label.setStyleSheet(
            "color: #30d158; font-size: 12px; background: transparent; border:"
            " none;"
        )
        self.status_label.setText("Успешно зарегистрировано!")
      except sqlite3.IntegrityError:
        self.status_label.setStyleSheet(
            "color: #ff453a; font-size: 12px; background: transparent; border:"
            " none;"
        )
        self.status_label.setText("Логин уже занят!")
    else:
      cursor.execute(
          "SELECT * FROM users WHERE username = ? AND password = ?",
          (username, password),
      )
      user = cursor.fetchone()
      if user:
        self.stack.setCurrentWidget(self.dashboard_widget)
        self.user_input.clear()
        self.pass_input.clear()
        self.status_label.clear()
      else:
        self.status_label.setStyleSheet(
            "color: #ff453a; font-size: 12px; background: transparent; border:"
            " none;"
        )
        self.status_label.setText("Неверный логин или пароль!")
    conn.close()

  def create_dashboard_screen(self):
    widget = QWidget()
    widget.setStyleSheet("background: transparent; border: none;")
    main_layout = QHBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(16)

    sidebar = QWidget()
    sidebar.setFixedWidth(220)
    sidebar.setStyleSheet("""
            QWidget {
                background: rgba(18, 18, 26, 150);
                border: 1px solid rgba(255, 255, 255, 12);
                border-radius: 16px;
            }
        """)
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(14, 20, 14, 20)
    sidebar_layout.setSpacing(8)

    app_title = QLabel("МЕНЮ")
    app_title.setStyleSheet(
        "color: #71717a; font-size: 10px; font-weight: bold; border: none;"
        " padding-left: 8px; background: transparent;"
    )
    sidebar_layout.addWidget(app_title)

    self.inner_stack = QStackedWidget()
    self.inner_stack.setStyleSheet("border: none; background: transparent;")

    self.nav_buttons = []
    for i in range(1, 4):
      btn = QPushButton(f"  Раздел {i}")
      btn.setCursor(Qt.CursorShape.PointingHandCursor)
      btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #d4d4d8;
                    border: none;
                    text-align: left;
                    padding: 12px 14px;
                    font-size: 14px;
                    border-radius: 10px;
                    outline: none;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 8);
                    color: white;
                }
            """)
      btn.clicked.connect(lambda _, index=i - 1: self.switch_section(index))
      sidebar_layout.addWidget(btn)
      self.nav_buttons.append(btn)

    sidebar_layout.addStretch()

    logout_btn = QPushButton("  Выйти")
    logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    logout_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 69, 58, 12);
                color: #ff453a;
                border: 1px solid rgba(255, 69, 58, 20);
                text-align: left;
                padding: 12px 14px;
                font-size: 13px;
                border-radius: 10px;
                outline: none;
            }
            QPushButton:hover {
                background: rgba(255, 69, 58, 25);
            }
        """)
    logout_btn.clicked.connect(
        lambda: self.stack.setCurrentWidget(self.auth_widget)
    )
    sidebar_layout.addWidget(logout_btn)

    content_area = QWidget()
    content_area.setStyleSheet("""
            QWidget {
                background: rgba(16, 16, 24, 150);
                border: 1px solid rgba(255, 255, 255, 12);
                border-radius: 16px;
            }
        """)
    content_layout = QVBoxLayout(content_area)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.addWidget(self.inner_stack)

    for i in range(1, 4):
      scroll = QScrollArea()
      scroll.setWidgetResizable(True)
      scroll.setStyleSheet("""
                QScrollArea { border: none; background: transparent; }
                QWidget { background: transparent; }
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(255, 255, 255, 25);
                    border-radius: 3px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            """)

      sec_widget = QWidget()
      sec_widget.setStyleSheet("border: none; background: transparent;")
      sec_layout = QVBoxLayout(sec_widget)
      sec_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
      sec_layout.setContentsMargins(32, 32, 32, 32)
      sec_layout.setSpacing(20)

      title = QLabel(f"Панель управления — Раздел {i}")
      title.setStyleSheet(
          "color: white; font-size: 20px; font-weight: 600; border: none;"
          " background: transparent;"
      )
      sec_layout.addWidget(title)
      sec_layout.addSpacing(5)

      for j in range(1, 4):
        card = QWidget()
        card.setStyleSheet("""
                    QWidget {
                        background-color: rgba(24, 24, 34, 160);
                        border: 1px solid rgba(255, 255, 255, 10);
                        border-radius: 14px;
                    }
                """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(14)

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)

        chk_label = QLabel(f"Активировать функцию {j}")
        chk_label.setStyleSheet(
            "color: #f4f4f5; font-size: 14px; font-weight: 500; background:"
            " transparent; border: none;"
        )
        row_layout.addWidget(chk_label)
        row_layout.addStretch()

        ios_switch = IOSSwitch()
        row_layout.addWidget(ios_switch)
        card_layout.addLayout(row_layout)

        lbl = QLabel(f"Регулировка параметра {j}:")
        lbl.setStyleSheet(
            "color: #a1a1aa; font-size: 12px; border: none; background:"
            " transparent;"
        )
        card_layout.addWidget(lbl)

        slider = SmoothSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(40)
        slider.setStyleSheet("""
                    QSlider {
                        background: transparent;
                        border: none;
                        outline: none;
                        height: 24px;
                    }
                    QSlider::groove:horizontal {
                        height: 6px;
                        background: rgba(255, 255, 255, 12);
                        border-radius: 3px;
                    }
                    QSlider::sub-page:horizontal {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 122, 255, 230), stop:1 rgba(90, 200, 250, 230));
                        border-radius: 3px;
                    }
                    QSlider::handle:horizontal {
                        background: #ffffff;
                        width: 18px;
                        height: 18px;
                        margin: -6px 0;
                        border-radius: 9px;
                        border: 1px solid rgba(0, 0, 0, 40);
                    }
                    QSlider::handle:horizontal:hover {
                        background: #f0f0f5;
                    }
                """)
        card_layout.addWidget(slider)

        sec_layout.addWidget(card)

      scroll.setWidget(sec_widget)
      self.inner_stack.addWidget(scroll)

    self.switch_section(0)

    main_layout.addWidget(sidebar)
    main_layout.addWidget(content_area)
    return widget

  def switch_section(self, index):
    self.inner_stack.setCurrentIndex(index)
    for i, btn in enumerate(self.nav_buttons):
      if i == index:
        btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(0, 122, 255, 22);
                        color: #ffffff;
                        border: 1px solid rgba(0, 122, 255, 45);
                        text-align: left;
                        padding: 12px 14px;
                        font-size: 14px;
                        font-weight: 500;
                        border-radius: 10px;
                        outline: none;
                    }
                """)
      else:
        btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #d4d4d8;
                        border: none;
                        text-align: left;
                        padding: 12px 14px;
                        font-size: 14px;
                        border-radius: 10px;
                        outline: none;
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 255, 8);
                        color: white;
                    }
                """)


if __name__ == "__main__":
  app = QApplication(sys.argv)
  ex = MainWindow()
  ex.show()
  sys.exit(app.exec())