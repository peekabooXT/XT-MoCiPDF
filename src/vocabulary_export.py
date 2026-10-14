"""Two-column vocabulary PDF using the app's existing Qt font support."""
import os
import tempfile
from pathlib import Path
from branding import APP_NAME, PROJECT_NAME, VERSION

from PySide6.QtCore import Qt, QPointF, QRectF, QMarginsF
from PySide6.QtGui import (QColor, QFont, QFontMetricsF, QPainter, QPageSize,
                          QPageLayout, QPdfWriter, QTextLayout, QTextOption)


def _meaning(entry):
    text = entry.get('translation') or entry.get('definition') or '暂无释义'
    text = text.replace('\\n', '\n').replace('\r\n', '\n').strip()
    return text if entry.get('translation') else '英文释义：\n' + text


def meaning_text(result):
    if result.get('error'):
        return result['error']
    if 'parts' in result:
        parts = ['未收录完整词组，以下为逐词释义：']
        for part in result['parts']:
            parts.append(part['query'] + '：\n' + meaning_text(part))
        if result.get('truncated'):
            parts.append('仅列出前 12 个词。')
        return '\n\n'.join(parts)
    parts = [_meaning(result['entry'])] if result.get('entry') else []
    for base in result.get('bases', []):
        parts.append('词形参考 ' + base['word'] + '：\n' + _meaning(base))
    return '\n\n'.join(parts) if parts else '词典未收录，请核对拼写或补充释义。'


def vocabulary_rows(record, dictionary, dedupe=True, ids=None):
    if not dictionary.ready:
        raise ValueError(dictionary.error)
    seen, rows = set(), []
    marks = sorted(record['marks'], key=lambda mark: (mark['page'], mark.get('order', 0), mark['created']))
    for mark in marks:
        if ids is not None and mark['id'] not in ids:
            continue
        term = mark['term']
        if dedupe and term in seen:
            continue
        seen.add(term)
        rows.append((term, meaning_text(dictionary.lookup(term))))
    return rows


def _font(size=11, bold=False):
    font = QFont('Microsoft YaHei')
    font.setPixelSize(size)
    font.setBold(bold)
    return font


def _wrap(text, font, width):
    result = []
    for paragraph in str(text).replace('\x00', '').replace('\r\n', '\n').split('\n'):
        if not paragraph:
            result.append('')
            continue
        layout = QTextLayout(paragraph, font)
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(option)
        layout.beginLayout()
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(width)
            # QTextLine indices are UTF-16 positions; Python indexes Unicode
            # codepoints. Keep non-BMP characters intact in manual definitions.
            encoded = paragraph.encode('utf-16-le', errors='replace')
            start, end = line.textStart(), line.textStart() + line.textLength()
            result.append(encoded[start * 2:end * 2].decode('utf-16-le'))
        layout.endLayout()
    return result or ['']


def export_vocabulary_pdf(path, title, rows):
    """Printable A4 table; repeat headers and continue very long meanings.

    Requires a QApplication / registered Chinese fonts, as in the native app.
    Write to a temporary sibling first so failed exports do not replace files.
    """
    rows = [(str(term), str(meaning)) for term, meaning in rows]
    if not rows:
        raise ValueError('没有可以导出的词条。')
    if any(not term.strip() for term, meaning in rows):
        raise ValueError('词条不能为空。')
    path = Path(path)
    handle, temporary = tempfile.mkstemp(prefix='.xt-vocabulary-', suffix='.pdf', dir=path.parent)
    os.close(handle)
    painter = None
    writer = None
    try:
        width, height, margin, pad = 595, 842, 36, 10
        table_width, left_width = width - margin * 2, 174
        font, small, bold = _font(), _font(9), _font(11, True)
        line_height = max(16, QFontMetricsF(font).height() + 2)
        title_lines = _wrap(title, small, table_width)[:2]
        top = 65 + len(title_lines) * 13
        header_height = 29
        bottom = height - 45
        pages, page = [], []
        used = 0
        for term, meaning in rows:
            left = _wrap(term, font, left_width - pad * 2)
            right = _wrap(meaning, font, table_width - left_width - pad * 2)
            offset = 0
            continuation = False
            total = max(len(left), len(right))
            # Keep an ordinary row whole; paginate oversized entries explicitly.
            while offset < total:
                remaining = bottom - top - header_height - used
                full = (total - offset) * line_height + pad * 2
                if full > remaining and used:
                    pages.append(page)
                    page, used = [], 0
                    remaining = bottom - top - header_height
                count = min(total - offset, int((remaining - pad * 2) // line_height))
                if count <= 0:
                    raise ValueError('表格布局空间不足。')
                left_part = left[offset:offset + count]
                if continuation and not left_part:
                    left_part = _wrap(term, font, left_width - pad * 2) + ['（续页）']
                    count = max(count, len(left_part))
                row_height = count * line_height + pad * 2
                page.append((left_part, right[offset:offset + count], row_height))
                used += row_height
                offset += count
                continuation = True
        if page:
            pages.append(page)
        writer = QPdfWriter(temporary)
        writer.setResolution(72)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Point)
        writer.setTitle(title + ' - 单词释义表')
        writer.setCreator(PROJECT_NAME + ' ' + VERSION)
        painter = QPainter()
        if not painter.begin(writer):
            raise OSError('无法创建 PDF，请检查保存位置权限。')
        metrics = QFontMetricsF(font)

        def text_lines(lines, x, y):
            painter.setFont(font)
            painter.setPen(QColor('#263c43'))
            for i, line in enumerate(lines):
                painter.drawText(QPointF(x, y + metrics.ascent() + i * line_height), line)

        for number, items in enumerate(pages, 1):
            if number > 1 and not writer.newPage():
                raise OSError('无法创建 PDF 后续页面。')
            painter.setFont(_font(18, True))
            painter.setPen(QColor('#087f73'))
            painter.drawText(QPointF(margin, 45), APP_NAME + ' · 单词释义表')
            painter.setFont(small)
            painter.setPen(QColor('#647d84'))
            for i, line in enumerate(title_lines):
                painter.drawText(QPointF(margin, 65 + i * 13), line)
            painter.fillRect(QRectF(margin, top, table_width, header_height), QColor('#e5f1ee'))
            painter.setFont(bold)
            painter.setPen(QColor('#087f73'))
            painter.drawText(QPointF(margin + pad, top + 19), '英文单词 / 词组')
            painter.drawText(QPointF(margin + left_width + pad, top + 19), '中文释义')
            y = top + header_height
            for index, (left, right, row_height) in enumerate(items):
                if index % 2:
                    painter.fillRect(QRectF(margin, y, table_width, row_height), QColor('#f7f9fa'))
                text_lines(left, margin + pad, y + pad)
                text_lines(right, margin + left_width + pad, y + pad)
                painter.setPen(QColor('#c8d5d9'))
                painter.drawLine(QPointF(margin, y + row_height), QPointF(margin + table_width, y + row_height))
                y += row_height
            painter.setPen(QColor('#aebfc4'))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(margin, top, table_width, y - top))
            painter.drawLine(QPointF(margin + left_width, top), QPointF(margin + left_width, y))
            painter.drawLine(QPointF(margin, top + header_height), QPointF(margin + table_width, top + header_height))
            painter.setFont(small)
            painter.setPen(QColor('#6b8087'))
            painter.drawText(QPointF(margin, height - 25), f'共 {len(rows)} 个词条 · 第 {number} / {len(pages)} 页')
        painter.end()
        painter = None
        writer = None
        os.replace(temporary, path)
        temporary = None
        return {'terms': len(rows), 'pages': len(pages)}
    finally:
        if painter and painter.isActive():
            painter.end()
        writer = None
        if temporary and Path(temporary).exists():
            Path(temporary).unlink()
