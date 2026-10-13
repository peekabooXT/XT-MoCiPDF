"""Visible annotation tools and user-configurable, single-chord shortcuts."""
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (QWidget, QPushButton, QButtonGroup, QLayout, QDialog,
                               QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QKeySequenceEdit)

TOOLS = [('选词 / 阅读', 'select'), ('文字高亮', 'highlight'), ('文字下划线', 'underline'),
         ('自由画笔', 'ink'), ('矩形框', 'rect'), ('文字备注', 'note'), ('橡皮擦', 'erase')]
DEFAULT_SHORTCUTS = {key: str(i + 1) for i, (_, key) in enumerate(TOOLS)}
RESERVED = {'Ctrl+O', 'Ctrl+E', 'Ctrl+F', 'Ctrl+Z', 'Ctrl+Y', 'Esc', 'Return', 'Enter', 'Tab', 'Backtab'}
PORTABLE = QKeySequence.SequenceFormat.PortableText
NATIVE = QKeySequence.SequenceFormat.NativeText


def validated_shortcuts(values):
    result, seen = {}, {}
    for label, key in TOOLS:
        text = values.get(key, DEFAULT_SHORTCUTS[key])
        if not isinstance(text, str):
            raise ValueError(f'{label}的快捷键格式不正确。')
        sequence = QKeySequence.fromString(text, PORTABLE)
        if text and (sequence.isEmpty() or sequence.count() != 1 or
                     sequence[0].key() in (Qt.Key.Key_unknown, 0)):
            raise ValueError(f'{label}请设置一个按键，可带 Ctrl、Alt 或 Shift。')
        text = sequence.toString(PORTABLE)
        if text in RESERVED:
            raise ValueError(f'{text} 已用于其他操作，请为「{label}」选择其他按键。')
        if text and text in seen:
            raise ValueError(f'「{label}」与「{seen[text]}」都使用 {text}，请避免重复。')
        if text:
            seen[text] = label
        result[key] = text
    return result


def load_shortcuts(state):
    try:
        values = state.get('tool_shortcuts', {})
        return validated_shortcuts(values if isinstance(values, dict) else {})
    except ValueError:
        return dict(DEFAULT_SHORTCUTS)


class FlowLayout(QLayout):
    """Wrap buttons without hiding any tool behind a menu or scrollbar."""
    def __init__(self, parent):
        super().__init__(parent)
        self.items = []
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(6)

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index):
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.arrange(QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.arrange(rect, apply=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        return size

    def arrange(self, rect, apply):
        x, y, height = rect.x(), rect.y(), 0
        for item in self.items:
            size = item.sizeHint()
            if x > rect.x() and x + size.width() > rect.x() + rect.width():
                x, y = rect.x(), y + height + self.spacing()
                height = 0
            if apply:
                item.setGeometry(QRect(x, y, size.width(), size.height()))
            x += size.width() + self.spacing()
            height = max(height, size.height())
        return y + height - rect.y()


class AnnotationToolBar(QWidget):
    currentIndexChanged = Signal(int)

    def __init__(self, shortcuts, parent=None):
        super().__init__(parent)
        self.index = 0
        self.buttons = []
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        layout = FlowLayout(self)
        for index, (label, key) in enumerate(TOOLS):
            button = QPushButton(label)
            button.setObjectName('annotationTool')
            button.setCheckable(True)
            self.group.addButton(button, index)
            self.buttons.append(button)
            layout.addWidget(button)
        self.buttons[0].setChecked(True)
        self.group.idClicked.connect(self.setCurrentIndex)
        self.set_shortcuts(shortcuts)

    def set_shortcuts(self, shortcuts):
        for (label, key), button in zip(TOOLS, self.buttons):
            shortcut = QKeySequence(shortcuts[key]).toString(NATIVE)
            button.setText(label + (f'  {shortcut}' if shortcut else ''))
            button.setToolTip(label + (f' · 快捷键 {shortcut}' if shortcut else ' · 未设置快捷键') +
                              '\n可在右上角「设置」修改；输入文字时不触发。')
        self.layout().invalidate()
        self.updateGeometry()

    def currentData(self):
        return TOOLS[self.index][1]

    def currentIndex(self):
        return self.index

    def findData(self, key):
        return next((i for i, (_, value) in enumerate(TOOLS) if value == key), -1)

    def setCurrentIndex(self, index):
        if 0 <= index < len(TOOLS) and index != self.index:
            self.index = index
            self.buttons[index].setChecked(True)
            self.currentIndexChanged.emit(index)


class ShortcutSettingsDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle('设置 · 工具快捷键')
        self.resize(530, 430)
        layout = QVBoxLayout(self)
        hint = QLabel('点击快捷键框，再按你想使用的按键，可搭配 Ctrl、Alt、Shift。\n清空可关闭该工具的快捷键。输入框内打字时不会切换工具。')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QFormLayout()
        self.editors = {}
        for label, key in TOOLS:
            editor = QKeySequenceEdit(QKeySequence(owner.tool_shortcuts[key]))
            editor.setMaximumSequenceLength(1)
            editor.setClearButtonEnabled(True)
            self.editors[key] = editor
            form.addRow(label, editor)
        layout.addLayout(form)
        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setStyleSheet('color: #b64c4c;')
        layout.addWidget(self.message)
        row = QHBoxLayout()
        reset = QPushButton('恢复默认 1–7')
        reset.clicked.connect(self.reset)
        row.addWidget(reset)
        row.addStretch()
        cancel = QPushButton('取消')
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        self.save_button = QPushButton('保存')
        self.save_button.setObjectName('primary')
        self.save_button.clicked.connect(self.save)
        row.addWidget(self.save_button)
        layout.addLayout(row)
        for editor in self.editors.values():
            editor.keySequenceChanged.connect(self.validate)
        self.validate()

    def values(self):
        return {key: editor.keySequence().toString(PORTABLE) for key, editor in self.editors.items()}

    def validate(self):
        try:
            validated_shortcuts(self.values())
            self.message.setText('')
            self.save_button.setEnabled(True)
        except ValueError as exc:
            self.message.setText(str(exc))
            self.save_button.setEnabled(False)

    def reset(self):
        for key, editor in self.editors.items():
            editor.setKeySequence(QKeySequence(DEFAULT_SHORTCUTS[key]))
        self.validate()

    def save(self):
        try:
            values = validated_shortcuts(self.values())
        except ValueError:
            self.validate()
            return
        if self.owner.save_tool_shortcuts(values):
            self.accept()
