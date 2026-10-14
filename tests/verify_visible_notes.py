import copy
import hashlib
import os
import sys
import tempfile
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import pymupdf as fitz
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox
from PySide6.QtTest import QTest
from app import MainWindow, configure_fonts, STYLE
from annotations import note_layout, annotation_at
from core import Library

qa = Path(tempfile.mkdtemp(prefix='visible-notes-qa-', dir=ROOT / 'work'))
source = qa / 'source.pdf'
with fitz.open() as doc:
    for rotation in (0, 90):
        page = doc.new_page(width=595, height=842)
        page.insert_text((40, 70), 'Original paper text stays selectable.', fontsize=15)
        page.set_rotation(rotation)
    doc.save(source)
source_hash = hashlib.sha256(source.read_bytes()).digest()
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
errors = []
QMessageBox.critical = QMessageBox.warning = lambda *a: errors.append(str(a[2]))
w = MainWindow(qa / 'data', reopen=False)
w.show()
w.import_file(str(source))
notes = [
    {'id': 'legacy-note', 'created': '0', 'page': 0, 'type': 'note', 'color': '#46a886',
     'width': 2, 'rect': [60, 140, 78, 158], 'text': '中文备注直接展示\n第二行：检查方法与假设。\nPlain <text> & symbols.'},
    {'id': 'rotated-note', 'created': '1', 'page': 1, 'type': 'note', 'color': '#4799de',
     'width': 2, 'rect': [575, 810, 593, 828], 'text': '旋转页面上的备注\nROTATED_COMPLETE_END'},
]
w.commit_annotations(notes)
record = copy.deepcopy(w.record['annotations'])
QTest.qWait(80)
w.canvas.grab().save(str(qa / 'canvas.png'))
assert w.canvas.note_cache
assert w.record['annotations'] == record  # Legacy anchors are not rewritten.
rect, font = note_layout(notes[0], w.canvas.page_bounds)
assert rect.width > 18 and rect.height > 40 and font == 11
assert w.canvas.page_bounds.contains(rect)
point = rect.br - fitz.Point(8, 8)
assert not fitz.Rect(notes[0]['rect']).contains(point)
assert annotation_at(notes, point, page_rect=w.canvas.page_bounds)['id'] == 'legacy-note'

# Edit and erase work anywhere inside the visible text box, beyond the old icon.
original_input = QInputDialog.getMultiLineText
QInputDialog.getMultiLineText = lambda *a, **k: ('编辑后的中文备注\nVISIBLE_EDIT_END', True)
QTest.mouseDClick(w.canvas, Qt.MouseButton.LeftButton, pos=w.canvas.screen_point(point).toPoint())
assert 'VISIBLE_EDIT_END' in w.record['annotations'][0]['text']
rect, _ = note_layout(w.record['annotations'][0], w.canvas.page_bounds)
point = rect.br - fitz.Point(8, 8)
w.annotation_tool.setCurrentIndex(w.annotation_tool.findData('erase'))
QTest.mouseClick(w.canvas, Qt.MouseButton.LeftButton, pos=w.canvas.screen_point(point).toPoint())
assert len(w.record['annotations']) == 1
w.canvas.setFocus()
w.undo_annotation()
assert len(w.record['annotations']) == 2
w.annotation_tool.setCurrentIndex(0)

w.layout_box.setCurrentIndex(1)
w.zoom_box.setCurrentText('150%')
w.go_page(1)
QTest.qWait(80)
canvas = w.reader.page_canvas(1)
rect, _ = note_layout(notes[1], canvas.page_bounds)
assert canvas.page_bounds.contains(rect)
canvas.grab().save(str(qa / 'rotated-canvas.png'))
assert canvas.note_cache
export = qa / 'visible.pdf'
w.write_highlight_pdf(export)
with fitz.open(export) as doc:
    for number, marker in [(0, 'VISIBLE_EDIT_END'), (1, 'ROTATED_COMPLETE_END')]:
        page = doc[number]
        note = next(page.annots())
        assert note.type[0] == fitz.PDF_ANNOT_FREE_TEXT
        assert marker in page.get_text() and marker in note.get_text()
        assert '中文' in doc[0].get_text()
        assert 'Original paper text stays selectable.' in page.get_text()
        page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(qa / f'export-{number}.png')

# Long notes fit on-page and retain every visible line in the PDF appearance.
long_note = dict(notes[0], text='\n'.join(f'第 {i} 行 中文说明 LINE_{i:03}' for i in range(60)))
w.commit_annotations([long_note])
w.write_highlight_pdf(qa / 'long.pdf')
with fitz.open(qa / 'long.pdf') as doc:
    page = doc[0]
    text = page.get_text()
    assert all(text.count(f'LINE_{i:03}') == 1 for i in range(60))
    page.get_pixmap().save(qa / 'long.png')
assert hashlib.sha256(source.read_bytes()).digest() == source_hash
w.close()
loaded = Library(qa / 'data').state['documents'][0]
assert loaded['annotations'][0]['text'] == long_note['text']
w = MainWindow(qa / 'data', reopen=False)
w.show()
w.open_record(loaded)
w.go_page(0)
QTest.qWait(40)
w.canvas.grab()
assert w.canvas.note_cache
w.close()
QInputDialog.getMultiLineText = original_input
assert not errors, errors
print('PASS: visible Chinese multiline notes, unchanged legacy anchors, full-box edit/erase/undo, zoom/dual/rotation, FreeText appearance/content/search, 60 complete lines, original preservation and reopen.')
print('Visual QA:', qa)
