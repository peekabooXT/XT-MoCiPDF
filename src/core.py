"""Local document library and cloud vocabulary export."""

from i18n import tr
import hashlib
import json
import re
import shutil
import uuid
import unicodedata
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path


def clean_term(text):
    text = unicodedata.normalize('NFKC', text)
    text = text.replace('\u00ad', '').replace('’', "'").replace('–', '-').replace('—', '-')
    text = re.sub(r'(?<=[A-Za-z])-\s*\n\s*(?=[a-z])', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.strip(' \t\r\n.,;:!?()[]{}<>"“”‘’/\\|•')


def validate_term(text):
    term = clean_term(text)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 '\-./&+]*", term) or not re.search('[A-Za-z]', term):
        raise ValueError(tr('请输入英文单词或词组；不要包含中文、换行或 #。'))
    if len(term) > 240:
        raise ValueError(tr('选中的内容过长，请只选择需要记忆的单词或词组。'))
    return term


def export_body(record, mode='chapter', lower=False, dedupe=True):
    marks = sorted(record['marks'], key=lambda m: (m['page'], m.get('order', 0), m['created']))
    seen, groups, terms = set(), {}, []
    for mark in marks:
        term = mark['term'].lower() if lower else mark['term']
        if dedupe and term in seen:
            continue
        seen.add(term)
        terms.append(term)
        groups.setdefault(mark['page'], []).append(term)
    if not terms:
        return ''
    title = re.sub(r'[\r\n#]', ' ', record['title']).strip() or tr('我的 PDF 词本')
    if mode == 'pages':
        return '\n'.join(tr('#{arg0} · 第 {arg1} 页\n', arg0=title, arg1=page + 1) + '\n'.join(ts) for page, ts in groups.items()) + '\n'
    prefix = f'#{title}\n' if mode == 'chapter' else '//\n' if mode == 'lemma' else ''
    return prefix + '\n'.join(terms) + '\n'


def merged_record(records, title=tr('合并词本'), lower=False):
    """Copy marks in document/read order; never change library records."""
    marks = []
    for index, record in enumerate(records):
        ordered = sorted(record['marks'], key=lambda m: (m['page'], m.get('order', 0), m['created']))
        for order, mark in enumerate(ordered):
            marks.append(dict(mark, id=record['id'] + ':' + mark['id'], page=index,
                              order=order, term=mark['term'].lower() if lower else mark['term']))
    return {'id': 'merged', 'title': title.strip() or tr('合并词本'), 'marks': marks,
            'source_ids': [record['id'] for record in records]}


def export_merged_body(records, title=tr('合并词本'), mode='documents', lower=False, dedupe=True):
    if mode not in ('documents', 'pages', 'chapter', 'plain', 'lemma'):
        raise ValueError(tr('不支持的词本格式。'))
    if mode not in ('documents', 'pages'):
        return export_body(merged_record(records, title, lower), mode, dedupe=dedupe)
    seen, chapters = set(), []
    for record in records:
        marks = []
        for mark in sorted(record['marks'], key=lambda m: (m['page'], m.get('order', 0), m['created'])):
            term = mark['term'].lower() if lower else mark['term']
            if dedupe and term in seen:
                continue
            seen.add(term)
            marks.append(dict(mark, term=term))
        text = export_body(dict(record, marks=marks), 'chapter' if mode == 'documents' else 'pages', dedupe=False)
        if text:
            chapters.append(text)
    return ''.join(chapters)


def protect_export_path(path, data_root, source_ids):
    path = Path(path)
    if path.resolve().is_relative_to(Path(data_root).resolve()):
        raise ValueError(tr('请选择文档数据目录以外的位置，不能覆盖原 PDF 或词库。'))
    if path.exists():
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() in source_ids:
                raise ValueError(tr('该文件是原 PDF，请使用新的文件名保存。'))


def write_export_text(path, body):
    """A failed text export leaves an existing target intact."""
    path = Path(path)
    handle, temporary = tempfile.mkstemp(prefix='.xt-wordbook-', suffix='.txt', dir=path.parent)
    try:
        with os.fdopen(handle, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(body)
        os.replace(temporary, path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


class Library:
    def __init__(self, root):
        self.root = Path(root)
        (self.root / 'pdfs').mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'library.json'
        self.warning = ''
        self.state = {'version': 1, 'documents': [], 'last': None}
        if self.path.exists():
            try:
                self.state = json.loads(self.path.read_text(encoding='utf-8'))
                if self.state.get('version') != 1 or not isinstance(self.state.get('documents'), list):
                    raise ValueError(tr('词库格式不正确'))
            except (ValueError, OSError) as exc:
                backup = self.path.with_suffix('.backup.json')
                if not backup.exists():
                    raise RuntimeError(tr('词库读取失败，请保留 data 文件夹后联系修复：{arg0}', arg0=exc)) from exc
                self.state = json.loads(backup.read_text(encoding='utf-8'))
                self.warning = tr('主词库读取失败，已恢复最近一次备份。请检查标记。')

    def save(self):
        tmp = self.path.with_suffix('.tmp')
        for attempt in range(5):
            try:
                tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding='utf-8')
                if self.path.exists() and not self.warning:
                    shutil.copy2(self.path, self.path.with_suffix('.backup.json'))
                tmp.replace(self.path)
                break
            except PermissionError as exc:
                # Windows file scanners can briefly hold a just-written JSON
                # file. Persistent permission failures still reach UI rollback.
                if getattr(exc, 'winerror', None) not in (5, 32, 33) or attempt == 4:
                    raise
                time.sleep(.03 * 2 ** attempt)
        self.warning = ''

    def import_pdf(self, source):
        with open(source, 'rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        existing = next((d for d in self.state['documents'] if d['id'] == digest), None)
        if existing:
            return existing
        target = self.root / 'pdfs' / f'{digest}.pdf'
        shutil.copy2(source, target)
        record = {'id': digest, 'title': Path(source).stem, 'marks': [], 'page': 0, 'ocr': {}}
        self.state['documents'].append(record)
        try:
            self.save()
        except OSError:
            self.state['documents'].remove(record)
            raise
        return record

    def pdf_path(self, record):
        return self.root / 'pdfs' / (record['id'] + '.pdf')

    def add_mark(self, record, term, page, rects=None, order=0):
        term = validate_term(term)
        rects = rects or []
        same = next((m for m in record['marks'] if m['term'] == term and m['page'] == page and m['rects'] == rects), None)
        if same:
            return same, False
        mark = {'id': uuid.uuid4().hex, 'term': term, 'page': page, 'rects': rects, 'order': order,
                'created': datetime.now().isoformat(timespec='microseconds')}
        record['marks'].append(mark)
        try:
            self.save()
        except OSError:
            record['marks'].remove(mark)
            raise
        return mark, True
