"""Native input regression for erasing, modifier drawing and grouped words."""
import copy
import hashlib
import math
import os
import sys
import tempfile
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import pymupdf as fitz
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog
from app import MainWindow, STYLE, configure_fonts
from core import Library, export_body
from annotations import export_annotated_pdf

qa = Path(tempfile.mkdtemp(prefix='editor-qa-', dir=ROOT / 'work'))
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
errors = []
QMessageBox.critical = QMessageBox.warning = lambda *args: errors.append(str(args[2]))
source = qa / 'source.pdf'
with fitz.open() as doc:
    for rotation in (0, 90):
        page = doc.new_page(width=595, height=842)
        page.insert_text((52, 80), 'research research Research carry with', fontsize=16)
        page.set_rotation(rotation)
    doc.save(source)
source_hash = hashlib.sha256(source.read_bytes()).digest()
w = MainWindow(qa / 'data', reopen=False, language='zh-CN')
w.show()
w.import_file(str(source))
QTest.qWait(100)

def tool(name):
    w.annotation_tool.setCurrentIndex(w.annotation_tool.findData(name))
    w.canvas.setFocus()

def mouse(kind, point, modifiers=Qt.KeyboardModifier.NoModifier):
    position = w.canvas.screen_point(point)
    button = Qt.MouseButton.NoButton if kind == QEvent.Type.MouseMove else Qt.MouseButton.LeftButton
    buttons = Qt.MouseButton.NoButton if kind == QEvent.Type.MouseButtonRelease else Qt.MouseButton.LeftButton
    event = QMouseEvent(kind, position, QPointF(w.canvas.mapToGlobal(position.toPoint())), button, buttons, modifiers)
    QApplication.sendEvent(w.canvas, event)

def stroke(start, middle, end, modifier):
    mouse(QEvent.Type.MouseButtonPress, start, modifier)
    mouse(QEvent.Type.MouseMove, middle, modifier)
    mouse(QEvent.Type.MouseMove, end, modifier)
    mouse(QEvent.Type.MouseButtonRelease, end, modifier)

for page_no in (0, 1):
    w.go_page(page_no)
    QTest.qWait(50)
    tool('ink')
    stroke((60, 150), (100, 210), (180, 150), Qt.KeyboardModifier.ControlModifier)
    straight = w.record['annotations'][-1]
    assert len(straight['points']) == 2 and math.dist(straight['points'][-1], [180, 150]) < 2
    stroke((60, 220), (100, 280), (180, 220), Qt.KeyboardModifier.ShiftModifier)
    wave = w.record['annotations'][-1]
    assert len(wave['points']) > 20
    assert max(p[1] for p in wave['points']) - min(p[1] for p in wave['points']) > 4
    assert math.dist(wave['points'][0], [60, 220]) < 2 and math.dist(wave['points'][-1], [180, 220]) < 2
    # Changing modifiers while drawing changes the preview immediately.
    mouse(QEvent.Type.MouseButtonPress, (60, 300))
    mouse(QEvent.Type.MouseMove, (90, 340))
    QTest.keyPress(w.canvas, Qt.Key.Key_Control)
    assert len(w.canvas.draft['points']) == 2
    QTest.keyRelease(w.canvas, Qt.Key.Key_Control)
    mouse(QEvent.Type.MouseMove, (130, 300))
    mouse(QEvent.Type.MouseButtonRelease, (130, 300))
    assert len(w.record['annotations'][-1]['points']) >= 3

w.go_page(0)
QTest.qWait(70)
tool('erase')
before = copy.deepcopy(w.record['annotations'])
idle_cursor = w.canvas.cursor().pixmap().toImage()
idle_cursor.save(str(qa / 'eraser-idle.png'))
mouse(QEvent.Type.MouseButtonPress, (120, 110))
pressed_cursor = w.canvas.cursor().pixmap().toImage()
pressed_cursor.save(str(qa / 'eraser-pressed.png'))
assert idle_cursor != pressed_cursor
# A sparse mouse event crosses all three strokes; intermediate hits still erase.
mouse(QEvent.Type.MouseMove, (120, 370))
mouse(QEvent.Type.MouseButtonRelease, (120, 370))
assert len(w.record['annotations']) == 3 and all(a['page'] == 1 for a in w.record['annotations'])
assert w.canvas.cursor().pixmap().toImage() == idle_cursor
w.undo_annotation()
assert w.record['annotations'] == before
w.redo_annotation()
assert len(w.record['annotations']) == 3
w.undo_annotation()
# Save failure keeps annotations and undo history intact.
history = copy.deepcopy(w.annotation_history)
save = w.lib.save
w.lib.save = lambda: (_ for _ in ()).throw(OSError('simulated write failure'))
mouse(QEvent.Type.MouseButtonPress, (120, 150))
mouse(QEvent.Type.MouseButtonRelease, (120, 150))
assert w.record['annotations'] == before and w.annotation_history == history
w.lib.save = save
assert errors and errors[-1].endswith('simulated write failure')
errors.clear()

tool('select')
for page_no in (0, 1):
    page_words = w.doc[page_no].get_text('words')
    for index, word in enumerate(page_words):
        w.lib.add_mark(w.record, word[4], page_no, [list(word[:4])], index)
w.refresh_marks()
assert len(w.record['marks']) == 10 and w.mark_list.count() == 4
assert '4 个词条' in w.mark_count.text() and '10 个标记' in w.mark_count.text()
item = w.mark_list.item(0)
assert '第 1, 2 页' in item.text() and len(item.data(Qt.ItemDataRole.UserRole + 1)) == 4
marks = copy.deepcopy(w.record['marks'])
# Filtering and repeated refresh never discard occurrences.
w.mark_filter.setText('research')
assert w.mark_list.count() == 2 and w.record['marks'] == marks
w.mark_filter.clear()
QInputDialog.getText = lambda *args, **kwargs: ('study', True)
w.mark_list.setCurrentRow(0)
w.edit_mark()
assert sum(m['term'] == 'study' for m in w.record['marks']) == 4
assert export_body(w.record).count('\nstudy\n') == 1
w.mark_list.setCurrentRow(0)
w.delete_marks()
assert len(w.record['marks']) == 6 and all(m['term'] != 'study' for m in w.record['marks'])
remaining = copy.deepcopy(w.record['marks'])
# Removing one page occurrence preserves the other grouped occurrences.
w.remove_mark_ids({remaining[0]['id']})
assert len(w.record['marks']) == 5 and w.mark_list.count() == 3
assert Library(qa / 'data').state['documents'][0]['marks'] == w.record['marks']
# Failed group editing rolls back every occurrence, then merging into an
# existing spelling collapses the row without losing its original positions.
group_item = next(w.mark_list.item(i) for i in range(w.mark_list.count())
                  if w.get_mark(w.mark_list.item(i))['term'] == 'carry')
w.mark_list.setCurrentItem(group_item)
QInputDialog.getText = lambda *args, **kwargs: ('with', True)
snapshot = copy.deepcopy(w.record['marks'])
w.lib.save = lambda: (_ for _ in ()).throw(OSError('simulated group edit failure'))
w.edit_mark()
assert w.record['marks'] == snapshot
w.lib.save = save
assert errors
errors.clear()
group_item = next(w.mark_list.item(i) for i in range(w.mark_list.count())
                  if w.get_mark(w.mark_list.item(i))['term'] == 'carry')
w.mark_list.setCurrentItem(group_item)
w.edit_mark()
assert w.mark_list.count() == 2 and len(w.record['marks']) == 5
assert sum(m['term'] == 'with' for m in w.record['marks']) == 4

exported = qa / 'annotations.pdf'
export_annotated_pdf(source, exported, w.record['marks'], w.record['annotations'])
with fitz.open(exported) as doc:
    assert sum(a.type[0] == fitz.PDF_ANNOT_INK for page in doc for a in page.annots()) == 6
assert hashlib.sha256(source.read_bytes()).digest() == source_hash

w.resize(2560, 1392)
QTest.qWait(200)
right = w.manage_annotation_button.mapTo(w.annotation_strip, w.manage_annotation_button.rect().topRight()).x()
assert w.annotation_strip.width() - right < 10
left = w.annotation_color.mapTo(w.annotation_strip, w.annotation_color.rect().topLeft()).x()
tool_right = w.annotation_tool.mapTo(w.annotation_strip, w.annotation_tool.rect().topRight()).x()
assert left - tool_right > 100
w.grab().save(str(qa / 'wide.png'))
w.annotation_width.grab().save(str(qa / 'stepper.png'))
w.resize(1040, 700)
QTest.qWait(250)
assert w.annotation_navigation.horizontalScrollBar().maximum() > 0
w.annotation_navigation.horizontalScrollBar().setValue(w.annotation_navigation.horizontalScrollBar().maximum())
w.grab().save(str(qa / 'minimum.png'))
w.close()
assert not errors, errors
print('PASS: right toolbar, white/black eraser, swept continuous erase and grouped undo, save rollback, Ctrl/Shift pen on rotated pages, deduplicated list/edit/delete, PDF export and data preservation.')
print('Screenshots:', qa)
