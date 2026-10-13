import copy
import os
import sys
import tempfile
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QMessageBox, QPlainTextEdit, QInputDialog
from PySide6.QtTest import QTest
from app import MainWindow, configure_fonts, STYLE
from core import Library
from tool_settings import TOOLS, DEFAULT_SHORTCUTS, ShortcutSettingsDialog, validated_shortcuts

qa = Path(tempfile.mkdtemp(prefix='tool-settings-qa-', dir=ROOT / 'work'))
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
errors = []
QMessageBox.warning = QMessageBox.critical = lambda *a: errors.append(str(a[2]))
w = MainWindow(qa / 'data', reopen=False)
w.show()
w.activateWindow()
w.import_file(str(ROOT / 'Example.pdf'))
QTest.qWait(80)
marks = copy.deepcopy(w.record['marks'])

def press(key, modifiers=Qt.KeyboardModifier.NoModifier, widget=None):
    target = widget or w.canvas
    target.setFocus()
    QTest.keyClick(target, key, modifiers)
    app.processEvents()

# Every tool is a visible button, and every default key switches the real canvas.
assert w.tool_shortcuts == DEFAULT_SHORTCUTS
for i, (label, key) in enumerate(TOOLS):
    press(getattr(Qt.Key, f'Key_{i + 1}'))
    assert w.annotation_tool.currentData() == w.canvas.tool == key
    assert w.annotation_tool.buttons[i].isChecked()
    assert sum(button.isChecked() for button in w.annotation_tool.buttons) == 1
    assert w.annotation_tool.buttons[i].isVisible()
    assert str(i + 1) in w.annotation_tool.buttons[i].text()
press(Qt.Key.Key_2, Qt.KeyboardModifier.KeypadModifier)
assert w.canvas.tool == 'highlight'
QTest.mouseClick(w.annotation_tool.buttons[4], Qt.MouseButton.LeftButton)
assert w.canvas.tool == 'rect'
press(Qt.Key.Key_Escape)
assert w.canvas.tool == 'select'

# Native text input remains native input: searching, vocabulary, and page numbers.
for edit in (w.pdf_search, w.dictionary_query, w.term_edit, w.doc_filter, w.mark_filter):
    edit.clear()
    press(Qt.Key.Key_4, widget=edit)
    assert edit.text() == '4' and w.canvas.tool == 'select'
    edit.clear()
w.page_spin.lineEdit().selectAll()
press(Qt.Key.Key_2, widget=w.page_spin.lineEdit())
assert w.page_spin.lineEdit().text() == '2' and w.canvas.tool == 'select'
w.page_spin.lineEdit().setText('1')
# A read-only dictionary panel still permits tool shortcuts.
press(Qt.Key.Key_3, widget=w.dictionary_view)
assert w.canvas.tool == 'underline'

dialog = ShortcutSettingsDialog(w)
dialog.show()
dialog.activateWindow()
QTest.qWait(30)
before = dict(w.tool_shortcuts)
editor = dialog.editors['highlight']
editor.setFocus()
QTest.keyClick(editor, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
QTest.qWait(20)
assert editor.keySequence().toString() == 'Ctrl+Shift+H'
assert w.tool_shortcuts == before and w.canvas.tool == 'underline'
dialog.editors['ink'].setKeySequence(QKeySequence('Ctrl+Shift+H'))
assert not dialog.save_button.isEnabled() and '重复' in dialog.message.text()
dialog.editors['ink'].setKeySequence(QKeySequence('Ctrl+O'))
assert not dialog.save_button.isEnabled() and '其他操作' in dialog.message.text()
dialog.editors['ink'].setKeySequence(QKeySequence('4'))
dialog.editors['erase'].clear()
assert dialog.save_button.isEnabled()
dialog.grab().save(str(qa / 'settings.png'))
dialog.save()
assert not dialog.isVisible()
assert w.tool_shortcuts['highlight'] == 'Ctrl+Shift+H' and w.tool_shortcuts['erase'] == ''
assert 'Ctrl+Shift+H' in w.annotation_tool.buttons[1].text()
assert w.annotation_tool.buttons[6].text() == '橡皮擦'
w.activateWindow()
QTest.qWait(30)
press(Qt.Key.Key_1)
press(Qt.Key.Key_2)
assert w.canvas.tool == 'select'  # Old binding no longer switches.
press(Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
assert w.canvas.tool == 'highlight'
press(Qt.Key.Key_7)
assert w.canvas.tool == 'highlight'  # Disabled binding.
press(Qt.Key.Key_1)
w.pdf_search.setText('abc')
w.pdf_search.setFocus()
QTest.keyClick(w.pdf_search, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
assert w.canvas.tool == 'select'
w.pdf_search.clear()

# Modal note input, including plain text, does not dispatch reading shortcuts.
modal = QInputDialog(w)
modal.setOption(QInputDialog.InputDialogOption.UsePlainTextEditForTextInput)
modal.setWindowTitle('测试备注输入')
modal.setModal(True)
modal.show()
modal.activateWindow()
QTest.qWait(20)
note_edit = modal.findChild(QPlainTextEdit)
note_edit.setFocus()
QTest.keyClicks(note_edit, '1234567')
assert note_edit.toPlainText() == '1234567' and w.canvas.tool == 'select'
modal.reject()
w.activateWindow()
QTest.qWait(20)

# Save failure rolls back settings; cancellation never saves changes.
saved = dict(w.tool_shortcuts)
save = w.lib.save
w.lib.save = lambda: (_ for _ in ()).throw(OSError('intentional shortcut save failure'))
assert not w.save_tool_shortcuts(DEFAULT_SHORTCUTS)
assert w.tool_shortcuts == saved and w.lib.state['tool_shortcuts'] == saved
assert 'intentional shortcut save failure' in errors.pop()
w.lib.save = save
dialog = ShortcutSettingsDialog(w)
dialog.reset()
dialog.reject()
assert w.tool_shortcuts == saved

# Responsive wrapping keeps all buttons within the navigation area at any size.
for size, image in [((2560, 1392), 'wide.png'), ((1040, 700), 'minimum.png')]:
    w.resize(*size)
    QTest.qWait(250)
    toolbar = w.annotation_tool
    assert all(toolbar.rect().contains(button.geometry()) for button in toolbar.buttons)
    for i, a in enumerate(toolbar.buttons):
        assert all(not a.geometry().intersects(b.geometry()) for b in toolbar.buttons[i + 1:])
    assert all(button.isVisible() for button in toolbar.buttons)
    w.grab().save(str(qa / image))
assert w.record['marks'] == marks and not w.record.get('annotations')
w.close()
loaded = Library(qa / 'data')
assert loaded.state['tool_shortcuts'] == saved
w = MainWindow(qa / 'data', reopen=False)
w.show()
w.activateWindow()
w.open_record(loaded.state['documents'][0])
QTest.qWait(30)
assert w.tool_shortcuts == saved
press(Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
assert w.canvas.tool == 'highlight'
dialog = ShortcutSettingsDialog(w)
dialog.reset()
dialog.save()
assert w.tool_shortcuts == DEFAULT_SHORTCUTS
w.activateWindow()
QTest.qWait(20)
press(Qt.Key.Key_7)
assert w.canvas.tool == 'erase'
w.close()
assert Library(qa / 'data').state['tool_shortcuts'] == DEFAULT_SHORTCUTS
for invalid in ('Ctrl+O', 'Esc', 'Return', 'Ctrl+K, Ctrl+H', 'NotAKey'):
    values = dict(DEFAULT_SHORTCUTS, highlight=invalid)
    try:
        validated_shortcuts(values)
        raise AssertionError('Invalid shortcut accepted: ' + invalid)
    except ValueError:
        pass
assert not errors, errors
print('PASS: visible/wrapped exclusive tool buttons, real keys 1–7/keypad, safe text/notes/spin input, editable chord capture, conflict rejection, disabling/reset/cancel, failed-save rollback, persistence/reopen and custom dispatch.')
print('Visual QA:', qa)
