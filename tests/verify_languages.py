import ast
import copy
import hashlib
import json
import os
import string
import sys
import tempfile
from pathlib import Path

os.environ['QT_QPA_PLATFORM']='offscreen'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pymupdf as fitz
from PySide6.QtGui import QPageSize,QTextLayout
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QMessageBox
from app import (MainWindow,MergeExportDialog,VocabularyExportDialog,ReadingExportDialog,
                 PersonalDefinitionDialog,configure_fonts,STYLE)
from tool_settings import ShortcutSettingsDialog
from core import Library,export_body
from i18n import LANGUAGES,catalog,current_language,tr,set_language
from vocabulary_export import export_vocabulary_pdf,vocabulary_rows
from author_statement import statement_html,CONTACT

qa=Path(tempfile.mkdtemp(prefix='languages-qa-',dir=ROOT/'work'))
app=QApplication([])
configure_fonts(app)
app.setStyle('Fusion')
app.setStyleSheet(STYLE)
errors=[]
QMessageBox.critical=lambda *args:errors.append(str(args[2]))
w=MainWindow(qa/'data',reopen=False)
w.show()
assert current_language()=='en' and 'language' not in w.lib.state
assert w.merge_export_button.text()=='Merge wordbooks'
assert w.annotation_tool.buttons[0].text()=='Select / Read  1'
settings=ShortcutSettingsDialog(w)
assert settings.language.count()==12 and settings.language.currentData()=='en'
# Merely changing the combo and cancelling never stores a preference.
settings.language.setCurrentIndex(settings.language.findData('fr'))
settings.reject()
assert current_language()=='en' and 'language' not in Library(qa/'data').state
assert w.save_preferences(w.tool_shortcuts,'de')
assert current_language()=='de' and 'Wortlisten' in w.merge_export_button.text()
assert Library(qa/'data').state['language']=='de'
w.close()
w=MainWindow(qa/'data',reopen=False)
w.show()
assert current_language()=='de'
w.import_file(str(ROOT/'Example.pdf'))
w.lib.add_mark(w.record,'research',0)
w.lib.add_mark(w.record,'predator-prey',0)
assert w.save_personal_definition('predator-prey','捕食者与猎物：用户内容不随界面语言变化。')
before=copy.deepcopy(w.record)
before_definition=copy.deepcopy(w.lib.state['dictionary_overrides'])
source_hash=hashlib.sha256(w.lib.pdf_path(w.record).read_bytes()).digest()
body_before=export_body(w.record,mode='chapter')
position=w.page_no

# Every catalog is complete and preserves all runtime format fields and HTML.
keys=set()
for path in (ROOT/'src').glob('*.py'):
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='tr' and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
            keys.add(node.args[0].value)
formatter=string.Formatter()
for code,label in LANGUAGES:
    values=catalog(code)
    assert keys<=values.keys(),(code,keys-values.keys())
    for key in keys:
        a=[name for literal,name,spec,conv in formatter.parse(key) if name is not None]
        b=[name for literal,name,spec,conv in formatter.parse(values[key]) if name is not None]
        assert sorted(a)==sorted(b),(code,key)
        if key.endswith('\n'):assert values[key].endswith('\n'),(code,key)
    assert w.save_preferences(w.tool_shortcuts,code)
    assert current_language()==code and Library(qa/'data').state['language']==code
    assert app.layoutDirection()==(Qt.LayoutDirection.RightToLeft if code=='ar' else Qt.LayoutDirection.LeftToRight)
    a4=QPageSize(QPageSize.PageSizeId.A4)
    assert a4.isValid() and a4.size(QPageSize.Unit.Point).width()==595
    glyphs=QTextLayout(str(tr('设置')),app.font())
    glyphs.beginLayout()
    glyphs.createLine().setLineWidth(600)
    glyphs.endLayout()
    assert glyphs.glyphRuns() and all(0 not in run.glyphIndexes() for run in glyphs.glyphRuns()),code
    assert w.annotation_tool.buttons[0].text()==str(tr('选词 / 阅读'))+'  1'
    assert w.merge_export_button.text()==str(tr('合并导出词本 · 多文件'))
    assert w.record==before and w.page_no==position
    assert w.lib.state['dictionary_overrides']==before_definition
    assert export_body(w.record,mode='chapter')==body_before
    assert '用户内容不随界面语言变化' in w.dictionary.lookup('predator-prey')['entry']['translation']
    settings=ShortcutSettingsDialog(w)
    settings.show()
    merge=MergeExportDialog(w)
    merge.show()
    table=VocabularyExportDialog(w)
    table.show()
    reading=ReadingExportDialog(w)
    reading.show()
    personal=PersonalDefinitionDialog(w,'predator-prey')
    personal.show()
    assert table.table.horizontalHeaderItem(0).text()==str(tr('英文单词 / 词组'))
    assert CONTACT in str(statement_html()) and 'https://www.hnust.edu.cn/' in str(statement_html())
    assert settings.language.currentData()==code
    w.resize(1480,920)
    QTest.qWait(60)
    w.grab().save(str(qa/(code+'-window.png')))
    settings.grab().save(str(qa/(code+'-settings.png')))
    merge.grab().save(str(qa/(code+'-merge.png')))
    for dialog in (personal,reading,table,merge,settings):dialog.close()
    if code in ('en','hi','ar','ja','ko'):
        target=qa/(code+'-table.pdf')
        export_vocabulary_pdf(target,'Language QA',vocabulary_rows(w.record,w.dictionary))
        with fitz.open(target) as doc:
            text=''.join(page.get_text() for page in doc)
            assert 'research' in text and '用户内容不随界面语言变化' in text
            doc[0].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(qa/(code+'-table.png'))

# Real settings Save writes the selection and updates current widgets.
settings=ShortcutSettingsDialog(w)
settings.language.setCurrentIndex(settings.language.findData('fr'))
settings.save()
assert current_language()=='fr'
# A disk failure restores both language and shortcuts and leaves UI as-is.
snapshot=copy.deepcopy(w.lib.state)
save=w.lib.save
w.lib.save=lambda:(_ for _ in ()).throw(OSError('simulated disk failure'))
assert not w.save_preferences(w.tool_shortcuts,'ja')
w.lib.save=save
assert w.lib.state==snapshot and current_language()=='fr' and errors
errors.clear()
try:
    w.save_preferences(w.tool_shortcuts,'unsupported')
    raise AssertionError('Expected invalid language rejection')
except ValueError:pass
assert w.lib.state==snapshot
assert source_hash==hashlib.sha256(w.lib.pdf_path(w.record).read_bytes()).digest()
w.close()
# Broken/unknown saved language falls back safely to English.
library=Library(qa/'fallback')
library.state['language']='unknown'
library.save()
w=MainWindow(qa/'fallback',reopen=False)
assert current_language()=='en'
w.close()
assert not errors
# Transient Windows sharing locks are retried; permanent denial preserves disk.
library=Library(qa/'file-lock')
library.save()
replace=Path.replace
calls=[]
def transient_replace(path,target):
    if path==library.path.with_suffix('.tmp'):
        calls.append(path)
        if len(calls)<3:
            exc=PermissionError('sharing lock')
            exc.winerror=32
            raise exc
    return replace(path,target)
Path.replace=transient_replace
try:
    library.state['language']='ko'
    library.save()
finally:
    Path.replace=replace
assert len(calls)==3 and Library(qa/'file-lock').state['language']=='ko'
disk_hash=hashlib.sha256(library.path.read_bytes()).digest()
def denied_replace(path,target):
    if path==library.path.with_suffix('.tmp'):
        exc=PermissionError('permanent denial')
        exc.winerror=5
        raise exc
    return replace(path,target)
Path.replace=denied_replace
try:
    library.state['language']='ar'
    try:
        library.save()
        raise AssertionError('Expected persistent permission failure')
    except PermissionError:pass
finally:
    Path.replace=replace
assert disk_hash==hashlib.sha256(library.path.read_bytes()).digest()
print('PASS: 12 complete offline catalogs, default English, live switch/persistence/cancel/failure, RTL, dialogs, PDF fonts and unchanged user data:',qa)
