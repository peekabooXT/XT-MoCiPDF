"""Printable PDF with an extra writing line between visual text rows.

Copy PDF bands as vectors instead of replacing the user's fonts or reflowing
the text. Never edit the input file. Images/tables with their own rectangles
are kept together; full-page scans use OCR only to locate splitting gaps.
"""

from i18n import tr, set_language
import os
import hashlib
import secrets
import tempfile
from pathlib import Path
from statistics import median

import pymupdf as fitz
from annotations import add_collected_style
from branding import PROJECT_NAME, VERSION


class ExportCancelled(Exception):
    pass


def reading_export_process(source, destination, options, stop_event, messages):
    """Separate process: PDF operations do not overlap the reader's renderer."""
    try:
        result = export_reading_pdf(source, destination, **options,
            progress=lambda done, total, text: messages.put(('progress', done, total, text)),
            cancelled=stop_event.is_set)
        messages.put(('ready', result, ''))
    except ExportCancelled:
        messages.put(('ready', None, ''))
    except Exception as exc:
        messages.put(('ready', None, str(exc)))


def page_numbers(text, count):
    numbers = set()
    for part in text.replace('，', ',').split(','):
        ends = part.strip().split('-')
        if len(ends) not in (1, 2) or not all(value.strip().isdigit() for value in ends):
            raise ValueError(tr('页码格式示例：1-3,5,8。'))
        first, last = int(ends[0]), int(ends[-1])
        if not 1 <= first <= last <= count:
            raise ValueError(tr('页码必须在 1 到 {arg0} 之间，且起始页不能大于结束页。', arg0=count))
        numbers.update(range(first - 1, last))
    return sorted(numbers)


def _text_rows(page, textpage=None):
    data = page.get_text('dict', textpage=textpage,
                         flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)
    boxes = []
    heights = []
    for block in data['blocks']:
        for line in block.get('lines', []):
            if not any(span['text'].strip() for span in line['spans']):
                continue
            rect = fitz.Rect(line['bbox'])
            if not textpage and abs(line.get('dir', (1, 0))[0]) > .98:
                # PDF font metric boxes often overlap adjacent rows, even when
                # the ink does not. Tighten them to one em around each baseline.
                spans = []
                for span in line['spans']:
                    if not span['text'].strip():
                        continue
                    r = fitz.Rect(span['bbox'])
                    a, d = span.get('ascender', 1), span.get('descender', 0)
                    size = span['size']
                    if a > d and size > 0:
                        baseline = span['origin'][1]
                        r.y0 = max(r.y0, baseline - size * a / (a - d) - .6)
                        r.y1 = min(r.y1, baseline - size * d / (a - d) + .6)
                    spans.append(r)
                    heights.append(size)
                if spans:
                    rect = fitz.Rect(spans[0])
                    for r in spans[1:]:
                        rect |= r
            else:
                heights.append(min(rect.height, 24))
            if not rect.is_empty and rect.intersects(page.rect):
                boxes.append((max(0, rect.y0), min(page.rect.height, rect.y1), True))
    return boxes, max(10, min(32, median(heights) * 1.4)) if heights else 14


def _bands(page, tessdata):
    images = page.get_image_info()
    area = page.rect.width * page.rect.height
    full_scan = any((fitz.Rect(image['bbox']) & page.rect).get_area() > area * .65 for image in images)
    rows, writing_height = _text_rows(page)
    used_ocr = False
    if not rows or (full_scan and len(page.get_text().strip()) < 100):
        tp = page.get_textpage_ocr(language='eng', dpi=200, full=True, tessdata=str(tessdata))
        rows, writing_height = _text_rows(page, tp)
        used_ocr = True
    protected = []
    visual_bottom = max((row[1] for row in rows), default=page.rect.height)
    for image in images:
        rect = fitz.Rect(image['bbox']) & page.rect
        if rect.get_area() < area * .65 and rect.height > 8:
            protected.append((rect.y0, rect.y1, False))
            visual_bottom = max(visual_bottom, rect.y1)
    if not full_scan:
        for drawing in page.get_drawings():
            rect = fitz.Rect(drawing['rect']) & page.rect
            if rect.get_area() < area * .8 and (drawing.get('color') or drawing.get('fill') not in (None, (1, 1, 1))):
                visual_bottom = max(visual_bottom, rect.y1)
            # Ignore page borders/backgrounds and small decoration rules.
            if rect.height > 12 and rect.width > 20 and rect.get_area() < area * .8:
                protected.append((rect.y0, rect.y1, False))
    merged = []
    for top, bottom, has_text in sorted(rows + protected):
        if merged and top < merged[-1][1] + .5:
            merged[-1][1] = max(merged[-1][1], bottom)
            merged[-1][2] |= has_text
        else:
            merged.append([top, bottom, has_text])
    if not merged or not rows:
        return [(0, page.rect.height, False)], writing_height, used_ocr, True
    # Do not push the last text row onto another sheet just to preserve unused
    # bottom paper. A scan's unrecognized graphic content may extend further,
    # so retain its full height rather than trimming by OCR alone.
    end = page.rect.height if full_scan else min(page.rect.height, max(visual_bottom, merged[-1][1]) + 12)
    cuts = [0] + [(a[1] + b[0]) / 2 for a, b in zip(merged, merged[1:])] + [end]
    bands = [(cuts[i], cuts[i + 1], merged[i][2]) for i in range(len(merged))]
    return bands, writing_height, used_ocr, len(rows) > 1 and len(merged) < 2


def export_reading_pdf(source, destination, *, password='', pages=None, blank_lines=1,
                       marks=(), tessdata=None, progress=None, cancelled=None, language=None):
    if language is not None:
        set_language(language)
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError(tr('请选择另一个导出位置，不能覆盖原 PDF。'))
    if destination.exists() and destination.stat().st_size == source.stat().st_size:
        with source.open('rb') as a, destination.open('rb') as b:
            if hashlib.file_digest(a, 'sha256').digest() == hashlib.file_digest(b, 'sha256').digest():
                raise ValueError(tr('该文件与导入的原 PDF 相同，请使用新的文件名保存精读副本。'))
    if blank_lines not in (1, 2):
        raise ValueError(tr('留白行数必须是 1 或 2。'))
    report = {'source_pages': 0, 'output_pages': 0, 'ocr_pages': [], 'unchanged_pages': []}
    temporary = None

    def check_cancel():
        if cancelled and cancelled():
            raise ExportCancelled()

    try:
        with fitz.open(source) as original, fitz.open() as output:
            encrypted = bool((original.metadata or {}).get('encryption')) or original.needs_pass
            if original.needs_pass and not original.authenticate(password):
                raise ValueError(tr('无法打开加密 PDF，请重新输入密码。'))
            permissions = original.permissions
            pages = list(range(len(original))) if pages is None else sorted(set(pages))
            if not pages or any(n < 0 or n >= len(original) for n in pages):
                raise ValueError(tr('请选择有效的导出页码。'))
            add_collected_style(original, [mark for mark in marks if mark['page'] in pages])
            # show_pdf_page excludes annotations; baking keeps their appearance.
            original.bake(annots=True, widgets=True)
            for done, number in enumerate(pages):
                check_cancel()
                if progress:
                    progress(done, len(pages), tr('正在处理原 PDF 第 {arg0} 页…', arg0=number + 1))
                page = original[number]
                page.remove_rotation()
                bands, gap, ocr, unchanged = _bands(page, tessdata)
                check_cancel()
                if ocr:
                    report['ocr_pages'].append(number + 1)
                if unchanged:
                    report['unchanged_pages'].append(number + 1)
                width, height = (842, 595) if page.rect.width > page.rect.height * 1.2 else (595, 842)
                margin, bottom = 20, height - 34
                scale = min(1, (width - margin * 2) / page.rect.width)
                y, target, part = margin, None, 0

                def next_sheet():
                    nonlocal target, y, part
                    target = output.new_page(width=width, height=height)
                    part += 1
                    y = margin
                    target.insert_text((margin, height - 20),
                                       f'Source {number + 1} | Part {part} | Print {len(output)}',
                                       fontsize=8, color=(.45, .45, .45))

                next_sheet()
                for index, (start, end, has_text) in enumerate(bands):
                    check_cancel()
                    capacity = bottom - margin
                    # A large diagram is kept whole, scaled only if necessary.
                    band_scale = min(scale, capacity / (end - start))
                    size = (end - start) * band_scale
                    if y + size > bottom + .01 and y > margin:
                        next_sheet()
                    rect = fitz.Rect((width - page.rect.width * band_scale) / 2, y,
                                     (width + page.rect.width * band_scale) / 2, y + size)
                    if page.get_contents():
                        target.show_pdf_page(rect, original, number,
                                             clip=fitz.Rect(0, start, page.rect.width, end))
                    y += size
                    if has_text and index < len(bands) - 1:
                        y += gap * scale * blank_lines
                report['source_pages'] += 1
            check_cancel()
            output.set_metadata({'title': (original.metadata.get('title') or source.stem) + ' - Reading notes',
                                 'creator': PROJECT_NAME + ' ' + VERSION, 'subject': 'Extra space between text rows for handwritten notes'})
            handle, temporary = tempfile.mkstemp(prefix='.readtrace-reading-', suffix='.pdf', dir=destination.parent)
            os.close(handle)
            kwargs = dict(garbage=4, deflate=True)
            if encrypted:
                kwargs.update(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password,
                              owner_pw=secrets.token_hex(16), permissions=permissions)
            output.save(temporary, **kwargs)
            report['output_pages'] = len(output)
            check_cancel()
            os.replace(temporary, destination)
            temporary = None
        if progress:
            progress(len(pages), len(pages), tr('导出完成'))
        return report
    finally:
        if temporary and Path(temporary).exists():
            Path(temporary).unlink()
