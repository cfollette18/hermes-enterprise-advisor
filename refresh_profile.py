"""Refresh the native Hermes profile from versioned knowledge. No server."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ADVISOR_KNOWLEDGE_ROOT", str(PACKAGE.parent / "production-ai-framework")))
PROFILE = Path.home() / '.hermes/profiles/enterprise-advisor'


def knowledge_pack():
    records = {}
    paths = ['docs/source-notes.md', 'docs/operating-framework.md', 'docs/retrieval-and-reproducibility.md']
    paths += ['templates/' + name + '.json' for name in ('project', 'evaluation-case', 'trace', 'change', 'incident')]
    for path in paths:
        text = (ROOT / path).read_text()
        parts = re.split(r'(?=^## \d+\.)', text, flags=re.M) if path.endswith('operating-framework.md') else [text]
        for part in parts:
            records[f'K{len(records)+1:02d}'] = {'path': path, 'text': part, 'sha256': hashlib.sha256(part.encode()).hexdigest()}
    return records


def install():
    import yaml
    sys.path.insert(0, os.environ.get('ADVISOR_HERMES_REPO', str(Path.home() / '.hermes/hermes-agent')))
    from toolsets import TOOLSETS
    if not (PROFILE / 'config.yaml').is_file():
        raise SystemExit('First run: hermes profile create enterprise-advisor --no-skills')
    config = yaml.safe_load((PROFILE / 'config.yaml').read_text()) or {}
    pack = knowledge_pack()
    config['agent'] = {'max_turns': 4, 'disabled_toolsets': sorted(TOOLSETS),
        'system_prompt': (PACKAGE / 'policy.md').read_text() + '\nADVISORY SKILL\n' + (PACKAGE / 'skills/enterprise-advisory/SKILL.md').read_text() + '\nKNOWLEDGE PACK\n' + json.dumps(pack)}
    config['platform_toolsets'] = {'cli': []}
    config['mcp_servers'] = {}
    config['memory'] = {'memory_enabled': False, 'user_profile_enabled': False}
    config['display'] = {'interface': 'cli'}
    (PROFILE / 'config.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    (PROFILE / 'config.yaml').chmod(0o600)
    (PROFILE / 'SOUL.md').write_text('You are Enterprise Advisor. Follow the dedicated advisory policy and knowledge pack in agent.system_prompt. Reply conversationally with citations.\n')
    (PROFILE / 'knowledge-pack.json').write_text(json.dumps(pack, indent=2))
    (PROFILE / '.no-bundled-skills').touch()
    shutil.copytree(PACKAGE / 'skills/enterprise-advisory', PROFILE / 'skills/enterprise-advisory', dirs_exist_ok=True)
    print(f'Installed native enterprise-advisor: {len(pack)} knowledge sections; zero enabled toolsets')


if __name__ == '__main__':
    install()
