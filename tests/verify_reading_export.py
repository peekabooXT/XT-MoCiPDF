import hashlib
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from i18n import set_language
set_language('zh-CN')
import pymupdf as fitz
from reading_export import export_reading_pdf, page_numbers, ExportCancelled, _bands
from app import MainWindow, ReadingExportDialog, ReadingExportWorker, TESSDATA, STYLE, configure_fonts
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QDialog
from PySide6.QtTest import QTest
from PySide6.QtCore import QTimer, QEventLoop

def verify():
    qa = Path(tempfile.mkdtemp(prefix='reading-export-qa-', dir=ROOT / 'work'))
    source = qa / 'source.pdf'
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    for n in range(48):
        page.insert_text((50, 58 + n * 15), f'ROW{n:02} The researchers developed an efficient delivery system.', fontsize=11, fontname='tiro')
    doc.new_page(width=595, height=842)  # intentional blank page
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 70), 'A table must remain intact.', fontsize=12)
    page.draw_rect(fitz.Rect(45, 100, 540, 220))
    for n in range(3):
        page.insert_text((55, 125 + 35 * n), f'CELL{n} values for the diagram', fontsize=12)
    page.insert_text((50, 255), 'Text resumes after the table.', fontsize=12)
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 70), 'ROTATED page remains legible.', fontsize=14)
    page.set_rotation(90)
    doc.save(source)
    doc.close()
    source_hash = hashlib.sha256(source.read_bytes()).digest()
    # Three short source pages should use spare paper continuously, while
    # intentional blank pages and orientation changes retain their boundaries.
    packed_source = qa / 'packed-source.pdf'
    with fitz.open() as doc:
        for source_no in range(3):
            page = doc.new_page(width=595, height=842)
            for row in range(12):
                page.insert_text((50, 58 + row * 15), f'PACK{source_no}_{row:02} original row', fontsize=11)
        doc.new_page(width=595, height=842)
        page = doc.new_page(width=842, height=595)
        page.insert_text((50, 58), 'LANDSCAPE preserved', fontsize=11)
        doc.save(packed_source)
    for lines in (1, 2):
        packed_output = qa / f'packed-{lines}.pdf'
        export_reading_pdf(packed_source, packed_output, blank_lines=lines, tessdata=TESSDATA)
        with fitz.open(packed_source) as a, fitz.open(packed_output) as b:
            expected = Counter(w[4] for p in a for w in p.get_text('words'))
            actual = Counter(w[4] for p in b for w in p.get_text('words') if w[1] < p.rect.height - 34)
            assert actual == expected, (expected - actual, actual - expected)
            assert any('PACK0_' in p.get_text() and 'PACK1_' in p.get_text() for p in b)
            assert len(b) == (4 if lines == 1 else 5), len(b)
            blank = b[-2]
            assert blank.get_text().strip() == f'Source 4 | Part 1 | Print {len(b) - 1}'
            assert tuple(b[-1].rect[2:]) == (842, 595)
            assert 'Source 1-2 | Print 1' in b[0].get_text()
    export_reading_pdf(packed_source, qa / 'nonconsecutive.pdf', pages=[0, 2], tessdata=TESSDATA)
    with fitz.open(qa / 'nonconsecutive.pdf') as doc:
        assert 'Source 1,3 | Print 1' in doc[0].get_text()
        assert 'Source 1-3' not in doc[0].get_text()
    report = export_reading_pdf(source, qa / 'spaced.pdf', tessdata=TESSDATA)
    assert report['source_pages'] == 4 and report['output_pages'] > 4
    with fitz.open(source) as a, fitz.open(qa / 'spaced.pdf') as b:
        source_tokens = Counter(w[4] for p in a for w in p.get_text('words'))
        exported_tokens = Counter(w[4] for p in b for w in p.get_text('words'))
        assert all(exported_tokens[token] == count for token, count in source_tokens.items()), (source_tokens - exported_tokens, exported_tokens - source_tokens)
        before = [w for w in a[0].get_text('words') if w[4].startswith('ROW')]
        after = [w for w in b[0].get_text('words') if w[4].startswith('ROW')]
        assert len(after) > 10
        assert after[1][1] - after[0][1] > (before[1][1] - before[0][1]) * 1.8
        assert abs((after[0][3] - after[0][1]) / (before[0][3] - before[0][1]) - 555 / 595) < .01
        for p in b:
            assert tuple(round(value) for value in p.rect[2:]) in ((595, 842), (842, 595))
            for word in p.get_text('words'):
                assert fitz.Rect(word[:4]).intersects(p.rect)
        table_page = next(p for p in b if 'CELL0' in p.get_text())
        assert all(f'CELL{n}' in table_page.get_text() for n in range(3))
        b[0].get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(qa / 'spaced-first.png')
        b[1].get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(qa / 'spaced-second.png')
        table_page.get_pixmap().save(qa / 'table.png')
    assert hashlib.sha256(source.read_bytes()).digest() == source_hash
    with fitz.open(source) as original:
        word = original[0].get_text('words')[0]
    marks = [{'page': 0, 'rects': [word[:4]]}]
    export_reading_pdf(source, qa / 'highlighted.pdf', pages=[0], marks=marks, tessdata=TESSDATA)
    with fitz.open(qa / 'highlighted.pdf') as highlighted:
        assert any(drawing.get('color') and drawing['color'][0] < .1 and drawing['color'][1] > .4
                   and drawing['color'][2] > .3 for p in highlighted for drawing in p.get_drawings())
    assert hashlib.sha256(source.read_bytes()).digest() == source_hash
    assert page_numbers('1-3,3,4', 4) == [0, 1, 2, 3]
    for text in ('0', '5', '3-2', '1,', 'a', '1-2-3'):
        try:
            page_numbers(text, 4)
            raise AssertionError(text)
        except ValueError:
            pass
    export_reading_pdf(source, qa / 'range.pdf', pages=[2], blank_lines=2, tessdata=TESSDATA)
    with fitz.open(qa / 'range.pdf') as doc:
        assert 'CELL0' in ''.join(p.get_text() for p in doc) and 'ROW00' not in ''.join(p.get_text() for p in doc)
    shutil.copy2(source, qa / 'original-copy.pdf')
    for path in (source, qa / 'original-copy.pdf'):
        try:
            export_reading_pdf(source, path, tessdata=TESSDATA)
            raise AssertionError('Must protect original')
        except ValueError:
            pass
    target = qa / 'cancelled.pdf'
    target.write_bytes(b'existing export kept')
    state = {'stop': False}
    def progress(done, total, message):
        if done == 1:
            state['stop'] = True
    try:
        export_reading_pdf(source, target, tessdata=TESSDATA, progress=progress, cancelled=lambda: state['stop'])
        raise AssertionError('Cancel failed')
    except ExportCancelled:
        pass
    assert target.read_bytes() == b'existing export kept' and not list(qa.glob('.readtrace-reading-*'))
    with fitz.open(source) as doc:
        doc.save(qa / 'protected.pdf', encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw='owner', user_pw='secret')
    export_reading_pdf(qa / 'protected.pdf', qa / 'protected-output.pdf', password='secret', pages=[0], tessdata=TESSDATA)
    with fitz.open(qa / 'protected-output.pdf') as doc:
        assert doc.needs_pass and doc.authenticate('secret')
        assert 'ROW00' in doc[0].get_text()

    # Raster scan: use OCR only for locating rows; preserve the original bitmap.
    with fitz.open(source) as doc:
        pixels = doc[0].get_pixmap(matrix=fitz.Matrix(1.6, 1.6))
    scan = fitz.open()
    p = scan.new_page(width=595, height=842)
    p.insert_image(p.rect, pixmap=pixels)
    scan.save(qa / 'scan.pdf')
    scan.close()
    scan_report = export_reading_pdf(qa / 'scan.pdf', qa / 'scan-output.pdf', tessdata=TESSDATA)
    assert scan_report['ocr_pages'] == [1] and scan_report['output_pages'] >= 2
    with fitz.open(qa / 'scan-output.pdf') as doc:
        doc[0].get_pixmap().save(qa / 'scan.png')

    # Actual native export dialog, background worker and completion wiring.
    app = QApplication([])
    configure_fonts(app)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    errors = []
    QMessageBox.critical = lambda *args: errors.append(args[2])
    w = MainWindow(qa / 'library', reopen=False, language='zh-CN')
    w.show()
    w.import_file(str(ROOT / 'Example.pdf'))
    QTest.qWait(150)
    options = ReadingExportDialog(w)
    options.show()
    options.grab().save(str(qa / 'dialog.png'))
    options.scope.setCurrentIndex(1)
    assert options.selected_pages() == [w.page_no]
    options.scope.setCurrentIndex(2)
    options.range_edit.setText('1-2')
    assert options.selected_pages() == [0, 1]
    options.close()
    original_exec = ReadingExportDialog.exec
    ReadingExportDialog.exec = lambda self: QDialog.DialogCode.Accepted
    original_save = QFileDialog.getSaveFileName
    QFileDialog.getSaveFileName = lambda *args, **kwargs: (str(qa / 'ui-export.pdf'), 'PDF')
    w.export_reading()
    loop = QEventLoop()
    w.reading_worker.finished.connect(loop.quit)
    QTimer.singleShot(20000, loop.quit)
    loop.exec()
    assert w.reading_worker is None and not errors and (qa / 'ui-export.pdf').exists(), errors
    assert w.reading_button.isEnabled()
    w.grab().save(str(qa / 'window.png'))
    ReadingExportDialog.exec = original_exec
    QFileDialog.getSaveFileName = original_save
    w.close()
    print('PASS: line gap, fonts/word counts, pagination, A4, tables/rotation/blank/scans, page ranges, encryption, original protection, cancellation/atomic save, native dialog/worker:', qa)


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    verify()
