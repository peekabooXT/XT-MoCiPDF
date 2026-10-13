"""Local reading annotations, distinct from vocabulary collection."""
import hashlib
import math
import os
import re
import tempfile
from pathlib import Path

import pymupdf as fitz

COLLECTED_COLOR = '#087f73'
KINDS = {'highlight': '文字高亮', 'underline': '文字下划线', 'ink': '画笔',
         'rect': '矩形框', 'note': '文字备注'}


def ink_rgba(rgb, width, height, stride):
    """Transparent teal glyphs from original pixels; preserve font shapes.

    Returned RGBA is premultiplied for both MuPDF and Qt. Pale scan backgrounds
    are discarded; this layer supplements rather than replaces selectable text.
    """
    result = bytearray(width * height * 4)
    for y in range(height):
        for x in range(width):
            offset = y * stride + x * 3
            r, g, b = rgb[offset:offset + 3]
            alpha = max(0, min(255, (255 - (r + g + b) // 3 - 45) * 255 // 180))
            target = (y * width + x) * 4
            result[target:target + 4] = bytes((8 * alpha // 255, 127 * alpha // 255,
                                               115 * alpha // 255, alpha))
    return bytes(result)


def color_rgb(color):
    return tuple(int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))


def distance_to_segment(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) /
                    (dx * dx + dy * dy))) if dx or dy else 0
    return math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy)


def annotation_at(annotations, point, tolerance=5):
    for item in reversed(annotations):
        kind = item['type']
        if kind == 'ink':
            pts = item['points']
            if len(pts) == 1:
                pts = pts * 2
            if any(distance_to_segment(point, a, b) <= tolerance + item['width'] / 2
                   for a, b in zip(pts, pts[1:])):
                return item
        elif kind == 'rect':
            r = fitz.Rect(item['rect'])
            corners = [r.tl, r.tr, r.br, r.bl, r.tl]
            if any(distance_to_segment(point, a, b) <= tolerance + item['width'] / 2
                   for a, b in zip(corners, corners[1:])):
                return item
        elif kind == 'note':
            if fitz.Rect(item['rect']).contains(point):
                return item
        else:
            for rect in item['rects']:
                r = fitz.Rect(rect)
                if kind == 'highlight' and (r + (-tolerance, -tolerance, tolerance, tolerance)).contains(point):
                    return item
                if kind == 'underline' and distance_to_segment(point, r.bl, r.br) <= tolerance + item['width'] / 2:
                    return item
    return None


def add_collected_style(doc, marks):
    """Underline annotations plus a transparent bold glyph appearance layer."""
    for mark in marks:
        if not mark['rects']:
            continue
        page = doc[mark['page']]
        # Clips and insertion coordinates are unrotated PDF coordinates.
        rotation = page.rotation
        page.set_rotation(0)
        try:
            layers = []
            for bounds in mark['rects']:
                rect = fitz.Rect(bounds) & page.rect
                if rect.is_empty:
                    continue
                pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=rect, alpha=False,
                                      colorspace=fitz.csRGB, annots=False)
                rgba = ink_rgba(pix.samples, pix.width, pix.height, pix.stride)
                layer = fitz.Pixmap(fitz.csRGB, pix.width, pix.height, rgba, True)
                # Pixel-aligned clip bounds prevent stretching the original glyphs.
                area = fitz.Rect(pix.x / 3, pix.y / 3, (pix.x + pix.width) / 3,
                                 (pix.y + pix.height) / 3)
                layers.append((area, layer.tobytes('png')))
            for area, png in layers:
                xref = 0
                for dx, dy in ((-.25, 0), (.25, 0), (0, -.15), (0, .15)):
                    xref = page.insert_image(area + (dx, dy, dx, dy), stream=png if not xref else None,
                                             xref=xref, overlay=True)
            annot = page.add_underline_annot([fitz.Rect(r).quad for r in mark['rects']])
            annot.set_info(content=mark.get('term', ''), subject='已收录词条', title='XT MoCiPDF')
            annot.set_colors(stroke=color_rgb(COLLECTED_COLOR))
            annot.update()
            set_underline_width(annot, 1.5)
        finally:
            page.set_rotation(rotation)


def set_underline_width(annot, width):
    # MuPDF does not expose a border setter for text markup. Its generated
    # appearance is a normal PDF stroked path; keep the standard annotation
    # and adjust only that path's width, with BS recorded for other editors.
    doc = annot.parent.parent
    doc.xref_set_key(annot.xref, 'BS', f'<</W {width} /S /S>>')
    kind, value = doc.xref_get_key(annot.xref, 'AP/N')
    if kind == 'xref':
        xref = int(value.split()[0])
        appearance = doc.xref_stream(xref)
        appearance = re.sub(rb'(?<![\w.])(?:\d+(?:\.\d*)?|\.\d+) w\b',
                            str(width).encode('ascii') + b' w', appearance)
        doc.update_stream(xref, appearance)


def add_reading_annotations(doc, annotations):
    for item in annotations:
        page = doc[item['page']]
        kind = item['type']
        if kind in ('highlight', 'underline'):
            method = page.add_highlight_annot if kind == 'highlight' else page.add_underline_annot
            annot = method([fitz.Rect(r).quad for r in item['rects']])
        elif kind == 'ink':
            points = item['points']
            if len(points) == 1:
                points = points + [[points[0][0] + .1, points[0][1]]]
            annot = page.add_ink_annot([points])
        elif kind == 'rect':
            annot = page.add_rect_annot(fitz.Rect(item['rect']))
        elif kind == 'note':
            annot = page.add_text_annot(fitz.Point(item['rect'][:2]), item['text'], icon='Comment')
        else:
            raise ValueError('不支持的批注类型：' + kind)
        annot.set_colors(stroke=color_rgb(item['color']))
        annot.set_info(content=item.get('text', ''), title='XT MoCiPDF')
        if kind in ('ink', 'rect'):
            annot.set_border(width=item['width'])
        annot.set_opacity(.35 if kind == 'highlight' else 1)
        annot.update()
        if kind == 'underline':
            set_underline_width(annot, item['width'])


def export_annotated_pdf(source, destination, marks, annotations, password=''):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('不能覆盖原 PDF，请选择另一个位置。')
    if destination.exists() and destination.stat().st_size == source.stat().st_size:
        if hashlib.sha256(destination.read_bytes()).digest() == hashlib.sha256(source.read_bytes()).digest():
            raise ValueError('不能覆盖原 PDF 的相同副本，请另选保存位置。')
    fd, temporary = tempfile.mkstemp(prefix='.xt-annotations-', suffix='.pdf', dir=destination.parent)
    os.close(fd)
    try:
        with fitz.open(source) as doc:
            if doc.needs_pass and not doc.authenticate(password):
                raise ValueError('PDF 密码无效。')
            add_collected_style(doc, marks)
            add_reading_annotations(doc, annotations)
            doc.save(temporary, garbage=4, deflate=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
