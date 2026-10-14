import hashlib
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from i18n import set_language
set_language('zh-CN')
from dictionary import OfflineDictionary, normalize, render_lookup
from core import export_body
from app import MainWindow, STYLE, configure_fonts
from PySide6.QtWidgets import QApplication, QInputDialog
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

database = ROOT / 'dictionary/ecdict.sqlite'
before = hashlib.sha256(database.read_bytes()).hexdigest()
d = OfflineDictionary(database)
assert d.ready and d.count == 770611
for word, meaning in [('discovery', '发现'), ('mother', '母亲'), ('Apple', '苹果'), ('research', '研究')]:
    assert meaning in render_lookup(d.lookup(word))
for word, base in [('flying', 'fly'), ('birds', 'bird'), ('saw', 'see')]:
    assert base in [entry['word'] for entry in d.lookup(word)['bases']]
assert '锯子' in d.lookup('saw')['entry']['translation']
assert d.lookup('in spite of')['entry'] and 'parts' not in d.lookup('in spite of')
phrase = d.lookup('collaborative delivery system')
assert len(phrase['parts']) == 3 and '未收录完整词组' in render_lookup(phrase)
assert '未收录' in render_lookup(d.lookup('zzreadtracefoozz'))
assert '较长' in d.lookup('x' * 241)['error']
assert '<script>' not in render_lookup(d.lookup('<script>alert</script>'))
assert normalize('  BirdS. ') == 'birds'
try:
    d.conn.execute("DELETE FROM metadata")
    raise AssertionError('Database must be read-only')
except sqlite3.OperationalError:
    pass
d.close()
qa = Path(tempfile.mkdtemp(dir=ROOT / 'work', prefix='dictionary-qa-'))
assert not OfflineDictionary(qa / 'missing.sqlite').ready
(qa / 'bad.sqlite').write_bytes(b'bad data')
assert not OfflineDictionary(qa / 'bad.sqlite').ready

app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
w = MainWindow(qa / 'library', reopen=False, language='zh-CN')
w.show()
w.import_file(str(ROOT / 'Example.pdf'))
QTest.qWait(200)
idx = next(i for i, word in enumerate(w.canvas.words) if word[4] == 'discovery.')
point = w.canvas.screen_rect(w.canvas.words[idx][:4]).center().toPoint()
QTest.mouseClick(w.canvas, Qt.MouseButton.LeftButton, pos=point)
QTest.qWait(220)
assert '发现' in w.dictionary_view.toPlainText() and not w.record['marks']
QTest.mouseDClick(w.canvas, Qt.MouseButton.LeftButton, pos=point)
QTest.mouseRelease(w.canvas, Qt.MouseButton.LeftButton, pos=point)
assert len(w.record['marks']) == 1 and '发现' in w.dictionary_view.toPlainText()
assert not w.term_edit.text() and '发现' not in export_body(w.record)
QTest.mouseClick(w.canvas, Qt.MouseButton.LeftButton, pos=point)
QTest.mouseDClick(w.canvas, Qt.MouseButton.LeftButton, pos=point)
QTest.mouseRelease(w.canvas, Qt.MouseButton.LeftButton, pos=point)
assert not w.record['marks'] and '发现' in w.dictionary_view.toPlainText()

w.term_edit.setText('birds')
QTest.qWait(220)
assert '鸟' in w.dictionary_view.toPlainText()
w.dictionary_query.setText('in spite of')
w.dictionary_query.setFocus()
QTest.keyClick(w.dictionary_query, Qt.Key.Key_Return)
assert '不管' in w.dictionary_view.toPlainText()
QTest.qWait(250)
assert w.dictionary_query.text() == 'in spite of'
w.layout_box.setCurrentIndex(1)
w.go_page(1)
QTest.qWait(80)
idx = next(i for i, word in enumerate(w.canvas.words) if word[4] == 'mother')
point = w.canvas.screen_rect(w.canvas.words[idx][:4]).center().toPoint()
QTest.mouseClick(w.canvas, Qt.MouseButton.LeftButton, pos=point)
QTest.qWait(220)
assert '母亲' in w.dictionary_view.toPlainText() and w.page_no == 1
w.add_mark()
assert 'mother' in export_body(w.record) and '母亲' not in export_body(w.record)
w.lookup_term('apple')
item = w.mark_list.item(0)
QTest.mouseClick(w.mark_list.viewport(), Qt.MouseButton.LeftButton, pos=w.mark_list.visualItemRect(item).center())
assert '母亲' in w.dictionary_view.toPlainText()
original_input = QInputDialog.getText
QInputDialog.getText = lambda *args, **kwargs: ('birds', True)
w.edit_mark()
QInputDialog.getText = original_input
assert '鸟' in w.dictionary_view.toPlainText()
w.lookup_term('collaborative delivery system')
assert '逐词释义' in w.dictionary_view.toPlainText()
w.grab().save(str(qa / 'window.png'))
w.resize(1040, 700)
QTest.qWait(240)
w.grab().save(str(qa / 'minimum.png'))
w.close()
assert hashlib.sha256(database.read_bytes()).hexdigest() == before
print('PASS: offline exact/phrase/forms, read-only, missing/corrupt, UI selection/toggle/dual/manual/edit/list, English export; screenshots:', qa)
