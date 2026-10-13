#!/usr/bin/env python3
"""Run deterministic processing regressions with synthetic fixtures, not art-quality tests."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

spec = importlib.util.spec_from_file_location('sprite_tools', Path(__file__).with_name('sprite_tools.py'))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for i in range(2):
            im = Image.new('RGBA', (16, 16))
            ImageDraw.Draw(im).rectangle((4 + i, 3, 10, 12), fill=(120, 80, 50, 255))
            im.save(self.root / f'{i}.png')
        self.m = {'schema_version': 1, 'asset_id': 'fixture', 'representation': 'pixel',
                  'cell_size': [16, 16], 'origin': [8, 13], 'alpha_required': True,
                  'required_clips': ['test_south'], 'max_texture_size': 128, 'gutter': 2,
                  'clips': [{'name': 'test_south', 'action': 'test', 'direction': 'south', 'loop': False,
                             'events': [{'name': 'impact', 'time_ms': 100}],
                             'frames': [{'id': f'f{i}', 'path': f'{i}.png', 'duration_ms': 100 + 50 * i} for i in range(2)]}]}
        self.manifest = self.root / 'set.json'
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.manifest.write_text(json.dumps(self.m))

    def review(self):
        evidence = self.root / 'evidence.txt'
        evidence.write_text('Synthetic assertion only, for gate mechanics testing. Not art approval.')
        review = {'schema_version': 2, 'evidence_files': {'evidence.txt': s.file_hash(evidence)}, 'binding': s.inspect(self.m, self.root)['binding'], 'reviewer': 'synthetic-test',
                  'clips': {'test_south': {k: {'verdict': 'pass', 'observation': 'Synthetic gate fixture', 'evidence': ['evidence.txt']} for k in s.CHECKS}}}
        p = self.root / 'review.json'; p.write_text(json.dumps(review)); return p

    def test_repair_preserves_untouched_frames_and_rejects_spillover(self):
        import shutil
        other = self.root / 'after'; other.mkdir()
        for name in ('0.png', '1.png', 'set.json'):
            shutil.copy2(self.root / name, other / name)
        im = Image.open(other / '0.png').convert('RGBA')
        im.putpixel((5, 5), (10, 20, 30, 255)); im.save(other / '0.png')
        report = s.repair_diff(self.manifest, other / 'set.json', ['f0'])
        self.assertEqual(report['status'], 'scope_pass')
        self.assertEqual(report['changed_frames'], ['f0'])
        self.assertEqual(report['unchanged_frames'], ['f1'])
        self.assertEqual(report['art_approval'], 'not_evaluated')
        im.save(other / '1.png')
        self.assertEqual(s.repair_diff(self.manifest, other / 'set.json', ['f0'])['status'], 'blocked')

    def test_repair_rejects_contract_change_and_unknown_scope(self):
        other = self.root / 'after.json'
        m = json.loads(json.dumps(self.m))
        m['clips'][0]['frames'][0]['duration_ms'] = 101
        other.write_text(json.dumps(m))
        self.assertEqual(s.repair_diff(self.manifest, other, ['f0'])['status'], 'blocked')
        self.assertEqual(s.repair_diff(self.manifest, self.manifest, ['missing'])['status'], 'blocked')

    def test_pack_roundtrip_and_timing(self):
        s.load_manifest(self.manifest)
        out = self.root / 'release'
        s.pack(self.m, self.root, self.review(), out)
        data = json.loads((out / 'pixi-atlas.json').read_text())
        with Image.open(out / 'atlas.png') as atlas:
            for _, f in s.frames(self.m):
                r = data['frames'][f['id']]['frame']
                with Image.open(self.root / f['path']) as original:
                    self.assertEqual(original.convert('RGBA').tobytes(), atlas.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])).tobytes())
        tres = (out / 'sprite_frames.tres').read_text()
        self.assertIn('"duration": 0.15', tres)
        self.assertIn('"loop": false', tres)
        clip = json.loads((out / 'animations.json').read_text())['clips'][0]
        self.assertEqual(clip['events'], self.m['clips'][0]['events'])
        self.assertEqual([f['duration_ms'] for f in clip['frames']], [100, 150])
        self.assertNotIn('path', clip['frames'][0])
        self.assertEqual(json.loads((out / 'runtime-review.template.json').read_text())['status'], 'not_tested')
        with self.assertRaises(ValueError):
            s.pack(self.m, self.root, self.review(), out)

    def test_missing_requirement_and_invalid_event(self):
        self.m['required_clips'].append('death_south'); self.save()
        with self.assertRaises(ValueError): s.load_manifest(self.manifest)
        self.m['required_clips'].pop()
        self.m['clips'][0]['events'][0]['time_ms'] = 250; self.save()
        with self.assertRaises(ValueError): s.load_manifest(self.manifest)

    def test_blank_and_stale_review_block(self):
        p = self.review()
        review = json.loads(p.read_text()); review['reviewer'] = ''; p.write_text(json.dumps(review))
        self.assertEqual(s.assess(self.m, self.root, p)['status'], 'blocked')
        p = self.review()
        self.m['clips'][0]['frames'][0]['duration_ms'] += 1
        self.assertTrue(any('stale' in e for e in s.assess(self.m, self.root, p)['errors']))
        with self.assertRaises(ValueError): s.pack(self.m, self.root, p, self.root / 'blocked')
        self.assertFalse((self.root / 'blocked').exists())

    def test_changed_pixels_invalidate(self):
        p = self.review()
        im = Image.open(self.root / '0.png').convert('RGBA'); im.putpixel((6, 6), (255, 0, 0, 255)); im.save(self.root / '0.png')
        self.assertTrue(any('stale' in e for e in s.assess(self.m, self.root, p)['errors']))

    def test_missing_evidence_blocks(self):
        p = self.review(); (self.root / 'evidence.txt').unlink()
        self.assertEqual(s.assess(self.m, self.root, p)['status'], 'blocked')

    def test_alpha_empty_and_dimensions(self):
        Image.new('RGBA', (16, 16), 'white').save(self.root / '0.png')
        self.assertTrue(any('transparent pixels' in e for e in s.inspect(self.m, self.root)['errors']))
        Image.new('RGBA', (17, 16)).save(self.root / '0.png')
        errs = s.inspect(self.m, self.root)['errors']
        self.assertTrue(any('empty' in e for e in errs)); self.assertTrue(any('size' in e for e in errs))

    def test_preview_and_texture_budget(self):
        s.preview(self.m, self.root, self.root / 'proof')
        self.assertTrue((self.root / 'proof/contact-sheet.png').exists())
        self.assertTrue((self.root / 'proof/test_south.webp').exists())
        self.m['max_texture_size'] = 19
        with self.assertRaises(ValueError): s.pack(self.m, self.root, self.review(), self.root / 'small')
        self.assertFalse((self.root / 'small').exists())

    def test_invalid_durations_duplicate_ids(self):
        self.m['clips'][0]['frames'][0]['duration_ms'] = True; self.save()
        with self.assertRaises(ValueError): s.load_manifest(self.manifest)
        self.m['clips'][0]['frames'][0]['duration_ms'] = 100
        self.m['clips'][0]['frames'][1]['id'] = 'f0'; self.save()
        with self.assertRaises(ValueError): s.load_manifest(self.manifest)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(Path(s.__file__)), *map(str, args)], capture_output=True, text=True)

    def test_pad_preserves_pixels_and_origin_translation(self):
        out = self.root / 'padded.png'
        result = self.run_cli('pad', self.root / '0.png', '--out', out, '--padding', 2, 3, 4, 5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['origin_translation'], [2, 3])
        with Image.open(out) as image, Image.open(self.root / '0.png') as source:
            self.assertEqual(image.size, (22, 24))
            self.assertEqual(image.crop((2, 3, 18, 19)).tobytes(), source.tobytes())
        self.assertEqual(self.run_cli('pad', out, '--out', out, '--padding', 0, 0, 0, 0).returncode, 2)

    def test_extract_authored_duration_and_exact_grid(self):
        ims = [Image.open(self.root / f'{i}.png').convert('RGBA') for i in range(2)]
        source = self.root / 'animated.webp'
        ims[0].save(source, save_all=True, append_images=ims[1:], duration=[80, 170], loop=0, lossless=True)
        out = self.root / 'extracted'
        result = self.run_cli('extract', source, '--out', out)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((out / 'extracted-frames.json').read_text())
        self.assertEqual([f['duration_ms'] for f in data['frames']], [80, 170])
        for i in range(2):
            with Image.open(out / data['frames'][i]['path']) as actual:
                self.assertEqual(actual.tobytes(), ims[i].tobytes())
        sheet = Image.new('RGBA', (32, 16)); sheet.paste(ims[0], (0, 0)); sheet.paste(ims[1], (16, 0)); sheet.save(self.root / 'sheet.png')
        result = self.run_cli('extract', self.root / 'sheet.png', '--cell', 16, 16, '--duration-ms', 110, '--out', self.root / 'grid')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_cli('extract', self.root / 'sheet.png', '--cell', 15, 16, '--duration-ms', 110, '--out', self.root / 'badgrid').returncode, 2)
        self.assertFalse((self.root / 'badgrid').exists())

    def test_malformed_objects_rejected(self):
        self.manifest.write_text('[]')
        self.assertEqual(self.run_cli('validate', self.manifest).returncode, 2)
        self.m['clips'] = [None]; self.save()
        self.assertEqual(self.run_cli('validate', self.manifest).returncode, 2)

    def test_repeated_frames_are_warning(self):
        self.m['clips'][0]['frames'][1]['path'] = '0.png'
        report = s.inspect(self.m, self.root)
        self.assertFalse(report['errors'])
        self.assertTrue(any('identical' in w for w in report['warnings']))

    def test_cli_blank_template_blocks_export(self):
        review = self.root / 'blank.json'
        self.assertEqual(self.run_cli('review-template', self.manifest, '--out', review).returncode, 0)
        self.assertEqual(self.run_cli('qa', self.manifest, '--review', review, '--out', self.root / 'qa.json').returncode, 1)
        self.assertEqual(self.run_cli('pack', self.manifest, '--review', review, '--out', self.root / 'blocked').returncode, 1)
        self.assertFalse((self.root / 'blocked').exists())

    def test_changed_evidence_blocks(self):
        p = self.review(); (self.root / 'evidence.txt').write_text('changed screenshot/log')
        self.assertTrue(any('evidence missing or changed' in e for e in s.assess(self.m, self.root, p)['errors']))

    def test_unbound_evidence_blocks(self):
        p = self.review(); data = json.loads(p.read_text()); data['evidence_files'] = {}; p.write_text(json.dumps(data))
        self.assertEqual(s.assess(self.m, self.root, p)['status'], 'blocked')

    def test_bound_cli_review_template(self):
        ev = self.root / 'proof.txt'; ev.write_text('fixture')
        p = self.root / 'blank-bound.json'
        result = self.run_cli('review-template', self.manifest, '--evidence', ev, '--out', p)
        self.assertEqual(result.returncode, 0, result.stderr)
        review = json.loads(p.read_text())
        self.assertEqual(review['evidence_files'], {'proof.txt': s.file_hash(ev)})
        self.assertEqual(review['schema_version'], 2)

    def test_alpha_policy_and_color_budget(self):
        im = Image.open(self.root / '0.png').convert('RGBA'); im.putpixel((5, 5), (250, 0, 0, 128)); im.save(self.root / '0.png')
        self.m['alpha_policy'] = 'binary'
        self.assertTrue(any('soft alpha' in e for e in s.inspect(self.m, self.root)['errors']))
        self.m['alpha_policy'] = 'soft'; self.m['max_colors'] = 1
        self.assertTrue(any('max_colors' in e for e in s.inspect(self.m, self.root)['errors']))
        self.m['max_colors'] = 2
        self.assertFalse(s.inspect(self.m, self.root)['errors'])

    def make_poses(self):
        plan = {'total_frames': 8, 'cell_size': [16, 16], 'origin': [8, 13],
                'keyframes': [{'index': i * 7, 'path': f'{i}.png', 'origin': [8, 13], 'role': 'fixture'} for i in range(2)]}
        p = self.root / 'poses.json'; p.write_text(json.dumps(plan)); return p, plan

    def test_pose_preflight_all_canvases_and_origins(self):
        p, plan = self.make_poses()
        self.assertEqual(s.keypose_check(p)['status'], 'structural_pass')
        plan['keyframes'][1]['origin'] = [7, 13]; p.write_text(json.dumps(plan))
        self.assertEqual(s.keypose_check(p)['status'], 'blocked')
        Image.new('RGBA', (15, 16)).save(self.root / '1.png')
        self.assertTrue(any('dimensions' in e for e in s.keypose_check(p)['errors']))

    def test_pose_preflight_indices(self):
        p, plan = self.make_poses()
        plan['keyframes'][0]['index'] = 1; p.write_text(json.dumps(plan))
        self.assertTrue(any('pose 0' in e for e in s.keypose_check(p)['errors']))
        plan['keyframes'][1]['index'] = 1; p.write_text(json.dumps(plan))
        with self.assertRaises(ValueError): s.keypose_check(p)

    def runtime_fixture(self):
        out = self.root / 'release'; s.pack(self.m, self.root, self.review(), out)
        ev = self.root / 'runtime.txt'; ev.write_text('Synthetic assertions only; not actual engine validation.')
        p = self.root / 'runtime-review.json'
        review = s.runtime_template(out, [ev], p)
        review.update(engine='fixture-engine', version='0', project_or_scene='synthetic-fixture', reviewer='synthetic-test')
        for row in review['checks'].values():
            row.update(verdict='pass', mode='visual', observation='Synthetic gate test only', evidence=['runtime.txt'])
        p.write_text(json.dumps(review)); return out, p, review

    def test_runtime_bound_assertions_and_changed_export(self):
        out, p, review = self.runtime_fixture()
        self.assertEqual(s.runtime_verify(out, p)['status'], 'runtime_assertions_pass')
        (out / 'atlas.png').write_bytes(b'changed')
        with self.assertRaises(ValueError): s.runtime_verify(out, p)

    def test_runtime_blank_and_headless_visual_block(self):
        out, p, review = self.runtime_fixture()
        review['checks']['playback']['mode'] = 'headless'; p.write_text(json.dumps(review))
        self.assertEqual(s.runtime_verify(out, p)['status'], 'blocked')
        review['version'] = ''; p.write_text(json.dumps(review))
        self.assertTrue(any('version' in e for e in s.runtime_verify(out, p)['errors']))

    def test_runtime_stale_manifest_and_evidence(self):
        out, p, review = self.runtime_fixture()
        (self.root / 'runtime.txt').write_text('changed')
        self.assertEqual(s.runtime_verify(out, p)['status'], 'blocked')
        review['export_manifest_sha256'] = 'bad'; p.write_text(json.dumps(review))
        self.assertTrue(any('stale' in e for e in s.runtime_verify(out, p)['errors']))

    def test_preview_embeds_safe_independent_frames(self):
        self.m['clips'][0]['note'] = '</script><script>bad()</script>'
        out = self.root / 'offline'; s.preview(self.m, self.root, out)
        content = (out / 'index.html').read_text()
        self.assertIn('data:image/png;base64,', content)
        self.assertNotIn('</script><script>bad()', content)
        self.assertTrue((out / 'timeline.js').exists())


if __name__ == '__main__':
    unittest.main()
