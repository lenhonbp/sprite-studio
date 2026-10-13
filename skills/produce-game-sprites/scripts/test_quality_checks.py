#!/usr/bin/env python3
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sprite_tools_v33', HERE / 'sprite_tools.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class QualityV33Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.frames = self.root / 'frames'; self.frames.mkdir()
        for i, x in enumerate((4, 5, 6)):
            im = Image.new('RGBA', (16, 16))
            d = ImageDraw.Draw(im)
            d.rectangle((x, 4, x + 5, 12), fill=(120, 80, 50, 255))
            d.rectangle((1, 14, 3, 15), fill=(20, 20, 20, 255))  # static anchor region
            im.save(self.frames / f'f{i}.png')
        self.manifest = {
            'schema_version': 1, 'asset_id': 'hero', 'representation': 'pixel',
            'cell_size': [16, 16], 'origin': [8, 14], 'alpha_required': True,
            'required_clips': ['walk_south'], 'max_texture_size': 128, 'gutter': 2,
            'clips': [{'name': 'walk_south', 'action': 'walk', 'direction': 'south', 'loop': True,
                       'events': [], 'frames': [
                           {'id': f'f{i}', 'path': f'frames/f{i}.png', 'duration_ms': 100} for i in range(3)]}]
        }
        self.manifest_path = self.root / 'animation-set.json'
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.contract = {
            'schema_version': 1, 'asset_id': 'hero', 'coordinate_space': 'cell_pixels',
            'required_landmarks': ['head', 'foot_l'],
            'landmarks': {f'f{i}': {'head': [8+i, 5], 'foot_l': [6+i, 13]} for i in range(3)},
            'sockets': {f'f{i}': {'hand_main': [9+i, 8], 'weapon_tip': [12+i, 7]} for i in range(3)},
            'required_sockets_by_action': {'walk': ['hand_main']},
            'depth_profiles': {'south': ['rear_arm', 'torso', 'front_arm']},
            'clip_depth_profile': {'walk_south': 'south'},
            'static_regions': [{'name': 'anchor', 'rect': [1, 14, 3, 2], 'clips': ['walk_south'], 'max_changed_ratio': 0}],
            'temporal_thresholds': {'silhouette_area_ratio': 0.5, 'bbox_center_px': 4, 'palette_jaccard_min': 0.3, 'landmark_step_px': 4},
            'locomotion': {'walk_south': {'stride_pixels': 6, 'cycle_ms': 300, 'pixels_per_world_unit': 0.2,
                                           'world_speed_units_per_s': 100, 'speed_tolerance_ratio': 0.01,
                                           'planted_foot_tolerance_px': 2}},
            'transitions': [{'from': 'walk_south', 'to': 'walk_south', 'intent': 'loop'}],
            'collision': {'f1': {'hurtboxes': [[4, 4, 6, 9]], 'hitboxes': []}},
            'provenance': {'frames': {f'f{i}': {'method': 'fixture', 'tool': 'unit-test', 'parent_frame_ids': []} for i in range(3)}},
            'performance_budget': {'max_total_rgba_bytes': 10000, 'max_simultaneous_actors': 2}
        }
        self.contract_path = self.root / 'production-metadata.json'
        self.contract_path.write_text(json.dumps(self.contract))

    def tearDown(self):
        self.temp.cleanup()

    def run_motion(self):
        m, root = s.load_manifest(self.manifest_path)
        return s.motion_check(m, root, self.contract_path)

    def test_motion_check_structural_and_calibration(self):
        report = self.run_motion()
        self.assertEqual(report['status'], 'review_required')
        self.assertFalse(report['errors'])
        self.assertEqual(report['locomotion'][0]['calibrated_speed_units_per_s'], 100.0)
        self.assertTrue(report['locomotion'][0]['within_declared_tolerance'])
        self.assertGreater(report['performance']['raw_rgba_bytes'], 0)

    def test_motion_check_flags_temporal_and_static_drift(self):
        im = Image.open(self.frames / 'f1.png').convert('RGBA')
        d = ImageDraw.Draw(im); d.rectangle((0, 0, 15, 15), fill=(250, 0, 0, 255)); im.save(self.frames / 'f1.png')
        report = self.run_motion()
        flags = {flag for row in report['temporal_findings'] for flag in row.get('flags', [])}
        self.assertIn('silhouette_area_jump', flags)
        self.assertIn('static_region_drift', flags)
        self.assertGreater(report['flagged_findings'], 0)
        self.assertEqual(report['art_approval'], 'not_evaluated')

    def test_motion_check_bad_socket_collision_and_transition_block(self):
        self.contract['sockets']['f0']['hand_main'] = [99, 4]
        self.contract['collision']['f1']['hurtboxes'] = [[14, 14, 4, 4]]
        self.contract['transitions'][0]['to'] = 'missing'
        self.contract_path.write_text(json.dumps(self.contract))
        report = self.run_motion()
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('outside cell' in e for e in report['errors']))
        self.assertTrue(any('exceeds cell' in e for e in report['errors']))
        self.assertTrue(any('transition' in e.lower() for e in report['errors']))

    def test_required_socket_missing_blocks_but_unobserved_landmark_warns(self):
        del self.contract['landmarks']['f2']['head']
        del self.contract['sockets']['f2']['hand_main']
        self.contract_path.write_text(json.dumps(self.contract))
        report = self.run_motion()
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('missing required landmarks' in w for w in report['warnings']))
        self.assertTrue(any('missing action sockets' in e for e in report['errors']))

    def test_loop_boundary_and_socket_jump_are_review_flags(self):
        self.contract['temporal_thresholds']['socket_step_px']=1.5
        self.contract_path.write_text(json.dumps(self.contract))
        report=self.run_motion()
        loop=[v for v in report['temporal_findings'] if v['from']=='f2' and v['to']=='f0']
        self.assertEqual(len(loop),1)
        self.assertIn('socket_jump',loop[0]['flags'])

    def test_malformed_metadata_is_structural_error_without_traceback(self):
        for field, value in [('sockets', ['bad']), ('landmarks', {'f0': ['bad']}), ('depth_profiles', {'south': [{}]}), ('clip_depth_profile', {'walk_south': []}), ('static_regions', [{'name':'x','rect':[0,0,1,1],'clips':5}])]:
            original=self.contract.get(field)
            self.contract[field]=value
            self.contract_path.write_text(json.dumps(self.contract))
            self.assertEqual(self.run_motion()['status'],'blocked',field)
            self.contract[field]=original

    def _make_member(self, folder, asset_id, height=9, include_attack=True):
        folder.mkdir()
        im = Image.new('RGBA', (16, 16)); ImageDraw.Draw(im).rectangle((5, 14-height, 10, 13), fill='white'); im.save(folder/'idle.png')
        clips = [{'name': 'idle_south', 'action': 'idle', 'direction': 'south', 'loop': True,
                  'events': [], 'frames': [{'id': f'{asset_id}_idle', 'path': 'idle.png', 'duration_ms': 100}]}]
        required = ['idle_south']
        if include_attack:
            clips.append({'name': 'attack_south', 'action': 'attack', 'direction': 'south', 'loop': False,
                          'events': [], 'frames': [{'id': f'{asset_id}_attack', 'path': 'idle.png', 'duration_ms': 100}]})
            required.append('attack_south')
        m = {'schema_version': 1, 'asset_id': asset_id, 'representation': 'pixel', 'cell_size': [16,16], 'origin': [8,14],
             'alpha_required': True, 'required_clips': required, 'clips': clips}
        (folder/'animation-set.json').write_text(json.dumps(m))
        return f'{folder.name}/animation-set.json', f'{asset_id}_idle'

    def test_family_check_pass_and_size_warning(self):
        a_path, a_ref = self._make_member(self.root/'a', 'a', 9)
        b_path, b_ref = self._make_member(self.root/'b', 'b', 6)
        family = {'schema_version': 1, 'family_id': 'roster', 'members': [
                    {'manifest': a_path, 'reference_frame_id': a_ref}, {'manifest': b_path, 'reference_frame_id': b_ref}],
                  'invariants': {'representation': 'pixel', 'cell_size': [16,16], 'required_actions': ['idle','attack'],
                                 'required_directions': ['south'], 'origin_y_tolerance_px': 1, 'visible_height_tolerance_ratio': 0.1}}
        fp=self.root/'family.json'; fp.write_text(json.dumps(family))
        report=s.family_check(fp, s.load_manifest)
        self.assertEqual(report['status'], 'review_required')
        self.assertFalse(report['errors'])
        self.assertTrue(any('visible reference height' in w for w in report['warnings']))

    def test_family_check_missing_required_action_blocks(self):
        a_path, a_ref = self._make_member(self.root/'a', 'a', 9)
        b_path, b_ref = self._make_member(self.root/'b', 'b', 9, include_attack=False)
        family = {'schema_version': 1, 'family_id': 'roster', 'members': [
                    {'manifest': a_path, 'reference_frame_id': a_ref}, {'manifest': b_path, 'reference_frame_id': b_ref}],
                  'invariants': {'required_actions': ['idle','attack'], 'required_directions': ['south']}}
        fp=self.root/'family.json'; fp.write_text(json.dumps(family))
        report=s.family_check(fp, s.load_manifest)
        self.assertEqual(report['status'], 'blocked')
        self.assertTrue(any('missing actions' in e for e in report['errors']))

    def test_family_requires_matrix_and_explicit_reasoned_exceptions(self):
        ap, ar=self._make_member(self.root/'a','a')
        bp, br=self._make_member(self.root/'b','b')
        for path in (ap,bp):
            mp=self.root/path
            m=json.loads(mp.read_text())
            m['clips'][1]['direction']='north'
            mp.write_text(json.dumps(m))
        family={'schema_version':1,'members':[{'manifest':ap,'reference_frame_id':ar},{'manifest':bp,'reference_frame_id':br}], 'invariants':{'required_actions':['idle','attack'],'required_directions':['south','north']}}
        fp=self.root/'family.json';fp.write_text(json.dumps(family))
        self.assertTrue(any('action-direction' in e for e in s.family_check(fp,s.load_manifest)['errors']))
        family['invariants']['allowed_missing_pairs']=[{'action':'idle','direction':'north','reason':'south-only menu idle'}, {'action':'attack','direction':'south','reason':'intentional prototype scope'}]
        fp.write_text(json.dumps(family))
        self.assertFalse(s.family_check(fp,s.load_manifest)['errors'])
        family['members'][1]=family['members'][0]
        fp.write_text(json.dumps(family))
        self.assertTrue(any('Duplicate' in e for e in s.family_check(fp,s.load_manifest)['errors']))

    def test_cli_motion_and_family_commands(self):
        import subprocess, sys
        out = self.root/'motion.json'
        r=subprocess.run([sys.executable, str(HERE/'sprite_tools.py'), 'motion-check', str(self.manifest_path), '--contract', str(self.contract_path), '--out', str(out)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(out.exists())
        a_path, a_ref = self._make_member(self.root/'a', 'a', 9)
        b_path, b_ref = self._make_member(self.root/'b', 'b', 9)
        fp=self.root/'family.json'; fp.write_text(json.dumps({'schema_version':1,'family_id':'r','members':[{'manifest':a_path,'reference_frame_id':a_ref},{'manifest':b_path,'reference_frame_id':b_ref}],'invariants':{'required_actions':['idle'],'required_directions':['south']}}))
        fout=self.root/'family-out.json'
        r=subprocess.run([sys.executable, str(HERE/'sprite_tools.py'), 'family-check', str(fp), '--out', str(fout)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(fout.exists())


if __name__ == '__main__':
    unittest.main()
