"""Generated/source sheet separability checks.

This gate answers a narrow production question: can a reviewed aggregate sheet be
deterministically sliced into independent poses without reconstructing hidden pixels?
It does not approve art quality.
"""
from __future__ import annotations
import json, math, hashlib
from pathlib import Path
from path_utils import is_safe_relative_path, resolve_under


def _rect(v):
    return isinstance(v,list) and len(v)==4 and all(type(x) is int for x in v) and v[0]>=0 and v[1]>=0 and v[2]>0 and v[3]>0

def sheet_separability_check(contract_path):
    from PIL import Image
    p=Path(contract_path).resolve(); data=json.loads(p.read_text())
    if not isinstance(data,dict) or data.get('schema_version')!=1:
        raise ValueError('Sheet layout must be a schema_version 1 object')
    source=data.get('source')
    if not is_safe_relative_path(source):
        raise ValueError('source must be a safe project-relative path')
    src=resolve_under(p.parent,source)
    groups=data.get('groups')
    if not isinstance(groups,list) or not groups:
        raise ValueError('groups must be a nonempty array')
    alpha_threshold=data.get('alpha_threshold',12)
    max_ratio=data.get('max_valley_to_peak_ratio',0.18)
    edge_limit=data.get('max_edge_opaque_ratio',0.02)
    if type(alpha_threshold) is not int or not 0<=alpha_threshold<=254:
        raise ValueError('alpha_threshold must be integer 0..254')
    if type(max_ratio) not in (int,float) or not 0<=max_ratio<=1:
        raise ValueError('max_valley_to_peak_ratio must be 0..1')
    if type(edge_limit) not in (int,float) or not 0<=edge_limit<=1:
        raise ValueError('max_edge_opaque_ratio must be 0..1')
    with Image.open(src) as im0:
        im=im0.convert('RGBA')
    minimum_gutter=data.get('minimum_gutter_px', 2)
    if type(minimum_gutter) is not int or minimum_gutter < 1:
        raise ValueError('minimum_gutter_px must be a positive integer')
    source_sha256=hashlib.sha256(src.read_bytes()).hexdigest()
    expected=data.get('source_sha256')
    if expected is not None and (not isinstance(expected,str) or len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected)):
        raise ValueError('source_sha256 must be a lowercase SHA256 hex digest')
    errors=[]; risks=[]; observations=[]
    if expected is not None and expected != source_sha256:
        errors.append('source_sha256 does not match current source sheet')
    seen_names=set()
    for g in groups:
        if not isinstance(g,dict) or not isinstance(g.get('name'),str) or not g['name'] or not _rect(g.get('rect')):
            errors.append('Each group needs name and rect [x,y,w,h]'); continue
        if g['name'] in seen_names:
            errors.append(f"{g['name']}: duplicate group name"); continue
        seen_names.add(g['name'])
        if type(g.get('allow_edge_contact',False)) is not bool:
            errors.append(f"{g['name']}: allow_edge_contact must be boolean"); continue
        x,y,w,h=g['rect']
        if x+w>im.width or y+h>im.height:
            errors.append(f"{g['name']}: rect exceeds source bounds"); continue
        centers=g.get('pose_centers')
        if not isinstance(centers,list) or not centers or not all(type(v) is int and 0<=v<w for v in centers) or centers!=sorted(set(centers)):
            errors.append(f"{g['name']}: pose_centers must be unique sorted local-x integers inside rect"); continue
        a=im.crop((x,y,x+w,y+h)).getchannel('A')
        pix=a.load()
        proj=[sum(1 for yy in range(h) if pix[xx,yy]>alpha_threshold) for xx in range(w)]
        peaks=[]
        for c in centers:
            lo=max(0,c-4); hi=min(w,c+5); peaks.append(max(proj[lo:hi]) if hi>lo else proj[c])
        pair_rows=[]
        for i in range(len(centers)-1):
            a0,b0=centers[i],centers[i+1]
            valley=min(proj[a0:b0+1]) if b0>a0 else proj[a0]
            denom=max(1,min(peaks[i],peaks[i+1]))
            ratio=valley/denom
            row={'from_center':a0,'to_center':b0,'valley_opaque_px':valley,'peak_floor_px':denom,'valley_to_peak_ratio':round(ratio,4)}
            longest=run=0
            for value in proj[a0:b0+1]:
                run=run+1 if value==0 else 0
                longest=max(longest,run)
            row['transparent_gutter_width_px']=longest
            if longest < minimum_gutter:
                risks.append(f"{g['name']}: centers {a0}->{b0} transparent gutter {longest}px below minimum {minimum_gutter}px")
            if ratio>max_ratio:
                row['risk']='pose_overlap_or_no_gutter'
                risks.append(f"{g['name']}: centers {a0}->{b0} valley/peak {ratio:.3f} exceeds {max_ratio:.3f}; auto-slice would risk amputating or mixing poses")
            pair_rows.append(row)
        edge_ratios={
            'left':sum(pix[0,yy]>alpha_threshold for yy in range(h))/h,
            'right':sum(pix[w-1,yy]>alpha_threshold for yy in range(h))/h,
            'top':sum(pix[xx,0]>alpha_threshold for xx in range(w))/w,
            'bottom':sum(pix[xx,h-1]>alpha_threshold for xx in range(w))/w,
        }
        edge_ratio=max(edge_ratios.values())
        if edge_ratio>edge_limit and not g.get('allow_edge_contact',False):
            risks.append(f"{g['name']}: visible source content touches group edges ({edge_ratio:.3f}); source may already be clipped or neighboring content may intrude")
        observations.append({'name':g['name'],'rect':g['rect'],'pose_centers':centers,'peak_opaque_px':peaks,'pairs':pair_rows,'edge_opaque_ratio':round(edge_ratio,4),'edge_ratios':edge_ratios})
    return {'status':'blocked' if errors else ('blocked_for_auto_slice' if risks else 'separable'),
            'source_binding':{'source':source,'sha256':source_sha256},'confidence':'heuristic_alpha_projection','minimum_gutter_px':minimum_gutter,
            'art_approval':'not_evaluated','errors':errors,'risks':risks,'groups':observations,
            'limitation':'This check estimates source separability from alpha/gutters. It cannot reconstruct pixels already occluded in a composited aggregate sheet and does not approve visual quality.'}
