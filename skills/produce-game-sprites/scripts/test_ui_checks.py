import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageDraw

from ui_checks import ui_check, ui_slice


class UiChecksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _image(self, rel, size=(40, 20), alpha=True):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        bg = (10, 20, 30, 0 if alpha else 255)
        im = Image.new('RGBA', size, bg)
        ImageDraw.Draw(im).rectangle((5, 5, size[0]-6, size[1]-6), fill=(200, 100, 50, 255))
        im.save(p)
        return p

    def _contract(self):
        return {
            'schema_version': 1,
            'ui_system_id': 'test_ui',
            'representation': 'pixel',
            'reference_canvas': [320, 180],
            'safe_area': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0},
            'text_policy': 'runtime_text',
            'minimum_touch_size': [20, 20],
            'runtime': {'pixel_snap': True, 'integer_scale_preferred': True},
            'components': [],
            'required_state_groups': {},
            'screen_flows': []
        }

    def test_valid_ui_contract_requires_review(self):
        self._image('ui/button.png')
        c = self._contract()
        c['components'] = [{
            'id': 'button_default', 'group': 'button', 'role': 'button', 'state': 'default',
            'path': 'ui/button.png', 'logical_size': [40, 20], 'touch_size': [40, 20],
            'nine_slice': [4, 4, 4, 4], 'text_baked': False, 'alpha_required': True
        }]
        c['required_state_groups'] = {'button': ['default']}
        c['screen_flows'] = [{'screen': 'main', 'components': ['button_default']}]
        p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        report = ui_check(p)
        self.assertEqual(report['status'], 'review_required')
        self.assertEqual(report['errors'], [])

    def test_missing_state_blocks(self):
        self._image('ui/button.png')
        c = self._contract()
        c['components'] = [{
            'id': 'button_default', 'group': 'button', 'role': 'button', 'state': 'default',
            'path': 'ui/button.png', 'logical_size': [40, 20], 'touch_size': [40, 20]
        }]
        c['required_state_groups'] = {'button': ['default', 'pressed']}
        p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        report = ui_check(p)
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('missing required UI states' in e for e in report['errors']))

    def test_runtime_text_rejects_baked_text(self):
        self._image('ui/label.png')
        c = self._contract()
        c['components'] = [{
            'id': 'label_main', 'group': 'label_main', 'role': 'label', 'state': 'default',
            'path': 'ui/label.png', 'logical_size': [40, 20], 'text_baked': True
        }]
        p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        report = ui_check(p)
        self.assertTrue(any('baked text' in e for e in report['errors']))

    def test_bad_nine_slice_blocks(self):
        self._image('ui/panel.png', size=(20, 20))
        c = self._contract()
        c['components'] = [{
            'id': 'panel_main', 'group': 'panel_main', 'role': 'panel', 'state': 'default',
            'path': 'ui/panel.png', 'logical_size': [20, 20], 'nine_slice': [10, 2, 10, 2]
        }]
        p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        report = ui_check(p)
        self.assertTrue(any('nine_slice' in e for e in report['errors']))

    def test_small_touch_target_blocks(self):
        self._image('ui/button.png')
        c = self._contract()
        c['components'] = [{
            'id': 'button_default', 'group': 'button', 'role': 'button', 'state': 'default',
            'path': 'ui/button.png', 'logical_size': [40, 20], 'touch_size': [10, 20]
        }]
        p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        report = ui_check(p)
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('minimum_touch_size' in e for e in report['errors']))

    def test_slice_crops_exact_rect(self):
        sheet = self.root / 'sheet.png'
        Image.new('RGBA', (64, 32), (255, 0, 0, 255)).save(sheet)
        c = self._contract()
        c['components'] = [{
            'id': 'piece', 'group': 'piece', 'role': 'panel', 'state': 'default',
            'path': 'out/piece.png', 'logical_size': [16, 12]
        }]
        c['slices'] = [{'id': 'piece', 'source_sheet': 'sheet.png', 'rect': [4, 5, 16, 12], 'output': 'out/piece.png'}]
        p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        result = ui_slice(p, self.root / 'sliced')
        self.assertEqual(result['count'], 1)
        with Image.open(self.root / 'sliced/out/piece.png') as im:
            self.assertEqual(im.size, (16, 12))

    def test_alias_parent_and_manifest_outputs_rejected_before_writes(self):
        self._image('sheet.png')
        for outputs in [('part.png','./part.png'), ('part.png','part.png/child.png'), ('ui-slices.json',), ('ui-slices.json/child.png',)]:
            c=self._contract()
            c['slices']=[{'id':f'p{i}','source_sheet':'sheet.png','rect':[0,0,8,8],'output':v} for i,v in enumerate(outputs)]
            p=self.root/'ui.json';p.write_text(json.dumps(c))
            out=self.root/'sliced'
            with self.assertRaises(ValueError): ui_slice(p,out)
            self.assertFalse(out.exists())

    def test_slice_rejects_out_of_bounds(self):
        sheet = self.root / 'sheet.png'
        Image.new('RGBA', (16, 16), (255, 0, 0, 255)).save(sheet)
        c = self._contract(); c['components'] = [{'id':'piece','group':'piece','role':'panel','state':'default','path':'out/piece.png','logical_size':[8,8]}]
        c['slices'] = [{'id': 'piece', 'source_sheet': 'sheet.png', 'rect': [10, 10, 8, 8], 'output': 'out/piece.png'}]
        p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        with self.assertRaises(ValueError):
            ui_slice(p, self.root / 'sliced')


if __name__ == '__main__':
    unittest.main()
