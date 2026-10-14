import copy
import hashlib
import os
import sys
import tempfile
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from i18n import set_language
set_language('zh-CN')
import pymupdf as fitz
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QInputDialog
import core
from core import export_merged_body, merged_record, write_export_text, protect_export_path
from app import MainWindow, MergeExportDialog, VocabularyExportDialog, configure_fonts, STYLE

qa = Path(tempfile.mkdtemp(prefix='merge-export-qa-', dir=ROOT / 'work'))
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
errors = []
QMessageBox.critical = lambda *args: errors.append(args[2])
w = MainWindow(qa / 'data', reopen=False, language='zh-CN')
w.show()
sources = []
for name in ('试卷 A', '论文 B', '空文档'):
    source = qa / (name + '.pdf')
    with fitz.open() as pdf:
        pdf.new_page().insert_text((60, 90), 'mother carry with China research')
        pdf.new_page().insert_text((60, 90), name.encode('ascii', errors='ignore').decode() + ' second page')
        pdf.save(source)
    sources.append(source)
    w.import_file(str(source))
    if name == '试卷 A':
        for term, page in [('carry with', 1), ('mother', 0), ('China', 0)]:
            w.lib.add_mark(w.record, term, page)
    elif name == '论文 B':
        for term, page in [('mother', 0), ('china', 0), ('research', 1), ('predator-prey', 1)]:
            w.lib.add_mark(w.record, term, page)
records = w.lib.state['documents']
assert w.save_personal_definition('predator-prey', '捕食者与猎物关系：本机自定义释义。')
before = copy.deepcopy(w.lib.state)
before_files = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (qa / 'data').rglob('*') if p.is_file() and p.name != 'session.lock'}
active = w.record['id']

# Cross-file duplicates are removed globally, preserving phrases and case.
body = export_merged_body(records)
assert body == '#试卷 A\nmother\nChina\ncarry with\n#论文 B\nchina\nresearch\npredator-prey\n', body
assert export_merged_body(records, lower=True).count('\nchina\n') == 1
assert export_merged_body(records, dedupe=False).count('\nmother\n') == 2
assert export_merged_body([records[1]]) == '#论文 B\nmother\nchina\nresearch\npredator-prey\n'
assert export_merged_body([records[2]]) == '' and export_merged_body([]) == ''
assert export_merged_body(records, '一#本\n词本', 'chapter').startswith('#一 本 词本\n')
assert '#试卷 A · 第 2 页\ncarry with' in export_merged_body(records, mode='pages')
assert '#论文 B · 第 2 页\nresearch\npredator-prey' in export_merged_body(records, mode='pages')
assert '#' not in export_merged_body(records, mode='plain')
assert export_merged_body(records, mode='lemma').startswith('//\n')
merged = merged_record(records[:2], '打印合并词本')
assert len(merged['marks']) == 7 and len({m['id'] for m in merged['marks']}) == 7
assert len({m['page'] for m in merged['marks']}) == 2

dialog = MergeExportDialog(w)
dialog.show()
QTest.qWait(80)
assert not dialog.selected_records() and not dialog.save_button.isEnabled()
dialog.check_all(True)
assert len(dialog.selected_records()) == 2 and dialog.preview.toPlainText() == body
assert '7 个标记 → 6 个导出词条' in dialog.count.text()
dialog.lower.setChecked(True)
assert '5 个导出词条' in dialog.count.text()
dialog.lower.setChecked(False)
dialog.dedupe.setChecked(False)
assert dialog.preview.toPlainText().count('\nmother\n') == 2
dialog.dedupe.setChecked(True)
dialog.title_edit.setText('合并打印词本')
dialog.copy()
assert QApplication.clipboard().text() == body
target = qa / 'merged.txt'
QFileDialog.getSaveFileName = lambda *args, **kwargs: (str(target), 'TXT')
dialog.save()
assert target.read_text(encoding='utf-8') == body and not errors

# Uncheck one source through the actual checkbox hit area.
rect = dialog.files.visualItemRect(dialog.files.item(0))
QTest.mouseClick(dialog.files.viewport(), Qt.MouseButton.LeftButton,
                 pos=rect.topLeft() + QPoint(10, rect.height() // 2))
assert [r['title'] for r in dialog.selected_records()] == ['论文 B']
assert '#试卷 A' not in dialog.preview.toPlainText()
dialog.check_all(False)
assert not dialog.preview.toPlainText() and not dialog.pdf_button.isEnabled()
dialog.check_all(True)

# Reuse the existing editable two-column preview; no current-PDF selection leaks.
original_exec = VocabularyExportDialog.exec
opened = []
VocabularyExportDialog.exec = lambda self: opened.append(self) or 0
QTest.mouseClick(dialog.pdf_button, Qt.MouseButton.LeftButton)
VocabularyExportDialog.exec = original_exec
pdf_dialog = opened[0]
pdf_dialog.show()
assert pdf_dialog.table.rowCount() == 6 and not pdf_dialog.selected_ids
assert pdf_dialog.record['source_ids'] == [r['id'] for r in records[:2]]
assert '本机自定义释义' in dict(pdf_dialog.export_rows())['predator-prey']
pdf_dialog.dedupe.setChecked(False)
assert pdf_dialog.table.rowCount() == 7
pdf_dialog.dedupe.setChecked(True)
row = next(i for i in range(pdf_dialog.table.rowCount()) if pdf_dialog.table.item(i, 0).text() == 'research')
pdf_dialog.table.setCurrentCell(row, 1)
QInputDialog.getMultiLineText = lambda *args, **kwargs: ('研究；本次合并打印解释。', True)
pdf_dialog.edit_meaning()
pdf_target = qa / 'merged.pdf'
QFileDialog.getSaveFileName = lambda *args, **kwargs: (str(pdf_target), 'PDF')
pdf_dialog.save()
with fitz.open(pdf_target) as pdf:
    text = ''.join(p.get_text() for p in pdf)
    assert all(term in text for term in ('mother', 'China', 'china', 'carry with', 'research', 'predator-prey'))
    assert '本次合并打印解释' in text and '本机自定义释义' in text
    assert '英文单词 / 词组' in text and '中文释义' in text
    pdf[0].get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(qa / 'merged-pdf.png')

# Both formats protect every selected source, including external copies.
for exporter in (dialog, pdf_dialog):
    for path in (w.lib.pdf_path(records[0]), sources[1], qa / 'data' / 'library.json'):
        digest = hashlib.sha256(path.read_bytes()).digest()
        QFileDialog.getSaveFileName = lambda *args, path=path, **kwargs: (str(path), 'PDF')
        exporter.save()
        assert hashlib.sha256(path.read_bytes()).digest() == digest
assert len(errors) == 6
errors.clear()
QFileDialog.getSaveFileName = lambda *args, **kwargs: ('', '')
dialog.save()
pdf_dialog.save()
previous = qa / 'existing.txt'
previous.write_text('keep this file', encoding='utf-8')
replace = core.os.replace
core.os.replace = lambda *args: (_ for _ in ()).throw(OSError('simulate failure'))
try:
    write_export_text(previous, body)
    raise AssertionError('Expected save failure')
except OSError:
    pass
finally:
    core.os.replace = replace
assert previous.read_text() == 'keep this file' and not list(qa.glob('.xt-wordbook-*'))
dialog.grab().save(str(qa / 'dialog.png'))
dialog.resize(780, 540)
QTest.qWait(60)
dialog.grab().save(str(qa / 'narrow.png'))
pdf_dialog.close()
dialog.close()
assert w.record['id'] == active and w.lib.state == before
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest for p, digest in before_files.items())
w.close()

# Library-wide merge remains available without opening an active PDF.
w = MainWindow(qa / 'data', reopen=False, language='zh-CN')
assert w.record is None
opened = []
original_exec = MergeExportDialog.exec
MergeExportDialog.exec = lambda self: opened.append(self) or 0
w.export_merged()
MergeExportDialog.exec = original_exec
assert len(opened) == 1
opened[0].check_all(True)
assert len(opened[0].selected_records()) == 2
opened[0].close()
w.close()
assert not errors
print('PASS: multi-file selection, global dedupe/case/phrases/chapters, TXT/PDF, personal meanings, preview edits, source/data preservation, atomic failure:', qa)
