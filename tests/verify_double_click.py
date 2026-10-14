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
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from app import MainWindow, STYLE, configure_fonts
from core import Library, export_body

qa = ROOT / 'work/double-click-qa'
qa.mkdir(exist_ok=True)
data = Path(tempfile.mkdtemp(dir=qa))
errors = []
QMessageBox.warning = lambda *args: errors.append(str(args[2]))
QMessageBox.critical = lambda *args: errors.append(str(args[2]))
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
w = MainWindow(data / 'library', reopen=False, language='zh-CN')
w.show()
w.import_file(str(ROOT / 'Example.pdf'))
QTest.qWait(120)

def index(text, n=0):
    return [i for i, word in enumerate(w.canvas.words) if word[4] == text][n]

def point(i):
    return w.canvas.screen_rect(w.canvas.words[i][:4]).center().toPoint()

def double(i):
    pt = point(i)
    # A real double click includes the initial normal press/release.
    QTest.mouseClick(w.canvas, Qt.MouseButton.LeftButton, pos=pt)
    QTest.mouseDClick(w.canvas, Qt.MouseButton.LeftButton, pos=pt)
    QTest.mouseRelease(w.canvas, Qt.MouseButton.LeftButton, pos=pt)
    QTest.qWait(40)

double(index('discovery.'))
assert len(w.record['marks']) == 1 and w.record['marks'][0]['term'] == 'discovery'
assert len(w.canvas.marks) == 1 and not w.canvas.selection
assert '\ndiscovery\n' in export_body(w.record)
double(index('discovery.'))
assert not w.record['marks'] and not w.canvas.marks
assert not export_body(w.record) and not w.term_edit.text()
assert not Library(data / 'library').state['documents'][0]['marks']

# Same spelling at another location remains marked after cancelling one occurrence.
double(index('discovery.'))
double(index('discovery'))
assert len(w.record['marks']) == 2
second_rects = w.record['marks'][1]['rects']
double(index('discovery.'))
assert len(w.record['marks']) == 1 and w.record['marks'][0]['rects'] == second_rects
double(index('discovery'))
assert not w.record['marks']

# Dragged phrase is cancelled as a whole by double-clicking its middle word.
start, end = index('collaborative'), index('system.')
QTest.mousePress(w.canvas, Qt.MouseButton.LeftButton, pos=point(start))
QTest.mouseMove(w.canvas, point(end), 10)
QTest.mouseRelease(w.canvas, Qt.MouseButton.LeftButton, pos=point(end))
QTest.keyClick(w.canvas, Qt.Key.Key_Return)
assert w.record['marks'][0]['term'] == 'collaborative delivery system'
double(index('delivery'))
assert not w.record['marks']
double(index('delivery'))
assert w.record['marks'][0]['term'] == 'delivery'
double(index('delivery'))
assert not w.record['marks']

# Dual view and zoom still use the correct page and PDF-space coordinates.
w.layout_box.setCurrentIndex(1)
w.go_page(1)
QTest.qWait(80)
double(index('mother'))
assert w.record['marks'][0]['page'] == 1
w.zoom_box.setCurrentText('150%')
double(index('mother'))
assert not w.record['marks']

# Overlapping single-word and phrase marks remove the shorter mark first.
w.go_page(0)
w.canvas.selection = [index('collaborative'), index('delivery'), index('system.')]
w.term_edit.setText('collaborative delivery system')
w.add_mark()
w.canvas.selection = [index('delivery')]
w.term_edit.setText('delivery')
w.add_mark()
double(index('delivery'))
assert len(w.record['marks']) == 1 and w.record['marks'][0]['term'] == 'collaborative delivery system'
double(index('delivery'))
assert not w.record['marks']

# Background double clicks must not add or remove entries.
QTest.mouseDClick(w.canvas, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))
assert not w.record['marks']

# Failed persistence must preserve the mark instead of reporting a cancellation.
double(index('discovery.'))
save = w.lib.save
def fail_save():
    raise OSError('intentional save failure')
w.lib.save = fail_save
double(index('discovery.'))
assert len(w.record['marks']) == 1 and len(w.canvas.marks) == 1
assert len(errors) == 1 and 'intentional save failure' in errors[0]
errors.clear()
w.lib.save = save
double(index('discovery.'))
assert not w.record['marks']
w.close()

# Rotated pages receive the same double-click toggle behavior.
rotated = qa / 'rotated.pdf'
with fitz.open() as doc:
    page = doc.new_page(width=400, height=500)
    page.insert_text((40, 70), 'rotated vocabulary', fontsize=15)
    page.set_rotation(90)
    doc.save(rotated)
w = MainWindow(data / 'rotated-library', reopen=False, language='zh-CN')
w.show()
w.import_file(str(rotated))
double(index('vocabulary'))
assert w.record['marks'][0]['term'] == 'vocabulary'
double(index('vocabulary'))
assert not w.record['marks']
w.close()
assert not errors, errors
print('PASS: real double-click add/cancel, highlight/export/persistence synchronization, duplicate occurrences, phrase cancellation, overlapping marks, dual view, zoom, rotation, blank clicks, save-failure rollback.')
