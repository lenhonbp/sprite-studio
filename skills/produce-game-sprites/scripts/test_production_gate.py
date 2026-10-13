"""Synthetic regressions for source/dependency/export correctness, not art approval."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_sprite_tools as fixture_module
import sprite_tools as s
from release_checks import vfx_pack_release_check
from test_vfx_pack import VfxPackFixture


class ProductionGateTests(unittest.TestCase):
    def setUp(self):
        self.fx = fixture_module.PipelineTests()
        self.fx.setUp()
        self.addCleanup(self.fx.tearDown)
        self.root, self.m = self.fx.root, self.fx.m

    def metadata(self, point):
        p = self.root / 'production-metadata.json'
        p.write_text(json.dumps({'schema_version':1,'asset_id':'fixture','sockets':{'f0':{'weapon_tip':point}}}))
        return p

    def test_invalid_socket_blocks_qa_and_pack(self):
        review = self.fx.review()
        self.metadata([999,999])
        r = s.assess(self.m,self.root,review)
        self.assertEqual(r['status'],'blocked')
        self.assertTrue(any('outside cell' in e for e in r['errors']))
        with self.assertRaises(s.ApprovalBlocked): s.pack(self.m,self.root,review,self.root/'release')
        self.assertFalse((self.root/'release').exists())

    def test_changed_metadata_invalidates_review(self):
        self.metadata([8,8]); review = self.fx.review()
        self.assertEqual(s.assess(self.m,self.root,review)['status'],'approved')
        self.metadata([9,8])
        self.assertTrue(any('stale' in e for e in s.assess(self.m,self.root,review)['errors']))

    def test_explicit_missing_dependency_blocks(self):
        self.m['production_contracts']={'metadata':'missing.json'}
        self.assertEqual(s.inspect(self.m,self.root)['status'],'blocked')

    def test_dependency_finding_requires_review(self):
        p=self.metadata([8,8]); data=json.loads(p.read_text());data['required_landmarks']=['head'];p.write_text(json.dumps(data))
        review=self.fx.review();r=s.assess(self.m,self.root,review)
        self.assertTrue(r['dependencies']['findings'])
        self.assertEqual(r['status'],'blocked')
        rv=json.loads(review.read_text());rv['finding_reviews']={f['id']:{'verdict':'pass','observation':'Synthetic gate-only rationale: missing observation remains a documented limitation.','evidence':['evidence.txt']} for f in r['dependencies']['findings']};review.write_text(json.dumps(rv))
        self.assertEqual(s.assess(self.m,self.root,review)['status'],'approved')

    def test_multipage_pack_and_exact_roundtrip(self):
        self.m['max_texture_size']=20; self.fx.save()
        out=self.root/'release';s.pack(self.m,self.root,self.fx.review(),out)
        timeline=json.loads((out/'animations.json').read_text())
        self.assertEqual(len(timeline['atlases']),2)
        self.assertFalse((out/'atlas.png').exists())
        for frame,page in zip(self.m['clips'][0]['frames'],timeline['atlases']):
            meta=json.loads((out/page['data']).read_text())['frames'][frame['id']]
            r=meta['frame']
            with Image.open(out/page['image']) as im, Image.open(self.root/frame['path']) as original:
                self.assertEqual(im.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])).tobytes(),original.tobytes())
        self.assertIn('atlas-001.png',(out/'sprite_frames.tres').read_text())

    def test_single_page_policy_blocks_before_output(self):
        self.m['max_texture_size']=20;self.m['atlas_policy']={'multipage':False}
        with self.assertRaises(ValueError):s.pack(self.m,self.root,self.fx.review(),self.root/'release')
        self.assertFalse((self.root/'release').exists())

    def test_trim_extrusion_preserves_offsets_and_rgba(self):
        self.m['atlas_policy']={'trim':True,'extrude':True}
        out=self.root/'release';s.pack(self.m,self.root,self.fx.review(),out)
        data=json.loads((out/'pixi-atlas.json').read_text())
        for frame in self.m['clips'][0]['frames']:
            meta=data['frames'][frame['id']];r,ss=meta['frame'],meta['spriteSourceSize']
            self.assertTrue(meta['trimmed']);self.assertEqual(ss['y'],3)
            with Image.open(out/'atlas.png') as atlas,Image.open(self.root/frame['path']) as original:
                restored=Image.new('RGBA',(16,16));restored.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(ss['x'],ss['y']))
                self.assertEqual(restored.tobytes(),original.tobytes())
                self.assertEqual(atlas.getpixel((r['x']-1,r['y'])),atlas.getpixel((r['x'],r['y'])))
        self.assertIn('margin = Rect2(4, 3, 9, 6)',(out/'sprite_frames.tres').read_text())

    def test_trim_refuses_hidden_rgba_loss(self):
        im=Image.open(self.root/'0.png').convert('RGBA');im.putpixel((0,0),(10,20,30,0));im.save(self.root/'0.png')
        self.m['atlas_policy']={'trim':True}
        with self.assertRaises(ValueError):s.pack(self.m,self.root,self.fx.review(),self.root/'release')

    def test_manifest_coverage_matrix_blocks_missing_pairs(self):
        self.m['coverage']={'actions':['test','idle'],'directions':['south','north']};self.fx.save()
        with self.assertRaisesRegex(ValueError,'combinations'):s.load_manifest(self.fx.manifest)

    def test_scaffold_declares_full_matrix_without_art(self):
        out=self.root/'scaffold'
        s.init_animation('wudang',['idle','walk','run','attack1','attack2','hit','death'],['n','ne','e','se','s','sw','w','nw'],[64,64],[32,56],'pixel',out,s.load_manifest)
        m,root=s.load_manifest(out/'animation-set.json')
        self.assertEqual(len(m['required_clips']),56)
        self.assertFalse(list(out.glob('**/*.png')))
        self.assertEqual(s.inspect(m,root)['status'],'blocked')

    def test_checkpoint_invalidates_metadata(self):
        self.metadata([8,8]);a=s.checkpoint(self.m,self.root,s.inspect)
        p=self.root/'checkpoint.json';p.write_text(json.dumps(a));self.metadata([9,8])
        b=s.checkpoint(self.m,self.root,s.inspect,p)
        self.assertTrue(b['review_invalidated']);self.assertTrue(b['dependencies_changed'])
        self.assertEqual(b['changed_frames'],[])
        self.assertEqual(b['clips_to_reinspect'],['test_south'])

    def test_repair_scope_rejects_metadata_only_edit(self):
        import shutil
        self.metadata([8,8])
        other=self.root/'candidate';shutil.copytree(self.root,other)
        (other/'production-metadata.json').write_text(json.dumps({'schema_version':1,'asset_id':'fixture','sockets':{'f0':{'weapon_tip':[9,8]}}}))
        r=s.repair_diff(self.fx.manifest,other/self.fx.manifest.name,[])
        self.assertEqual(r['status'],'blocked')
        self.assertEqual(r['changed_frames'],[])
        self.assertTrue(any('dependencies changed' in e for e in r['errors']))

    def test_family_cannot_substitute_same_id_manifest(self):
        wrong=json.loads(json.dumps(self.m));wrong['origin']=[7,13]
        (self.root/'other.json').write_text(json.dumps(wrong))
        peer=json.loads(json.dumps(self.m));peer['asset_id']='peer'
        (self.root/'peer.json').write_text(json.dumps(peer))
        family={'schema_version':1,'invariants':{},'members':[{'manifest':'other.json','reference_frame_id':'f0'},{'manifest':'peer.json','reference_frame_id':'f0'}]}
        (self.root/'family-contract.json').write_text(json.dumps(family))
        r=s.inspect(self.m,self.root)
        self.assertEqual(r['status'],'blocked')
        self.assertTrue(any('does not match the current' in e for e in r['errors']))
        family['members'][0]['manifest']=self.fx.manifest.name
        (self.root/'family-contract.json').write_text(json.dumps(family))
        self.assertEqual(s.inspect(self.m,self.root)['errors'],[])

    def test_family_bound_allowed_repair_preserves_peer(self):
        import shutil
        peer=json.loads(json.dumps(self.m));peer['asset_id']='peer'
        for i,frame in enumerate(peer['clips'][0]['frames']):
            frame['path']=f'peer{i}.png';shutil.copyfile(self.root/f'{i}.png',self.root/frame['path'])
        (self.root/'peer.json').write_text(json.dumps(peer))
        family={'schema_version':1,'members':[{'manifest':self.fx.manifest.name,'reference_frame_id':'f0'},{'manifest':'peer.json','reference_frame_id':'f0'}]}
        (self.root/'family-contract.json').write_text(json.dumps(family))
        other=self.root/'after';shutil.copytree(self.root,other)
        image=Image.open(other/'0.png').convert('RGBA');image.putpixel((5,5),(1,2,3,255));image.save(other/'0.png')
        self.assertEqual(s.repair_diff(self.fx.manifest,other/self.fx.manifest.name,['f0'])['status'],'scope_pass')
        image.save(other/'peer0.png')
        self.assertEqual(s.repair_diff(self.fx.manifest,other/self.fx.manifest.name,['f0'])['status'],'blocked')

    def test_slice_provenance_bound_to_current_frames_and_timing(self):
        import hashlib,shutil
        source=Image.new('RGBA',(32,16))
        for i in range(2):source.paste(Image.open(self.root/f'{i}.png'),(i*16,0))
        source.save(self.root/'source.png')
        data={'schema_version':1,'source':'source.png','source_rgba_sha256':hashlib.sha256(source.tobytes()).hexdigest(),'expected_ids':['f0','f1'],
              'frames':[{'id':f['id'],'output':f['path'],'source_rect':[i*16,0,16,16],'offset':[0,0],'origin':[8,13],'duration_ms':f['duration_ms']} for i,f in enumerate(self.m['clips'][0]['frames'])]}
        path=self.root/'slice-provenance.json';path.write_text(json.dumps(data))
        self.assertEqual(s.inspect(self.m,self.root)['errors'],[])
        shutil.copyfile(self.root/'0.png',self.root/'unrelated.png');data['frames'][0]['output']='unrelated.png';path.write_text(json.dumps(data))
        self.assertTrue(any('not the current frame' in e for e in s.inspect(self.m,self.root)['errors']))
        data['frames'][0]['output']='0.png';data['frames'][0]['duration_ms']=1;path.write_text(json.dumps(data))
        self.assertTrue(any('timing differs' in e for e in s.inspect(self.m,self.root)['errors']))

    def test_vfx_nested_contract_cannot_approve_other_sources(self):
        with tempfile.TemporaryDirectory() as d:
            fx=VfxPackFixture(d).build();effect=fx.spec['effects'][0];root=Path(d)
            cp=root/effect['vfx_contract'];contract=json.loads(cp.read_text())
            nested=root/'nested';nested.mkdir()
            for frame in contract['frames']:
                dest=nested/frame['path'];dest.parent.mkdir(parents=True,exist_ok=True)
                image=Image.open(root/frame['path']).convert('RGBA');image.putpixel((10,10),(0,255,0,255));image.save(dest)
            (nested/'contract.json').write_text(json.dumps(contract));effect['vfx_contract']='nested/contract.json'
            Path(fx.spec_path()).write_text(json.dumps(fx.spec))
            from vfx_pack import vfx_pack_bundle_check
            r=vfx_pack_bundle_check(fx.spec_path(),fx.bundle_dir())
            self.assertEqual(r['status'],'blocked')
            self.assertTrue(any('source identity' in e for e in r['errors']))

    def test_vfx_bundle_ready_does_not_grant_release(self):
        with tempfile.TemporaryDirectory() as d:
            fx=VfxPackFixture(d).build();r=vfx_pack_release_check(fx.spec_path(),fx.bundle_dir())
            self.assertEqual(r['status'],'blocked')
            self.assertTrue(any('review' in e for e in r['errors']))


if __name__=='__main__':unittest.main()
