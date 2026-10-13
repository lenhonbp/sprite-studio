import json, tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
from sheet_checks import sheet_separability_check

class SheetChecks(unittest.TestCase):
    def make(self, overlap=False):
        td=tempfile.TemporaryDirectory(); root=Path(td.name)
        im=Image.new('RGBA',(100,50),(0,0,0,0)); d=ImageDraw.Draw(im)
        d.ellipse((10,10,35,40),fill=(255,255,255,255))
        if overlap:
            d.rectangle((34,20,66,30),fill=(255,255,255,255))
        d.ellipse((65,10,90,40),fill=(255,255,255,255)); im.save(root/'sheet.png')
        c={'schema_version':1,'source':'sheet.png','max_valley_to_peak_ratio':0.18,'groups':[{'name':'g','rect':[0,0,100,50],'pose_centers':[22,78]}]}
        (root/'layout.json').write_text(json.dumps(c)); return td,root
    def test_separable(self):
        td,r=self.make(False); self.addCleanup(td.cleanup)
        self.assertEqual(sheet_separability_check(r/'layout.json')['status'],'separable')
    def test_overlap_blocks_auto_slice(self):
        td,r=self.make(True); self.addCleanup(td.cleanup)
        q=sheet_separability_check(r/'layout.json'); self.assertEqual(q['status'],'blocked_for_auto_slice'); self.assertTrue(q['risks'])
    def test_top_edge_contact_blocks_and_binding_tracks_source(self):
        td,r=self.make(False);self.addCleanup(td.cleanup)
        before=sheet_separability_check(r/'layout.json')['source_binding']['sha256']
        im=Image.open(r/'sheet.png').convert('RGBA')
        ImageDraw.Draw(im).rectangle((10,0,35,10), fill='white');im.save(r/'sheet.png')
        q=sheet_separability_check(r/'layout.json')
        self.assertEqual(q['status'],'blocked_for_auto_slice')
        self.assertNotEqual(before,q['source_binding']['sha256'])
        c=json.loads((r/'layout.json').read_text());c['source_sha256']=before;(r/'layout.json').write_text(json.dumps(c))
        self.assertEqual(sheet_separability_check(r/'layout.json')['status'],'blocked')

    def test_one_pixel_gutter_not_sufficient(self):
        td,r=self.make(False);self.addCleanup(td.cleanup)
        im=Image.new('RGBA',(100,50))
        d=ImageDraw.Draw(im);d.rectangle((10,10,49,40),fill='white');d.rectangle((51,10,90,40),fill='white');im.save(r/'sheet.png')
        q=sheet_separability_check(r/'layout.json')
        self.assertEqual(q['status'],'blocked_for_auto_slice')
        self.assertEqual(q['groups'][0]['pairs'][0]['transparent_gutter_width_px'],1)

    def test_path_escape_rejected(self):
        td,r=self.make(False); self.addCleanup(td.cleanup)
        c=json.loads((r/'layout.json').read_text()); c['source']='../outside.png'; (r/'bad.json').write_text(json.dumps(c))
        with self.assertRaises(ValueError): sheet_separability_check(r/'bad.json')
if __name__=='__main__': unittest.main()
