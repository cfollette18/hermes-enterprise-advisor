"""Build a pinned distribution, or install its validated snapshot into Hermes."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml

from validate_bundle import system_prompt, validate, validate_pack

PACKAGE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('ADVISOR_KNOWLEDGE_ROOT', str(PACKAGE.parent / 'production-ai-framework')))
PROFILE = Path(os.environ.get('ADVISOR_PROFILE_ROOT', str(Path.home() / '.hermes/profiles/enterprise-advisor')))


def atomic_write(path, text, mode=0o644):
    """Never expose a partially written native config to a new Hermes process."""
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def json_text(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def configure(config, bundle, disabled):
    config['agent'] = {'max_turns': 4, 'disabled_toolsets': sorted(disabled),
                       'system_prompt': system_prompt(PACKAGE, bundle)}
    config['platform_toolsets'] = {'cli': []}
    config['mcp_servers'] = {}
    config['memory'] = {'memory_enabled': False, 'user_profile_enabled': False}
    config['display'] = {'interface': 'cli'}
    return config


def package_snapshot():
    """Only publish an exported, committed framework; never copy private config."""
    def git(*args):
        return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()
    revision = git('rev-parse', 'HEAD')
    if git('status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Commit the reviewed framework and exports before packaging')
    for command in ('validate', 'check-export'):
        subprocess.run([sys.executable, str(ROOT / 'scripts/knowledge.py'), command], check=True)
    committed = subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':dist/knowledge.json'])
    if (ROOT / 'dist/knowledge.json').read_bytes() != committed:
        raise ValueError('Bundle differs from the pinned commit')
    bundle = json.loads(committed)
    lock = {'repository': 'https://github.com/cfollette18/production-ai-framework',
            'commit': revision, 'schema_version': 1, 'content_sha256': bundle['content_sha256']}
    validate_pack(bundle, lock)
    config = yaml.safe_load((PACKAGE / 'config.yaml').read_text(encoding='utf-8'))
    config = configure(config, bundle, config['agent']['disabled_toolsets'])
    atomic_write(PACKAGE / 'knowledge-pack.json', json_text(bundle))
    atomic_write(PACKAGE / 'framework-lock.json', json_text(lock))
    atomic_write(PACKAGE / 'config.yaml', yaml.safe_dump(config, sort_keys=False))
    validate(PACKAGE)


def install():
    # Validate every input before touching the installed profile.
    bundle, lock = validate(PACKAGE, quiet=True)
    sys.path.insert(0, os.environ.get('ADVISOR_HERMES_REPO', str(Path.home() / '.hermes/hermes-agent')))
    from toolsets import TOOLSETS
    if not (PROFILE / 'config.yaml').is_file():
        raise SystemExit('First run: hermes profile create enterprise-advisor --no-skills')
    config = yaml.safe_load((PROFILE / 'config.yaml').read_text(encoding='utf-8')) or {}
    config = configure(config, bundle, TOOLSETS)
    rendered = yaml.safe_dump(config, sort_keys=False)
    # Keep private model settings in place; never copy this config into the repo.
    atomic_write(PROFILE / 'SOUL.md', (PACKAGE / 'SOUL.md').read_text(encoding='utf-8'))
    atomic_write(PROFILE / 'policy.md', (PACKAGE / 'policy.md').read_text(encoding='utf-8'))
    atomic_write(PROFILE / 'knowledge-pack.json', json_text(bundle))
    atomic_write(PROFILE / 'framework-lock.json', json_text(lock))
    (PROFILE / '.no-bundled-skills').touch()
    shutil.copytree(PACKAGE / 'skills/enterprise-advisory', PROFILE / 'skills/enterprise-advisory', dirs_exist_ok=True)
    # Runtime authority is self-contained in this file; activate it last.
    atomic_write(PROFILE / 'config.yaml', rendered, mode=0o600)
    validate(PROFILE, quiet=True)
    print(f'Installed enterprise-advisor: {len(bundle["records"])} records at {lock["commit"]}; zero enabled toolsets. Start a new chat.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', action='store_true', help='Build distribution from a clean committed framework; does not install')
    args = parser.parse_args()
    if args.package:
        package_snapshot()
    else:
        install()
