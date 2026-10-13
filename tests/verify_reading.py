import os
import sys
import tempfile
from pathlib import Path
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import pymupdf as fitz
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QWheelEvent
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtTest import QTest
from app import MainWindow, STYLE, configure_fonts
from core import Library, export_body

qa = ROOT / 'work/reading-qa'
qa.mkdir(exist_ok=True)
data = Path(tempfile.mkdtemp(dir=qa))
errors = []
QMessageBox.warning = lambda *args: errors.append(str(args[2]))
QMessageBox.critical = lambda *args: errors.append(str(args[2]))
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
paper = qa / 'LongPaper.pdf'
with fitz.open() as doc:
    for i in range(60):
        page = doc.new_page(width=595 if i % 3 else 620, height=842 if i % 4 else 880)
        page.insert_text((48, 66), f'READING / PAGE {i + 1:02}', fontsize=12, color=(.04,.5,.45))
        page.insert_text((48, 114), f'Chapter {i + 1}: Ideas worth keeping', fontsize=21)
        for j in range(18):
            page.insert_text((48, 176 + j * 29), f'Page{i + 1} collaborative delivery improves efficiency.', fontsize=12)
        if i == 4:
            page.set_rotation(90)
    doc.save(paper)
w = MainWindow(data / 'library', reopen=False)
w.show()
app.processEvents()
w.import_file(str(paper))
QTest.qWait(260)
assert len(w.reader.boxes) == 60
assert len(w.reader.canvases) < 10, len(w.reader.canvases)
assert w.reader.boxes[1].y() > w.reader.boxes[0].bottom()

# Real wheel events through the scroll-area viewport cross a page boundary.
viewport = w.scroll.viewport()
for _ in range(25):
    position = QPointF(100, 100)
    event = QWheelEvent(position, QPointF(viewport.mapToGlobal(QPoint(100, 100))),
                        QPoint(0, -180), QPoint(0, -120), Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.ScrollUpdate, False)
    QApplication.sendEvent(viewport, event)
    QTest.qWait(50)
assert w.page_no > 0, (w.page_no, w.scroll.verticalScrollBar().value())
assert w.page_spin.value() == w.page_no + 1
assert w.reader.canvases[w.page_no].words

# Double-page view, select on the right; annotations use that PDF page.
w.layout_box.setCurrentIndex(1)
w.go_page(0)
QTest.qWait(100)
left, right = w.reader.boxes[:2]
assert left.y() == right.y() and right.x() > left.right()
right_canvas = w.reader.page_canvas(1)
idx = next(i for i, word in enumerate(right_canvas.words) if word[4] == 'collaborative')
pt = right_canvas.screen_rect(right_canvas.words[idx][:4]).center().toPoint()
QTest.mouseClick(right_canvas, Qt.MouseButton.LeftButton, pos=pt)
QTest.qWait(80)
assert w.page_no == 1 and w.term_edit.text() == 'collaborative'
assert w.canvas is right_canvas
QTest.keyClick(right_canvas, Qt.Key.Key_Return)
assert w.record['marks'][-1]['page'] == 1
assert w.record['marks'][-1]['term'] == 'collaborative'
w.grab().save(str(qa / 'dual.png'))

# Odd final spread and rotated/mixed-size pages fit the requested layout.
w.go_page(4)
assert w.reader.boxes[4].width() > w.reader.boxes[4].height()
w.go_page(59)
QTest.qWait(80)
assert w.page_no == 59
assert len(w.reader.canvases) < 10
w.layout_box.setCurrentIndex(0)
w.zoom_box.setCurrentText('150%')
w.go_page(30)
QTest.qWait(100)
assert w.page_no == 30 and len(w.reader.canvases) < 10
w.zoom_box.setCurrentText('适合宽度')
QTest.qWait(100)
assert w.page_no == 30

# Search and mark-list navigation include the document-space page offset.
w.pdf_search.setText('Page45')
w.search_pdf()
QTest.qWait(80)
assert w.page_no == 44 and w.term_edit.text() == 'Page45'
w.add_mark()
item = next(w.mark_list.item(i) for i in range(w.mark_list.count()) if w.get_mark(w.mark_list.item(i))['page'] == 1)
w.jump_mark(item)
QTest.qWait(80)
assert w.page_no == 1
assert w.scroll.verticalScrollBar().value() > 0
assert '\ncollaborative\n' in export_body(w.record)

# Both pages remain correctly selected at different zoom levels.
w.layout_box.setCurrentIndex(1)
w.zoom_box.setCurrentText('125%')
w.go_page(10)
canvas = w.reader.page_canvas(11)
idx = next(i for i, word in enumerate(canvas.words) if word[4] == 'delivery')
pt = canvas.screen_rect(canvas.words[idx][:4]).center().toPoint()
QTest.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=pt)
assert w.page_no == 11 and w.term_edit.text() == 'delivery'
w.add_mark()
assert w.record['marks'][-1]['page'] == 11

# Cache remains bounded even after traversing an entire long document.
w.zoom_box.setCurrentText('适合宽度')
for n in range(0, 60, 4):
    w.go_page(n)
    QTest.qWait(40)
assert len(w.reader.canvases) < 10, len(w.reader.canvases)
w.go_page(11)
QTest.qWait(80)
w.close()
lib = Library(data / 'library')
assert lib.state['documents'][0]['page'] == 11
assert lib.state['view_columns'] == 2
reload = MainWindow(data / 'library', reopen=True)
reload.show()
QTest.qWait(250)
assert reload.layout_box.currentData() == 2 and reload.page_no == 11
reload.close()
assert not errors, errors
print('PASS: wheel pagination, lazy rendering, two-page layout, right-page marking, rotated/mixed pages, zoom, search, mark navigation, bounded cache, view/read-position restore.')
