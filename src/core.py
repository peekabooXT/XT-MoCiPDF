"""Local document library and Momo cloud-book export."""
import hashlib
import json
import re
import shutil
import uuid
import unicodedata
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
        raise ValueError('请输入英文单词或词组；不要包含中文、换行或 #。')
    if len(term) > 240:
        raise ValueError('选中的内容过长，请只选择需要记忆的单词或词组。')
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
    title = re.sub(r'[\r\n#]', ' ', record['title']).strip() or '我的 PDF 词本'
    if mode == 'pages':
        return '\n'.join(f'#{title} · 第 {page + 1} 页\n' + '\n'.join(ts) for page, ts in groups.items()) + '\n'
    prefix = f'#{title}\n' if mode == 'chapter' else '//\n' if mode == 'lemma' else ''
    return prefix + '\n'.join(terms) + '\n'


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
                    raise ValueError('词库格式不正确')
            except (ValueError, OSError) as exc:
                backup = self.path.with_suffix('.backup.json')
                if not backup.exists():
                    raise RuntimeError(f'词库读取失败，请保留 data 文件夹后联系修复：{exc}') from exc
                self.state = json.loads(backup.read_text(encoding='utf-8'))
                self.warning = '主词库读取失败，已恢复最近一次备份。请检查标记。'

    def save(self):
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding='utf-8')
        if self.path.exists() and not self.warning:
            shutil.copy2(self.path, self.path.with_suffix('.backup.json'))
        tmp.replace(self.path)
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
