"""Build the redistributable offline database from ECDICT's MIT CSV."""
import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path

from dictionary import normalize


def build(source, target):
    source, target = Path(source), Path(target)
    target.mkdir(parents=True, exist_ok=True)
    database = target / 'ecdict.sqlite'
    if database.exists():
        raise FileExistsError(f'Already exists: {database}')
    conn = sqlite3.connect(database)
    conn.executescript('''
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        CREATE TABLE entries(word TEXT PRIMARY KEY, norm TEXT, phonetic TEXT,
            translation TEXT, definition TEXT, exchange TEXT, tag TEXT);
        CREATE TABLE forms(form TEXT, base TEXT, kind TEXT,
            PRIMARY KEY(form, base, kind)) WITHOUT ROWID;
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT);
    ''')
    count = 0
    chinese = 0
    with source.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            word = row['word'].strip()
            if not word:
                continue
            norm = normalize(word)
            values = (word, norm, row['phonetic'], row['translation'],
                      row['definition'], row['exchange'], row['tag'])
            inserted = conn.execute('INSERT OR IGNORE INTO entries VALUES(?,?,?,?,?,?,?)', values).rowcount
            count += inserted
            chinese += inserted * bool(row['translation'].strip())
            for field in row['exchange'].split('/'):
                kind, sep, form = field.partition(':')
                if not sep or not form.strip():
                    continue
                if kind in ('p', 'd', 'i', '3', 'r', 't', 's'):
                    conn.execute('INSERT OR IGNORE INTO forms VALUES(?,?,?)', (normalize(form), norm, kind))
                elif kind == '0' and normalize(form) != norm:
                    conn.execute('INSERT OR IGNORE INTO forms VALUES(?,?,?)', (norm, normalize(form), '0'))
            if count % 10000 == 0:
                conn.commit()
    conn.execute('CREATE INDEX entries_norm ON entries(norm)')
    provenance = json.loads(source.with_name('source.json').read_text(encoding='utf-8-sig'))
    provenance.update(entries=count, chinese_entries=chinese,
                      csv_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      license='MIT', format_version=1,
                      forms_source='ECDICT exchange field')
    conn.executemany('INSERT INTO metadata VALUES(?,?)',
                     [(key, str(value)) for key, value in provenance.items()])
    conn.commit()
    conn.execute('ANALYZE')
    conn.close()
    (target / 'source.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf-8')
    (target / 'LICENSE.txt').write_bytes(source.with_name('LICENSE').read_bytes())
    print(json.dumps(provenance, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csv')
    parser.add_argument('output_folder')
    args = parser.parse_args()
    build(args.csv, args.output_folder)
