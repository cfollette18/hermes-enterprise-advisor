"""Refresh the native Hermes profile from versioned knowledge. No server."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ADVISOR_KNOWLEDGE_ROOT", str(PACKAGE.parent / "production-ai-framework")))
PROFILE = Path.home() / '.hermes/profiles/enterprise-advisor'


def knowledge_pack():
    """Consume the framework's public contract; do not maintain a second parser."""
    obj = json.loads((ROOT / 'dist/knowledge.json').read_text(encoding='utf-8'))
    if obj.get('schema_version') != 1 or obj.get('framework_id') != 'production-ai-framework':
        raise ValueError('Unsupported framework bundle')
    canonical = json.dumps(obj['records'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    if hashlib.sha256(canonical.encode()).hexdigest() != obj['content_sha256']:
        raise ValueError('Framework bundle hash mismatch')
    records = {}
    for record in obj['records']:
        if record['id'] in records or hashlib.sha256(record['text'].encode()).hexdigest() != record['sha256']:
            raise ValueError('Invalid framework record')
        records[record['id']] = record
    if obj['entrypoint_id'] not in records:
        raise ValueError('Missing framework entrypoint')
    return obj, records


def install():
    import yaml
    sys.path.insert(0, os.environ.get('ADVISOR_HERMES_REPO', str(Path.home() / '.hermes/hermes-agent')))
    from toolsets import TOOLSETS
    if not (PROFILE / 'config.yaml').is_file():
        raise SystemExit('First run: hermes profile create enterprise-advisor --no-skills')
    config = yaml.safe_load((PROFILE / 'config.yaml').read_text()) or {}
    bundle, pack = knowledge_pack()
    config['agent'] = {'max_turns': 4, 'disabled_toolsets': sorted(TOOLSETS),
        'system_prompt': (PACKAGE / 'policy.md').read_text() + '\nADVISORY SKILL\n' + (PACKAGE / 'skills/enterprise-advisory/SKILL.md').read_text() + '\nKNOWLEDGE PACK\n' + json.dumps(pack)}
    config['platform_toolsets'] = {'cli': []}
    config['mcp_servers'] = {}
    config['memory'] = {'memory_enabled': False, 'user_profile_enabled': False}
    config['display'] = {'interface': 'cli'}
    (PROFILE / 'config.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    (PROFILE / 'config.yaml').chmod(0o600)
    (PROFILE / 'SOUL.md').write_text('You are Enterprise Advisor. Follow the dedicated advisory policy and knowledge pack in agent.system_prompt. Reply conversationally with citations.\n')
    (PROFILE / 'knowledge-pack.json').write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + '\n')
    (PROFILE / '.no-bundled-skills').touch()
    shutil.copytree(PACKAGE / 'skills/enterprise-advisory', PROFILE / 'skills/enterprise-advisory', dirs_exist_ok=True)
    print(f'Installed native enterprise-advisor: {len(pack)} knowledge sections; zero enabled toolsets')


if __name__ == '__main__':
    install()
