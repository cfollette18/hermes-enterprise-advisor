"""Check snapshot integrity and its binding to the native Hermes prompt."""
import hashlib
import json
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parent


def validate_pack(bundle, lock):
    if bundle.get('schema_version') != 1 or bundle.get('framework_id') != 'production-ai-framework':
        raise ValueError('Unsupported framework bundle')
    if lock.get('schema_version') != 1 or not re.fullmatch(r'[0-9a-f]{40}', lock.get('commit', '')):
        raise ValueError('Invalid framework revision')
    if lock.get('repository') != 'https://github.com/cfollette18/production-ai-framework':
        raise ValueError('Unexpected framework repository')
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
    return ids


def system_prompt(root, bundle):
    pack = {row['id']: row for row in bundle['records']}
    return ((root / 'policy.md').read_text(encoding='utf-8') + '\nADVISORY SKILL\n'
            + (root / 'skills/enterprise-advisory/SKILL.md').read_text(encoding='utf-8')
            + '\nKNOWLEDGE PACK\n' + json.dumps(pack))


def validate(root=ROOT, quiet=False):
    bundle = json.loads((root / 'knowledge-pack.json').read_text(encoding='utf-8'))
    lock = json.loads((root / 'framework-lock.json').read_text(encoding='utf-8'))
    ids = validate_pack(bundle, lock)
    config = yaml.safe_load((root / 'config.yaml').read_text(encoding='utf-8'))
    agent = config.get('agent', {})
    if agent.get('system_prompt') != system_prompt(root, bundle):
        raise ValueError('Runtime prompt differs from policy, skill, or knowledge snapshot')
    if config.get('platform_toolsets') != {'cli': []} or config.get('mcp_servers') != {}:
        raise ValueError('Advisor must have no enabled toolsets or MCP servers')
    if config.get('memory') != {'memory_enabled': False, 'user_profile_enabled': False}:
        raise ValueError('Unexpected persistent memory configuration')
    if agent.get('max_turns') != 4 or not agent.get('disabled_toolsets'):
        raise ValueError('Missing advisor capability restrictions')
    if not quiet:
        print(f'Validated {len(ids)} framework records and native prompt at {lock["commit"]}')
    return bundle, lock


if __name__ == '__main__':
    validate()
