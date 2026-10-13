import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vfx_pack import vfx_pack_plan, vfx_pack_bundle_check


def _frame_image(size, seed):
    im = Image.new('RGBA', size, (0, 0, 0, 0))
    px = im.load()
    cx, cy = size[0] // 2, size[1] // 2
    r = 8 + seed * 4
    for y in range(size[1]):
        for x in range(size[0]):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px[x, y] = (255, 120 + seed * 20, 30, 200)
    return im


class VfxPackFixture:
    def __init__(self, root):
        self.root = Path(root)
        self.spec = {
            'schema_version': 1,
            'pack_id': 'test_pack',
            'title': 'Test Pack',
            'representation': 'pixel',
            'default_cell_size': [64, 64],
            'effects': [
                {'vfx_id': 'fire_burst', 'taxonomy': 'impact-burst', 'loop': False,
                 'blend_intent': 'additive', 'alpha_policy': 'soft',
                 'events': {'visual_peak_ms': 120, 'gameplay_hit_ms': 60},
                 'vfx_contract': 'fire_burst.contract.json',
                 'frames': [{'id': f'fx_{i:03d}', 'path': f'vfx/fire_burst_{i:03d}.png',
                             'duration_ms': 60} for i in range(4)]},
                {'vfx_id': 'ember_aura', 'taxonomy': 'status-aura', 'loop': True,
                 'blend_intent': 'additive', 'alpha_policy': 'soft',
                 'cell_size': [32, 32],
                 'frames': [{'id': f'fx_{i:03d}', 'path': f'vfx/ember_aura_{i:03d}.png',
                             'duration_ms': 120} for i in range(4)]},
            ],
            'generation': {'adapter': 'pixellab', 'fixed_seed': 7,
                           'cost_per_effect_usd': 0.05,
                           'log_fields': ['model', 'seed', 'prompt', 'date']},
            'marketplace': {'target': 'itch.io', 'ai_generated': True,
                            'ai_disclosure': True, 'price_usd': 5.0,
                            'license': 'test license'},
        }
        self.contract = {
            'schema_version': 1, 'vfx_id': 'fire_burst', 'representation': 'pixel',
            'attachment_space': 'world', 'loop': False,
            'blend_intent': 'additive', 'alpha_policy': 'soft',
            'events': {'visual_peak_ms': 120, 'gameplay_hit_ms': 60},
            'performance_budget': {'max_simultaneous_instances': 8},
            'cell_size': [64, 64],
            'frames': [{'id': f'fx_{i:03d}', 'path': f'vfx/fire_burst_{i:03d}.png',
                        'duration_ms': 60} for i in range(4)],
        }

    def build(self):
        (self.root / 'vfx').mkdir(parents=True)
        for effect in self.spec['effects']:
            cell = effect.get('cell_size', self.spec['default_cell_size'])
            for i, frame in enumerate(effect['frames']):
                _frame_image(tuple(cell), i).save(self.root / frame['path'])
        (self.root / 'vfx-pack.json').write_text(json.dumps(self.spec))
        (self.root / 'fire_burst.contract.json').write_text(json.dumps(self.contract))
        bundle = self.root / 'bundle'
        for effect in self.spec['effects']:
            vid = effect['vfx_id']
            cell = tuple(effect.get('cell_size', self.spec['default_cell_size']))
            n = len(effect['frames'])
            frames = [_frame_image(cell, i) for i in range(n)]
            sheet = Image.new('RGBA', (cell[0] * n, cell[1]), (0, 0, 0, 0))
            for i, f in enumerate(frames):
                sheet.paste(f, (i * cell[0], 0))
            (bundle / 'sheets').mkdir(parents=True, exist_ok=True)
            sheet.save(bundle / f'sheets/{vid}.png')
            (bundle / 'previews').mkdir(parents=True, exist_ok=True)
            previews = []
            for src in frames:
                preview = Image.new('RGBA', cell, (20, 20, 20, 255))
                preview.alpha_composite(src)
                previews.append(preview.convert('RGB'))
            options = {'loop': 0} if effect['loop'] else {}
            previews[0].save(bundle / f'previews/{vid}.gif', save_all=True,
                           append_images=previews[1:],
                           duration=[fr['duration_ms'] for fr in effect['frames']], **options)
            (bundle / 'meta').mkdir(parents=True, exist_ok=True)
            (bundle / f'meta/{vid}.json').write_text(json.dumps(
                {'vfx_id': vid, 'frames': [dict(f) for f in effect['frames']],
                 'loop': effect['loop'], 'blend_intent': effect['blend_intent'],
                 'alpha_policy': effect['alpha_policy'], 'events': effect.get('events', {}),
                 'gif_preview': {'mode': 'composite', 'background_rgb': [20, 20, 20]}}))
        (bundle / 'pack-manifest.json').write_text(json.dumps(
            {'pack_id': 'test_pack',
             'effects': [{'vfx_id': e['vfx_id'], 'sheet': f"sheets/{e['vfx_id']}.png",
                         'gif': f"previews/{e['vfx_id']}.gif", 'meta': f"meta/{e['vfx_id']}.json"}
                        for e in self.spec['effects']]}))
        (bundle / 'LICENSE').write_text('test license')
        (bundle / 'README.md').write_text('# Test Pack')
        (bundle / 'AI_DISCLOSURE.txt').write_text('AI-generated, disclosed')
        with (bundle / 'generation-log.csv').open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['vfx_id', 'model', 'seed', 'prompt', 'date'])
            w.writeheader()
            for e in self.spec['effects']:
                w.writerow({'vfx_id': e['vfx_id'], 'model': 'pixellab', 'seed': 7, 'prompt': 'x', 'date': '2026-10-07'})
        return self

    def spec_path(self):
        return str(self.root / 'vfx-pack.json')

    def bundle_dir(self):
        return str(self.root / 'bundle')


class PackPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fx = VfxPackFixture(self.temp.name).build()

    def mutate_spec(self, fn):
        spec = copy.deepcopy(self.fx.spec)
        fn(spec)
        p = Path(self.temp.name) / 'vfx-pack.json'
        p.write_text(json.dumps(spec))
        return vfx_pack_plan(str(p))

    def test_plan_ready_and_totals(self):
        report = vfx_pack_plan(self.fx.spec_path())
        self.assertEqual(report['status'], 'ready')
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['totals']['effects'], 2)
        self.assertEqual(report['totals']['frames'], 8)
        self.assertEqual(report['totals']['duration_ms'], 4 * 60 + 4 * 120)
        self.assertAlmostEqual(report['totals']['cost_estimate_usd'], 0.05 * 2)
        manifest = report['bundle_manifest']
        for need in ('LICENSE', 'README.md', 'pack-manifest.json',
                     'AI_DISCLOSURE.txt', 'generation-log.csv',
                     'sheets/fire_burst.png', 'previews/ember_aura.gif'):
            self.assertIn(need, manifest)

    def test_plan_gamedev_market_blocked(self):
        report = self.mutate_spec(lambda s: s['marketplace'].__setitem__('target', 'gamedev-market'))
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('gamedev-market' in e for e in report['errors']))

    def test_plan_itch_needs_disclosure(self):
        report = self.mutate_spec(lambda s: s['marketplace'].__setitem__('ai_disclosure', False))
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('disclosure' in e for e in report['errors']))

    def test_plan_bad_taxonomy(self):
        def bad(s):
            s['effects'][0]['taxonomy'] = 'big-boom'
        report = self.mutate_spec(bad)
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('taxonomy' in e for e in report['errors']))

    def test_plan_missing_seed_warns(self):
        report = self.mutate_spec(lambda s: s['generation'].pop('fixed_seed'))
        self.assertEqual(report['status'], 'ready')
        self.assertTrue(any('fixed_seed' in w for w in report['warnings']))

    def test_plan_missing_log_fields_warns(self):
        report = self.mutate_spec(lambda s: s['generation'].__setitem__('log_fields', ['model']))
        self.assertTrue(any('log_fields' in w for w in report['warnings']))

    def test_plan_unity_warns(self):
        report = self.mutate_spec(lambda s: s['marketplace'].__setitem__('target', 'unity-asset-store'))
        self.assertEqual(report['status'], 'ready')
        self.assertTrue(any('unity' in w.lower() for w in report['warnings']))

    def test_plan_malformed_types(self):
        for field, value in [('log_fields', None), ('log_fields', 'model'),
                             ('cost_per_effect_usd', True)]:
            report = self.mutate_spec(lambda spec: spec['generation'].__setitem__(field, value))
            self.assertEqual(report['status'], 'blocked', report)
        report = self.mutate_spec(lambda spec: spec['effects'][0].__setitem__('events', []))
        self.assertEqual(report['status'], 'blocked')
        report = self.mutate_spec(lambda spec: spec.__setitem__('schema_version', True))
        self.assertEqual(report['status'], 'blocked')

    def test_plan_unreadable(self):
        report = vfx_pack_plan(str(Path(self.temp.name) / 'missing.json'))
        self.assertEqual(report['status'], 'blocked')


class BundleCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fx = VfxPackFixture(self.temp.name).build()

    def test_bundle_ready(self):
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertEqual(report['status'], 'ready', report['errors'])
        self.assertEqual(report['errors'], [])

    def test_bundle_missing_gif(self):
        (Path(self.fx.bundle_dir()) / 'previews/ember_aura.gif').unlink()
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('previews/ember_aura.gif' in e for e in report['errors']))

    def test_bundle_sheet_grid_mismatch(self):
        bad = Image.new('RGBA', (100, 64), (0, 0, 0, 0))
        bad.save(Path(self.fx.bundle_dir()) / 'sheets/fire_burst.png')
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('grid' in e for e in report['errors']))

    def test_bundle_gif_frame_mismatch(self):
        p = Path(self.fx.bundle_dir()) / 'previews/fire_burst.gif'
        frames = [_frame_image((64, 64), i) for i in range(3)]
        frames[0].save(p, save_all=True, append_images=frames[1:], duration=60, loop=0)
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('frames' in e for e in report['errors']))

    def test_bundle_contract_error_folds(self):
        cpath = Path(self.temp.name) / 'fire_burst.contract.json'
        contract = json.loads(cpath.read_text())
        contract['frames'][0]['path'] = 'vfx/does_not_exist.png'
        cpath.write_text(json.dumps(contract))
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('contract' in e for e in report['errors']))

    def test_bundle_manifest_mismatch(self):
        mp = Path(self.fx.bundle_dir()) / 'pack-manifest.json'
        mp.write_text(json.dumps({'pack_id': 'test_pack', 'effects': [{'vfx_id': 'fire_burst'}]}))
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('ember_aura' in e for e in report['errors']))

    def test_malformed_metadata_and_manifest(self):
        for path, value in [('pack-manifest.json', []), ('meta/fire_burst.json',
                           {'vfx_id': 'fire_burst', 'frames': 'xxxx'})]:
            with self.subTest(path=path):
                p = Path(self.fx.bundle_dir()) / path
                original = p.read_text()
                p.write_text(json.dumps(value))
                self.assertEqual(vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())['status'], 'blocked')
                p.write_text(original)

    def test_one_pixel_sheet_and_wrong_order_blocked(self):
        p = Path(self.fx.bundle_dir()) / 'sheets/fire_burst.png'
        original = Image.open(p).convert('RGBA')
        for bad in [Image.new('RGBA', original.size, (0, 0, 0, 0)),
                    original.transpose(Image.Transpose.FLIP_LEFT_RIGHT)]:
            bad.putpixel((0, 0), (255, 255, 255, 255))
            bad.save(p)
            report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
            self.assertTrue(any('RGBA' in e for e in report['errors']))

    def test_metadata_timing_and_event_drift(self):
        p = Path(self.fx.bundle_dir()) / 'meta/fire_burst.json'
        meta = json.loads(p.read_text())
        meta['frames'][0]['duration_ms'] = 100
        meta['events']['visual_peak_ms'] = 200
        p.write_text(json.dumps(meta))
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertTrue(any('ordered frames' in e for e in report['errors']))
        self.assertTrue(any('events' in e for e in report['errors']))

    def test_empty_or_identityless_generation_log_blocked(self):
        p = Path(self.fx.bundle_dir()) / 'generation-log.csv'
        for content in ['model,seed,prompt,date\n', 'vfx_id,model,seed,prompt,date\nwrong,x,7,x,today\n']:
            p.write_text(content)
            self.assertEqual(vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())['status'], 'blocked')

    def test_manifest_duplicate_and_wrong_path_blocked(self):
        p = Path(self.fx.bundle_dir()) / 'pack-manifest.json'
        manifest = json.loads(p.read_text())
        manifest['effects'].append(manifest['effects'][0])
        manifest['effects'][0]['sheet'] = '../escape.png'
        p.write_text(json.dumps(manifest))
        self.assertEqual(vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())['status'], 'blocked')

    def test_soft_alpha_preview_and_binding(self):
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertTrue(report['structural_ready'])
        self.assertEqual(len(report['source_binding']), 8)
        self.assertEqual(report['art_approval'], 'not_evaluated')
        p = Path(self.fx.bundle_dir()) / 'meta/fire_burst.json'
        meta = json.loads(p.read_text())
        meta['gif_preview'] = {'mode': 'binary-alpha'}
        p.write_text(json.dumps(meta))
        self.assertEqual(vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())['status'], 'blocked')

    def test_wrong_gif_timing_same_total_blocked(self):
        p = Path(self.fx.bundle_dir()) / 'previews/fire_burst.gif'
        previews = []
        for i in range(4):
            im = Image.new('RGBA', (64, 64), (20, 20, 20, 255))
            im.alpha_composite(_frame_image((64, 64), i))
            previews.append(im.convert('RGB'))
        previews[0].save(p, save_all=True, append_images=previews[1:], duration=[30, 90, 60, 60])
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertTrue(any('duration' in e for e in report['errors']))

    def test_missing_source_blocked_without_contract(self):
        (self.fx.root / 'vfx/ember_aura_000.png').unlink()
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertTrue(any('source frame' in e for e in report['errors']))

    def test_source_identity_and_bundle_identity_present(self):
        report = vfx_pack_bundle_check(self.fx.spec_path(), self.fx.bundle_dir())
        self.assertEqual(len(report['spec_binding']), 64)
        self.assertIn('pack-manifest.json', report['artifact_binding'])
        self.assertIn('sheets/fire_burst.png', report['artifact_binding'])
        self.assertIn('meta/fire_burst.json', report['artifact_binding'])

    def test_bundle_missing_dir(self):
        report = vfx_pack_bundle_check(self.fx.spec_path(), str(Path(self.temp.name) / 'nope'))
        self.assertEqual(report['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
