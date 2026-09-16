"""Verify the packaged framework snapshot against its declared content hashes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def validate():
    bundle = json.loads((ROOT / 'knowledge-pack.json').read_text())
    lock = json.loads((ROOT / 'framework-lock.json').read_text())
    canonical = json.dumps(bundle['records'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    if digest != bundle['content_sha256'] or digest != lock['content_sha256']:
        raise ValueError('Snapshot does not match framework lock')
    ids = set()
    for row in bundle['records']:
        if row['id'] in ids or hashlib.sha256(row['text'].encode()).hexdigest() != row['sha256']:
            raise ValueError('Duplicate or corrupted record')
        ids.add(row['id'])
    if bundle['entrypoint_id'] not in ids:
        raise ValueError('Missing entrypoint')
    print(f'Validated {len(ids)} framework records at {lock["commit"]}')


if __name__ == '__main__':
    validate()
