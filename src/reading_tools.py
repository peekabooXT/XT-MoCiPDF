"""Small on-page editing and reading controls, with no separate note window."""
from PySide6.QtCore import Qt, QElapsedTimer, QTimer, Signal, QEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QPainter, QPen, QColor
from localized_widgets import QLabel, QPushButton, QPlainTextEdit
from i18n import tr


class NoteEditor(QWidget):
    finished = Signal(bool)

    def __init__(self, canvas, text, rect):
        super().__init__(canvas)
        self.canvas = canvas
        self.handle = None
        self.drag_origin = None
        self.setObjectName('inlineNote')
        self.setStyleSheet('''QWidget#inlineNote { background: transparent; border: 1px dashed #087f73; }
            QPlainTextEdit { background: transparent; border: none; padding: 4px; color: #233a41; }
            QPushButton { padding: 3px 7px; }''')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        self.text = QPlainTextEdit()
        self.text.setStyleSheet('background: transparent;')
        self.text.viewport().setAutoFillBackground(False)
        self.text.setPlainText(text)
        self.text.installEventFilter(self)
        self.text.setPlaceholderText(tr('在页面上输入备注…'))
        layout.addWidget(self.text, 1)
        actions = QHBoxLayout()
        self.handle = QLabel(':::')
        self.handle.setCursor(Qt.CursorShape.SizeAllCursor)
        self.handle.setToolTip(tr('拖动这里移动备注'))
        self.handle.installEventFilter(self)
        actions.addWidget(self.handle)
        actions.addStretch()
        save = QPushButton(tr('保存'))
        save.clicked.connect(lambda: self.finished.emit(True))
        cancel = QPushButton(tr('取消'))
        cancel.clicked.connect(lambda: self.finished.emit(False))
        actions.addWidget(save)
        actions.addWidget(cancel)
        layout.addLayout(actions)
        width = min(max(240, round(rect.width())), canvas.width())
        height = min(max(130, round(rect.height()) + 38), canvas.height())
        self.setGeometry(max(0, min(round(rect.x()), canvas.width() - width)),
                         max(0, min(round(rect.y()), canvas.height() - height)), width, height)
        self.start_position = self.pos()
        self.drag_origin = None
        self.show()
        self.text.setFocus()

    def eventFilter(self, watched, event):
        if watched is self.text and event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            cancel = event.key() == Qt.Key.Key_Escape
            save = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            if cancel or save:
                event.accept()
                if event.type() == QEvent.Type.KeyPress:
                    self.finished.emit(not cancel)
                return True
        if watched is self.handle:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.drag_origin = event.globalPosition().toPoint() - self.pos()
                return True
            if event.type() == QEvent.Type.MouseMove and self.drag_origin is not None:
                pos = event.globalPosition().toPoint() - self.drag_origin
                self.move(max(0, min(pos.x(), self.canvas.width() - self.width())),
                          max(0, min(pos.y(), self.canvas.height() - self.height())))
                return True
            if event.type() == QEvent.Type.MouseButtonRelease:
                self.drag_origin = None
                return True
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor('#087f73'), 1, Qt.PenStyle.DashLine))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))


class ReadingTimer(QWidget):
    """Stopwatch uses monotonic time; reopening restores elapsed time paused."""
    state_changed = Signal()
    def __init__(self, parent=None, seconds=0):
        super().__init__(parent)
        self.total_ms = max(0, int(seconds)) * 1000
        self.clock = QElapsedTimer()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.label = QLabel()
        self.label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label.setStyleSheet('font-family: Consolas; font-size: 16px; font-weight: 600;')
        layout.addWidget(self.label)
        self.toggle_button = QPushButton(tr('开始计时'))
        self.toggle_button.clicked.connect(self.toggle)
        layout.addWidget(self.toggle_button)
        reset = QPushButton(tr('重置'))
        reset.setToolTip(tr('重置计时'))
        reset.clicked.connect(self.reset)
        layout.addWidget(reset)
        self.tick = QTimer(self)
        self.tick.timeout.connect(self.refresh)
        self.tick.start(200)
        self.refresh()

    def milliseconds(self):
        return self.total_ms + (self.clock.elapsed() if self.clock.isValid() else 0)

    def toggle(self):
        if self.clock.isValid():
            self.total_ms += self.clock.elapsed()
            self.clock.invalidate()
        else:
            self.clock.start()
        self.toggle_button.setText(tr('暂停计时') if self.clock.isValid() else tr('开始计时'))
        self.refresh()
        self.state_changed.emit()

    def reset(self):
        self.total_ms = 0
        self.clock.invalidate()
        self.toggle_button.setText(tr('开始计时'))
        self.refresh()
        self.state_changed.emit()

    def refresh(self):
        seconds = self.milliseconds() // 1000
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        self.label.setText(f'{hours:02}:{minutes:02}:{seconds:02}')
