import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from verify_slices import verify


class SliceVerification(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = Image.new('RGBA', (8, 4))
        self.src.putpixel((1, 1), (255, 0, 0, 255))
        self.src.save(self.root/'source.png')
        self.src.crop((0, 0, 4, 4)).save(self.root/'a.png')
        self.src.crop((4, 0, 8, 4)).save(self.root/'b.png')
        self.data = {'schema_version': 1, 'source': 'source.png',
                     'source_rgba_sha256': hashlib.sha256(self.src.tobytes()).hexdigest(),
                     'expected_ids': ['a', 'b'], 'frames': [
                         {'id': name, 'output': name+'.png', 'source_rect': [x, 0, 4, 4],
                          'offset': [0, 0], 'origin': [2, 4], 'duration_ms': 100}
                         for name, x in [('a', 0), ('b', 4)]]}

    def run_verify(self):
        path = self.root/'provenance.json'
        path.write_text(json.dumps(self.data))
        return verify(path)

    def test_full_cells_and_empty_slot(self):
        self.assertEqual(self.run_verify()['status'], 'pass')

    def test_lossless_trim_offset(self):
        self.src.crop((1, 1, 2, 2)).save(self.root/'a.png')
        self.data['frames'][0]['offset'] = [1, 1]
        self.assertEqual(self.run_verify()['status'], 'pass')

    def test_wrong_trim_offset(self):
        self.src.crop((1, 1, 2, 2)).save(self.root/'a.png')
        self.assertEqual(self.run_verify()['status'], 'blocked')

    def test_source_mutation(self):
        self.data['source_rgba_sha256'] = 'wrong'
        self.assertEqual(self.run_verify()['status'], 'blocked')

    def test_missing_empty_slot(self):
        self.data['frames'].pop()
        self.assertEqual(self.run_verify()['status'], 'blocked')

    def test_duplicate_output(self):
        self.data['frames'][1]['output'] = './a.png'
        with self.assertRaises(ValueError):
            self.run_verify()

    def test_path_escape(self):
        self.data['frames'][0]['output'] = '../a.png'
        with self.assertRaises(ValueError):
            self.run_verify()

    def test_out_of_bounds(self):
        self.data['frames'][0]['source_rect'][2] = 9
        with self.assertRaises(ValueError):
            self.run_verify()

    def test_origin_drift(self):
        self.data['frames'][1]['origin'] = [1, 4]
        self.assertEqual(self.run_verify()['status'], 'blocked')

    def test_invalid_duration(self):
        self.data['frames'][0]['duration_ms'] = 0
        with self.assertRaises(ValueError):
            self.run_verify()


if __name__ == '__main__':
    unittest.main()
