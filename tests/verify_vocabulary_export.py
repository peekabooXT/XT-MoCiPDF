import hashlib
import os
import sys
import tempfile
from pathlib import Path
from collections import Counter

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from i18n import set_language
set_language('zh-CN')
import pymupdf as fitz
from PySide6.QtWidgets import QApplication, QInputDialog, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from app import MainWindow, VocabularyExportDialog, STYLE, configure_fonts
from vocabulary_export import vocabulary_rows, meaning_text, export_vocabulary_pdf
from core import export_body

ROOT.joinpath('work').mkdir(exist_ok=True)
qa = Path(tempfile.mkdtemp(prefix='vocabulary-qa-', dir=ROOT / 'work'))
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
errors = []
QMessageBox.critical = lambda *args: errors.append(args[2])
QMessageBox.warning = lambda *args: errors.append(args[2])
w = MainWindow(qa / 'library', reopen=False, language='zh-CN')
w.show()
w.import_file(str(ROOT / 'Example.pdf'))
QTest.qWait(150)
for page, term in [(0, 'discovery'), (0, 'mother'), (1, 'mother'), (1, 'china'),
                   (1, 'China'), (1, 'flying'), (1, 'collaborative delivery system'), (1, 'zzreadtracefoozz')]:
    w.go_page(page)
    w.term_edit.setText(term)
    w.add_mark()
record = w.record
before_marks = repr(record['marks'])
before_txt = export_body(record)
rows = vocabulary_rows(record, w.dictionary)
assert len(rows) == 7 and len(vocabulary_rows(record, w.dictionary, False)) == 8
assert [term for term, meaning in rows][:2] == ['discovery', 'mother']
assert {'china', 'China'} <= {term for term, meaning in rows}
assert '母亲' in dict(rows)['mother'] and '词形参考 fly' in dict(rows)['flying']
assert '逐词释义' in dict(rows)['collaborative delivery system']
assert '未收录' in dict(rows)['zzreadtracefoozz']
selected = {record['marks'][1]['id']}
assert vocabulary_rows(record, w.dictionary, ids=selected)[0][0] == 'mother'
pdf = qa / 'table.pdf'
report = export_vocabulary_pdf(pdf, '英语精读词本', rows)
assert report['terms'] == 7
with fitz.open(pdf) as doc:
    all_text = ''.join(page.get_text() for page in doc)
    assert '母亲' in all_text and 'discovery' in all_text and '中文释义' in all_text
    for page in doc:
        assert '英文单词 / 词组' in page.get_text() and '中文释义' in page.get_text()
        assert page.rect.width < 596 and page.rect.height < 843
        for word in page.get_text('words'):
            assert 35 <= word[0] and word[2] <= 560, word
            assert word[1] >= 24 and word[3] <= 830, word
        assert any(doc.extract_font(font[0])[3] for font in page.get_fonts())
    doc[0].get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(qa / 'table.png')

# Multi-page tables and a definition that spans several pages: no clipping/loss.
stress_rows = [(f'entry-{n:03}', f'中文释义第 {n} 条\nSecond line') for n in range(80)]
stress_rows.append(('long-definition', '\n'.join(f'meaning-{n:03} 完整释义' for n in range(100))))
stress_rows.append(('last-word', '最后一条也必须完整。'))
stress = qa / 'stress.pdf'
stress_report = export_vocabulary_pdf(stress, '长词本分页检查', stress_rows)
assert stress_report['pages'] > 5
with fitz.open(stress) as doc:
    texts = ''.join(page.get_text() for page in doc)
    for n in range(100):
        assert texts.count(f'meaning-{n:03}') == 1, n
    assert texts.count('last-word') == 1 and '最后一条也必须完整。' in texts
    assert '（续页）' in texts
    doc[-2].get_pixmap(matrix=fitz.Matrix(1.2, 1.2)).save(qa / 'continuation.png')
    doc[-1].get_pixmap(matrix=fitz.Matrix(1.2, 1.2)).save(qa / 'last.png')
    for page in doc:
        for word in page.get_text('words'):
            assert word[2] <= 560 and word[3] <= 830, word

target = qa / 'existing.pdf'
target.write_bytes(b'previous file')
try:
    export_vocabulary_pdf(target, 'test', [])
    raise AssertionError('Empty table should fail')
except ValueError:
    pass
assert target.read_bytes() == b'previous file' and not list(qa.glob('.xt-vocabulary-*'))

# Native preview: scope, dedupe and temporary edits do not change PDF marks.
item = next(w.mark_list.item(i) for i in range(w.mark_list.count())
            if w.get_mark(w.mark_list.item(i))['id'] in selected)
item.setSelected(True)
dialog = VocabularyExportDialog(w)
dialog.show()
assert dialog.table.columnCount() == 2 and dialog.table.rowCount() == 7
assert not dialog.table.item(0, 0).flags() & Qt.ItemFlag.ItemIsEditable
dialog.scope.setCurrentIndex(1)
assert dialog.table.rowCount() == 1 and dialog.table.item(0, 0).text() == 'mother'
dialog.scope.setCurrentIndex(0)
dialog.dedupe.setChecked(False)
assert dialog.table.rowCount() == 8
dialog.dedupe.setChecked(True)
row = next(i for i in range(dialog.table.rowCount()) if dialog.table.item(i, 0).text() == 'mother')
dialog.table.setCurrentCell(row, 1)
original_edit = QInputDialog.getMultiLineText
QInputDialog.getMultiLineText = lambda *args, **kwargs: ('n. 母亲（本次自定义）', True)
dialog.edit_meaning()
QInputDialog.getMultiLineText = original_edit
assert dialog.table.item(row, 1).text() == 'n. 母亲（本次自定义）'
original_save = QFileDialog.getSaveFileName
QFileDialog.getSaveFileName = lambda *args, **kwargs: (str(qa / 'edited.pdf'), 'PDF')
dialog.save()
with fitz.open(qa / 'edited.pdf') as doc:
    assert '本次自定义' in ''.join(page.get_text() for page in doc)
assert not errors
QFileDialog.getSaveFileName = lambda *args, **kwargs: (str(w.lib.pdf_path(record)), 'PDF')
original_hash = hashlib.sha256(w.lib.pdf_path(record).read_bytes()).digest()
dialog.save()
assert errors and hashlib.sha256(w.lib.pdf_path(record).read_bytes()).digest() == original_hash
errors.clear()
QFileDialog.getSaveFileName = original_save
dialog.restore_meaning()
assert '母亲' in dialog.table.item(row, 1).text() and '本次自定义' not in dialog.table.item(row, 1).text()
dialog.grab().save(str(qa / 'dialog.png'))
dialog.close()
w.grab().save(str(qa / 'window.png'))
w.resize(1040, 700)
QTest.qWait(200)
w.grab().save(str(qa / 'minimum.png'))
assert repr(record['marks']) == before_marks and export_body(record) == before_txt
w.close()
print('PASS: two columns, Chinese embedded fonts, full definitions/pagination/continuation, dedupe/case/scope, preview edits, original/TXT preservation:', qa)
