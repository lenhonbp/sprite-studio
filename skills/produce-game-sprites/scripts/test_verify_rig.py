#!/usr/bin/env python3
"""Regression tests for verify_rig.py with synthetic fixtures."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

SCRIPT = Path(__file__).with_name('verify_rig.py')


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


class VerifyRigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        # 16x16 master: body rect + head circle
        self.master = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.master)
        d.rectangle((5, 6, 10, 14), fill=(120, 80, 50, 255))   # torso+legs
        d.ellipse((5, 1, 10, 6), fill=(200, 150, 110, 255))     # head
        self.master.save(self.root / 'master.png')
        self.parts = self.root / 'parts'
        self.parts.mkdir()
        # split into two full-canvas parts
        head = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        head.alpha_composite(self.master.crop((0, 0, 16, 7)))
        head.save(self.parts / 'head.png')
        body = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        body.alpha_composite(self.master.crop((0, 6, 16, 16)), (0, 6))
        body.save(self.parts / 'body.png')
        self.rig = {
            'cell_size': [16, 16], 'origin': [8, 14],
            'joints': {'neck': [8, 6]},
            'parts': [
                {'name': 'body', 'rect': [0, 6, 16, 10],
                 'pivot_body': [8, 6], 'pivot_joint': 'neck', 'draw_order': 1},
                {'name': 'head', 'rect': [0, 0, 16, 7],
                 'pivot_body': [8, 6], 'pivot_joint': 'neck', 'draw_order': 2},
            ],
        }
        (self.root / 'rig.json').write_text(json.dumps(self.rig))

    def tearDown(self):
        self.temp.cleanup()

    def base_args(self):
        return [str(self.root / 'rig.json'), str(self.root / 'master.png'),
                str(self.parts)]

    def test_perfect_reassembly_passes(self):
        r = run(*self.base_args())
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out['status'], 'pass')
        self.assertGreaterEqual(out['ncc'], 0.99)

    def test_shifted_part_fails(self):
        # simulate misalignment: shift body part 2px right
        bad = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        crop = Image.open(self.parts / 'body.png').crop((0, 6, 16, 16))
        bad.alpha_composite(crop, (2, 6))
        bad.save(self.parts / 'body.png')
        r = run(*self.base_args())
        self.assertEqual(r.returncode, 1, r.stdout)
        out = json.loads(r.stdout)
        self.assertEqual(out['status'], 'fail')
        self.assertLess(out['ncc'], 0.99)

    def test_crop_sized_parts_pass(self):
        # parts stored as crops matching rect size
        for p in self.parts.glob('*.png'):
            p.unlink()
        self.master.crop((0, 0, 16, 7)).save(self.parts / 'head.png')
        self.master.crop((0, 6, 16, 16)).save(self.parts / 'body.png')
        r = run(*self.base_args())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)['status'], 'pass')

    def test_missing_part_fails(self):
        (self.parts / 'head.png').unlink()
        r = run(*self.base_args())
        self.assertEqual(r.returncode, 1)
        self.assertIn('missing part file', r.stdout)

    def test_pivot_off_part_fails(self):
        self.rig['parts'][0]['pivot_body'] = [0, 0]  # transparent corner
        del self.rig['parts'][0]['pivot_joint']  # isolate opacity failure from joint consistency
        (self.root / 'rig.json').write_text(json.dumps(self.rig))
        r = run(*self.base_args())
        self.assertEqual(r.returncode, 1)
        self.assertIn('not on opaque part pixels', r.stdout)

    def test_alpha_change_fails_even_if_grayscale_ncc_passes(self):
        for path in self.parts.glob('*.png'):
            im = Image.open(path).convert('RGBA')
            im.putalpha(im.getchannel('A').point(lambda v: 1 if v else 0))
            im.save(path)
        result = run(*self.base_args())
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertFalse(report['rgba_exact'])
        self.assertGreater(report['rgba_changed_pixels'], 0)

    def test_malformed_rig_and_joint_mismatch_exit_cleanly(self):
        for rig in ([], {'cell_size': 'bad'}, {**self.rig, 'parts': [{'name':'../escape'}]}):
            (self.root/'rig.json').write_text(json.dumps(rig))
            result=run(*self.base_args())
            self.assertEqual(result.returncode,2)
            self.assertNotIn('Traceback',result.stderr)
        self.rig['parts'][0]['pivot_body']=[7,6]
        (self.root/'rig.json').write_text(json.dumps(self.rig))
        result=run(*self.base_args())
        self.assertEqual(result.returncode,2)
        self.assertIn('pivot_joint',result.stderr)

    def test_bad_input_exits_2(self):
        r = run(str(self.root / 'nope.json'), str(self.root / 'master.png'),
                str(self.parts))
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
