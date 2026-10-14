import os
import sys
import copy
import multiprocessing
import queue
import uuid
from datetime import datetime
from pathlib import Path

import pymupdf as fitz
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QTimer, QThread, QLockFile, QEvent, QEventLoop
from PySide6.QtGui import QColor, QPainter, QImage, QPixmap, QFont, QFontDatabase, QShortcut, QKeySequence, QIcon, QMouseEvent, QPen, QPainterPath, QKeyEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QLineEdit, QScrollArea, QSplitter,
    QSpinBox, QComboBox, QCheckBox, QFileDialog, QInputDialog, QMessageBox, QDialog,
    QPlainTextEdit, QAbstractItemView, QTextBrowser, QProgressDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QAbstractSpinBox, QKeySequenceEdit, QSizePolicy)

from core import Library, clean_term, validate_term, export_body
from branding import APP_NAME, PROJECT_NAME, VERIFY_ENV
from dictionary import OfflineDictionary, render_lookup
from reading_export import export_reading_pdf, reading_export_process, page_numbers
from vocabulary_export import vocabulary_rows, export_vocabulary_pdf
from annotations import (COLLECTED_COLOR, KINDS, ink_rgba, annotation_at,
                         export_annotated_pdf)
from tool_settings import (AnnotationToolBar, ShortcutSettingsDialog, TOOLS, PORTABLE,
                           load_shortcuts, validated_shortcuts)

APP_ROOT = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
ASSETS = Path(getattr(sys, '_MEIPASS', APP_ROOT))
TESSDATA = ASSETS / 'tessdata'
if not TESSDATA.exists():
    TESSDATA = APP_ROOT / 'tessdata'

STYLE = '''
QMainWindow, QDialog { background: #f5f7f8; }
QWidget { font-family: "Microsoft YaHei UI"; font-size: 13px; color: #233a41; }
QPushButton { background: #ffffff; border: 1px solid #d5e0e3; border-radius: 7px; padding: 8px 12px; }
QPushButton:hover { background: #e9f4f2; border-color: #9fc9c0; }
QPushButton:pressed { background: #d4ebe5; }
QPushButton:disabled { color: #a5b2b6; background: #f0f3f4; }
QPushButton#annotationTool { padding: 7px 9px; }
QPushButton#annotationTool:checked { color: white; background: #087f73; border-color: #087f73; font-weight: 600; }
QPushButton#primary { background: #087f73; color: white; border: none; font-weight: 600; }
QPushButton#primary:hover { background: #066a60; }
QLineEdit, QSpinBox, QComboBox, QPlainTextEdit { background: white; border: 1px solid #d5e0e3; border-radius: 6px; padding: 7px; selection-background-color: #087f73; }
QListWidget { background: white; border: 1px solid #e1e8ea; border-radius: 8px; padding: 4px; outline: none; }
QTextBrowser { background: white; border: 1px solid #e1e8ea; border-radius: 8px; padding: 7px; }
QListWidget::item { border-radius: 5px; padding: 9px 6px; }
QListWidget::item:selected { background: #e0f2ee; color: #076b60; }
QListWidget::item:hover { background: #f0f6f5; }
QLabel#muted { color: #758990; font-size: 12px; }
QLabel#title { font-size: 24px; font-weight: 700; color: #087f73; }
QScrollArea { border: none; background: #e5ebee; }
QSplitter::handle { background: #edf1f3; width: 5px; }
QStatusBar { background: white; color: #60767d; }
'''


def configure_fonts(app):
    # Explicitly register Windows fonts, also works in headless rendering tests.
    for font in ('msyh.ttc', 'msyhbd.ttc', 'consola.ttf'):
        path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / font
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
    app.setFont(QFont('Microsoft YaHei', 10))


def button(text, callback, primary=False):
    b = QPushButton(text)
    if primary:
        b.setObjectName('primary')
    b.clicked.connect(callback)
    return b


def muted(text):
    w = QLabel(text)
    w.setObjectName('muted')
    w.setWordWrap(True)
    return w


class PDFCanvas(QWidget):
    selected = Signal(str)
    word_toggled = Signal(int)
    annotation_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.image = QPixmap()
        self.words = []
        self.scale = 1.0
        self.rotation = fitz.Identity
        self.marks = []
        self.annotations = []
        self.tool, self.color, self.pen_width = 'select', '#f4c542', 2
        self.draft = None
        self.ink_cache = {}
        self.selection = []
        self.anchor = None
        self.dragging = False
        self.page_no = 0
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def set_page(self, page, words, scale, marks):
        self.scale, self.rotation = scale, page.rotation_matrix
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        self.image = QPixmap.fromImage(QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy())
        self.words, self.marks = words, marks
        self.ink_cache.clear()
        self.selection, self.anchor = [], None
        self.setFixedSize(pix.width, pix.height)
        self.update()

    def screen_rect(self, rect):
        r = fitz.Rect(rect) * self.rotation
        return QRectF(r.x0 * self.scale, r.y0 * self.scale, r.width * self.scale, r.height * self.scale)

    def paintEvent(self, event):
        p = QPainter(self)
        if self.image.isNull():
            p.fillRect(self.rect(), Qt.GlobalColor.white)
            p.setPen(QColor('#758990'))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f'第 {self.page_no + 1} 页 · 正在加载')
            return
        p.drawPixmap(0, 0, self.image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Reuse original glyph shapes instead of substituting a different font.
        for m in self.marks:
            for rect in m['rects']:
                target = self.screen_rect(rect)
                key = tuple(rect)
                if key not in self.ink_cache:
                    bounds = target.toAlignedRect().intersected(self.image.rect())
                    image = self.image.copy(bounds).toImage().convertToFormat(QImage.Format.Format_RGB888)
                    if image.width() and image.height():
                        rgba = ink_rgba(bytes(image.bits()), image.width(), image.height(), image.bytesPerLine())
                        overlay = QImage(rgba, image.width(), image.height(), image.width() * 4,
                                         QImage.Format.Format_RGBA8888_Premultiplied).copy()
                        self.ink_cache[key] = (bounds, QPixmap.fromImage(overlay))
                if key in self.ink_cache:
                    bounds, overlay = self.ink_cache[key]
                    for dx, dy in ((-.25, 0), (.25, 0), (0, -.15), (0, .15)):
                        p.drawPixmap(QPointF(bounds.x() + dx * self.scale,
                                            bounds.y() + dy * self.scale), overlay)
                # Follow the PDF baseline, including on rotated pages.
                r = fitz.Rect(rect)
                p.setPen(QPen(QColor(COLLECTED_COLOR), max(1.5, 1.5 * self.scale)))
                p.drawLine(self.screen_point(r.bl), self.screen_point(r.br))
        for item in self.annotations + ([self.draft] if self.draft else []):
            self.paint_annotation(p, item)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 135, 122, 85))
        for i in self.selection:
            p.drawRect(self.screen_rect(self.words[i][:4]))

    def screen_point(self, point):
        q = fitz.Point(point) * self.rotation
        return QPointF(q.x * self.scale, q.y * self.scale)

    def pdf_point(self, point):
        q = fitz.Point(max(0, min(self.width(), point.x())) / self.scale,
                       max(0, min(self.height(), point.y())) / self.scale) * ~self.rotation
        return [q.x, q.y]

    def set_tool(self, tool, color, width):
        self.tool, self.color, self.pen_width = tool, color, width
        self.cancel_draft()
        self.setCursor(Qt.CursorShape.IBeamCursor if tool in ('select', 'highlight', 'underline')
                       else Qt.CursorShape.CrossCursor)

    def cancel_draft(self):
        self.draft, self.dragging, self.anchor = None, False, None
        self.selection = []
        self.update()

    def paint_annotation(self, p, item):
        p.save()
        p.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(QColor(item['color']), max(1, item['width'] * self.scale))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        kind = item['type']
        if kind == 'highlight':
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
            color = QColor(item['color'])
            color.setAlpha(90)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            for rect in item['rects']:
                p.drawRect(self.screen_rect(rect))
        elif kind == 'underline':
            for rect in item['rects']:
                r = fitz.Rect(rect)
                p.drawLine(self.screen_point(r.bl), self.screen_point(r.br))
        elif kind == 'ink':
            points = item['points']
            if len(points) == 1:
                p.drawPoint(self.screen_point(points[0]))
            elif points:
                path = QPainterPath(self.screen_point(points[0]))
                for point in points[1:]:
                    path.lineTo(self.screen_point(point))
                p.drawPath(path)
        elif kind == 'rect':
            p.drawRect(self.screen_rect(item['rect']))
        elif kind == 'note':
            r = self.screen_rect(item['rect'])
            p.setBrush(QColor(item['color']))
            p.drawRoundedRect(r, 3, 3)
            p.setPen(QColor('#233a41'))
            p.setFont(QFont('Microsoft YaHei', max(7, int(9 * self.scale))))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, '✎')
        p.restore()

    def hit(self, point):
        for i, word in enumerate(self.words):
            if self.screen_rect(word[:4]).adjusted(-2, -2, 2, 2).contains(point):
                return i
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            point = self.pdf_point(event.position())
            if self.tool == 'erase':
                self.annotation_requested.emit({'erase': point})
                return
            if self.tool == 'note':
                found = annotation_at([a for a in self.annotations if a['type'] == 'note'], point)
                self.annotation_requested.emit({'edit': found['id']} if found else
                    {'type': 'note', 'rect': [point[0], point[1], point[0] + 18, point[1] + 18],
                     'color': self.color, 'width': self.pen_width})
                return
            if self.tool in ('ink', 'rect'):
                self.dragging = True
                self.draft = {'type': self.tool, 'color': self.color, 'width': self.pen_width,
                              'points': [point], 'rect': [*point, *point]}
                return
            self.anchor = self.hit(event.position())
            self.dragging = self.anchor is not None
            self.selection = [self.anchor] if self.dragging else []
            if self.tool == 'select':
                self.selected.emit(self.selection_text())
            self.update()

    def mouseMoveEvent(self, event):
        if not self.dragging:
            found = annotation_at(self.annotations, self.pdf_point(event.position()))
            self.setToolTip(found.get('text', '') if found else '')
            return
        if self.draft:
            point = self.pdf_point(event.position())
            if self.tool == 'ink':
                last = self.draft['points'][-1]
                if abs(last[0] - point[0]) + abs(last[1] - point[1]) >= .5:
                    self.draft['points'].append(point)
            elif self.tool == 'rect':
                a = self.draft['points'][0]
                self.draft['rect'] = [min(a[0], point[0]), min(a[1], point[1]),
                                      max(a[0], point[0]), max(a[1], point[1])]
            self.update()
            return
        end = self.hit(event.position())
        if end is not None:
            self.selection = list(range(min(self.anchor, end), max(self.anchor, end) + 1))
            if self.tool == 'select':
                self.selected.emit(self.selection_text())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self.dragging:
            return
        self.mouseMoveEvent(event)
        self.dragging = False
        if self.draft:
            item, self.draft = self.draft, None
            if item['type'] != 'rect' or (fitz.Rect(item['rect']).width > 2 and fitz.Rect(item['rect']).height > 2):
                self.annotation_requested.emit(item)
        elif self.tool in ('highlight', 'underline') and self.selection:
            self.annotation_requested.emit({'type': self.tool, 'color': self.color, 'width': self.pen_width,
                'rects': [list(self.words[i][:4]) for i in self.selection], 'text': self.selection_text()})
            self.selection = []
        self.update()

    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self.tool != 'select':
            event.accept()
            return
        self.setFocus()
        note = annotation_at([a for a in self.annotations if a['type'] == 'note'],
                             self.pdf_point(event.position()))
        if note:
            self.annotation_requested.emit({'edit': note['id']})
            return
        self.dragging = False
        self.anchor = None
        index = self.hit(event.position())
        if index is not None:
            self.word_toggled.emit(index)
        event.accept()

    def selection_text(self):
        text, last_line = '', None
        for i in self.selection:
            w = self.words[i]
            line = tuple(w[5:7])
            if text:
                text += '\n' if last_line != line else ' '
            text += w[4]
            last_line = line
        return clean_term(text)


class PDFDocumentView(QWidget):
    """Continuous page geometry with a bounded cache of nearby page canvases."""
    selected = Signal(int, str)
    word_toggled = Signal(int, int)
    active_changed = Signal(int)
    annotation_requested = Signal(int, object)

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.sizes, self.boxes, self.canvases = [], [], {}
        self.columns, self.scale, self.active = 1, 1.0, 0
        self.signature = None
        self.busy = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh_visible)

    def clear(self):
        self.timer.stop()
        for canvas in self.canvases.values():
            canvas.hide()
            canvas.deleteLater()
        self.canvases.clear()
        self.sizes, self.boxes = [], []
        self.signature = None

    def attach(self):
        self.clear()
        self.sizes = [(page.rect.width, page.rect.height) for page in self.owner.doc]
        self.active = self.owner.page_no

    def layout_pages(self, columns, width, scale=None):
        if not self.sizes:
            return
        row_width = max(sum(w for w, h in self.sizes[i:i + columns])
                        for i in range(0, len(self.sizes), columns))
        if scale is None:
            scale = min(3.0, max(.15, (width - 32 - 16 * (columns - 1)) / row_width))
        signature = (columns, round(scale, 5))
        if self.signature == signature:
            return
        self.busy = True
        self.columns, self.scale = columns, scale
        self.signature = signature
        for canvas in self.canvases.values():
            canvas.hide()
            canvas.deleteLater()
        self.canvases.clear()
        self.boxes = []
        content_width = int(row_width * scale) + 32 + 16 * (columns - 1)
        y = 36
        for first in range(0, len(self.sizes), columns):
            row = self.sizes[first:first + columns]
            widths = [int(w * scale + .999) for w, h in row]
            heights = [int(h * scale + .999) for w, h in row]
            x = (content_width - sum(widths) - 16 * (len(row) - 1)) // 2
            for pw, ph in zip(widths, heights):
                self.boxes.append(QRectF(x, y, pw, ph))
                x += pw + 16
            y += max(heights) + 40
        self.setFixedSize(content_width, y - 16)
        self.busy = False
        self.update()

    def page_canvas(self, number):
        if number not in self.canvases:
            canvas = PDFCanvas()
            canvas.setParent(self)
            canvas.page_no = number
            canvas.setGeometry(self.boxes[number].toRect())
            canvas.selected.connect(lambda text, n=number: self.selected.emit(n, text))
            canvas.word_toggled.connect(lambda index, n=number: self.word_toggled.emit(n, index))
            canvas.annotation_requested.connect(lambda item, n=number: self.annotation_requested.emit(n, item))
            canvas.set_tool(self.owner.annotation_tool.currentData(), self.owner.annotation_color.currentData(),
                            self.owner.annotation_width.value())
            shortcut = QShortcut(QKeySequence('Return'), canvas, self.owner.add_mark)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            canvas.show()
            self.canvases[number] = canvas
        canvas = self.canvases[number]
        if canvas.image.isNull():
            page = self.owner.doc[number]
            marks = [m for m in self.owner.record['marks'] if m['page'] == number]
            canvas.set_page(page, self.owner.words_for_page(number), self.scale, marks)
            canvas.annotations = [a for a in self.owner.record.get('annotations', []) if a['page'] == number]
        return canvas

    def refresh_visible(self):
        if not self.boxes or not self.owner.doc or self.busy:
            return
        scroll = self.owner.scroll
        visible = QRectF(scroll.horizontalScrollBar().value(), scroll.verticalScrollBar().value(),
                         scroll.viewport().width(), scroll.viewport().height())
        nearby = visible.adjusted(0, -350, 0, 350)
        wanted = {n for n, box in enumerate(self.boxes) if box.intersects(nearby)}
        areas = [(n, box.intersected(visible).width() * box.intersected(visible).height())
                 for n, box in enumerate(self.boxes) if box.intersects(visible)]
        if areas:
            best, area = max(areas, key=lambda item: item[1])
            current = next((v for n, v in areas if n == self.active), 0)
            selected = self.canvases.get(self.active)
            keep_selection = selected is not None and selected.selection and current > 0
            if not keep_selection and current < area * .85:
                self.active_changed.emit(best)
        wanted.add(self.active)
        for n in sorted(wanted):
            self.page_canvas(n)
        for n in list(self.canvases):
            if n not in wanted:
                canvas = self.canvases.pop(n)
                canvas.hide()
                canvas.deleteLater()

    def schedule_visible(self):
        # Coalesce resize/scroll bursts without postponing cache eviction on
        # every event during window resizing.
        if not self.busy and not self.timer.isActive():
            self.timer.start(25)

    def update_marks(self):
        for n, canvas in self.canvases.items():
            canvas.marks = [m for m in self.owner.record['marks'] if m['page'] == n]
            canvas.annotations = [a for a in self.owner.record.get('annotations', []) if a['page'] == n]
            used = {tuple(r) for m in canvas.marks for r in m['rects']}
            canvas.ink_cache = {k: v for k, v in canvas.ink_cache.items() if k in used}
            canvas.update()

    def ensure_rect(self, number, rect):
        box = self.boxes[number]
        self.owner.scroll.ensureVisible(int(box.x() + rect.center().x()),
                                        int(box.y() + rect.center().y()), 80, 120)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#e5ebee'))
        p.setPen(QColor('#60767d'))
        for n, box in enumerate(self.boxes):
            if box.adjusted(0, -24, 0, 0).intersects(QRectF(event.rect())):
                p.drawText(QRectF(box.x(), box.y() - 24, box.width(), 20),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f'第 {n + 1} 页')


class AnnotationDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle('管理论文批注')
        self.resize(600, 460)
        layout = QVBoxLayout(self)
        layout.addWidget(muted('双击定位批注；文字备注可编辑。删除批注可以撤销。'))
        self.items = QListWidget()
        self.items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.items)
        row = QHBoxLayout()
        row.addWidget(button('定位', self.locate))
        row.addWidget(button('编辑备注', self.edit))
        row.addWidget(button('删除所选', self.delete))
        row.addWidget(button('关闭', self.accept))
        layout.addLayout(row)
        self.items.itemDoubleClicked.connect(lambda _: self.locate())
        self.refresh()

    def refresh(self):
        self.items.clear()
        for annotation in sorted(self.owner.record.get('annotations', []), key=lambda a: (a['page'], a['created'])):
            text = annotation.get('text', '').replace('\n', ' ')[:120]
            item = QListWidgetItem(f"第 {annotation['page'] + 1} 页 · {KINDS[annotation['type']]}  {text}")
            item.setData(Qt.ItemDataRole.UserRole, annotation['id'])
            item.setToolTip(annotation.get('text', ''))
            self.items.addItem(item)

    def current(self):
        item = self.items.currentItem()
        return next((a for a in self.owner.record.get('annotations', [])
                     if item and a['id'] == item.data(Qt.ItemDataRole.UserRole)), None)

    def locate(self):
        item = self.current()
        if item:
            self.owner.go_page(item['page'])
            if item['type'] == 'ink':
                pt = item['points'][0]
                rect = [pt[0], pt[1], pt[0] + 1, pt[1] + 1]
            else:
                rect = item.get('rect') or item['rects'][0]
            self.owner.reader.ensure_rect(item['page'], self.owner.canvas.screen_rect(rect))

    def edit(self):
        item = self.current()
        if item and item['type'] == 'note':
            self.owner.annotation_action(item['page'], {'edit': item['id']})
            self.refresh()
        else:
            QMessageBox.information(self, '编辑备注', '请选择一条文字备注。')

    def delete(self):
        ids = {i.data(Qt.ItemDataRole.UserRole) for i in self.items.selectedItems()}
        if ids:
            self.owner.commit_annotations([a for a in self.owner.record.get('annotations', []) if a['id'] not in ids])
            self.refresh()


class OCRWorker(QThread):
    ready = Signal(object, str)

    def __init__(self, path, page, password):
        super().__init__()
        self.path, self.page, self.password = path, page, password

    def run(self):
        try:
            with fitz.open(self.path) as doc:
                if doc.needs_pass and not doc.authenticate(self.password):
                    raise ValueError('PDF 密码无效')
                page = doc[self.page]
                tp = page.get_textpage_ocr(language='eng', dpi=200, full=True, tessdata=str(TESSDATA))
                self.ready.emit(page.get_text('words', textpage=tp), '')
        except Exception as exc:
            self.ready.emit([], str(exc))


class ExportDialog(QDialog):
    def __init__(self, parent, record):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle('导出云词本 · 正文')
        self.resize(690, 680)
        layout = QVBoxLayout(self)
        title = QLabel('让今天读到的词，成为明天记住的词')
        title.setStyleSheet('font-size: 19px; font-weight: 600; padding: 8px 0;')
        layout.addWidget(title)
        self.mode = QComboBox()
        for text, value in [('章节模式 · 保留完整词组（推荐）', 'chapter'), ('按 PDF 页码分章节 · 保留完整词组', 'pages'),
                            ('普通模式 · 由墨墨背单词提取单词和短语', 'plain'), ('原型模式 // · 由墨墨背单词还原单词原型', 'lemma')]:
            self.mode.addItem(text, value)
        layout.addWidget(self.mode)
        options = QHBoxLayout()
        self.dedupe = QCheckBox('合并重复词条')
        self.dedupe.setChecked(True)
        self.lower = QCheckBox('全部转为小写')
        options.addWidget(self.dedupe)
        options.addWidget(self.lower)
        options.addStretch()
        layout.addLayout(options)
        self.note = muted('')
        layout.addWidget(self.note)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont('Consolas', 13))
        layout.addWidget(self.preview, 1)
        self.count = muted('')
        layout.addWidget(self.count)
        row = QHBoxLayout()
        row.addWidget(button('复制正文', self.copy))
        row.addWidget(button('保存 TXT', self.save, True))
        row.addWidget(button('关闭', self.accept))
        layout.addLayout(row)
        layout.addWidget(muted('把正文粘贴到墨墨背单词的云词本正文输入框。TXT 不包含翻译、编号或页码说明。'))
        for signal in (self.mode.currentIndexChanged, self.dedupe.toggled, self.lower.toggled):
            signal.connect(self.refresh)
        self.refresh()

    def refresh(self):
        body = export_body(self.record, self.mode.currentData(), self.lower.isChecked(), self.dedupe.isChecked())
        self.preview.setPlainText(body)
        n = sum(bool(line) and not line.startswith(('#', '//')) for line in body.splitlines())
        self.count.setText(f'{n} 个词条 · UTF-8 文本 · 按 PDF 阅读位置排序')
        self.note.setText('章节模式：每行一个词条，词组不拆分，保留大小写。' if self.mode.currentData() in ('chapter', 'pages')
                          else '此模式会由墨墨背单词提取短语中的单词，且不区分首字母大小写。原型还原由墨墨背单词完成。')

    def copy(self):
        QApplication.clipboard().setText(self.preview.toPlainText())
        self.count.setText('已复制，可以粘贴到墨墨背单词云词本。')

    def save(self):
        path, _ = QFileDialog.getSaveFileName(self, '保存云词本正文', str(APP_ROOT / 'exports' / (safe_name(self.record['title']) + '_云词本.txt')), '文本文件 (*.txt)')
        if path:
            try:
                Path(path).write_text(self.preview.toPlainText(), encoding='utf-8')
                self.count.setText('已保存：' + path)
            except OSError as exc:
                QMessageBox.critical(self, '保存失败', str(exc))


def safe_name(title):
    return ''.join('_' if c in '<>:"/\\|?*' else c for c in title).strip(' .')[:120] or '词本'


class VocabularyExportDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.record = copy.deepcopy(owner.record)
        self.selected_ids = {item.data(Qt.ItemDataRole.UserRole) for item in owner.mark_list.selectedItems()}
        self.edits = {}
        self.setWindowTitle('导出单词释义表 PDF')
        self.resize(860, 670)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('左列英文词条，右列中文释义 · A4 打印表格'))
        layout.addWidget(muted('释义来自离线词典；双击右列或点击「编辑释义」可调整本次导出的内容。'))
        options = QHBoxLayout()
        self.scope = QComboBox()
        self.scope.addItem('当前 PDF 全部标记', None)
        if self.selected_ids:
            self.scope.addItem(f'仅导出选中的 {len(self.selected_ids)} 条标记', 'selected')
        options.addWidget(self.scope, 1)
        self.dedupe = QCheckBox('合并相同拼写的词条')
        self.dedupe.setChecked(True)
        options.addWidget(self.dedupe)
        layout.addLayout(options)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['英文单词 / 词组', '中文释义'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setWordWrap(True)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 240)
        layout.addWidget(self.table, 1)
        self.count = muted('')
        layout.addWidget(self.count)
        layout.addWidget(muted('保留词组和大小写；未收录词组会明确标注逐词释义。这里的修改不会改变 PDF 标记或词典。'))
        row = QHBoxLayout()
        row.addWidget(button('编辑释义', self.edit_meaning))
        row.addWidget(button('恢复词典释义', self.restore_meaning))
        row.addStretch()
        row.addWidget(button('关闭', self.reject))
        row.addWidget(button('导出 PDF', self.save, True))
        layout.addLayout(row)
        self.scope.currentIndexChanged.connect(self.refresh)
        self.dedupe.toggled.connect(self.refresh)
        self.table.itemDoubleClicked.connect(lambda item: self.edit_meaning() if item.column() == 1 else None)
        self.refresh()

    def refresh(self):
        ids = self.selected_ids if self.scope.currentData() == 'selected' else None
        self.rows = vocabulary_rows(self.record, self.owner.dictionary, self.dedupe.isChecked(), ids)
        self.table.setRowCount(len(self.rows))
        for row, (term, meaning) in enumerate(self.rows):
            meaning = self.edits.get(term, meaning)
            for column, text in enumerate((term, meaning)):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, item)
        self.table.resizeRowsToContents()
        # Long definitions can be edited in full without occupying the entire
        # preview; PDF pagination preserves their complete text.
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, min(160, max(44, self.table.rowHeight(row))))
        self.count.setText(f'{len(self.rows)} 个词条 · 释义自动换行，表头在每页重复')

    def edit_meaning(self):
        row = self.table.currentRow()
        if row < 0:
            self.count.setText('请先选择一个词条。')
            return
        term = self.table.item(row, 0).text()
        meaning, ok = QInputDialog.getMultiLineText(self, '编辑本次导出的释义', term,
                                                  self.table.item(row, 1).text())
        if ok:
            self.edits[term] = meaning
            self.refresh()
            self.table.selectRow(row)

    def restore_meaning(self):
        row = self.table.currentRow()
        if row >= 0:
            self.edits.pop(self.table.item(row, 0).text(), None)
            self.refresh()
            self.table.selectRow(row)

    def export_rows(self):
        return [(self.table.item(row, 0).text(), self.table.item(row, 1).text())
                for row in range(self.table.rowCount())]

    def save(self):
        (APP_ROOT / 'exports').mkdir(exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(self, '保存单词释义表 PDF',
            str(APP_ROOT / 'exports' / (safe_name(self.record['title']) + '_单词释义表.pdf')), 'PDF (*.pdf)')
        if not path:
            return
        try:
            if Path(path).resolve().is_relative_to(self.owner.lib.root.resolve()):
                raise ValueError('请选择文档数据目录以外的位置，不能覆盖原 PDF。')
            # The source PDF is stored as a local copy; protect identical
            # original files selected outside the data folder as well.
            if Path(path).exists():
                import hashlib
                with open(path, 'rb') as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() == self.record['id']:
                        raise ValueError('该文件是原 PDF，请使用新的文件名保存。')
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                result = export_vocabulary_pdf(path, self.record['title'], self.export_rows())
            finally:
                QApplication.restoreOverrideCursor()
            self.count.setText(f"已保存：{result['terms']} 个词条，{result['pages']} 页 · {path}")
            self.owner.statusBar().showMessage('已导出单词释义表：' + path, 12000)
        except Exception as exc:
            QMessageBox.critical(self, '表格导出失败', str(exc))


class ReadingExportWorker(QThread):
    progress = Signal(int, int, str)
    ready = Signal(object, str)

    def __init__(self, source, destination, options, parent=None):
        super().__init__(parent)
        self.source, self.destination, self.options = source, destination, options

    def run(self):
        messages = None
        process = None
        try:
            context = multiprocessing.get_context('spawn')
            stop_event, messages = context.Event(), context.Queue()
            process = context.Process(target=reading_export_process,
                args=(self.source, self.destination, self.options, stop_event, messages), daemon=True)
            process.start()
            while True:
                if self.isInterruptionRequested():
                    stop_event.set()
                try:
                    message = messages.get(timeout=.1)
                except queue.Empty:
                    if not process.is_alive():
                        raise RuntimeError('导出进程意外结束，请保留原 PDF 后重试。')
                    continue
                if message[0] == 'progress':
                    self.progress.emit(*message[1:])
                else:
                    process.join()
                    self.ready.emit(message[1], message[2])
                    break
        except Exception as exc:
            self.ready.emit(None, str(exc))
        finally:
            if messages:
                messages.close()
            if process and process.pid:
                process.join()
                process.close()


class ReadingExportDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle('导出精读 PDF')
        self.setMinimumWidth(450)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('在文字行之间加入留白，方便打印后手写笔记。'))
        layout.addWidget(muted('保留原文字体与图像，自动分页到 A4，横竖方向随原页调整。'))
        scope_row = QHBoxLayout()
        scope_row.addWidget(QLabel('导出范围'))
        self.scope = QComboBox()
        self.scope.addItems(['全部页', '当前页', '指定页码'])
        scope_row.addWidget(self.scope, 1)
        layout.addLayout(scope_row)
        self.range_edit = QLineEdit()
        self.range_edit.setPlaceholderText(f'例：1-3,5（原 PDF 共 {len(owner.doc)} 页）')
        self.range_edit.setVisible(False)
        self.scope.currentIndexChanged.connect(lambda n: self.range_edit.setVisible(n == 2))
        layout.addWidget(self.range_edit)
        gap_row = QHBoxLayout()
        gap_row.addWidget(QLabel('每行后留白'))
        self.gap = QComboBox()
        self.gap.addItems(['1 行空白', '2 行空白'])
        gap_row.addWidget(self.gap, 1)
        layout.addLayout(gap_row)
        self.highlights = QCheckBox('加入已收录单词的青绿加粗与下划线')
        layout.addWidget(self.highlights)
        layout.addWidget(muted('扫描页会离线识别行位置。复杂表格和图片区域会尽量保持完整；识别不到行时保留原页。'))
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(button('取消', self.reject))
        actions.addWidget(button('选择保存位置', self.accept, True))
        layout.addLayout(actions)

    def selected_pages(self):
        if self.scope.currentIndex() == 0:
            return list(range(len(self.owner.doc)))
        if self.scope.currentIndex() == 1:
            return [self.owner.page_no]
        return page_numbers(self.range_edit.text(), len(self.owner.doc))

    def accept(self):
        try:
            self.selected_pages()
        except ValueError as exc:
            QMessageBox.warning(self, '请检查页码', str(exc))
            return
        super().accept()


class MainWindow(QMainWindow):
    def __init__(self, root=APP_ROOT / 'data', reopen=True):
        super().__init__()
        self.lib = Library(root)
        self.doc = self.record = None
        self.password = ''
        self.page_no = 0
        self.worker = None
        self.reading_worker = None
        self.fit = True
        self.zoom = 1.4
        self.search_cursor = None
        self.annotation_history = {}
        self.tool_shortcuts = load_shortcuts(self.lib.state)
        self.dictionary = OfflineDictionary(APP_ROOT / 'dictionary' / 'ecdict.sqlite')
        self.dictionary_pending = ''
        self.dictionary_timer = QTimer(self)
        self.dictionary_timer.setSingleShot(True)
        self.dictionary_timer.timeout.connect(lambda: self.lookup_term(self.dictionary_pending))
        self.setWindowTitle(APP_NAME + ' · 读一页，记一点')
        self.setMinimumSize(1040, 700)
        self.resize(1480, 920)
        if (ASSETS / 'icon.ico').exists():
            self.setWindowIcon(QIcon(str(ASSETS / 'icon.ico')))
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(16, 14, 16, 8)
        header = QHBoxLayout()
        brand = QLabel(APP_NAME)
        brand.setObjectName('title')
        header.addWidget(brand)
        header.addWidget(muted('XT · 精读与积累'))
        header.addStretch()
        header.addWidget(button('设置', self.shortcut_settings))
        header.addWidget(button('使用帮助', self.help))
        header.addWidget(button('导入 PDF', self.import_dialog, True))
        outer.addLayout(header)
        splitter = QSplitter()
        outer.addWidget(splitter, 1)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 8, 8, 0)
        ll.addWidget(QLabel('我的文档'))
        self.doc_filter = QLineEdit()
        self.doc_filter.setPlaceholderText('搜索文档名')
        ll.addWidget(self.doc_filter)
        self.library_list = QListWidget()
        ll.addWidget(self.library_list, 1)
        left.setMinimumWidth(190)
        lr = QHBoxLayout()
        lr.addWidget(button('重命名', self.rename_doc))
        lr.addWidget(button('移除', self.remove_doc))
        ll.addLayout(lr)
        ll.addWidget(muted('PDF 副本和标记保存在本机。\n原始 PDF 不会被改写。'))
        splitter.addWidget(left)
        center = QWidget()
        cl = QVBoxLayout(center)
        cl.setContentsMargins(4, 8, 4, 0)
        self.doc_title = QLabel('开始一段新的阅读')
        self.doc_title.setStyleSheet('font-size: 17px; font-weight: 600;')
        cl.addWidget(self.doc_title)
        toolbar = QHBoxLayout()
        self.prev = button('‹', lambda: self.go_page(self.page_no - 1))
        self.next = button('›', lambda: self.go_page(self.page_no + 1))
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.setFixedWidth(68)
        self.page_total = QLabel('/ 0')
        toolbar.addWidget(self.prev)
        toolbar.addWidget(self.page_spin)
        toolbar.addWidget(self.page_total)
        toolbar.addWidget(self.next)
        toolbar.addStretch()
        self.layout_box = QComboBox()
        self.layout_box.addItem('单页连续', 1)
        self.layout_box.addItem('双页并排', 2)
        self.layout_box.setToolTip('像 Word 一样连续滚动；双页模式每行并排显示两页。')
        toolbar.addWidget(self.layout_box)
        self.zoom_box = QComboBox()
        self.zoom_box.addItems(['适合宽度', '75%', '100%', '125%', '150%', '200%'])
        toolbar.addWidget(self.zoom_box)
        self.ocr_button = button('识别当前页', self.ocr)
        self.ocr_button.setToolTip('扫描页使用离线英文 OCR；识别完成后请核对词条。')
        toolbar.addWidget(self.ocr_button)
        cl.addLayout(toolbar)
        searchrow = QHBoxLayout()
        self.pdf_search = QLineEdit()
        self.pdf_search.setPlaceholderText('查找 PDF 中的英文（Enter 查找下一个）')
        searchrow.addWidget(self.pdf_search)
        searchrow.addWidget(button('查找', self.search_pdf))
        cl.addLayout(searchrow)
        self.annotation_tool = AnnotationToolBar(self.tool_shortcuts)
        self.annotation_tool.setToolTip('选词模式双击收录；批注模式拖动做记号，备注模式单击添加。Esc 返回选词。')
        self.annotation_strip = QWidget()
        annotation_row = QHBoxLayout(self.annotation_strip)
        annotation_row.setContentsMargins(0, 0, 0, 0)
        annotation_row.setSpacing(5)
        self.annotation_tool.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        annotation_row.addWidget(self.annotation_tool)
        self.annotation_color = QComboBox()
        for label, color in [('金黄', '#f4c542'), ('珊瑚红', '#e87070'), ('湖蓝', '#4799de'),
                              ('紫色', '#a077d8'), ('绿色', '#46a886')]:
            self.annotation_color.addItem(label, color)
            self.annotation_color.setItemData(self.annotation_color.count() - 1, QColor(color), Qt.ItemDataRole.DecorationRole)
        annotation_row.addWidget(self.annotation_color)
        self.annotation_width = QSpinBox()
        self.annotation_width.setRange(1, 8)
        self.annotation_width.setValue(2)
        self.annotation_width.setSuffix(' pt')
        self.annotation_width.setToolTip('画笔、框线、下划线的粗细，随 PDF 缩放')
        annotation_row.addWidget(self.annotation_width)
        self.undo_annotation_button = button('撤销', self.undo_annotation)
        self.redo_annotation_button = button('重做', self.redo_annotation)
        annotation_row.addWidget(self.undo_annotation_button)
        annotation_row.addWidget(self.redo_annotation_button)
        self.manage_annotation_button = button('批注 · 0', self.manage_annotations)
        annotation_row.addWidget(self.manage_annotation_button)
        annotation_row.addStretch()
        self.annotation_navigation = QScrollArea()
        self.annotation_navigation.setObjectName('annotationNavigation')
        self.annotation_navigation.setStyleSheet('QScrollArea#annotationNavigation { background: transparent; border: none; }')
        self.annotation_navigation.setWidgetResizable(True)
        self.annotation_navigation.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.annotation_navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.annotation_navigation.setFixedHeight(54)
        self.annotation_navigation.setWidget(self.annotation_strip)
        cl.addWidget(self.annotation_navigation)
        self.scroll = QScrollArea()
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.reader = PDFDocumentView(self)
        self.canvas = PDFCanvas()
        self.scroll.setWidget(self.reader)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        cl.addWidget(self.scroll, 1)
        self.empty = QLabel('导入英文试卷或论文\n\n单击选择单词，拖动选择词组\n按 Enter 或点击「标记选词」收藏\n\n扫描 PDF 可先点击「识别当前页」')
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setStyleSheet('font-size: 17px; color: #67838a; padding: 50px;')
        cl.addWidget(self.empty, 1)
        self.scroll.hide()
        self.page_hint = muted('标记会自动保存；导出时词组保持在同一行。')
        cl.addWidget(self.page_hint)
        selectedrow = QHBoxLayout()
        self.term_edit = QLineEdit()
        self.term_edit.setPlaceholderText('选词会显示在这里，也可以手动输入或修正')
        selectedrow.addWidget(self.term_edit, 1)
        self.add_button = button('标记选词 Enter', self.add_mark, True)
        selectedrow.addWidget(self.add_button)
        cl.addLayout(selectedrow)
        splitter.addWidget(center)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 8, 0, 0)
        dictionary_title = QLabel('离线英汉词典')
        dictionary_title.setStyleSheet('font-size: 15px; font-weight: 600; color: #087f73;')
        rl.addWidget(dictionary_title)
        dictionary_row = QHBoxLayout()
        self.dictionary_query = QLineEdit()
        self.dictionary_query.setPlaceholderText('单词 / 词组（可手动查词）')
        self.dictionary_query.setMaxLength(240)
        dictionary_row.addWidget(self.dictionary_query, 1)
        dictionary_row.addWidget(button('查词', lambda: self.lookup_term(self.dictionary_query.text())))
        rl.addLayout(dictionary_row)
        self.dictionary_view = QTextBrowser()
        self.dictionary_view.setOpenLinks(False)
        self.dictionary_view.setOpenExternalLinks(False)
        self.dictionary_view.setMinimumHeight(160)
        self.dictionary_view.setMaximumHeight(300)
        self.dictionary_view.setHtml(render_lookup(self.dictionary.lookup('')))
        rl.addWidget(self.dictionary_view, 1)
        self.mark_count = QLabel('本篇词本 · 0')
        self.mark_count.setStyleSheet('font-size: 15px; font-weight: 600;')
        rl.addWidget(self.mark_count)
        self.mark_filter = QLineEdit()
        self.mark_filter.setPlaceholderText('筛选已标记词条')
        rl.addWidget(self.mark_filter)
        self.mark_list = QListWidget()
        self.mark_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        rl.addWidget(self.mark_list, 2)
        right.setMinimumWidth(300)
        row = QHBoxLayout()
        row.addWidget(button('编辑词条', self.edit_mark))
        row.addWidget(button('删除', self.delete_marks))
        rl.addLayout(row)
        rl.addWidget(button('一键导出云词本 TXT', self.quick_export, True))
        rl.addWidget(button('预览 / 复制 / 导出设置', self.export_dialog))
        rl.addWidget(button('导出收录与批注 PDF', self.export_pdf))
        self.vocabulary_button = button('导出单词释义表 PDF', self.export_vocabulary)
        rl.addWidget(self.vocabulary_button)
        self.reading_button = button('导出精读 PDF（留空行）', self.export_reading)
        rl.addWidget(self.reading_button)
        rl.addWidget(muted('双击词条返回所在页。\n导出默认合并同样拼写的词条。'))
        splitter.addWidget(right)
        splitter.setSizes([220, 900, 340])
        splitter.setStretchFactor(1, 1)
        self.statusBar().showMessage('欢迎使用XT 阅迹')
        self.doc_filter.textChanged.connect(self.refresh_library)
        self.library_list.itemClicked.connect(self.library_clicked)
        self.page_spin.valueChanged.connect(lambda v: self.go_page(v - 1))
        self.zoom_box.currentTextChanged.connect(self.change_zoom)
        self.reader.selected.connect(self.page_selected)
        self.reader.word_toggled.connect(self.toggle_word)
        self.reader.active_changed.connect(self.set_active_page)
        self.reader.annotation_requested.connect(self.annotation_action)
        self.annotation_tool.currentIndexChanged.connect(self.change_annotation_tool)
        self.annotation_color.currentIndexChanged.connect(self.change_annotation_tool)
        self.annotation_width.valueChanged.connect(self.change_annotation_tool)
        self.scroll.verticalScrollBar().valueChanged.connect(self.reader.schedule_visible)
        self.scroll.horizontalScrollBar().valueChanged.connect(self.reader.schedule_visible)
        self.layout_box.currentIndexChanged.connect(self.change_layout)
        self.term_edit.returnPressed.connect(self.add_mark)
        self.term_edit.textChanged.connect(self.schedule_lookup)
        self.dictionary_query.returnPressed.connect(lambda: self.lookup_term(self.dictionary_query.text()))
        self.pdf_search.returnPressed.connect(self.search_pdf)
        self.mark_filter.textChanged.connect(self.refresh_marks)
        self.mark_list.itemDoubleClicked.connect(self.jump_mark)
        self.mark_list.itemClicked.connect(lambda item: self.lookup_term(self.get_mark(item)['term']))
        QShortcut(QKeySequence('Ctrl+O'), self, self.import_dialog)
        QShortcut(QKeySequence('Ctrl+E'), self, self.quick_export)
        QShortcut(QKeySequence('Ctrl+F'), self, lambda: self.pdf_search.setFocus())
        QShortcut(QKeySequence('Ctrl+Z'), self, self.undo_annotation)
        QShortcut(QKeySequence('Ctrl+Y'), self, self.redo_annotation)
        QShortcut(QKeySequence('Escape'), self, lambda: self.annotation_tool.setCurrentIndex(0))
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.render_page)
        self.position_timer = QTimer(self)
        self.position_timer.setSingleShot(True)
        self.position_timer.timeout.connect(self.persist)
        self.refresh_library()
        self.refresh_annotation_controls()
        QApplication.instance().installEventFilter(self)
        if self.lib.warning:
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, '词库恢复', self.lib.warning))
        if reopen:
            last = next((d for d in self.lib.state['documents'] if d['id'] == self.lib.state['last']), None)
            if last:
                QTimer.singleShot(0, lambda: self.open_record(last))
        self.setAcceptDrops(True)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            if QApplication.activeWindow() is not self:
                return False
            focus = QApplication.focusWidget()
            while focus is not None and focus is not self:
                if isinstance(focus, (QLineEdit, QPlainTextEdit, QTextEdit)) and not focus.isReadOnly():
                    return False
                if isinstance(focus, (QAbstractSpinBox, QComboBox, QKeySequenceEdit)):
                    return False
                focus = focus.parentWidget()
            # Keypad digits and the main number row share the default mappings.
            modifiers = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
            sequence = QKeySequence(event.key() | modifiers.value).toString(PORTABLE)
            key = next((key for key, shortcut in self.tool_shortcuts.items() if shortcut and shortcut == sequence), None)
            if key:
                event.accept()
                if event.type() == QEvent.Type.KeyPress and not event.isAutoRepeat():
                    self.annotation_tool.setCurrentIndex(self.annotation_tool.findData(key))
                    if self.record:
                        self.canvas.setFocus()
                return True
        return super().eventFilter(watched, event)

    def shortcut_settings(self):
        ShortcutSettingsDialog(self).exec()

    def save_tool_shortcuts(self, values):
        values = validated_shortcuts(values)
        previous = copy.deepcopy(self.lib.state.get('tool_shortcuts'))
        self.lib.state['tool_shortcuts'] = values
        if not self.persist():
            if previous is None:
                self.lib.state.pop('tool_shortcuts', None)
            else:
                self.lib.state['tool_shortcuts'] = previous
            return False
        self.tool_shortcuts = values
        self.annotation_tool.set_shortcuts(values)
        self.statusBar().showMessage('工具快捷键已保存，重新打开软件后仍有效。', 6000)
        return True

    def change_annotation_tool(self):
        for canvas in self.reader.canvases.values():
            canvas.set_tool(self.annotation_tool.currentData(), self.annotation_color.currentData(),
                            self.annotation_width.value())
        self.term_edit.clear()
        self.add_button.setEnabled(self.annotation_tool.currentData() == 'select')
        if self.annotation_tool.currentData() == 'erase':
            self.statusBar().showMessage('单击删除普通批注；已收录词条在选词模式下双击取消。', 7000)

    def refresh_annotation_controls(self):
        history = self.annotation_history.get(self.record['id'], ([], [])) if self.record else ([], [])
        self.undo_annotation_button.setEnabled(bool(history[0]))
        self.redo_annotation_button.setEnabled(bool(history[1]))
        self.manage_annotation_button.setText('批注 · ' + str(len(self.record.get('annotations', [])) if self.record else 0))
        self.manage_annotation_button.setEnabled(self.record is not None)

    def commit_annotations(self, items, history=True):
        before = copy.deepcopy(self.record.get('annotations', []))
        if before == items:
            return False
        self.record['annotations'] = copy.deepcopy(items)
        if not self.persist():
            self.record['annotations'] = before
            return False
        if history:
            undo, redo = self.annotation_history.setdefault(self.record['id'], ([], []))
            undo.append(before)
            del undo[:-100]
            redo.clear()
        self.reader.update_marks()
        self.refresh_annotation_controls()
        return True

    def annotation_action(self, page_no, action):
        if not self.record:
            return
        self.set_active_page(page_no)
        items = copy.deepcopy(self.record.get('annotations', []))
        if 'erase' in action:
            found = annotation_at([a for a in items if a['page'] == page_no], action['erase'],
                                  max(3, 6 / self.reader.scale))
            if found:
                self.commit_annotations([a for a in items if a['id'] != found['id']])
            return
        if 'edit' in action:
            item = next((a for a in items if a['id'] == action['edit']), None)
            if not item or item['type'] != 'note':
                return
        else:
            item = dict(action, page=page_no, id=uuid.uuid4().hex,
                        created=datetime.now().isoformat(timespec='microseconds'))
        if item['type'] == 'note':
            text, ok = QInputDialog.getMultiLineText(self, '文字备注', '写下你的阅读笔记（双击备注可以编辑）',
                                                    item.get('text', ''))
            if not ok or not text.strip():
                return
            item['text'] = text.strip()
            # Keep the note icon fully on-page, even when clicking the edge.
            bounds = self.doc[page_no].cropbox
            x = max(0, min(bounds.width - 18, item['rect'][0]))
            y = max(0, min(bounds.height - 18, item['rect'][1]))
            item['rect'] = [x, y, x + 18, y + 18]
        if 'edit' not in action:
            items.append(item)
        self.commit_annotations(items)

    def undo_annotation(self):
        focus = QApplication.focusWidget()
        if isinstance(focus, (QLineEdit, QPlainTextEdit)):
            focus.undo()
            return
        if not self.record:
            return
        if self.canvas.draft:
            self.canvas.cancel_draft()
            return
        undo, redo = self.annotation_history.setdefault(self.record['id'], ([], []))
        if undo:
            current = copy.deepcopy(self.record.get('annotations', []))
            if self.commit_annotations(undo[-1], history=False):
                undo.pop()
                redo.append(current)
                self.refresh_annotation_controls()

    def redo_annotation(self):
        focus = QApplication.focusWidget()
        if isinstance(focus, (QLineEdit, QPlainTextEdit)):
            focus.redo()
            return
        if not self.record:
            return
        undo, redo = self.annotation_history.setdefault(self.record['id'], ([], []))
        if redo:
            current = copy.deepcopy(self.record.get('annotations', []))
            if self.commit_annotations(redo[-1], history=False):
                redo.pop()
                undo.append(current)
                self.refresh_annotation_controls()

    def manage_annotations(self):
        if self.record:
            AnnotationDialog(self).exec()

    def schedule_lookup(self, text):
        # Clearing the marking input must not erase the definition just read.
        if text.strip():
            self.dictionary_pending = text
            self.dictionary_timer.start(180)

    def lookup_term(self, text):
        self.dictionary_timer.stop()
        if not text.strip():
            return
        self.dictionary_query.setText(clean_term(text)[:240])
        self.dictionary_view.setHtml(render_lookup(self.dictionary.lookup(text)))
        self.dictionary_view.verticalScrollBar().setValue(0)

    def persist(self):
        try:
            self.lib.save()
            self.statusBar().showMessage('已自动保存到本机', 4000)
            return True
        except OSError as exc:
            QMessageBox.critical(self, '未能保存', f'请检查磁盘权限或剩余空间。当前改动尚未保存。\n{exc}')
            return False

    def refresh_library(self):
        self.library_list.clear()
        query = self.doc_filter.text().casefold()
        for doc in self.lib.state['documents']:
            if query not in doc['title'].casefold():
                continue
            item = QListWidgetItem(f"{doc['title']}\n{len(doc['marks'])} 个标记")
            item.setData(Qt.ItemDataRole.UserRole, doc['id'])
            item.setToolTip(doc['title'])
            self.library_list.addItem(item)
            if self.record and doc['id'] == self.record['id']:
                self.library_list.setCurrentItem(item)

    def library_clicked(self, item):
        if self.worker and self.worker.isRunning():
            self.statusBar().showMessage('正在识别当前页，请稍后切换文档。')
            return
        rec = next(d for d in self.lib.state['documents'] if d['id'] == item.data(Qt.ItemDataRole.UserRole))
        self.open_record(rec)

    def import_dialog(self):
        if self.worker and self.worker.isRunning():
            return
        paths, _ = QFileDialog.getOpenFileNames(self, '导入英文 PDF', '', 'PDF 文件 (*.pdf)')
        for path in paths:
            self.import_file(path)

    def unlock(self, doc):
        password = ''
        if doc.needs_pass:
            password, ok = QInputDialog.getText(self, '加密 PDF', '请输入打开密码（不会保存到磁盘）', QLineEdit.EchoMode.Password)
            if not ok or not doc.authenticate(password):
                doc.close()
                if ok:
                    QMessageBox.warning(self, '无法打开', '密码不正确。')
                return None
        return password

    def import_file(self, path):
        if self.worker and self.worker.isRunning():
            return
        try:
            with fitz.open(path) as check:
                if not check.is_pdf or not len(check):
                    raise ValueError('这不是有效的 PDF 文件。')
                password = self.unlock(check)
                if password is None:
                    return
            rec = self.lib.import_pdf(path)
            self.refresh_library()
            self.open_record(rec, password)
        except Exception as exc:
            QMessageBox.warning(self, '导入失败', str(exc))

    def open_record(self, record, password=None):
        try:
            doc = fitz.open(self.lib.pdf_path(record))
            if password is None:
                password = self.unlock(doc)
                if password is None:
                    return
            elif doc.needs_pass and not doc.authenticate(password):
                doc.close()
                raise ValueError('密码无效')
            if self.doc:
                self.doc.close()
            self.doc, self.record, self.password = doc, record, password
            self.search_cursor = None
            self.page_no = max(0, min(record.get('page', 0), len(doc) - 1))
            self.layout_box.blockSignals(True)
            self.layout_box.setCurrentIndex(1 if self.lib.state.get('view_columns') == 2 else 0)
            self.layout_box.blockSignals(False)
            self.lib.state['last'] = record['id']
            self.doc_title.setText(record['title'])
            self.doc_title.setToolTip(record['title'])
            self.page_spin.blockSignals(True)
            self.page_spin.setMaximum(len(doc))
            self.page_spin.setValue(self.page_no + 1)
            self.page_spin.blockSignals(False)
            self.page_total.setText(f'/ {len(doc)}')
            self.empty.hide()
            self.scroll.show()
            self.term_edit.clear()
            self.reader.attach()
            self.render_page()
            self.go_page(self.page_no)
            self.refresh_marks()
            self.refresh_annotation_controls()
            self.refresh_library()
            self.persist()
        except Exception as exc:
            QMessageBox.warning(self, '打开失败', str(exc))

    def words_for_page(self, n):
        cached = self.record.get('ocr', {}).get(str(n))
        words = cached if cached is not None else self.doc[n].get_text('words')
        return sorted(words, key=lambda w: (w[5], w[6], w[7]))

    def render_page(self):
        if not self.doc:
            return
        try:
            old_box = self.reader.boxes[self.page_no] if self.reader.boxes else None
            fraction = ((self.scroll.verticalScrollBar().value() - old_box.y()) / old_box.height()) if old_box else 0
            self.reader.layout_pages(self.layout_box.currentData(), self.scroll.viewport().width(),
                                     None if self.fit else self.zoom)
            self.zoom = self.reader.scale
            if old_box:
                new_box = self.reader.boxes[self.page_no]
                self.scroll.verticalScrollBar().setValue(int(new_box.y() + fraction * new_box.height()))
                self.scroll.horizontalScrollBar().setValue(max(0, int(new_box.x()) - 16))
            self.canvas = self.reader.page_canvas(self.page_no)
            self.update_page_info()
            self.reader.schedule_visible()
        except Exception as exc:
            QMessageBox.warning(self, '页面显示失败', str(exc))

    def update_page_info(self):
        self.prev.setEnabled(self.page_no > 0)
        self.next.setEnabled(self.page_no < len(self.doc) - 1)
        self.page_hint.setText('本页没有可选择的文字，请点击「识别当前页」进行英文 OCR。' if not self.canvas.words else
            '本页已使用英文 OCR，请核对识别结果。' if str(self.page_no) in self.record.get('ocr', {}) else
            '双击标记 / 取消 · 拖动选词组 · Enter 标记 · 滚轮连续阅读')

    def set_active_page(self, n):
        if not self.doc or not 0 <= n < len(self.doc):
            return
        if n != self.page_no:
            self.canvas.selection = []
            self.canvas.update()
            self.term_edit.clear()
        self.page_no = n
        self.reader.active = n
        self.canvas = self.reader.page_canvas(n)
        self.record['page'] = n
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(n + 1)
        self.page_spin.blockSignals(False)
        self.update_page_info()
        self.position_timer.start(650)

    def page_selected(self, n, text):
        self.set_active_page(n)
        self.term_edit.setText(text)

    def toggle_word(self, page_no, index):
        self.set_active_page(page_no)
        word = self.canvas.words[index]
        center = fitz.Rect(word[:4]).tl + (fitz.Rect(word[:4]).br - fitz.Rect(word[:4]).tl) / 2
        matches = [m for m in self.record['marks'] if m['page'] == page_no and
                   any(fitz.Rect(rect).contains(center) for rect in m['rects'])]
        if matches:
            # For overlapping highlights, remove the smallest matching entry first.
            mark = min(matches, key=lambda m: len(m['rects']))
            self.lookup_term(mark['term'])
            if self.remove_mark_ids({mark['id']}):
                self.canvas.selection = []
                self.canvas.update()
                self.term_edit.clear()
                self.statusBar().showMessage('已取消标记并保存：' + mark['term'], 5000)
        else:
            try:
                term = validate_term(word[4])
            except ValueError as exc:
                self.statusBar().showMessage(str(exc), 5000)
                return
            self.canvas.selection = [index]
            self.term_edit.setText(term)
            self.add_mark()

    def go_page(self, n):
        if not self.doc or not 0 <= n < len(self.doc):
            return
        self.set_active_page(n)
        box = self.reader.boxes[n]
        self.reader.busy = True
        self.scroll.verticalScrollBar().setValue(max(0, int(box.y()) - 24))
        self.scroll.horizontalScrollBar().setValue(max(0, int(box.x()) - 16))
        self.reader.busy = False
        self.reader.schedule_visible()

    def change_layout(self):
        self.lib.state['view_columns'] = self.layout_box.currentData()
        if self.doc:
            self.render_page()
            self.go_page(self.page_no)
        self.persist()

    def change_zoom(self, text):
        self.fit = text == '适合宽度'
        if not self.fit:
            self.zoom = float(text.strip('%')) / 100
        self.render_page()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'resize_timer') and self.fit:
            self.resize_timer.start(180)

    def add_mark(self):
        if not self.record:
            return
        if self.annotation_tool.currentData() != 'select':
            return
        try:
            term = validate_term(self.term_edit.text())
            rects = [list(self.canvas.words[i][:4]) for i in self.canvas.selection]
            order = self.canvas.selection[0] if self.canvas.selection else 1000000 + len(self.record['marks'])
            _, added = self.lib.add_mark(self.record, term, self.page_no, rects, order)
            self.canvas.selection = []
            self.canvas.marks = [m for m in self.record['marks'] if m['page'] == self.page_no]
            self.canvas.update()
            self.reader.update_marks()
            self.term_edit.clear()
            self.lookup_term(term)
            self.refresh_marks()
            self.refresh_library()
            self.statusBar().showMessage(('已标记并保存：' if added else '已经标记过：') + term, 5000)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, '未能标记', str(exc))

    def refresh_marks(self):
        self.mark_list.clear()
        marks = self.record['marks'] if self.record else []
        query = self.mark_filter.text().casefold()
        self.mark_count.setText(f'本篇词本 · {len(marks)} 个标记')
        for mark in sorted(marks, key=lambda m: (m['page'], m.get('order', 0), m['created'])):
            if query not in mark['term'].casefold():
                continue
            item = QListWidgetItem(f"{mark['term']}\n第 {mark['page'] + 1} 页")
            item.setData(Qt.ItemDataRole.UserRole, mark['id'])
            item.setToolTip(mark['term'])
            item.setForeground(QColor(COLLECTED_COLOR))
            font = item.font()
            font.setBold(True)
            font.setUnderline(True)
            item.setFont(font)
            self.mark_list.addItem(item)

    def get_mark(self, item):
        return next(m for m in self.record['marks'] if m['id'] == item.data(Qt.ItemDataRole.UserRole))

    def jump_mark(self, item):
        mark = self.get_mark(item)
        self.lookup_term(mark['term'])
        self.go_page(mark['page'])
        if mark['rects']:
            self.canvas.selection = [i for i, word in enumerate(self.canvas.words)
                                     if any(fitz.Rect(word[:4]).intersects(fitz.Rect(r)) for r in mark['rects'])]
            self.canvas.update()
            self.term_edit.setText(mark['term'])
            r = self.canvas.screen_rect(mark['rects'][0])
            self.reader.ensure_rect(mark['page'], r)
        self.statusBar().showMessage('已定位：' + mark['term'], 4000)

    def edit_mark(self):
        items = self.mark_list.selectedItems()
        if len(items) != 1:
            self.statusBar().showMessage('请选择一个词条后编辑。', 4000)
            return
        mark = self.get_mark(items[0])
        text, ok = QInputDialog.getText(self, '编辑词条', '修正英文单词或词组', text=mark['term'])
        if ok:
            try:
                previous = mark['term']
                mark['term'] = validate_term(text)
                if not self.persist():
                    mark['term'] = previous
                self.refresh_marks()
                self.lookup_term(mark['term'])
            except ValueError as exc:
                QMessageBox.warning(self, '词条不正确', str(exc))

    def delete_marks(self):
        ids = {i.data(Qt.ItemDataRole.UserRole) for i in self.mark_list.selectedItems()}
        self.remove_mark_ids(ids)

    def remove_mark_ids(self, ids):
        if not ids or not self.record:
            return False
        previous = self.record['marks']
        self.record['marks'] = [m for m in previous if m['id'] not in ids]
        if not self.persist():
            self.record['marks'] = previous
            return False
        self.refresh_marks()
        self.refresh_library()
        self.canvas.marks = [m for m in self.record['marks'] if m['page'] == self.page_no]
        self.canvas.update()
        self.reader.update_marks()
        return True

    def has_marks(self):
        if not self.record or not self.record['marks']:
            self.statusBar().showMessage('请先标记至少一个词条。', 5000)
            return False
        return True

    def quick_export(self):
        if not self.has_marks():
            return
        (APP_ROOT / 'exports').mkdir(exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(self, '一键导出云词本', str(APP_ROOT / 'exports' / (safe_name(self.record['title']) + '_云词本.txt')), '文本文件 (*.txt)')
        if path:
            try:
                Path(path).write_text(export_body(self.record), encoding='utf-8')
                self.statusBar().showMessage('已导出：' + path, 10000)
            except OSError as exc:
                QMessageBox.critical(self, '导出失败', str(exc))

    def export_dialog(self):
        if self.has_marks():
            (APP_ROOT / 'exports').mkdir(exist_ok=True)
            ExportDialog(self, self.record).exec()

    def export_vocabulary(self):
        if not self.has_marks():
            return
        if not self.dictionary.ready:
            QMessageBox.warning(self, '离线词典无法读取', self.dictionary.error)
            return
        try:
            VocabularyExportDialog(self).exec()
        except Exception as exc:
            QMessageBox.critical(self, '无法准备释义表', str(exc))

    def write_highlight_pdf(self, path):
        if Path(path).resolve().is_relative_to(self.lib.root.resolve()):
            raise ValueError('不能将导出文件写入文档数据目录，请另选位置。')
        return export_annotated_pdf(self.lib.pdf_path(self.record), path, self.record['marks'],
                                    self.record.get('annotations', []), self.password)

    def export_pdf(self):
        if not self.record or not (self.record['marks'] or self.record.get('annotations')):
            self.statusBar().showMessage('请先收录词条或添加论文批注。', 5000)
            return
        (APP_ROOT / 'exports').mkdir(exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(self, '导出收录词条和论文批注', str(APP_ROOT / 'exports' / (safe_name(self.record['title']) + '_批注.pdf')), 'PDF (*.pdf)')
        if path:
            try:
                if Path(path).resolve() == self.lib.pdf_path(self.record).resolve():
                    raise ValueError('请选择另一个导出位置，不能覆盖词库中的 PDF。')
                self.write_highlight_pdf(path)
                self.statusBar().showMessage('已导出收录与批注 PDF：' + path, 10000)
            except Exception as exc:
                QMessageBox.critical(self, '导出失败', str(exc))

    def export_reading(self):
        if not self.record:
            self.statusBar().showMessage('请先导入并打开 PDF。', 5000)
            return
        if self.reading_worker and self.reading_worker.isRunning():
            return
        if self.worker and self.worker.isRunning():
            self.statusBar().showMessage('请等待当前页识别完成后导出。', 5000)
            return
        dialog = ReadingExportDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        (APP_ROOT / 'exports').mkdir(exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(self, '保存精读 PDF',
            str(APP_ROOT / 'exports' / (safe_name(self.record['title']) + '_精读留白.pdf')), 'PDF (*.pdf)')
        if not path:
            return
        if Path(path).resolve().is_relative_to(self.lib.root.resolve()):
            QMessageBox.warning(self, '请选择其他位置', '不能将导出文件写入文档数据目录，请选择 exports 或其他文件夹。')
            return
        options = {'password': self.password, 'pages': dialog.selected_pages(),
                   'blank_lines': dialog.gap.currentIndex() + 1, 'tessdata': TESSDATA,
                   'marks': copy.deepcopy(self.record['marks']) if dialog.highlights.isChecked() else ()}
        self.reading_destination = path
        self.reading_progress = QProgressDialog('准备生成精读 PDF…', '取消', 0, len(options['pages']), self)
        self.reading_progress.setWindowTitle('导出精读 PDF')
        self.reading_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.reading_progress.setMinimumDuration(0)
        self.reading_progress.setAutoClose(False)
        self.reading_progress.setAutoReset(False)
        self.reading_worker = ReadingExportWorker(str(self.lib.pdf_path(self.record)), path, options, self)
        self.reading_progress.canceled.connect(self.reading_worker.requestInterruption)
        self.reading_worker.progress.connect(self.reading_export_progress)
        self.reading_worker.ready.connect(self.reading_export_done)
        self.reading_worker.finished.connect(self.reading_worker_finished)
        self.reading_button.setEnabled(False)
        self.reading_progress.show()
        self.reading_worker.start()

    def reading_export_progress(self, done, total, message):
        if not self.reading_progress.wasCanceled():
            self.reading_progress.setMaximum(total)
            self.reading_progress.setValue(done)
            self.reading_progress.setLabelText(message)

    def reading_export_done(self, report, error):
        self.reading_progress.close()
        if error:
            QMessageBox.critical(self, '精读导出失败', error)
        elif report is None:
            self.statusBar().showMessage('已取消精读导出，保存位置中的原有文件保持完整。', 8000)
        else:
            self.statusBar().showMessage(f"已导出精读 PDF：{report['source_pages']} 个原页 → {report['output_pages']} 个打印页 · {self.reading_destination}", 15000)
            if report['unchanged_pages']:
                numbers = ', '.join(map(str, report['unchanged_pages'][:20]))
                QMessageBox.information(self, '精读导出完成',
                    f'已保存到：{self.reading_destination}\n\n原 PDF 第 {numbers} 页未找到可安全分开的文字行，保持原版面。请打印前预览。')

    def reading_worker_finished(self):
        self.reading_button.setEnabled(True)
        self.reading_worker.deleteLater()
        self.reading_worker = None

    def rename_doc(self):
        if not self.record:
            return
        text, ok = QInputDialog.getText(self, '重命名文档 / 章节', '文档名称', text=self.record['title'])
        if ok and text.strip():
            previous = self.record['title']
            self.record['title'] = text.strip()
            if not self.persist():
                self.record['title'] = previous
            self.doc_title.setText(self.record['title'])
            self.refresh_library()

    def remove_doc(self):
        if not self.record or (self.worker and self.worker.isRunning()):
            return
        if QMessageBox.question(self, '移除文档', '从词库移除此文档和它的标记？\n原始 PDF 保持不变。') != QMessageBox.StandardButton.Yes:
            return
        previous = self.lib.state['documents'][:]
        self.lib.state['documents'].remove(self.record)
        if not self.persist():
            self.lib.state['documents'] = previous
            return
        self.doc.close()
        self.reader.clear()
        self.doc = self.record = None
        self.lib.state['last'] = None
        self.scroll.hide()
        self.empty.show()
        self.doc_title.setText('开始一段新的阅读')
        self.term_edit.clear()
        self.page_spin.setMaximum(1)
        self.page_total.setText('/ 0')
        self.refresh_library()
        self.refresh_marks()

    def ocr(self):
        if not self.doc or (self.worker and self.worker.isRunning()):
            return
        if not (TESSDATA / 'eng.traineddata').exists():
            QMessageBox.warning(self, '缺少 OCR 字库', '请恢复软件 tessdata 目录中的 eng.traineddata。')
            return
        self.ocr_page = self.page_no
        self.worker = OCRWorker(str(self.lib.pdf_path(self.record)), self.page_no, self.password)
        self.worker.ready.connect(self.ocr_done)
        self.ocr_button.setEnabled(False)
        self.statusBar().showMessage('正在离线识别当前页英文，通常需要数秒……')
        self.worker.start()

    def ocr_done(self, words, error):
        self.ocr_button.setEnabled(True)
        if error:
            QMessageBox.warning(self, '识别失败', error)
            return
        if not words:
            self.statusBar().showMessage('没有识别到英文；可手动输入词条。', 8000)
            return
        self.record.setdefault('ocr', {})[str(self.ocr_page)] = words
        self.persist()
        if self.ocr_page in self.reader.canvases:
            self.reader.canvases[self.ocr_page].image = QPixmap()
            self.reader.page_canvas(self.ocr_page)
        self.canvas = self.reader.page_canvas(self.page_no)
        self.update_page_info()
        self.statusBar().showMessage(f'本页已识别 {len(words)} 个文字区域，请核对后标记。', 8000)

    def search_pdf(self):
        if not self.doc or not self.pdf_search.text().strip() or (self.worker and self.worker.isRunning()):
            return
        query = self.pdf_search.text().strip()
        current = (query, self.page_no)
        start = self.search_cursor[2] + 1 if self.search_cursor and self.search_cursor[:2] == current else 0
        for step in range(len(self.doc) + 1):
            n = (self.page_no + step) % len(self.doc)
            page = self.doc[n]
            hits = page.search_for(query)
            if not hits and str(n) in self.record.get('ocr', {}):
                hits = [fitz.Rect(w[:4]) for w in self.words_for_page(n) if query.casefold() in w[4].casefold()]
            offset = start if step == 0 else 0
            if offset < len(hits):
                self.go_page(n)
                rect = hits[offset]
                self.canvas.selection = [i for i, w in enumerate(self.canvas.words) if fitz.Rect(w[:4]).intersects(rect)]
                self.canvas.update()
                self.term_edit.setText(self.canvas.selection_text())
                r = self.canvas.screen_rect(rect)
                self.reader.ensure_rect(n, r)
                self.search_cursor = (query, n, offset)
                self.statusBar().showMessage(f'找到匹配：第 {n + 1} 页', 5000)
                return
        self.statusBar().showMessage('未找到匹配。扫描页需先识别，词组请使用 PDF 中的原文查找。', 7000)

    def help(self):
        QMessageBox.information(self, 'XT 阅迹 · 使用帮助',
            '1. 点击「导入 PDF」，也可以把 PDF 拖入窗口。\n'
            '2. 单击一个单词，或从词组第一个词拖到最后一个词。\n'
            '3. 核对下方输入框，按 Enter 或点击「标记选词」。\n'
            '   快捷操作：双击单词直接收录，再次双击青绿下划线词条即可取消。\n'
            '4. 点击「一键导出云词本 TXT」，把 TXT 正文粘贴到墨墨背单词云词本。\n\n'
            '扫描页：点击「识别当前页」，完成后同样选择词条。OCR 结果可能有误，请核对。\n'
            '词本：双击返回原页；编辑修正拼写；Ctrl 多选后删除。\n'
            '章节模式保留词组与大小写。// 原型模式由墨墨背单词进行词形还原。\n'
            '快捷键：Ctrl+O 导入，Ctrl+E 导出，Ctrl+F 查找。\n\n'
            '精读：右侧「导出精读 PDF」可生成留空行的打印副本。\n'
            '批注：顶部选择高亮、下划线、画笔、矩形框或文字备注，旁边可选颜色和线宽。\n'
            '批注管理可定位、编辑备注、删除；Ctrl+Z 撤销，Ctrl+Y 重做，Esc 返回选词。\n'
            '工具按钮全部展开；默认 1–7 依次切换选词、高亮、下划线、画笔、框、备注、橡皮擦。\n'
            '右上角「设置」可修改工具快捷键；输入框打字时不触发工具切换。\n'
            '右侧「导出收录与批注 PDF」会保存全部收录样式和论文批注。\n'
            '查词：选词后右侧显示离线中文释义，也可手动输入查词。\n'
            '阅读：默认单页连续滚动，顶部可切换「双页并排」。滚动时自动加载附近页面。\n'
            '所有 PDF 和标记只在本机保存。备份整个 data 文件夹即可迁移。')

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(u.toLocalFile().lower().endswith('.pdf') for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for u in event.mimeData().urls():
            if u.toLocalFile().lower().endswith('.pdf'):
                self.import_file(u.toLocalFile())

    def closeEvent(self, event):
        if self.reading_worker and self.reading_worker.isRunning():
            self.statusBar().showMessage('正在生成精读 PDF，可先在进度窗口取消，完成后再关闭。')
            event.ignore()
            return
        if self.worker and self.worker.isRunning():
            self.statusBar().showMessage('正在识别，请等待完成后关闭。')
            event.ignore()
            return
        if not self.persist():
            event.ignore()
            return
        if self.doc:
            self.reader.clear()
            self.position_timer.stop()
            self.resize_timer.stop()
            self.doc.close()
            self.doc = None
        self.dictionary_timer.stop()
        self.dictionary.close()
        QApplication.instance().removeEventFilter(self)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(PROJECT_NAME)
    configure_fonts(app)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    try:
        verify_dir = os.environ.get(VERIFY_ENV)
        data_root = Path(verify_dir) / 'data' if verify_dir else APP_ROOT / 'data'
        data_root.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(data_root / 'session.lock'))
        lock.setStaleLockTime(30000)
        if not lock.tryLock(100):
            QMessageBox.information(None, 'XT 阅迹', '软件已经在运行，请切换到已打开的XT 阅迹 窗口。')
            return 0
        window = MainWindow(data_root, reopen=not bool(verify_dir))
        window.show()
        if verify_dir:
            def verify_packaged():
                import json
                try:
                    sample = APP_ROOT / 'Example.pdf'
                    window.import_file(str(sample))
                    window.activateWindow()
                    QApplication.processEvents()
                    for index, (_, key) in enumerate(TOOLS):
                        window.canvas.setFocus()
                        QApplication.sendEvent(window.canvas, QKeyEvent(QEvent.Type.KeyPress,
                            Qt.Key.Key_1 + index, Qt.KeyboardModifier.NoModifier, str(index + 1)))
                        assert window.canvas.tool == key
                        assert window.annotation_tool.buttons[index].isVisible()
                    window.annotation_tool.setCurrentIndex(0)
                    window.pdf_search.setFocus()
                    QApplication.sendEvent(window.pdf_search, QKeyEvent(QEvent.Type.KeyPress,
                        Qt.Key.Key_2, Qt.KeyboardModifier.NoModifier, '2'))
                    assert window.pdf_search.text() == '2' and window.canvas.tool == 'select'
                    window.pdf_search.clear()
                    keys = dict(window.tool_shortcuts, highlight='Ctrl+Shift+H')
                    assert window.save_tool_shortcuts(keys)
                    window.canvas.setFocus()
                    QApplication.sendEvent(window.canvas, QKeyEvent(QEvent.Type.KeyPress,
                        Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier, 'H'))
                    assert window.canvas.tool == 'highlight'
                    assert window.save_tool_shortcuts({key: str(index + 1) for index, (_, key) in enumerate(TOOLS)})
                    window.annotation_tool.setCurrentIndex(0)
                    idx = next(i for i, word in enumerate(window.canvas.words) if word[4] == 'discovery.')
                    window.canvas.selection = [idx]
                    window.term_edit.setText(window.canvas.selection_text())
                    window.add_mark()
                    assert window.dictionary.ready
                    assert '发现' in window.dictionary_view.toPlainText()
                    point = window.canvas.screen_rect(window.canvas.words[idx][:4]).center()
                    for expected in (0, 1):
                        event = QMouseEvent(QEvent.Type.MouseButtonDblClick, point,
                            QPointF(window.canvas.mapToGlobal(point.toPoint())), Qt.MouseButton.LeftButton,
                            Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                        QApplication.sendEvent(window.canvas, event)
                        assert len(window.record['marks']) == expected
                    Path(verify_dir, 'momo.txt').write_text(export_body(window.record), encoding='utf-8')
                    window.write_highlight_pdf(str(Path(verify_dir, 'highlight.pdf')))
                    window.layout_box.setCurrentIndex(1)
                    window.go_page(1)
                    idx = next(i for i, word in enumerate(window.canvas.words) if word[4] == 'mother')
                    window.canvas.selection = [idx]
                    window.term_edit.setText(window.canvas.selection_text())
                    window.add_mark()
                    assert window.record['marks'][-1]['page'] == 1
                    assert window.reader.boxes[0].y() == window.reader.boxes[1].y()
                    assert '母亲' in window.dictionary_view.toPlainText()
                    vocabulary_report = export_vocabulary_pdf(Path(verify_dir, 'vocabulary.pdf'),
                        window.record['title'], vocabulary_rows(window.record, window.dictionary))
                    with fitz.open(Path(verify_dir, 'vocabulary.pdf')) as vocabulary:
                        text = ''.join(page.get_text() for page in vocabulary)
                        assert '母亲' in text and 'discovery' in text and '中文释义' in text
                    # Exercise local annotation persistence, undo/redo and native
                    # PDF appearances in the packaged runtime as well.
                    for kind, geometry in [('highlight', {'rects': [list(window.canvas.words[idx][:4])]}),
                                           ('underline', {'rects': [list(window.canvas.words[idx][:4])]}),
                                           ('ink', {'points': [[52, 290], [100, 310], [145, 290]]}),
                                           ('rect', {'rect': [52, 340, 240, 390]})]:
                        window.annotation_action(1, dict(type=kind, color='#e87070', width=2, **geometry))
                    window.commit_annotations(window.record['annotations'] + [{
                        'id': uuid.uuid4().hex, 'created': datetime.now().isoformat(), 'page': 1,
                        'type': 'note', 'color': '#f4c542', 'width': 2,
                        'rect': [260, 340, 278, 358], 'text': '中文备注：核对方法与假设。'}])
                    window.canvas.setFocus()
                    window.undo_annotation()
                    assert len(window.record['annotations']) == 4
                    window.redo_annotation()
                    assert len(window.record['annotations']) == 5
                    window.write_highlight_pdf(Path(verify_dir, 'annotations.pdf'))
                    with fitz.open(Path(verify_dir, 'annotations.pdf')) as annotated:
                        page = annotated[1]
                        kinds = {a.type[0] for a in page.annots()}
                        assert {fitz.PDF_ANNOT_TEXT, fitz.PDF_ANNOT_INK, fitz.PDF_ANNOT_SQUARE,
                                fitz.PDF_ANNOT_HIGHLIGHT, fitz.PDF_ANNOT_UNDERLINE} <= kinds
                        assert any('中文备注' in a.info['content'] for a in page.annots())
                    reading_report = export_reading_pdf(window.lib.pdf_path(window.record),
                        Path(verify_dir, 'reading.pdf'), tessdata=TESSDATA,
                        marks=window.record['marks'])
                    assert reading_report['source_pages'] == 2
                    with fitz.open(Path(verify_dir, 'reading.pdf')) as reading:
                        assert any('discovery' in p.get_text() for p in reading)
                    # Exercise the isolated background exporter in the actual
                    # frozen executable, including Windows spawn/freeze support.
                    reading_worker = ReadingExportWorker(str(window.lib.pdf_path(window.record)),
                        str(Path(verify_dir, 'reading-background.pdf')),
                        {'tessdata': TESSDATA, 'pages': [0], 'marks': window.record['marks']}, window)
                    results = []
                    reading_worker.ready.connect(lambda result, error: results.append((result, error)))
                    wait_loop = QEventLoop(window)
                    reading_worker.finished.connect(wait_loop.quit)
                    QTimer.singleShot(15000, wait_loop.quit)
                    reading_worker.start()
                    wait_loop.exec()
                    assert not reading_worker.isRunning(), 'Background export timed out'
                    assert results and results[0][0] and not results[0][1], str(results)
                    with fitz.open(sample) as doc:
                        page = doc[0]
                        tp = page.get_textpage_ocr(language='eng', dpi=120, full=True, tessdata=str(TESSDATA))
                        ocr_count = len(page.get_text('words', textpage=tp))
                    window.grab().save(str(Path(verify_dir, 'window.png')))
                    Path(verify_dir, 'result.json').write_text(json.dumps({'ok': True, 'marks': len(window.record['marks']),
                        'ocr_words': ocr_count, 'columns': window.reader.columns, 'continuous_pages': len(window.reader.boxes),
                        'double_click_toggle': True, 'offline_lookup': True,
                        'dictionary_entries': window.dictionary.count,
                        'reading_export': reading_report, 'reading_background': True,
                        'vocabulary_export': vocabulary_report, 'annotations': 5,
                        'tool_shortcuts': True, 'visible_tools': len(TOOLS)}), encoding='utf-8')
                except Exception as exc:
                    Path(verify_dir, 'result.json').write_text(json.dumps({'ok': False, 'error': str(exc)}), encoding='utf-8')
                window.close()
            QTimer.singleShot(800, verify_packaged)
        for path in sys.argv[1:]:
            if path.lower().endswith('.pdf'):
                window.import_file(path)
        return app.exec()
    except Exception as exc:
        QMessageBox.critical(None, 'XT 阅迹 启动失败', str(exc))
        return 1


if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(main())
