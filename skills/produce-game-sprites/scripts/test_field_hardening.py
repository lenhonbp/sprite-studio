import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageDraw

from sprite_tools import load_manifest
from production_support import keypose_check
from ui_checks import (
    ui_check, ui_slice, ui_review_template, ui_qa,
    ui_runtime_template, ui_runtime_verify,
)
from artifact_checks import (environment_check, vfx_check, environment_review_template, environment_qa, environment_runtime_template, environment_runtime_verify, vfx_review_template, vfx_qa, vfx_runtime_template, vfx_runtime_verify)


class FieldHardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _img(self, rel, size=(32, 32), fill=(200, 100, 50, 255)):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        im = Image.new('RGBA', size, (0, 0, 0, 0))
        ImageDraw.Draw(im).rectangle((4, 4, size[0]-5, size[1]-5), fill=fill)
        im.save(p)
        return p

    def _ui_contract(self):
        self._img('ui/button.png', (40, 24))
        return {
            'schema_version': 1, 'ui_system_id': 'qa_ui', 'representation': 'hd',
            'reference_canvas': [390, 844],
            'safe_area': {'top': 47, 'right': 0, 'bottom': 34, 'left': 0},
            'text_policy': 'runtime_text', 'minimum_touch_size': [44, 44],
            'runtime': {'engine': 'generic'},
            'runtime_test_matrix': {'viewports': ['390x844', '430x932'], 'locales': ['en', 'vi'], 'input_modes': ['touch']},
            'components': [{
                'id': 'button_default', 'group': 'button', 'role': 'button', 'state': 'default',
                'path': 'ui/button.png', 'logical_size': [80, 48], 'touch_size': [80, 48],
                'nine_slice': [6, 6, 6, 6], 'text_baked': False, 'alpha_required': True,
            }],
            'required_state_groups': {'button': ['default']},
            'screen_flows': [{'screen': 'main', 'components': ['button_default']}],
        }

    def _fill_visual(self, path, evidence_name):
        d = json.loads(Path(path).read_text())
        d['reviewer'] = 'qa_reviewer'
        for row in d['checks'].values():
            row.update({'verdict': 'pass', 'observation': 'Inspected current evidence at reference scale.', 'evidence': [evidence_name]})
        Path(path).write_text(json.dumps(d))

    def _fill_runtime(self, path, evidence_name):
        d = json.loads(Path(path).read_text())
        d.update({
            'engine': 'TestEngine', 'version': '1.0', 'project_or_scene': 'ui_test', 'reviewer': 'qa_reviewer',
            'viewports_tested': ['390x844', '430x932'], 'locales_tested': ['en', 'vi'],
            'input_modes_tested': ['touch'], 'devices_or_browsers': ['mock-device'],
        })
        for key, row in d['checks'].items():
            mode = 'visual' if key not in ('screen_import', 'performance') else 'automated'
            row.update({'verdict': 'pass', 'mode': mode, 'observation': 'Observed in bound runtime evidence.', 'evidence': [evidence_name]})
        Path(path).write_text(json.dumps(d))

    def test_manifest_rejects_parent_escape(self):
        m = {
            'schema_version': 1, 'asset_id': 'hero', 'representation': 'pixel', 'cell_size': [16, 16], 'origin': [8, 15],
            'alpha_required': True, 'required_clips': ['idle'],
            'clips': [{'name': 'idle', 'action': 'idle', 'direction': 'down', 'loop': True,
                       'frames': [{'id': 'f0', 'path': '../outside.png', 'duration_ms': 100}], 'events': []}],
        }
        p = self.root / 'manifest.json'; p.write_text(json.dumps(m))
        with self.assertRaises(ValueError):
            load_manifest(p)

    def test_keypose_rejects_parent_escape(self):
        plan = {'total_frames': 2, 'cell_size': [16,16], 'origin': [8,15], 'keyframes': [
            {'index':0, 'path':'../outside.png', 'origin':[8,15], 'role':'contact'},
            {'index':1, 'path':'inside.png', 'origin':[8,15], 'role':'recover'}]}
        self._img('inside.png', (16,16))
        p = self.root / 'plan.json'; p.write_text(json.dumps(plan))
        with self.assertRaises(ValueError):
            keypose_check(p)

    def test_ui_rejects_path_escape_and_impossible_safe_area(self):
        c = self._ui_contract()
        c['components'][0]['path'] = '../outside.png'
        c['safe_area'] = {'top': 500, 'bottom': 500, 'left': 0, 'right': 0}
        p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        r = ui_check(p)
        self.assertEqual(r['status'], 'blocked')
        self.assertTrue(any('safe_area' in e for e in r['errors']))
        self.assertTrue(any('project-relative' in e for e in r['errors']))

    def test_ui_slice_duplicate_output_fails_before_creating_output(self):
        self._img('sheet.png', (64, 32))
        c = self._ui_contract()
        c['slices'] = [
            {'id':'a','source_sheet':'sheet.png','rect':[0,0,16,16],'output':'x.png'},
            {'id':'b','source_sheet':'sheet.png','rect':[16,0,16,16],'output':'x.png'},
        ]
        p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        out = self.root / 'sliced'
        with self.assertRaises(ValueError):
            ui_slice(p, out)
        self.assertFalse(out.exists())

    def test_ui_visual_and_runtime_gates_are_evidence_bound(self):
        c = self._ui_contract(); p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        ev = self.root / 'screen.png'; self._img('screen.png', (100, 100))
        visual_path = self.root / 'ui-review.json'
        visual_path.write_text(json.dumps(ui_review_template(p, [ev], visual_path)))
        rel = next(iter(json.loads(visual_path.read_text())['evidence_files']))
        self._fill_visual(visual_path, rel)
        vr = ui_qa(p, visual_path)
        self.assertEqual(vr['status'], 'approved')
        runtime_path = self.root / 'ui-runtime.json'
        runtime_path.write_text(json.dumps(ui_runtime_template(p, visual_path, [ev], runtime_path)))
        rrel = next(iter(json.loads(runtime_path.read_text())['evidence_files']))
        self._fill_runtime(runtime_path, rrel)
        rr = ui_runtime_verify(p, visual_path, runtime_path)
        self.assertEqual(rr['status'], 'runtime_assertions_pass')
        # Changing a bound component invalidates both gates.
        self._img('ui/button.png', (40, 24), fill=(10, 220, 40, 255))
        self.assertEqual(ui_qa(p, visual_path)['status'], 'blocked')
        self.assertEqual(ui_runtime_verify(p, visual_path, runtime_path)['status'], 'blocked')

    def test_ui_runtime_matrix_missing_case_blocks(self):
        c = self._ui_contract(); p = self.root / 'ui.json'; p.write_text(json.dumps(c))
        ev = self.root / 'screen.png'; self._img('screen.png', (100,100))
        visual_path = self.root / 'ui-review.json'; visual_path.write_text(json.dumps(ui_review_template(p,[ev],visual_path)))
        rel = next(iter(json.loads(visual_path.read_text())['evidence_files'])); self._fill_visual(visual_path, rel)
        runtime_path = self.root / 'ui-runtime.json'; runtime_path.write_text(json.dumps(ui_runtime_template(p,visual_path,[ev],runtime_path)))
        rrel = next(iter(json.loads(runtime_path.read_text())['evidence_files'])); self._fill_runtime(runtime_path, rrel)
        d=json.loads(runtime_path.read_text()); d['viewports_tested']=['390x844']; runtime_path.write_text(json.dumps(d))
        rr=ui_runtime_verify(p,visual_path,runtime_path)
        self.assertTrue(any('430x932' in e for e in rr['errors']))

    def test_environment_check_valid_and_bad_pivot(self):
        self._img('environment/tree.png', (64,96))
        c = {'schema_version':1,'environment_id':'forest','projection':'top_down_3_4','representation':'pixel',
             'world_tile':[32,32],'depth_sort':'base_point_y','sampling':'nearest',
             'terrain':{'seam_test_repeat':[3,3],'collision_is_separate_from_visible_bounds':True},
             'props':[{'id':'tree','path':'environment/tree.png','base_pivot':[32,90],'footprint_cells':[[0,0]],
                       'collision_rect':[20,70,24,20],'occluder':True}]}
        p=self.root/'env.json'; p.write_text(json.dumps(c)); self.assertEqual(environment_check(p)['status'],'review_required')
        c['props'][0]['base_pivot']=[100,100]; p.write_text(json.dumps(c)); self.assertEqual(environment_check(p)['status'],'blocked')

    def test_vfx_check_valid_and_canvas_mismatch(self):
        self._img('vfx/f0.png',(32,32)); self._img('vfx/f1.png',(32,32))
        c={'schema_version':1,'vfx_id':'slash','representation':'pixel','attachment_space':'socket','socket':'weapon_tip',
           'loop':False,'blend_intent':'additive','alpha_policy':'soft','cell_size':[32,32],
           'frames':[{'id':'f0','path':'vfx/f0.png','duration_ms':50},{'id':'f1','path':'vfx/f1.png','duration_ms':80}],
           'events':{'gameplay_hit_ms':60,'visual_peak_ms':70},'performance_budget':{'max_simultaneous_instances':4,'allow_large_transparent_canvas':False}}
        p=self.root/'vfx.json'; p.write_text(json.dumps(c)); self.assertEqual(vfx_check(p)['status'],'review_required')
        self._img('vfx/f1.png',(40,32)); self.assertEqual(vfx_check(p)['status'],'blocked')

    def _fill_generic_runtime(self, path, evidence_name, visual_required):
        d = json.loads(Path(path).read_text())
        d.update({'engine':'TestEngine','version':'1.0','project_or_scene':'field_scene','reviewer':'qa_reviewer'})
        for key,row in d['checks'].items():
            row.update({'verdict':'pass','mode':'visual' if key in visual_required else 'automated',
                        'observation':'Observed in bound field evidence.','evidence':[evidence_name]})
        Path(path).write_text(json.dumps(d))

    def test_environment_visual_runtime_binding(self):
        self._img('environment/tree.png',(64,96))
        c={'schema_version':1,'environment_id':'forest','projection':'top_down_3_4','representation':'pixel',
           'world_tile':[32,32],'depth_sort':'base_point_y','sampling':'nearest',
           'terrain':{'seam_test_repeat':[3,3],'collision_is_separate_from_visible_bounds':True},
           'props':[{'id':'tree','path':'environment/tree.png','base_pivot':[32,90],'footprint_cells':[[0,0]],'collision_rect':[20,70,24,20],'occluder':True}]}
        cp=self.root/'env.json'; cp.write_text(json.dumps(c)); ev=self._img('env-screen.png',(100,100))
        vp=self.root/'env-review.json'; vp.write_text(json.dumps(environment_review_template(cp,[ev],vp)))
        rel=next(iter(json.loads(vp.read_text())['evidence_files'])); self._fill_visual(vp,rel)
        self.assertEqual(environment_qa(cp,vp)['status'],'approved')
        rp=self.root/'env-runtime.json'; rp.write_text(json.dumps(environment_runtime_template(cp,vp,[ev],rp)))
        rrel=next(iter(json.loads(rp.read_text())['evidence_files']))
        self._fill_generic_runtime(rp,rrel,{'assembled_seams','depth_sort_occlusion','collision_walkability','camera_scale'})
        self.assertEqual(environment_runtime_verify(cp,vp,rp)['status'],'runtime_assertions_pass')

    def test_vfx_visual_runtime_binding(self):
        self._img('vfx/f0.png',(32,32)); self._img('vfx/f1.png',(32,32))
        c={'schema_version':1,'vfx_id':'slash','representation':'pixel','attachment_space':'socket','socket':'weapon_tip',
           'loop':False,'blend_intent':'additive','alpha_policy':'soft','cell_size':[32,32],
           'frames':[{'id':'f0','path':'vfx/f0.png','duration_ms':50},{'id':'f1','path':'vfx/f1.png','duration_ms':80}],
           'events':{'gameplay_hit_ms':60,'visual_peak_ms':70},'performance_budget':{'max_simultaneous_instances':4,'allow_large_transparent_canvas':False}}
        cp=self.root/'vfx.json'; cp.write_text(json.dumps(c)); ev=self._img('vfx-screen.png',(100,100))
        vp=self.root/'vfx-review.json'; vp.write_text(json.dumps(vfx_review_template(cp,[ev],vp)))
        rel=next(iter(json.loads(vp.read_text())['evidence_files'])); self._fill_visual(vp,rel)
        self.assertEqual(vfx_qa(cp,vp)['status'],'approved')
        rp=self.root/'vfx-runtime.json'; rp.write_text(json.dumps(vfx_runtime_template(cp,vp,[ev],rp)))
        rrel=next(iter(json.loads(rp.read_text())['evidence_files']))
        self._fill_generic_runtime(rp,rrel,{'import_blend','playback_timing','socket_transform','gameplay_hit_alignment','multi_instance_readability'})
        self.assertEqual(vfx_runtime_verify(cp,vp,rp)['status'],'runtime_assertions_pass')


if __name__ == '__main__':
    unittest.main()
