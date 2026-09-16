import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import types
import unittest
from unittest.mock import patch

import yaml

import refresh_profile
from validate_bundle import ROOT, validate


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'package'
        self.profile = Path(self.temp.name) / 'profile'
        self.root.mkdir()
        self.profile.mkdir()
        for name in ('config.yaml', 'knowledge-pack.json', 'framework-lock.json', 'policy.md', 'SOUL.md'):
            shutil.copy2(ROOT / name, self.root / name)
        shutil.copytree(ROOT / 'skills', self.root / 'skills')

    def tearDown(self):
        self.temp.cleanup()

    def mutate_config(self, change):
        path = self.root / 'config.yaml'
        config = yaml.safe_load(path.read_text())
        change(config)
        path.write_text(yaml.safe_dump(config))

    def test_packaged_prompt_matches_snapshot(self):
        validate(self.root, quiet=True)

    def test_stale_runtime_prompt_rejected(self):
        self.mutate_config(lambda c: c['agent'].update(system_prompt='old knowledge'))
        with self.assertRaisesRegex(ValueError, 'Runtime prompt'):
            validate(self.root, quiet=True)

    def test_enabled_terminal_rejected(self):
        self.mutate_config(lambda c: c.update(platform_toolsets={'cli': ['terminal']}))
        with self.assertRaisesRegex(ValueError, 'enabled toolsets'):
            validate(self.root, quiet=True)

    def test_mcp_and_memory_rejected(self):
        self.mutate_config(lambda c: c.update(mcp_servers={'unexpected': {'command': 'server'}}))
        with self.assertRaises(ValueError):
            validate(self.root, quiet=True)
        self.mutate_config(lambda c: c.update(mcp_servers={}, memory={'memory_enabled': True}))
        with self.assertRaises(ValueError):
            validate(self.root, quiet=True)

    def test_corrupted_snapshot_rejected(self):
        path = self.root / 'knowledge-pack.json'
        bundle = json.loads(path.read_text())
        bundle['records'][0]['text'] += '\nUnreviewed change'
        path.write_text(json.dumps(bundle))
        with self.assertRaises(ValueError):
            validate(self.root, quiet=True)

    def run_install(self):
        fake_tools = types.SimpleNamespace(TOOLSETS={'terminal': {}, 'web': {}, 'new-tool': {}})
        with patch.object(refresh_profile, 'PACKAGE', self.root), patch.object(refresh_profile, 'PROFILE', self.profile), patch.dict('sys.modules', {'toolsets': fake_tools}), contextlib.redirect_stdout(io.StringIO()):
            refresh_profile.install()

    def test_refresh_preserves_private_settings_and_updates_runtime(self):
        model = {'default': 'private-model', 'api_key': 'synthetic-test-value'}
        (self.profile / 'config.yaml').write_text(yaml.safe_dump({'model': model, 'agent': {'system_prompt': 'stale'}}))
        (self.profile / '.env').write_text('SYNTHETIC_SECRET=unchanged\n')
        (self.profile / 'sessions').mkdir()
        (self.profile / 'sessions/test').write_text('preserved')
        self.run_install()
        validate(self.profile, quiet=True)
        config = yaml.safe_load((self.profile / 'config.yaml').read_text())
        self.assertEqual(model, config['model'])
        self.assertIn('new-tool', config['agent']['disabled_toolsets'])
        self.assertEqual((self.profile / '.env').read_text(), 'SYNTHETIC_SECRET=unchanged\n')
        self.assertEqual((self.profile / 'sessions/test').read_text(), 'preserved')
        self.assertEqual((self.profile / 'config.yaml').stat().st_mode & 0o777, 0o600)
        self.assertNotIn('synthetic-test-value', (self.root / 'config.yaml').read_text())

    def test_failed_validation_keeps_installed_config(self):
        path = self.profile / 'config.yaml'
        path.write_text('old: config\n')
        (self.root / 'policy.md').write_text('changed without rebuilding prompt')
        with self.assertRaises(ValueError):
            self.run_install()
        self.assertEqual(path.read_text(), 'old: config\n')


if __name__ == '__main__':
    unittest.main()
