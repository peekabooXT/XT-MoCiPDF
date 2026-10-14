"""Visible annotation tools and user-configurable, single-chord shortcuts."""

from i18n import tr
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (QWidget, QPushButton, QButtonGroup, QDialog,
                               QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QKeySequenceEdit)
from localized_widgets import QPushButton, QDialog, QLabel, QComboBox
from i18n import LANGUAGES, current_language

TOOLS = [(tr('选词 / 阅读'), 'select'), (tr('文字高亮'), 'highlight'), (tr('文字下划线'), 'underline'),
         (tr('自由画笔'), 'ink'), (tr('矩形框'), 'rect'), (tr('文字备注'), 'note'), (tr('橡皮擦'), 'erase')]
DEFAULT_SHORTCUTS = {key: str(i + 1) for i, (_, key) in enumerate(TOOLS)}
RESERVED = {'Ctrl+O', 'Ctrl+E', 'Ctrl+F', 'Ctrl+Z', 'Ctrl+Y', 'Esc', 'Return', 'Enter', 'Tab', 'Backtab'}
PORTABLE = QKeySequence.SequenceFormat.PortableText
NATIVE = QKeySequence.SequenceFormat.NativeText


def validated_shortcuts(values):
    result, seen = {}, {}
    for label, key in TOOLS:
        text = values.get(key, DEFAULT_SHORTCUTS[key])
        if not isinstance(text, str):
            raise ValueError(tr('{arg0}的快捷键格式不正确。', arg0=label))
        sequence = QKeySequence.fromString(text, PORTABLE)
        if text and (sequence.isEmpty() or sequence.count() != 1 or
                     sequence[0].key() in (Qt.Key.Key_unknown, 0)):
            raise ValueError(tr('{arg0}请设置一个按键，可带 Ctrl、Alt 或 Shift。', arg0=label))
        text = sequence.toString(PORTABLE)
        if text in RESERVED:
            raise ValueError(tr('{arg0} 已用于其他操作，请为「{arg1}」选择其他按键。', arg0=text, arg1=label))
        if text and text in seen:
            raise ValueError(tr('「{arg0}」与「{arg1}」都使用 {arg2}，请避免重复。', arg0=label, arg1=seen[text], arg2=text))
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


class AnnotationToolBar(QWidget):
    currentIndexChanged = Signal(int)

    def __init__(self, shortcuts, parent=None):
        super().__init__(parent)
        self.index = 0
        self.buttons = []
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
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
            button.setToolTip(label + (tr(' · 快捷键 {arg0}', arg0=shortcut) if shortcut else tr(' · 未设置快捷键')) +
                              tr('\n可在右上角「设置」修改；输入文字时不触发。'))
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
        self.setWindowTitle(tr('设置 · 语言与快捷键'))
        self.resize(640, 580)
        layout = QVBoxLayout(self)
        language_row = QFormLayout()
        self.language = QComboBox()
        for code, label in LANGUAGES:
            self.language.addItem(label, code)
        self.language.setCurrentIndex(self.language.findData(current_language()))
        language_row.addRow(tr('界面语言'), self.language)
        layout.addLayout(language_row)
        language_hint = QLabel(tr('默认为英语。保存后立即切换，并记住你的常用语言。PDF 正文、词条和个人释义保持原内容。'))
        language_hint.setWordWrap(True)
        layout.addWidget(language_hint)
        hint = QLabel(tr('点击快捷键框，再按你想使用的按键，可搭配 Ctrl、Alt、Shift。\n清空可关闭该工具的快捷键。输入框内打字时不会切换工具。'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QFormLayout()
        self.editors = {}
        for label, key in TOOLS:
            editor = QKeySequenceEdit(QKeySequence(owner.tool_shortcuts[key]))
            editor.setMaximumSequenceLength(1)
            editor.setClearButtonEnabled(True)
            self.editors[key] = editor
            form.addRow(tr(label), editor)
        layout.addLayout(form)
        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setStyleSheet('color: #b64c4c;')
        layout.addWidget(self.message)
        row = QHBoxLayout()
        reset = QPushButton(tr('恢复默认 1–7'))
        reset.clicked.connect(self.reset)
        row.addWidget(reset)
        row.addStretch()
        cancel = QPushButton(tr('取消'))
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        self.save_button = QPushButton(tr('保存'))
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
        if self.owner.save_preferences(values, self.language.currentData()):
            self.accept()
