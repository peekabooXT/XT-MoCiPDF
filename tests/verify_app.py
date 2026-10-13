import json
import os
import sys
import tempfile
from pathlib import Path
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import pymupdf as fitz
from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog, QInputDialog
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from app import MainWindow, ExportDialog, OCRWorker, STYLE, TESSDATA, configure_fonts
from core import Library, export_body, clean_term

CHECK = ROOT / 'work/qa'
CHECK.mkdir(parents=True, exist_ok=True)
DATA = Path(tempfile.mkdtemp(prefix='run-', dir=CHECK))
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
errors = []
QMessageBox.warning = lambda *args: errors.append(str(args[2]))
QMessageBox.critical = lambda *args: errors.append(str(args[2]))

sample = ROOT / 'Example.pdf'
doc = fitz.open()
page = doc.new_page(width=595, height=842)
page.insert_text((52, 64), 'READ. NOTICE. REMEMBER.', fontsize=11, color=(.04,.5,.45))
page.insert_text((52, 102), 'Small steps, lasting progress', fontsize=23)
page.insert_text((52, 154), 'A reading practice for your first vocabulary book', fontsize=12, color=(.4,.45,.5))
lines = [
    'Reading is a journey of discovery. Every paper brings new ideas',
    'and a chance to carry with you something worth remembering.',
    'I saw many flying birds near the river yesterday.',
    'The researchers developed a collaborative delivery system.',
    'Their approach can improve efficiency and reduce energy use.',
    '',
    'Try selecting one word: discovery',
    'Try selecting a phrase: carry with',
    'Try a technical phrase: collaborative delivery system',
    '',
    'Small daily habits help us make steady progress.',
    'Keep the original spelling and check every unfamiliar word.',
]
for i, line in enumerate(lines):
    page.insert_text((52, 206 + i * 27), line, fontsize=13)
page.insert_text((52, 720), 'Click a word. Drag across a phrase. Press Enter to save.', fontsize=11, color=(.04,.5,.45))
page.insert_text((52, 786), 'MoCi PDF / Sample 01', fontsize=9, color=(.5,.55,.6))
page2 = doc.new_page(width=595, height=842)
page2.insert_text((52, 70), 'Your next chapter', fontsize=23)
page2.insert_text((52, 126), 'Watching TV can help with listening comprehension.', fontsize=13)
page2.insert_text((52, 164), 'mother china China carry with watching TV', fontsize=13)
page2.insert_text((52, 230), 'A long word may wrap: inter-', fontsize=13)
page2.insert_text((52, 255), 'national cooperation.', fontsize=13)
doc.save(sample)
doc.close()

w = MainWindow(DATA / 'data', reopen=False)
w.show()
app.processEvents()
w.import_file(str(sample))
app.processEvents()
assert w.doc and len(w.doc) == 2, errors

def word_index(text, nth=0):
    return [i for i, x in enumerate(w.canvas.words) if x[4] == text][nth]

def pt(i):
    return w.canvas.screen_rect(w.canvas.words[i][:4]).center().toPoint()

def select(a, b=None):
    QTest.mousePress(w.canvas, Qt.MouseButton.LeftButton, pos=pt(a))
    if b is not None:
        QTest.mouseMove(w.canvas, pt(b), 20)
    QTest.mouseRelease(w.canvas, Qt.MouseButton.LeftButton, pos=pt(a if b is None else b))
    app.processEvents()

select(word_index('discovery.'))
assert w.term_edit.text() == 'discovery'
QTest.keyClick(w.canvas, Qt.Key.Key_Return)
assert len(w.record['marks']) == 1, 'Enter shortcut did not add term'
assert w.record['marks'][0]['rects']
select(word_index('carry'), word_index('with'))
assert w.term_edit.text() == 'carry with', w.term_edit.text()
w.add_mark()
select(word_index('collaborative'), word_index('system.'))
assert w.term_edit.text() == 'collaborative delivery system'
w.add_mark()
w.go_page(1)
select(word_index('Watching'), word_index('TV'))
assert w.term_edit.text() == 'Watching TV'
w.add_mark()
select(word_index('inter-'), word_index('cooperation.'))
assert w.term_edit.text() == 'international cooperation', w.term_edit.text()
w.add_mark()
for term in ('mother', 'china', 'China', 'carry with', 'watching TV'):
    w.term_edit.setText(term)
    w.add_mark()
body = export_body(w.record)
assert body.startswith('#Example\ndiscovery\ncarry with\n')
assert body.count('\ncarry with\n') == 1
assert '\nchina\nChina\n' in body
assert 'collaborative delivery system\n' in body
assert export_body(w.record, 'lemma').startswith('//\n')
assert not export_body(w.record, 'plain').startswith('#')
assert '#Example · 第 2 页' in export_body(w.record, 'pages')
(CHECK / 'expected_momo.txt').write_text(body, encoding='utf-8')
export_path = CHECK / 'quick_export.txt'
original_save = QFileDialog.getSaveFileName
QFileDialog.getSaveFileName = lambda *args, **kwargs: (str(export_path), '')
w.quick_export()
assert export_path.read_text(encoding='utf-8') == body
QFileDialog.getSaveFileName = original_save
highlights = CHECK / 'highlights.pdf'
w.write_highlight_pdf(str(highlights))
with fitz.open(highlights) as annotated:
    assert sum(len(list(p.annots() or [])) for p in annotated) == 5
with fitz.open(sample) as original:
    assert sum(len(list(p.annots() or [])) for p in original) == 0

dialog = ExportDialog(w, w.record)
dialog.copy()
assert app.clipboard().text() == body
dialog.show()
app.processEvents()
dialog.grab().save(str(CHECK / 'export.png'))
dialog.close()
w.go_page(0)
select(word_index('discovery.'))
w.grab().save(str(CHECK / 'main.png'))

# Search, edit and delete must update the actual persisted library.
w.pdf_search.setText('discovery')
w.search_pdf()
assert w.term_edit.text() == 'discovery'
w.mark_list.setCurrentRow(0)
old_input = QInputDialog.getText
QInputDialog.getText = lambda *args, **kwargs: ('discover', True)
w.edit_mark()
assert w.record['marks'][0]['term'] == 'discover'
QInputDialog.getText = lambda *args, **kwargs: ('discovery', True)
w.mark_list.setCurrentRow(0)
w.edit_mark()
QInputDialog.getText = old_input
before = len(w.record['marks'])
w.canvas.selection = []
w.term_edit.setText('temporary term')
w.add_mark()
temp_id = w.record['marks'][-1]['id']
for i in range(w.mark_list.count()):
    item = w.mark_list.item(i)
    if item.data(Qt.ItemDataRole.UserRole) == temp_id:
        w.mark_list.clearSelection()
        item.setSelected(True)
w.delete_marks()
assert len(w.record['marks']) == before

state_id = w.record['id']
count = len(w.record['marks'])
w.close()
reload = Library(DATA / 'data')
assert len(reload.state['documents'][0]['marks']) == count
assert reload.import_pdf(sample)['id'] == state_id
assert len(reload.state['documents']) == 1

# A rotated text page must select and export in PDF coordinates.
rot = CHECK / 'rotated.pdf'
with fitz.open() as rd:
    rp = rd.new_page(width=400, height=500)
    rp.insert_text((40, 70), 'rotated phrase test', fontsize=16)
    rp.set_rotation(90)
    rd.save(rot)
w = MainWindow(DATA / 'rotate-data', reopen=False)
w.show()
app.processEvents()
w.import_file(str(rot))
select(0, 1)
assert w.term_edit.text() == 'rotated phrase'
w.add_mark()
w.write_highlight_pdf(str(CHECK / 'rotated_highlight.pdf'))
with fitz.open(CHECK / 'rotated_highlight.pdf') as rd:
    annot = rd[0].first_annot
    assert annot and annot.info['content'] == 'rotated phrase'
w.close()

# Scanned page: genuine image only, offline OCR gives selectable coordinates.
scan = CHECK / 'scanned.pdf'
with fitz.open(sample) as d:
    pix = d[0].get_pixmap(matrix=fitz.Matrix(2, 2))
    with fitz.open() as s:
        p = s.new_page(width=595, height=842)
        p.insert_image(p.rect, stream=pix.tobytes('png'))
        assert not p.get_text('words')
        s.save(scan)
with fitz.open(scan) as s:
    scan_page = s[0]
    tp = scan_page.get_textpage_ocr(language='eng', dpi=200, full=True, tessdata=str(TESSDATA))
    words = scan_page.get_text('words', textpage=tp)
    assert any('discovery' in x[4].lower() for x in words), words
    print('OCR regions:', len(words))
w = MainWindow(DATA / 'scan-data', reopen=False)
w.show()
app.processEvents()
w.import_file(str(scan))
assert not w.canvas.words
w.ocr()
for _ in range(300):
    QTest.qWait(100)
    if not w.worker.isRunning():
        break
app.processEvents()
assert not w.worker.isRunning(), 'OCR timeout'
assert w.canvas.words, errors
select(next(i for i, x in enumerate(w.canvas.words) if 'discovery' in x[4].lower()))
w.add_mark()
assert w.record['marks']
w.close()

# Password PDFs can be authenticated and annotation export retains encryption.
encrypted = CHECK / 'encrypted.pdf'
with fitz.open(sample) as d:
    d.save(encrypted, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw='owner-test', user_pw='reader-test')
w = MainWindow(DATA / 'encrypted-data', reopen=False)
rec = w.lib.import_pdf(encrypted)
w.open_record(rec, 'reader-test')
select(word_index('discovery.'))
w.add_mark()
w.write_highlight_pdf(str(CHECK / 'encrypted_highlight.pdf'))
with fitz.open(CHECK / 'encrypted_highlight.pdf') as d:
    assert d.needs_pass
    assert d.authenticate('reader-test')
    assert d[0].first_annot
w.close()

assert not errors, errors
print('PASS: native click/drag/Enter, phrases, wrap, rotation, save/reopen, dedup, case, four exports, clipboard, highlights, scanned OCR, passwords.')
