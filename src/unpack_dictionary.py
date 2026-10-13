"""Unpack the repository's bundled ECDICT database without network access."""
import gzip
import hashlib
import json
import os
import tempfile
from pathlib import Path


def unpack(folder):
    folder = Path(folder)
    target = folder / 'ecdict.sqlite'
    if target.exists():
        return target
    archive = folder / 'ecdict.sqlite.gz'
    metadata = json.loads((folder / 'source.json').read_text(encoding='utf-8-sig'))
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != metadata['sqlite_gzip_sha256']:
            raise ValueError('Bundled dictionary archive checksum mismatch')
    handle, temporary = tempfile.mkstemp(prefix='.dictionary-', suffix='.tmp', dir=folder)
    try:
        digest = hashlib.sha256()
        with os.fdopen(handle, 'wb') as output, gzip.open(archive, 'rb') as source:
            while chunk := source.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
        if digest.hexdigest() != metadata['sqlite_sha256']:
            raise ValueError('Unpacked dictionary checksum mismatch')
        os.replace(temporary, target)
        temporary = None
        return target
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)


if __name__ == '__main__':
    print(unpack(Path(__file__).resolve().parents[1] / 'dictionary'))
