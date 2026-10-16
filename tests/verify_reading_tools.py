"""On-page transparent note editing, dragging, timer, export menu and dictionary cover."""
import copy
import hashlib
import os
import sys
import tempfile
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pymupdf as fitz
from PySide6.QtCore import Qt, QPointF, QEvent
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog
from app import MainWindow,configure_fonts,STYLE
from core import Library
from annotations import note_layout,render_note
qa=Path(tempfile.mkdtemp(prefix='reading-tools-qa-',dir=ROOT/'work'))
source=qa/'source.pdf'
with fitz.open() as doc:
 for rotation in (0,90):
  page=doc.new_page(width=595,height=842)
  page.draw_rect(fitz.Rect(20,100,570,380),color=None,fill=(.7,.85,.95))
  page.insert_text((50,180),'Background text must remain visible.',fontsize=20)
  page.set_rotation(rotation)
 doc.save(source)
source_hash=hashlib.sha256(source.read_bytes()).digest()
app=QApplication([]);configure_fonts(app);app.setStyle('Fusion');app.setStyleSheet(STYLE)
errors=[]
QMessageBox.critical=QMessageBox.warning=lambda *a:errors.append(str(a[2]))
QInputDialog.getMultiLineText=lambda *a: (_ for _ in ()).throw(AssertionError('No modal note editor'))
w=MainWindow(qa/'data',reopen=False,language='zh-CN');w.show();w.import_file(str(source));QTest.qWait(80)
w.annotation_tool.setCurrentIndex(w.annotation_tool.findData('note'))
canvas=w.canvas
QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=canvas.screen_point((100,150)).toPoint())
assert canvas.note_editor is not None and not w.record.get('annotations')
canvas.note_editor.text.setPlainText('中文透明备注\nTRANSPARENT_NOTE')
w.grab().save(str(qa/'inline-editor.png'))
QTest.keyClick(canvas.note_editor.text,Qt.Key.Key_Return,Qt.KeyboardModifier.ControlModifier)
assert canvas.note_editor is None
note=copy.deepcopy(w.record['annotations'][0]);assert 'TRANSPARENT_NOTE' in note['text']
rect,pix=render_note(note,canvas.page_bounds,1.5)
assert pix.alpha and min(pix.samples[3::4])==0 and max(pix.samples[3::4])>0
canvas.grab().save(str(qa/'transparent-canvas.png'))
# Existing note dragging commits once and undo/redo restores positions.
w.annotation_tool.setCurrentIndex(0)
start=canvas.screen_point((rect.x0+15,rect.y0+12)).toPoint()
end=start+canvas.screen_point((70,60)).toPoint()-canvas.screen_point((0,0)).toPoint()
QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=start)
move=QMouseEvent(QEvent.Type.MouseMove,QPointF(end),QPointF(canvas.mapToGlobal(end)),Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
app.sendEvent(canvas,move)
assert w.record['annotations'][0]==note
QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=end)
moved=copy.deepcopy(w.record['annotations'][0]);assert moved['rect'][0]>note['rect'][0]+60
canvas.setFocus();w.undo_annotation();assert w.record['annotations'][0]==note
w.redo_annotation();assert w.record['annotations'][0]==moved
# Double-click edits inline; Escape discards edits, not the existing note.
rect,_=note_layout(moved,canvas.page_bounds)
QTest.mouseDClick(canvas,Qt.MouseButton.LeftButton,pos=canvas.screen_point((rect.x0+15,rect.y0+12)).toPoint())
assert canvas.note_editor
canvas.note_editor.text.setPlainText('DISCARDED')
QTest.keyClick(canvas.note_editor.text,Qt.Key.Key_Escape)
assert canvas.note_editor is None and w.record['annotations'][0]==moved
# Editor handle moves a new note, then saving and export keep it transparent.
w.annotation_action(0,{'edit':moved['id']})
editor=canvas.note_editor
pos=editor.pos()
QTest.mousePress(editor.handle,Qt.MouseButton.LeftButton)
QTest.mouseMove(editor.handle,editor.handle.rect().center()+canvas.screen_point((30,20)).toPoint(),5)
QTest.mouseRelease(editor.handle,Qt.MouseButton.LeftButton)
canvas.finish_note()
# Rotate and move a second note. Coordinates stay in unrotated PDF space.
w.go_page(1);canvas=w.canvas
w.annotation_action(1,{'type':'note','rect':[100,150,118,168],'color':'#4799de','width':2})
canvas.note_editor.text.setPlainText('ROTATED_NOTE 中文')
canvas.finish_note()
rotated=w.record['annotations'][-1]
rect,_=note_layout(rotated,canvas.page_bounds)
start=canvas.screen_point(rect.tl+fitz.Point(15,12)).toPoint();end=start+canvas.screen_point((30,20)).toPoint()-canvas.screen_point((0,0)).toPoint()
QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=start);QTest.mouseMove(canvas,end,10);QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=end)
assert fitz.Rect(w.record['annotations'][-1]['rect']).x0>rect.x0+20
w.write_highlight_pdf(qa/'notes.pdf')
with fitz.open(qa/'notes.pdf') as doc:
 for i in range(2):
  page=doc[i];annot=next(page.annots())
  assert annot.type[0]==fitz.PDF_ANNOT_FREE_TEXT and not annot.colors['fill']
  assert 'NOTE' in annot.get_text()
  page.get_pixmap().save(qa/f'export-{i}.png')
# Stopwatch is monotonic, pauses without advancing, resets, restores paused.
timer=w.reading_timer;timer.toggle();QTest.qWait(1100);timer.toggle()
assert timer.milliseconds()>=1000 and not timer.clock.isValid()
paused=timer.milliseconds();QTest.qWait(240);assert timer.milliseconds()==paused
assert Library(qa/'data').state['reading_timer_seconds']>=1
timer.reset();assert timer.milliseconds()==0 and timer.label.text()=='00:00:00'
timer.total_ms=3723000;timer.refresh();assert timer.label.text()=='01:02:03'
# Cover cannot reveal by selection/scrolling, resets for every lookup, persists.
w.hide_definition.setChecked(True);w.lookup_term('research')
assert w.dictionary_stack.currentWidget() is w.definition_cover and not w.dictionary_view.isVisible()
w.reveal_current_definition();assert w.dictionary_stack.currentWidget() is w.dictionary_view
w.lookup_term('word');assert w.dictionary_stack.currentWidget() is w.definition_cover
w.grab().save(str(qa/'window-cover.png'))
# All six existing exports live behind a single visible button, translated live.
w.prepare_export_menu();assert len(w.export_actions)==6 and w.reading_button.isEnabled()
assert w.export_button.isVisible() and w.merge_export_button in w.export_menu.actions()
w.export_menu.popup(w.export_button.mapToGlobal(w.export_button.rect().topLeft()));QTest.qWait(30)
w.export_menu.grab().save(str(qa/'export-menu.png'));w.export_menu.close()
# Failed saves keep the inline editor and block document switches/closing.
w.annotation_action(1,{'edit':w.record['annotations'][-1]['id']})
w.canvas.note_editor.text.setPlainText('RETRY_AFTER_SAVE_FAILURE')
before_failure=copy.deepcopy(w.record['annotations'])
real_persist=w.persist
w.persist=lambda:False
assert not w.finish_notes() and w.canvas.note_editor is not None
assert w.record['annotations']==before_failure
w.close();assert w.isVisible() and w.canvas.note_editor is not None
w.persist=real_persist
assert w.finish_notes() and w.record['annotations'][-1]['text']=='RETRY_AFTER_SAVE_FAILURE'
# Switching documents saves pending text to the original document only.
w.annotation_action(1,{'edit':w.record['annotations'][-1]['id']})
w.canvas.note_editor.text.setPlainText('AUTOSAVE_ON_SWITCH')
other=qa/'other.pdf'
with fitz.open() as doc:doc.new_page();doc.save(other)
first=w.record
w.import_file(str(other))
assert first['annotations'][-1]['text']=='AUTOSAVE_ON_SWITCH' and not w.record.get('annotations')
w.close()
w=MainWindow(qa/'data',reopen=False,language='zh-CN');w.show()
assert w.hide_definition.isChecked() and w.dictionary_stack.currentWidget() is w.definition_cover
assert w.reading_timer.label.text()=='01:02:03' and not w.reading_timer.clock.isValid()
w.close()
assert not errors,errors
assert hashlib.sha256(source.read_bytes()).digest()==source_hash
print('PASS: inline edit/save/cancel/autosave, transparent screen and native PDF notes, dragging/undo/rotation, monotonic persistent timer, six exports, persistent reveal-and-remask dictionary cover.')
print('Visual QA:',qa)
