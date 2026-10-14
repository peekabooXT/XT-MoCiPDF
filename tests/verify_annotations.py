import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import pymupdf as fitz
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog, QFileDialog
from PySide6.QtTest import QTest
from app import MainWindow, AnnotationDialog, STYLE, configure_fonts
from annotations import export_annotated_pdf, annotation_at
from core import Library, export_body

qa = Path(tempfile.mkdtemp(prefix='annotations-qa-', dir=ROOT / 'work'))
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
errors = []
QMessageBox.critical = QMessageBox.warning = lambda *a: errors.append(str(a[2]))
source = qa / 'source.pdf'
with fitz.open() as doc:
    for rotation in (0, 90):
        p = doc.new_page(width=595, height=842)
        p.insert_text((52, 80), 'Collected vocabulary stays distinct from reading notes.', fontsize=18)
        p.insert_text((52, 120), 'A paper can contain important observations and questions.', fontsize=16)
        p.insert_text((52, 200), 'Read, reflect, and write your own interpretation.', fontsize=16)
        p.set_rotation(rotation)
    p = doc[0]
    existing = p.add_text_annot((520, 220), 'Existing original note')
    existing.update()
    doc.save(source)
original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
w = MainWindow(qa / 'data', reopen=False)
w.show()
w.import_file(str(source))
QTest.qWait(70)

def tool(name):
    w.annotation_tool.setCurrentIndex(w.annotation_tool.findData(name))
    w.canvas.setFocus()

def point(x, y):
    return w.canvas.screen_point((x, y)).toPoint()

def drag(a, b, middle=None):
    QTest.mousePress(w.canvas, Qt.MouseButton.LeftButton, pos=a)
    if middle is not None:
        QTest.mouseMove(w.canvas, middle, 5)
    QTest.mouseMove(w.canvas, b, 5)
    QTest.mouseRelease(w.canvas, Qt.MouseButton.LeftButton, pos=b)
    QTest.qWait(10)

def word(text):
    return next(i for i, value in enumerate(w.canvas.words) if value[4] == text)

def word_point(text):
    return w.canvas.screen_rect(w.canvas.words[word(text)][:4]).center().toPoint()

QTest.mouseDClick(w.canvas, Qt.MouseButton.LeftButton, pos=word_point('vocabulary'))
assert len(w.record['marks']) == 1
assert w.mark_list.item(0).font().bold() and w.mark_list.item(0).font().underline()
momo = export_body(w.record)
marked = copy.deepcopy(w.record['marks'])

tool('highlight')
drag(word_point('important'), word_point('observations'))
assert len(w.record['annotations']) == 1 and len(w.record['annotations'][0]['rects']) == 2
assert not w.canvas.selection and not w.term_edit.text()
# Annotating never collects words, including Enter / double clicks.
QTest.mouseDClick(w.canvas, Qt.MouseButton.LeftButton, pos=word_point('questions.'))
QTest.keyClick(w.canvas, Qt.Key.Key_Return)
assert w.record['marks'] == marked

tool('underline')
w.annotation_color.setCurrentIndex(w.annotation_color.findData('#e87070'))
w.annotation_width.setValue(4)
drag(word_point('own'), word_point('interpretation.'))
assert w.record['annotations'][-1]['width'] == 4
tool('ink')
drag(point(90, 255), point(170, 270), point(120, 290))
assert len(w.record['annotations'][-1]['points']) >= 3
tool('rect')
drag(point(340, 290), point(210, 230))
r = fitz.Rect(w.record['annotations'][-1]['rect'])
assert r.width > 125 and r.height > 55 and not r.is_empty
count = len(w.record['annotations'])
drag(point(200, 210), point(201, 211))
assert len(w.record['annotations']) == count

old_input = QInputDialog.getMultiLineText
QInputDialog.getMultiLineText = lambda *a, **k: ('中文备注：这里的方法值得对比。\nNext step: check the assumptions.', True)
tool('note')
QTest.mouseClick(w.canvas, Qt.MouseButton.LeftButton, pos=point(420, 230))
note = w.record['annotations'][-1]
assert note['type'] == 'note' and '中文备注' in note['text']
QInputDialog.getMultiLineText = lambda *a, **k: ('取消的备注', False)
QTest.mouseClick(w.canvas, Qt.MouseButton.LeftButton, pos=point(440, 340))
assert len(w.record['annotations']) == count + 1
QInputDialog.getMultiLineText = lambda *a, **k: ('修改后：Chinese note retained 完整中文。', True)
tool('select')
QTest.mouseDClick(w.canvas, Qt.MouseButton.LeftButton, pos=point(425, 235))
assert '修改后' in w.record['annotations'][-1]['text']
assert len(w.record['marks']) == 1

before_erase = copy.deepcopy(w.record['annotations'])
tool('erase')
QTest.mouseClick(w.canvas, Qt.MouseButton.LeftButton, pos=point(425, 235))
assert len(w.record['annotations']) == count
w.canvas.setFocus()
QTest.keyClick(w.canvas, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
assert w.record['annotations'] == before_erase
QTest.keyClick(w.canvas, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
assert len(w.record['annotations']) == count
w.undo_annotation()
assert w.record['annotations'] == before_erase
# An eraser never removes a collected vocabulary entry.
QTest.mouseClick(w.canvas, Qt.MouseButton.LeftButton, pos=word_point('vocabulary'))
assert w.record['marks'] == marked and export_body(w.record) == momo

dialog = AnnotationDialog(w)
assert dialog.items.count() == count + 1
dialog.items.setCurrentRow(0)
dialog.locate()
dialog.delete()
assert len(w.record['annotations']) == count
w.canvas.setFocus()
w.undo_annotation()
assert w.record['annotations'] == before_erase
dialog.refresh()
dialog.show()
app.processEvents()
dialog.grab().save(str(qa / 'manager.png'))
dialog.close()
w.activateWindow()
QTest.qWait(30)

tool('ink')
QTest.mousePress(w.canvas, Qt.MouseButton.LeftButton, pos=point(30, 400))
QTest.mouseMove(w.canvas, point(120, 400))
assert w.canvas.draft
QTest.keyClick(w.canvas, Qt.Key.Key_Escape)
QTest.mouseRelease(w.canvas, Qt.MouseButton.LeftButton, pos=point(120, 400))
assert not w.canvas.draft and w.annotation_tool.currentData() == 'select'
assert w.record['annotations'] == before_erase

# Geometry persists through dual-page, zoom and rotated pages.
w.layout_box.setCurrentIndex(1)
w.go_page(1)
w.zoom_box.setCurrentText('150%')
tool('ink')
drag(point(80, 250), point(150, 280), point(110, 270))
assert w.record['annotations'][-1]['page'] == 1
assert abs(w.record['annotations'][-1]['points'][0][0] - 80) < 1
assert abs(w.record['annotations'][-1]['points'][0][1] - 250) < 1
tool('highlight')
drag(word_point('important'), word_point('observations'))
assert w.record['annotations'][-1]['page'] == 1
tool('select')
QTest.mouseDClick(w.canvas, Qt.MouseButton.LeftButton, pos=word_point('vocabulary'))
assert w.record['marks'][-1]['page'] == 1
w.zoom_box.setCurrentText('100%')
assert len(w.canvas.annotations) == 2

# Failed saves roll back mutations/history and leave the original library intact.
current = copy.deepcopy(w.record['annotations'])
saved_history = copy.deepcopy(w.annotation_history)
save = w.lib.save
w.lib.save = lambda: (_ for _ in ()).throw(OSError('intentional annotation save failure'))
w.annotation_action(1, {'type': 'ink', 'color': '#4799de', 'width': 2, 'points': [[80, 400], [90, 400]]})
assert w.record['annotations'] == current and w.annotation_history == saved_history
assert 'intentional annotation save failure' in errors.pop()
w.lib.save = save

destination = qa / 'annotated.pdf'
w.write_highlight_pdf(destination)
with fitz.open(source) as original, fitz.open(destination) as annotated:
    assert annotated[0].get_text().startswith(original[0].get_text())
    annots = [(a.type[0], a.info['content']) for page in annotated for a in (page.annots() or [])]
    assert len(annots) == 1 + len(w.record['marks']) + len(w.record['annotations'])
    types = {a[0] for a in annots}
    assert {fitz.PDF_ANNOT_TEXT, fitz.PDF_ANNOT_FREE_TEXT, fitz.PDF_ANNOT_INK, fitz.PDF_ANNOT_SQUARE,
            fitz.PDF_ANNOT_HIGHLIGHT, fitz.PDF_ANNOT_UNDERLINE} <= types
    texts = [a[1] for a in annots]
    assert 'Existing original note' in texts and any('完整中文' in text for text in texts)
    annotated[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(qa / 'export.png')
    annotated[1].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(qa / 'rotated.png')

assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
for target in (source, w.lib.pdf_path(w.record)):
    try:
        w.write_highlight_pdf(target)
        raise AssertionError('Source overwrite accepted')
    except ValueError:
        pass
# Atomic failure preserves a previously exported file.
old_hash = hashlib.sha256(destination.read_bytes()).digest()
try:
    export_annotated_pdf(source, destination, [], [{'page': 0, 'type': 'unknown'}])
    raise AssertionError('Invalid annotation accepted')
except ValueError:
    pass
assert hashlib.sha256(destination.read_bytes()).digest() == old_hash

state = copy.deepcopy(w.record)
w.go_page(0)
w.zoom_box.setCurrentText('适合宽度')
w.resize(1480, 920)
w.grab().save(str(qa / 'window.png'))
w.resize(1040, 700)
QTest.qWait(240)
w.grab().save(str(qa / 'minimum.png'))
w.close()
loaded = Library(qa / 'data').state['documents'][0]
assert loaded['annotations'] == state['annotations'] and loaded['marks'] == state['marks']
w = MainWindow(qa / 'data', reopen=False)
w.show()
w.open_record(loaded)
assert w.canvas.annotations and w.manage_annotation_button.text() == '批注 · 7'
w.close()

# Password protection stays intact in exported copies.
encrypted = qa / 'encrypted.pdf'
with fitz.open(source) as original:
    original.save(encrypted, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw='test-pass', owner_pw='owner')
export_annotated_pdf(encrypted, qa / 'encrypted-export.pdf', state['marks'], state['annotations'], 'test-pass')
with fitz.open(qa / 'encrypted-export.pdf') as doc:
    assert doc.needs_pass and doc.authenticate('test-pass')
    assert len(doc) == 2 and len(list(doc[1].annots())) == 3
QInputDialog.getMultiLineText = old_input
assert not errors, errors
(qa / 'result.json').write_text(json.dumps({'ok': True, 'annotations': 7, 'marks': 2, 'qa': str(qa)}))
print('PASS: real highlight/underline/ink/rectangle/Chinese notes, distinct vocabulary, undo/redo/erase, manage/edit, auto-save/reopen, save rollback, zoom/dual/rotation, preserved original annotations, protected atomic encrypted PDF export.')
print('Visual QA:', qa)
