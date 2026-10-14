"""Local reading annotations, distinct from vocabulary collection."""
import hashlib
import math
import os
import re
import html
from functools import lru_cache
import tempfile
from pathlib import Path

import pymupdf as fitz
from branding import PROJECT_NAME

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


def note_html(text):
    return html.escape(text).replace('\n', '<br>')


def note_style(fontsize):
    return f'font-family:sans-serif; font-size:{fontsize}pt; line-height:1.35; color:#233a41;'


@lru_cache(maxsize=256)
def _note_geometry(text, anchor, bounds, preferred):
    page = fitz.Rect(bounds)
    margin = min(6, page.width / 10, page.height / 10)
    max_width, max_height = page.width - margin * 2, page.height - margin * 2
    width = min(240, max_width)
    height = 32
    fontsize = preferred
    # Widen a long note before reducing type size. Full content remains in the
    # standard PDF annotation even in exceptionally large notes.
    for fontsize in (preferred, 10, 9, 8, 7, 6, 5):
        for width in (min(240, max_width), max_width):
            story = fitz.Story(html=note_html(text), user_css='body { margin:6pt; ' + note_style(fontsize) + ' }')
            more, filled = story.place(fitz.Rect(0, 0, width, max_height))
            height = min(max_height, max(32, math.ceil(filled[3]) + 6))
            if not more:
                break
        if not more:
            break
    x = max(page.x0 + margin, min(anchor[0], page.x1 - margin - width))
    y = max(page.y0 + margin, min(anchor[1], page.y1 - margin - height))
    return (x, y, x + width, y + height), fontsize


def note_layout(item, page_rect):
    bounds, fontsize = _note_geometry(item['text'], tuple(item['rect']), tuple(page_rect), item.get('fontsize', 11))
    return fitz.Rect(bounds), fontsize


def add_visible_note(page, item, rect=None, fontsize=None):
    if rect is None:
        rect, fontsize = note_layout(item, fitz.Rect(0, 0, page.cropbox.width, page.cropbox.height))
    color = color_rgb(item['color'])
    fill = tuple(.92 + component * .08 for component in color)
    annot = page.add_freetext_annot(rect, note_html(item['text']), fontsize=fontsize, richtext=True,
        style=note_style(fontsize), fill_color=fill, border_color=color, border_width=.8)
    annot.set_info(content=item['text'], title=PROJECT_NAME)
    # Regenerate after changing Contents: this removes the HTML wrapper's
    # leading whitespace and preserves all plain-text lines and embedded fonts.
    annot.update(fontsize=fontsize, text_color=(.137, .227, .255))
    return annot


def render_note(item, page_rect, scale):
    rect, fontsize = note_layout(item, page_rect)
    with fitz.open() as doc:
        page = doc.new_page(width=rect.width, height=rect.height)
        add_visible_note(page, item, fitz.Rect(0, 0, rect.width, rect.height), fontsize)
        return rect, page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)


def annotation_at(annotations, point, tolerance=5, page_rect=None):
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
            rect = note_layout(item, page_rect)[0] if page_rect is not None else fitz.Rect(item['rect'])
            if rect.contains(point):
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
            annot.set_info(content=mark.get('term', ''), subject='已收录词条', title=PROJECT_NAME)
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
            add_visible_note(page, item)
            continue
        else:
            raise ValueError('不支持的批注类型：' + kind)
        annot.set_colors(stroke=color_rgb(item['color']))
        annot.set_info(content=item.get('text', ''), title=PROJECT_NAME)
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
