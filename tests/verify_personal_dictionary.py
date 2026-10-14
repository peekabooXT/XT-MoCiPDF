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
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtTest import QTest
from app import MainWindow, PersonalDefinitionDialog, VocabularyExportDialog, configure_fonts, STYLE
from core import Library, export_body
from dictionary import OfflineDictionary, normalize, render_lookup
from vocabulary_export import vocabulary_rows, export_vocabulary_pdf

qa = Path(tempfile.mkdtemp(prefix='personal-dictionary-qa-', dir=ROOT / 'work'))
database = ROOT / 'dictionary/ecdict.sqlite'
base_hash = hashlib.sha256(database.read_bytes()).digest()
pdf_hash = hashlib.sha256((ROOT / 'Example.pdf').read_bytes()).digest()
app = QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
errors = []
QMessageBox.warning = QMessageBox.critical = lambda *args: errors.append(str(args[2]))
w = MainWindow(qa / 'data', reopen=False)
w.show()
w.activateWindow()
QTest.qWait(30)
assert not w.edit_definition_button.isEnabled() and not w.reset_definition_button.isEnabled()

# Unknown word groups may be saved even without a PDF or a collected entry.
w.lookup_term('predator-prey')
assert not w.dictionary.lookup('predator-prey')['entry']
before = copy.deepcopy(w.lib.state)
save = w.lib.save
w.lib.save = lambda: (_ for _ in ()).throw(OSError('intentional first save failure'))
assert not w.save_personal_definition('predator-prey', '未成功的解释')
assert w.lib.state == before and not w.dictionary.overrides
assert 'intentional first save failure' in errors.pop()
w.lib.save = save

meaning = '捕食者与猎物的关系\n用于描述生态系统中的捕食关系。\nNote: <script> is plain text & is escaped.'
phonetic = 'ˈpredətə preɪ'
def edit_unknown():
    dialog = QApplication.activeModalWidget()
    assert isinstance(dialog, PersonalDefinitionDialog)
    assert dialog.term.text() == 'predator-prey' and dialog.term.isReadOnly()
    assert not dialog.meaning.toPlainText()
    dialog.meaning.setFocus()
    QTest.keyClicks(dialog.meaning, '1234567')
    assert dialog.meaning.toPlainText() == '1234567'
    assert w.annotation_tool.currentData() == 'ink'
    dialog.meaning.setPlainText(meaning)
    dialog.phonetic.setText(phonetic)
    dialog.grab().save(str(qa / 'editor.png'))
    QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
w.annotation_tool.setCurrentIndex(w.annotation_tool.findData('ink'))
w.dictionary_pending = 'discovery'
w.dictionary_timer.start(180)
QTimer.singleShot(0, edit_unknown)
w.edit_personal_definition()
QTest.qWait(220)
assert w.dictionary_query.text() == 'predator-prey'
assert meaning in w.dictionary_view.toPlainText()
assert '个人释义 · 已保存' in w.dictionary_view.toPlainText()
assert '<script>' not in render_lookup(w.dictionary.lookup('predator-prey'))
assert w.reset_definition_button.isEnabled()
assert w.dictionary.lookup('PREDATOR–PREY.')['entry']['translation'] == meaning
assert not w.lib.state['documents']

# Cancel and blank edits preserve the saved content and keep an unsaved editor open.
dialog = PersonalDefinitionDialog(w, 'predator-prey')
dialog.meaning.clear()
dialog.save()
assert dialog.message.text() and w.dictionary.lookup('predator-prey')['entry']['translation'] == meaning
dialog.meaning.setPlainText('取消的修改')
dialog.reject()
assert w.dictionary.lookup('predator-prey')['entry']['translation'] == meaning

# Existing definitions are pre-filled, editable, and replace cached results.
w.lookup_term('mother')
dialog = PersonalDefinitionDialog(w, 'mother')
assert '母亲' in dialog.meaning.toPlainText()
dialog.meaning.setPlainText('母亲；在本文中指母体或来源。')
dialog.save()
assert w.dictionary.lookup('mother')['entry']['custom']
assert w.dictionary.lookup('MOTHER')['entry']['translation'] == '母亲；在本文中指母体或来源。'
w.lookup_term('predator-prey')
updated = '捕食者—猎物关系；这是我补充的论文释义。'
assert w.save_personal_definition('predator-prey', updated, phonetic)
assert w.dictionary.lookup('PREDATOR–PREY.')['entry']['translation'] == updated

before = copy.deepcopy(w.lib.state)
saved_overrides = copy.deepcopy(w.dictionary.overrides)
library_hash = hashlib.sha256(w.lib.path.read_bytes()).digest()
w.lib.save = lambda: (_ for _ in ()).throw(OSError('intentional edit save failure'))
assert not w.save_personal_definition('predator-prey', '未成功的覆盖')
assert w.lib.state == before and w.dictionary.overrides == saved_overrides
assert hashlib.sha256(w.lib.path.read_bytes()).digest() == library_hash
assert 'intentional edit save failure' in errors.pop()
w.lib.save = save

# All PDF documents share the personal dictionary, and printing uses the same data.
w.annotation_tool.setCurrentIndex(0)
w.import_file(str(ROOT / 'Example.pdf'))
for term in ('predator-prey', 'mother'):
    w.canvas.selection = []
    w.term_edit.setText(term)
    w.add_mark()
marks = copy.deepcopy(w.record['marks'])
cloudbook = export_body(w.record)
rows = vocabulary_rows(w.record, w.dictionary)
assert dict(rows)['predator-prey'] == updated
assert '在本文中' in dict(rows)['mother']
report = export_vocabulary_pdf(qa / 'personal-table.pdf', w.record['title'], rows)
with fitz.open(qa / 'personal-table.pdf') as doc:
    text = ''.join(p.get_text() for p in doc)
    assert updated in text and '在本文中' in text
    doc[0].get_pixmap().save(qa / 'table.png')
preview = VocabularyExportDialog(w)
assert preview.table.item(0, 1).text() == updated
preview.close()
assert w.record['marks'] == marks and export_body(w.record) == cloudbook
assert updated not in cloudbook
assert hashlib.sha256(database.read_bytes()).digest() == base_hash
assert hashlib.sha256((ROOT / 'Example.pdf').read_bytes()).digest() == pdf_hash
w.lookup_term('predator-prey')
w.resize(1480, 920)
QTest.qWait(220)
w.grab().save(str(qa / 'window.png'))
w.resize(1040, 700)
QTest.qWait(220)
w.grab().save(str(qa / 'minimum.png'))
w.close()
loaded = Library(qa / 'data')
assert loaded.state['dictionary_overrides'][normalize('predator-prey')]['translation'] == updated
w = MainWindow(qa / 'data', reopen=False)
w.show()
w.lookup_term('predator-prey')
assert updated in w.dictionary_view.toPlainText() and phonetic in w.dictionary_view.toPlainText()
assert w.dictionary.lookup('mother')['entry']['custom']

# Reset explicitly confirms deletion, clears lookup caches and returns base data.
question = QMessageBox.question
QMessageBox.question = lambda *a, **k: QMessageBox.StandardButton.No
w.reset_personal_definition()
assert w.dictionary.personal_entry('predator-prey')
QMessageBox.question = lambda *a, **k: QMessageBox.StandardButton.Yes
w.lookup_term('mother')
w.reset_personal_definition()
assert not w.dictionary.lookup('mother')['entry'].get('custom')
assert '母亲' in w.dictionary_view.toPlainText()
w.lookup_term('predator-prey')
w.reset_personal_definition()
assert not w.dictionary.lookup('predator-prey')['entry']
assert '未收录' in w.dictionary_view.toPlainText()
assert not w.reset_definition_button.isEnabled()
w.close()
assert Library(qa / 'data').state['dictionary_overrides'] == {}
QMessageBox.question = question

# Personal definitions remain usable if the packaged base dictionary is missing.
dictionary = OfflineDictionary(qa / 'missing.sqlite', saved_overrides)
assert dictionary.ready and dictionary.lookup('predator-prey')['entry']['translation'] == updated
assert dictionary.lookup('unlisted')['error']
dictionary.close()
assert not errors, errors
print('PASS: unknown/existing entries, multiline meaning/phonetic, actual edit/save UI, typing protection, cache update, global persistence/reopen, print/export integration, reset confirmation, save rollback, read-only base/PDF/TXT preservation.')
print('Visual QA:', qa)
