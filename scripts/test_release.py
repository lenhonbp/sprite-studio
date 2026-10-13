"""Negative/roundtrip tests for the archive mechanism; full skill audit runs separately."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('packaging_under_test', Path(__file__).with_name('package-release.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from verify_release import verify


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        self.root.mkdir()
        for name in module.ALLOWLIST:
            p = self.root / name
            if '.' in p.name or p.name in {'README.md', 'AGENTS.md'}:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('fixture\n')
            else:
                p.mkdir(parents=True, exist_ok=True)
        (self.root / 'package.json').write_text(json.dumps({'version': '4.1.1'}))
        (self.root / 'scripts/audit-bundle.py').write_text('# Unit fixture only; full bundle audit is separate.\n')
        (self.root / 'skills/produce-game-sprites').mkdir()
        (self.root / 'skills/produce-game-sprites/SKILL.md').write_text('fixture skill')
        (self.root / 'local/server.mjs').write_text('fixture server')
        self.out = self.base / 'release.zip'

    def test_no_git_and_deterministic_archive(self):
        result = module.package(self.root, self.out)
        self.assertEqual(result['status'], 'passed')
        second = self.base / 'second.zip'
        module.package(self.root, second)
        self.assertEqual(self.out.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(self.out) as z:
            m = json.loads(z.read('Nhon-Le-Sprite-Studio-v4.1.1/release.json'))
            self.assertIsNone(m['source_commit'])
            self.assertIsNone(m['source_git_dirty'])

    def test_refuses_overwrite(self):
        self.out.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            module.package(self.root, self.out)
        self.assertEqual(self.out.read_bytes(), b'keep')

    def test_symlink_and_private_files_are_rejected(self):
        for name in ['outside.mjs', '.env.production', 'secret.pem']:
            p = self.root / 'scripts' / name
            if name == 'outside.mjs':
                p.symlink_to(self.root / 'package.json')
            else:
                p.write_text('do not ship')
            with self.assertRaises(ValueError):
                module.package(self.root, self.out)
            self.assertFalse(self.out.exists())
            self.assertEqual(list(self.base.glob('.studio-release-*')), [])
            p.unlink()

    def test_failure_keeps_destination_absent_and_removes_temp(self):
        # Missing mandatory member fails after archive assembly, before atomic publish.
        (self.root / 'local/server.mjs').unlink()
        with self.assertRaises(ValueError):
            module.package(self.root, self.out)
        self.assertFalse(self.out.exists())
        self.assertEqual(list(self.base.glob('.studio-release-*')), [])

    def corrupted(self, mode):
        module.package(self.root, self.out)
        bad = self.base / 'bad.zip'
        with zipfile.ZipFile(self.out) as source, zipfile.ZipFile(bad, 'w') as target:
            for n in source.namelist():
                data = source.read(n)
                if mode == 'changed' and n.endswith('/package.json'):
                    data += b' '
                if mode == 'missing' and n.endswith('/package.json'):
                    continue
                target.writestr(n, data)
            if mode == 'extra':
                target.writestr('Nhon-Le-Sprite-Studio-v4.1.1/extra.txt', 'extra')
            if mode == 'escape':
                target.writestr('Nhon-Le-Sprite-Studio-v4.1.1/../escape', 'bad')
        return bad

    def test_changed_archive_bytes_fail(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            verify(self.corrupted('changed'))

    def test_missing_extra_and_traversal_members_fail(self):
        for mode in ['missing', 'extra', 'escape']:
            with self.assertRaises(ValueError):
                verify(self.corrupted(mode))
            self.out.unlink()


if __name__ == '__main__':
    unittest.main()
