"""Read-only base dictionary with a separate personal definition overlay."""
import html
import re
import sqlite3
import unicodedata
from functools import lru_cache
from pathlib import Path


def normalize(text):
    text = unicodedata.normalize('NFKC', text)
    text = text.translate(str.maketrans({'’': "'", '‘': "'", '‐': '-', '‑': '-', '–': '-'}))
    return ' '.join(text.split()).strip(' .,;:!?"“”()[]{}').casefold()


class OfflineDictionary:
    def __init__(self, path, overrides=None):
        self.conn = None
        self.overrides = dict(overrides or {})
        self.error = ''
        self.count = 0
        try:
            self.conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
            self.conn.row_factory = sqlite3.Row
            self.count = int(self.conn.execute("SELECT value FROM metadata WHERE key='entries'").fetchone()[0])
            self.conn.execute('SELECT word, norm, phonetic, translation, definition, exchange, tag FROM entries LIMIT 1')
            self.conn.execute('SELECT form, base, kind FROM forms LIMIT 1')
        except (sqlite3.Error, OSError, TypeError, ValueError):
            if self.conn:
                self.conn.close()
            self.conn = None
            self.error = '离线词典无法读取，请恢复软件目录中的 dictionary 文件夹。选词和导出仍可使用。'

    @property
    def ready(self):
        return self.conn is not None or bool(self.overrides)

    def set_overrides(self, entries):
        self.overrides = dict(entries)
        self.lookup.cache_clear()

    def personal_entry(self, text):
        saved = self.overrides.get(normalize(text))
        if not saved:
            return None
        return {'word': saved['word'], 'translation': saved['translation'],
                'phonetic': saved.get('phonetic', ''), 'definition': '',
                'exchange': '', 'tag': '', 'custom': True}

    def entry(self, text):
        personal = self.personal_entry(text)
        if personal:
            return personal
        if self.conn is None:
            return None
        row = self.conn.execute('SELECT * FROM entries WHERE word=?', (text,)).fetchone()
        if row is None:
            row = self.conn.execute('SELECT * FROM entries WHERE norm=? ORDER BY word=? DESC, length(word), word LIMIT 1',
                                    (normalize(text), normalize(text))).fetchone()
        return dict(row) if row else None

    def word(self, text):
        norm = normalize(text)
        entry = self.entry(text)
        if (entry or {}).get('custom') or self.conn is None:
            return {'query': text, 'entry': entry, 'bases': []}
        forms = self.conn.execute("SELECT DISTINCT base FROM forms WHERE form=? AND base<>? ORDER BY kind='0' DESC, base LIMIT 3",
                                  (norm, norm)).fetchall()
        bases = []
        for row in forms:
            base = self.entry(row['base'])
            if base and base['word'] != (entry or {}).get('word'):
                bases.append(base)
        return {'query': text, 'entry': entry, 'bases': bases}

    @lru_cache(maxsize=512)
    def lookup(self, text):
        text = ' '.join(unicodedata.normalize('NFKC', text).split()).strip(' .,;:!?"“”()[]{}')
        if not self.ready:
            return {'query': text, 'error': self.error}
        if not text:
            return {'query': '', 'error': '选中 PDF 单词即可查看释义，也可以输入单词或词组查词。'}
        if len(text) > 240:
            return {'query': text[:240], 'error': '内容较长，请选择一个单词或较短的词组。'}
        if self.conn is None and not self.personal_entry(text):
            return {'query': text, 'error': self.error}
        try:
            result = self.word(text)
            if result['entry'] or result['bases']:
                return result
            tokens = re.findall(r"[a-zA-Z]+(?:['’-][a-zA-Z]+)*", text)
            if len(tokens) > 1:
                return {'query': text, 'parts': [self.word(t) for t in dict.fromkeys(tokens[:12])],
                        'truncated': len(tokens) > 12}
            return result
        except sqlite3.Error:
            return {'query': text, 'error': '词典查询失败，请恢复 dictionary 文件夹后重新打开软件。'}

    def close(self):
        self.lookup.cache_clear()
        if self.conn:
            self.conn.close()
            self.conn = None


def render_lookup(result):
    def escaped(text):
        return html.escape(str(text)).replace('\\n', '<br>').replace('\n', '<br>')

    def entry_html(entry):
        meaning = entry['translation'] or entry['definition'] or '暂无释义'
        label = '' if entry['translation'] else '（英文释义）<br>'
        ipa = f" <span style='color:#71858b'>/{escaped(entry['phonetic'])}/</span>" if entry['phonetic'] else ''
        badge = '<br><span style="color:#087f73">个人释义 · 已保存</span>' if entry.get('custom') else ''
        return f"<p><b>{escaped(entry['word'])}</b>{ipa}{badge}<br>{label}{escaped(meaning)}</p>"

    def word_html(item):
        output = entry_html(item['entry']) if item['entry'] else ''
        if item['bases']:
            output += '<p style="color:#087f73">词形参考（需结合上下文）</p>'
            output += ''.join(entry_html(base) for base in item['bases'])
        if not output:
            output = '<p><b>' + escaped(item['query']) + '</b><br>词典未收录，可修正拼写后查词。</p>'
        return output

    if result.get('error'):
        body = '<p>' + escaped(result['error']) + '</p>'
    elif 'parts' in result:
        body = '<p><b>' + escaped(result['query']) + '</b></p>'
        body += '<p style="color:#71858b">未收录完整词组，以下为逐词释义。</p>'
        body += ''.join(word_html(part) for part in result['parts'])
        if result.get('truncated'):
            body += '<p>仅显示前 12 个词，请缩短选词范围。</p>'
    else:
        body = word_html(result)
    return '<html><body style="font-family:Microsoft YaHei;font-size:13px;">' + body + '</body></html>'
