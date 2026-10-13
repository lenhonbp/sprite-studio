#!/usr/bin/env python3
"""Provider-independent game-art preparation, sprite/UI validation, review binding and fixed-cell export.
Python 3.10+; Pillow for raster operations. No network or generation calls.
"""
import argparse
import base64
import io
import hashlib
import html
import json
import math
import shutil
import sys
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_support import bind_evidence, evidence_errors, keypose_check, runtime_template, runtime_verify
from quality_checks import motion_check, family_check
from ui_checks import ui_check, ui_slice, ui_review_template, ui_qa, ui_runtime_template, ui_runtime_verify
from artifact_checks import (environment_check, vfx_check, environment_review_template, environment_qa, environment_runtime_template, environment_runtime_verify, vfx_review_template, vfx_qa, vfx_runtime_template, vfx_runtime_verify)
from sheet_checks import sheet_separability_check
from path_utils import is_safe_relative_path, resolve_under
from vfx_pack import vfx_pack_plan, vfx_pack_bundle_check
from production_gate import dependency_paths, check_dependencies
from atlas_export import build_atlases
from workflow_tools import init_animation, checkpoint
from release_checks import sprite_release_check, vfx_pack_release_check

class ApprovalBlocked(ValueError):
    """Valid request cannot proceed before approval."""


CHECKS = ('identity', 'camera_facing', 'anatomy_grip', 'motion_timing',
          'origin_ground', 'alpha_clipping', 'transitions_events')


def dump(path, data):
    path = Path(path)
    if path.exists():
        raise ValueError(f'Refusing to overwrite: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def positive_int(value):
    return type(value) is int and value > 0


def safe_name(value):
    return isinstance(value, str) and value and all(c.isascii() and (c.isalnum() or c in '_-') for c in value)


def load_manifest(path):
    path = Path(path).resolve()
    m = json.loads(path.read_text())
    if not isinstance(m, dict):
        raise ValueError('Manifest must be an object')
    if type(m.get('schema_version')) is not int or m['schema_version'] != 1:
        raise ValueError('Unsupported schema_version; expected 1')
    if not safe_name(m.get('asset_id')):
        raise ValueError('asset_id must be a nonempty ASCII name')
    if m.get('representation') not in ('pixel', 'hd'):
        raise ValueError('representation must be pixel or hd')
    size = m.get('cell_size')
    if not isinstance(size, list) or len(size) != 2 or not all(positive_int(v) for v in size):
        raise ValueError('cell_size must contain two positive integers')
    origin = m.get('origin')
    if not isinstance(origin, list) or len(origin) != 2 or not all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= size[i] for i, v in enumerate(origin)):
        raise ValueError('origin must be finite cell-local coordinates')
    if m.get('alpha_policy', 'soft') not in ('binary', 'soft'):
        raise ValueError('alpha_policy must be binary or soft')
    if 'max_colors' in m and (m['representation'] != 'pixel' or not positive_int(m['max_colors'])):
        raise ValueError('max_colors is a positive pixel-art color budget')
    if type(m.get('alpha_required')) is not bool:
        raise ValueError('alpha_required must be a boolean')
    if not positive_int(m.get('max_texture_size', 2048)):
        raise ValueError('max_texture_size must be a positive integer')
    if type(m.get('gutter', 2)) is not int or m.get('gutter', 2) < 0:
        raise ValueError('gutter must be a nonnegative integer')
    policy = m.get('atlas_policy', {})
    if not isinstance(policy, dict) or set(policy) - {'multipage', 'trim', 'extrude'} or any(type(v) is not bool for v in policy.values()):
        raise ValueError('atlas_policy permits boolean multipage, trim and extrude only')
    dependency_paths(m, path.parent)
    target = m.get('engine_target')
    if target is not None and (not isinstance(target, dict) or target.get('name') not in ('PixiJS', 'Godot') or
                               not isinstance(target.get('version'), str) or not target['version'].strip()):
        raise ValueError('engine_target requires name PixiJS/Godot and an exact nonempty version')
    clips = m.get('clips')
    required = m.get('required_clips')
    if not isinstance(clips, list) or not clips or not isinstance(required, list) or not required or not all(safe_name(n) for n in required) or len(set(required)) != len(required):
        raise ValueError('Provide nonempty clips and unique required_clips')
    names, ids = set(), set()
    for c in clips:
        if not isinstance(c, dict):
            raise ValueError('Each clip must be an object')
        name = c.get('name')
        if not safe_name(name) or name in names:
            raise ValueError('Invalid or duplicate clip name')
        names.add(name)
        if not safe_name(c.get('action')) or not safe_name(c.get('direction')) or type(c.get('loop')) is not bool:
            raise ValueError(f'{name}: action, direction and boolean loop required')
        if not isinstance(c.get('frames'), list) or not c['frames']:
            raise ValueError(f'{name}: nonempty frames required')
        total = 0
        for f in c['frames']:
            if not isinstance(f, dict):
                raise ValueError('Each frame must be an object')
            if not safe_name(f.get('id')) or f['id'] in ids:
                raise ValueError('Invalid or duplicate frame ID')
            ids.add(f['id'])
            if not is_safe_relative_path(f.get('path')):
                raise ValueError(f"{f['id']}: safe project-relative frame path required")
            if not positive_int(f.get('duration_ms')):
                raise ValueError(f"{f['id']}: positive integer duration_ms required")
            total += f['duration_ms']
        events = c.get('events', [])
        if not isinstance(events, list):
            raise ValueError(f'{name}: events must be an array')
        for e in events:
            if not isinstance(e, dict):
                raise ValueError('Each event must be an object')
            if not safe_name(e.get('name')) or type(e.get('time_ms')) is not int or not 0 <= e['time_ms'] < total:
                raise ValueError(f'{name}: event must have a name and time inside the clip')
    if not set(required) <= names:
        raise ValueError('Missing required clips: ' + ', '.join(sorted(set(required) - names)))
    coverage = m.get('coverage')
    if coverage is not None:
        if not isinstance(coverage, dict):
            raise ValueError('coverage must be an object')
        for key in ('actions', 'directions'):
            values = coverage.get(key)
            if not isinstance(values, list) or not values or not all(safe_name(v) for v in values) or len(values) != len(set(values)):
                raise ValueError(f'coverage/{key}: unique nonempty names required')
        exceptions = coverage.get('exceptions', [])
        if not isinstance(exceptions, list) or not all(isinstance(v, list) and len(v) == 2 and v[0] in coverage['actions'] and v[1] in coverage['directions'] for v in exceptions):
            raise ValueError('coverage/exceptions must contain declared [action,direction] pairs')
        actual = {(c['action'], c['direction']) for c in clips if c['name'] in required}
        missing = {(a, d) for a in coverage['actions'] for d in coverage['directions']} - {tuple(v) for v in exceptions} - actual
        if missing:
            raise ValueError('Missing required action/direction combinations: ' + ', '.join(a+'/'+d for a,d in sorted(missing)))
    return m, path.parent


def frames(m):
    for c in m['clips']:
        for f in c['frames']:
            yield c, f


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(m, root):
    from PIL import Image
    errors, warnings, observations, bindings = [], [], [], {}
    for c, f in frames(m):
        p = resolve_under(root, f['path'])
        try:
            with Image.open(p) as src:
                if getattr(src, 'n_frames', 1) != 1:
                    raise ValueError('Frame input is animated; extract first')
                im = src.convert('RGBA')
                alpha = im.getchannel('A')
                bounds = alpha.getbbox()
                if list(im.size) != m['cell_size']:
                    errors.append(f"{f['id']}: size {im.size} does not match cell_size")
                if bounds is None:
                    errors.append(f"{f['id']}: empty transparent frame")
                if m['alpha_required'] and alpha.getextrema()[0] == 255:
                    errors.append(f"{f['id']}: no transparent pixels")
                if bounds and (bounds[0] == 0 or bounds[1] == 0 or bounds[2] == im.width or bounds[3] == im.height):
                    warnings.append(f"{f['id']}: visible pixels touch a canvas edge; inspect clipping")
                rgba_bytes = im.tobytes()
                visible_colors = {tuple(rgba_bytes[i:i+3]) for i in range(0, len(rgba_bytes), 4) if rgba_bytes[i+3] > 0}
                soft_pixels = sum(alpha.histogram()[1:255])
                if m.get('alpha_policy') == 'binary' and soft_pixels:
                    errors.append(f"{f['id']}: soft alpha violates binary alpha policy")
                if 'max_colors' in m and len(visible_colors) > m['max_colors']:
                    errors.append(f"{f['id']}: visible RGB color count exceeds max_colors")
                pixel_hash = hashlib.sha256(im.tobytes()).hexdigest()
                observations.append({'id': f['id'], 'size': list(im.size), 'alpha_bounds': bounds, 'pixel_hash': pixel_hash, 'visible_rgb_colors': len(visible_colors), 'soft_alpha_pixels': soft_pixels})
                bindings[f['id']] = file_hash(p)
        except (OSError, ValueError) as e:
            errors.append(f"{f['id']}: {e}")
    by_id = {x['id']: x for x in observations}
    for c in m['clips']:
        hashes = [by_id[f['id']]['pixel_hash'] for f in c['frames'] if f['id'] in by_id]
        if len(hashes) > 1 and len(set(hashes)) == 1:
            warnings.append(f"{c['name']}: all frames are identical; inspect intended motion")
        elif len(set(hashes)) < len(hashes):
            warnings.append(f"{c['name']}: repeated frames; inspect authored holds")
    dependencies = check_dependencies(m, root, load_manifest)
    errors.extend(dependencies['errors'])
    canonical = json.dumps({'manifest': m, 'files': bindings, 'dependencies': dependencies['files']}, sort_keys=True, separators=(',', ':')).encode()
    return {'status': 'blocked' if errors else 'technical_pass', 'binding': hashlib.sha256(canonical).hexdigest(),
            'errors': errors, 'warnings': warnings, 'frames': observations, 'dependencies': dependencies}


def assess(m, root, review_path):
    report = inspect(m, root)
    review = json.loads(Path(review_path).read_text())
    if not isinstance(review, dict) or not isinstance(review.get('clips'), dict):
        raise ValueError('Review must be an object with a clips object')
    if review.get('binding') != report['binding']:
        report['errors'].append('Review is stale or belongs to different inputs; create a new blank review')
    if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip():
        report['errors'].append('Actual reviewer identity is required')
    review_rows = []
    if review.get('schema_version') != 2:
        report['errors'].append('Review schema 2 required; create a new bound template')
    for c in m['clips']:
        checks = review.get('clips', {}).get(c['name'], {})
        if not isinstance(checks, dict):
            checks = {}
        for key in CHECKS:
            row = checks.get(key, {})
            if not isinstance(row, dict):
                row = {}
            if row.get('verdict') != 'pass' or not isinstance(row.get('observation'), str) or not row['observation'].strip():
                report['errors'].append(f"{c['name']}/{key}: incomplete or failing visual review")
            review_rows.append((f"{c['name']}/{key}", row))
    finding_reviews = review.get('finding_reviews', {})
    if not isinstance(finding_reviews, dict):
        finding_reviews = {}
    for finding in report['dependencies']['findings']:
        fid = finding['id']
        row = finding_reviews.get(fid, {})
        if not isinstance(row, dict):
            row = {}
        if row.get('verdict') != 'pass' or not isinstance(row.get('observation'), str) or not row['observation'].strip():
            report['errors'].append(f'{fid}: inspect and resolve this dependency finding')
        review_rows.append((fid, row))
    report['errors'] += evidence_errors(review, Path(review_path).resolve().parent, review_rows)
    report['status'] = 'approved' if not report['errors'] else 'blocked'
    report['runtime_status'] = 'not_tested'
    return report


def new_dir(path):
    p = Path(path)
    if p.exists():
        raise ValueError(f'Refusing to overwrite directory: {p}')
    p.mkdir(parents=True)
    return p


def preview(m, root, output):
    from PIL import Image, ImageDraw
    out = new_dir(output)
    w, h = m['cell_size']
    count = sum(len(c['frames']) for c in m['clips'])
    cols = min(8, count)
    sheet = Image.new('RGB', (cols * (w + 8), math.ceil(count / cols) * (h + 24)), '#dddddd')
    draw = ImageDraw.Draw(sheet)
    n, cards = 0, []
    for c in m['clips']:
        images = []
        for f in c['frames']:
            with Image.open(resolve_under(root, f['path'])) as src:
                im = src.convert('RGBA')
            images.append(im)
            x, y = n % cols * (w + 8), n // cols * (h + 24)
            sheet.paste(im, (x, y), im)
            draw.text((x, y + h + 2), f['id'][:18], fill='black')
            n += 1
        target = out / (c['name'] + '.webp')
        opts = {'loop': 0} if c['loop'] else {'loop': 1}
        images[0].save(target, format='WEBP', save_all=True, append_images=images[1:],
                       duration=[f['duration_ms'] for f in c['frames']], lossless=True, **opts)
        duration = sum(f['duration_ms'] for f in c['frames'])
        cards.append(f'<section><h2>{html.escape(c["name"])}</h2><p>{duration} ms; loop={c["loop"]}. WebP preview; verify one-shot hold in engine.</p><img src="{target.name}" width="{w}" height="{h}"></section>')
    sheet.save(out / 'contact-sheet.png')
    assets = Path(__file__).resolve().parent.parent / 'assets'
    encoded = {}
    for _, f in frames(m):
        with Image.open(resolve_under(root, f['path'])) as source:
            buffer = io.BytesIO()
            source.convert('RGBA').save(buffer, format='PNG')
            encoded[f['id']] = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
    payload = json.dumps({'manifest': m, 'images': encoded}).replace('<', chr(92) + 'u003c')
    player = (assets / 'player.html').read_text().replace('__SPRITE_DATA__', payload)
    (out / 'index.html').write_text(player)
    shutil.copyfile(assets / 'timeline.js', out / 'timeline.js')
    dump(out / 'preview-binding.json', inspect(m, root))


def pack(m, root, review_path, output):
    from PIL import Image
    report = assess(m, root, review_path)
    if report['status'] != 'approved':
        raise ApprovalBlocked('Export blocked: ' + '; '.join(report['errors']))
    fs = list(frames(m))
    w, h = m['cell_size']
    pages, mapping = build_atlases(m, root, fs, resolve_under)
    out = new_dir(output)
    atlas_rows, texture_bytes = [], 0
    for i, page in enumerate(pages):
        image_name = 'atlas.png' if len(pages) == 1 else f'atlas-{i:03d}.png'
        data_name = 'pixi-atlas.json' if len(pages) == 1 else f'pixi-atlas-{i:03d}.json'
        atlas = page['image']
        atlas.save(out / image_name)
        # Reopen written bytes and reconstruct every frame before release.
        with Image.open(out / image_name) as decoded:
            for fid, meta in page['frames'].items():
                r, ss = meta['frame'], meta['spriteSourceSize']
                restored = Image.new('RGBA', (w, h))
                restored.paste(decoded.convert('RGBA').crop((r['x'], r['y'], r['x']+r['w'], r['y']+r['h'])), (ss['x'], ss['y']))
                original_frame = next(f for _, f in fs if f['id'] == fid)
                with Image.open(resolve_under(root, original_frame['path'])) as original:
                    if restored.tobytes() != original.convert('RGBA').tobytes():
                        raise ValueError(f'{fid}: exported RGBA round-trip failed')
        dump(out / data_name, {'frames': page['frames'],
                              'animations': {c['name']: [f['id'] for f in c['frames'] if f['id'] in page['frames']] for c in m['clips']},
                              'meta': {'image': image_name, 'format': 'RGBA8888', 'size': {'w': atlas.width, 'h': atlas.height}, 'scale': '1'}})
        atlas_rows.append({'image': image_name, 'data': data_name, 'width': atlas.width, 'height': atlas.height})
        texture_bytes += atlas.width * atlas.height * 4
    timeline = [{**c, 'frames': [{'id': f['id'], 'duration_ms': f['duration_ms']} for f in c['frames']]} for c in m['clips']]
    dump(out / 'animations.json', {'schema_version': 1, 'asset_id': m['asset_id'], 'cell_size': m['cell_size'],
                                  'origin': m['origin'], 'representation': m['representation'], 'clips': timeline, 'atlases': atlas_rows})
    resource = ['[gd_resource type="SpriteFrames" load_steps=' + str(len(fs) + len(pages) + 1) + ' format=3]', '']
    resource += [f'[ext_resource type="Texture2D" path="{a["image"]}" id="{i+1}"]' for i, a in enumerate(atlas_rows)]
    for i, (_, f) in enumerate(fs):
        r = mapping[f['id']]['frame']
        meta = mapping[f['id']]
        ss = meta['spriteSourceSize']
        resource += ['', f'[sub_resource type="AtlasTexture" id="f{i}"]', f'atlas = ExtResource("{meta["page"]+1}")',
                     f'region = Rect2({r["x"]}, {r["y"]}, {r["w"]}, {r["h"]})',
                     f'margin = Rect2({ss["x"]}, {ss["y"]}, {w-r["w"]}, {h-r["h"]})']
    indexes = {f['id']: i for i, (_, f) in enumerate(fs)}
    entries = []
    for c in m['clips']:
        data = ', '.join('{"duration": ' + str(f['duration_ms'] / 1000) + ', "texture": SubResource("f' + str(indexes[f['id']]) + '")}' for f in c['frames'])
        entries.append('{"frames": [' + data + '], "loop": ' + str(c['loop']).lower() + ', "name": &' + json.dumps(c['name']) + ', "speed": 1.0}')
    resource += ['', '[resource]', 'animations = [' + ',\n'.join(entries) + ']']
    (out / 'sprite_frames.tres').write_text('\n'.join(resource) + '\n')
    shutil.copyfile(Path(__file__).resolve().parent.parent / 'assets/pixi-adapter.mjs', out / 'pixi-adapter.mjs')
    shutil.copyfile(Path(__file__).resolve().parent.parent / 'assets/clip-clock.mjs', out / 'clip-clock.mjs')
    dump(out / 'qa.json', report)
    identity = {p.name: file_hash(p) for p in sorted(out.iterdir()) if p.is_file()}
    dump(out / 'export-manifest.json', {'binding': report['binding'], 'files': identity,
                                      'texture_bytes_rgba': texture_bytes, 'atlas_pages': len(pages),
                                      'round_trip': 'exact_rgba_pass', 'dependency_files': report['dependencies']['files'],
                                      'visual_review_sha256': file_hash(review_path), 'engine_target': m.get('engine_target')})
    dump(out / 'runtime-review.template.json', runtime_template(out, [], out / 'runtime-review.template.json'))


def repair_diff(before_path, after_path, allowed):
    """Check repair scope/preservation; this does not approve the repaired artwork."""
    before, before_root = load_manifest(before_path)
    after, after_root = load_manifest(after_path)
    def contract(m):
        # Relocated files are allowed. All pose identities, timing and geometry remain locked.
        copy = json.loads(json.dumps(m))
        for _, frame in frames(copy):
            frame.pop('path', None)
        return copy
    errors = []
    if contract(before) != contract(after):
        errors.append('Production contract changed; geometry, clips, frame order, timing and events must remain identical for a scoped repair')
    before_dependencies = check_dependencies(before, before_root, load_manifest)
    after_dependencies = check_dependencies(after, after_root, load_manifest)
    def scope_dependencies(dependencies):
        return {key: value for key, value in dependencies['files'].items()
                if dependencies['current_frame_aliases'].get(key) not in set(allowed)}
    if scope_dependencies(before_dependencies) != scope_dependencies(after_dependencies):
        errors.append('Production dependencies changed; a frame-only scoped repair cannot approve contract edits')
    errors.extend('before dependency: ' + e for e in before_dependencies['errors'])
    errors.extend('after dependency: ' + e for e in after_dependencies['errors'])
    old = {f['id']: file_hash(resolve_under(before_root, f['path'])) for _, f in frames(before)}
    new = {f['id']: file_hash(resolve_under(after_root, f['path'])) for _, f in frames(after)}
    allowed = set(allowed)
    unknown = sorted(allowed - (set(old) & set(new)))
    if unknown:
        errors.append('Unknown allowed frame IDs: ' + ', '.join(unknown))
    changed = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
    unexpected = sorted(set(changed) - allowed)
    if unexpected:
        errors.append('Changed frames outside repair scope: ' + ', '.join(unexpected))
    return {'status': 'scope_pass' if not errors else 'blocked',
            'art_approval': 'not_evaluated', 'errors': errors,
            'before_manifest_sha256': file_hash(before_path),
            'after_manifest_sha256': file_hash(after_path),
            'before_frame_sha256': old, 'after_frame_sha256': new,
            'before_dependency_sha256': before_dependencies['files'],
            'after_dependency_sha256': after_dependencies['files'],
            'allowed_frames': sorted(allowed), 'changed_frames': changed,
            'unchanged_frames': sorted(k for k in set(old) & set(new) if old[k] == new[k]),
            'unused_allowed_frames': sorted(allowed - set(changed))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    p = sub.add_parser('init-animation', help='Create an unapproved complete coverage scaffold without placeholder images')
    p.add_argument('--asset-id', required=True); p.add_argument('--out', required=True)
    p.add_argument('--actions', nargs='+', default=['idle','walk','run','attack1','attack2','hit','death'])
    p.add_argument('--directions', nargs='+', required=True)
    p.add_argument('--cell', type=int, nargs=2, required=True); p.add_argument('--origin', type=float, nargs=2, required=True)
    p.add_argument('--representation', choices=['pixel','hd'], default='pixel')
    p = sub.add_parser('checkpoint', help='Bind current inputs and show invalidation relative to a previous checkpoint')
    p.add_argument('manifest'); p.add_argument('--previous'); p.add_argument('--out', required=True)
    p = sub.add_parser('release-check', help='Require current source/visual/export/runtime identities for a finished release')
    p.add_argument('manifest'); p.add_argument('--review', required=True); p.add_argument('--release', required=True)
    p.add_argument('--runtime-review', required=True); p.add_argument('--out', required=True)
    for cmd in ('validate', 'inspect', 'preview', 'review-template', 'qa', 'pack'):
        p = sub.add_parser(cmd)
        p.add_argument('manifest')
        if cmd != 'validate':
            p.add_argument('--out', required=True)
        if cmd == 'review-template':
            p.add_argument('--evidence', action='append', default=[], help='Existing inspected artifact to hash-bind before review')
        if cmd in ('qa', 'pack'):
            p.add_argument('--review', required=True)
    p = sub.add_parser('keypose-check', help='Validate all action key poses before generating a transition')
    p.add_argument('plan'); p.add_argument('--out', required=True)
    for cmd in ('runtime-template', 'runtime-verify'):
        p = sub.add_parser(cmd); p.add_argument('release'); p.add_argument('--out', required=True)
        if cmd == 'runtime-template':
            p.add_argument('--evidence', action='append', default=[])
        else:
            p.add_argument('--review', required=True)
    p = sub.add_parser('extract', help='Extract fully composited GIF/WebP frames, or explicit row-major grid')
    p.add_argument('source'); p.add_argument('--out', required=True)
    p.add_argument('--cell', type=int, nargs=2); p.add_argument('--duration-ms', type=int)
    p = sub.add_parser('pad', help='Expand static image canvas without resampling; never overwrite source')
    p.add_argument('source'); p.add_argument('--out', required=True)
    p.add_argument('--padding', type=int, nargs=4, required=True, metavar=('LEFT', 'TOP', 'RIGHT', 'BOTTOM'))
    p = sub.add_parser('repair-diff', help='Verify only declared frames changed and preserve timing/geometry; not art approval')
    p.add_argument('before'); p.add_argument('after'); p.add_argument('--out', required=True)
    p.add_argument('--allowed-frame', action='append', default=[])
    p = sub.add_parser('motion-check', help='Check temporal consistency metadata, sockets, depth, locomotion and budgets; review signals only')
    p.add_argument('manifest'); p.add_argument('--contract', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('family-check', help='Compare roster/family invariants and reference geometry; visual cohesion still requires review')
    p.add_argument('family'); p.add_argument('--out', required=True)
    p = sub.add_parser('sheet-separability-check', help='Detect overlap/gutter risks before deterministic slicing of aggregate generated sheets')
    p.add_argument('contract'); p.add_argument('--out', required=True)
    p = sub.add_parser('ui-check', help='Validate UI component/state/touch/nine-slice contracts; UX and visual approval remain separate')
    p.add_argument('contract'); p.add_argument('--out', required=True)
    p = sub.add_parser('ui-slice', help='Crop declared reviewed UI sheet rectangles without resampling or semantic guessing')
    p.add_argument('contract'); p.add_argument('--out', required=True)
    p = sub.add_parser('ui-review-template', help='Create evidence-bound blank UI visual review')
    p.add_argument('contract'); p.add_argument('--out', required=True); p.add_argument('--evidence', action='append', default=[])
    p = sub.add_parser('ui-qa', help='Verify evidence-bound UI visual review; structural pass alone is insufficient')
    p.add_argument('contract'); p.add_argument('--review', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('ui-runtime-template', help='Create blank UI runtime/interaction review bound to current assets')
    p.add_argument('contract'); p.add_argument('--visual-review', required=True); p.add_argument('--out', required=True); p.add_argument('--evidence', action='append', default=[])
    p = sub.add_parser('ui-runtime-verify', help='Verify bound UI runtime/interaction assertions')
    p.add_argument('contract'); p.add_argument('--visual-review', required=True); p.add_argument('--review', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('environment-check', help='Validate top-down/isometric environment/prop contract structure')
    p.add_argument('contract'); p.add_argument('--out', required=True)
    p = sub.add_parser('vfx-check', help='Validate VFX timing/canvas/socket/performance contract structure')
    p.add_argument('contract'); p.add_argument('--out', required=True)
    p = sub.add_parser('vfx-pack-plan', help='Validate a sellable VFX pack spec and compute the production plan')
    p.add_argument('pack'); p.add_argument('--out', required=True)
    p = sub.add_parser('vfx-pack-bundle-check', help='Validate a built sales bundle against the VFX pack spec')
    p.add_argument('pack'); p.add_argument('--dir', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('vfx-pack-release-check', help='Require bound visual/runtime approval for every bundled VFX')
    p.add_argument('pack'); p.add_argument('--dir', required=True); p.add_argument('--out', required=True)
    for prefix in ('environment', 'vfx'):
        p = sub.add_parser(prefix + '-review-template', help='Create evidence-bound blank visual review for ' + prefix)
        p.add_argument('contract'); p.add_argument('--out', required=True); p.add_argument('--evidence', action='append', default=[])
        p = sub.add_parser(prefix + '-qa', help='Verify evidence-bound visual review for ' + prefix)
        p.add_argument('contract'); p.add_argument('--review', required=True); p.add_argument('--out', required=True)
        p = sub.add_parser(prefix + '-runtime-template', help='Create blank runtime review for ' + prefix + ' bound to approved visual review')
        p.add_argument('contract'); p.add_argument('--visual-review', required=True); p.add_argument('--out', required=True); p.add_argument('--evidence', action='append', default=[])
        p = sub.add_parser(prefix + '-runtime-verify', help='Verify runtime assertions for ' + prefix)
        p.add_argument('contract'); p.add_argument('--visual-review', required=True); p.add_argument('--review', required=True); p.add_argument('--out', required=True)
    args = parser.parse_args()
    if args.command == 'doctor':
        try:
            import PIL
            pillow = PIL.__version__
        except ImportError:
            pillow = None
        print(json.dumps({'python': sys.version.split()[0], 'pillow': pillow, 'executables': {n: shutil.which(n) for n in ('aseprite', 'godot', 'ffmpeg', 'node')}, 'api_required': False}, indent=2))
        return 0 if pillow else 2
    if args.command == 'init-animation':
        result = init_animation(args.asset_id, args.actions, args.directions, args.cell, args.origin, args.representation, args.out, load_manifest)
        print(json.dumps(result, indent=2)); return 0
    if args.command == 'checkpoint':
        m, root = load_manifest(args.manifest)
        report = checkpoint(m, root, inspect, args.previous); dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'release-check':
        report = sprite_release_check(args.manifest, args.review, args.release, args.runtime_review, load_manifest, assess)
        dump(args.out, report); return 1 if report['errors'] else 0
    if args.command == 'keypose-check':
        report = keypose_check(args.plan); dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'runtime-template':
        dump(args.out, runtime_template(args.release, args.evidence, args.out)); return 0
    if args.command == 'runtime-verify':
        report = runtime_verify(args.release, args.review); dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'repair-diff':
        report = repair_diff(args.before, args.after, args.allowed_frame)
        dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'family-check':
        report = family_check(args.family, load_manifest)
        dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'sheet-separability-check':
        report = sheet_separability_check(args.contract)
        dump(args.out, report)
        return 1 if report['status'] in ('blocked','blocked_for_auto_slice') else 0
    if args.command == 'motion-check':
        m, root = load_manifest(args.manifest)
        report = motion_check(m, root, args.contract)
        dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'environment-check':
        report = environment_check(args.contract); dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'vfx-check':
        report = vfx_check(args.contract); dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'environment-review-template':
        dump(args.out, environment_review_template(args.contract, args.evidence, args.out)); return 0
    if args.command == 'environment-qa':
        report = environment_qa(args.contract, args.review); dump(args.out, report); return 1 if report['errors'] else 0
    if args.command == 'environment-runtime-template':
        dump(args.out, environment_runtime_template(args.contract, args.visual_review, args.evidence, args.out)); return 0
    if args.command == 'environment-runtime-verify':
        report = environment_runtime_verify(args.contract, args.visual_review, args.review); dump(args.out, report); return 1 if report['errors'] else 0
    if args.command == 'vfx-review-template':
        dump(args.out, vfx_review_template(args.contract, args.evidence, args.out)); return 0
    if args.command == 'vfx-qa':
        report = vfx_qa(args.contract, args.review); dump(args.out, report); return 1 if report['errors'] else 0
    if args.command == 'vfx-runtime-template':
        dump(args.out, vfx_runtime_template(args.contract, args.visual_review, args.evidence, args.out)); return 0
    if args.command == 'vfx-runtime-verify':
        report = vfx_runtime_verify(args.contract, args.visual_review, args.review); dump(args.out, report); return 1 if report['errors'] else 0
    if args.command == 'vfx-pack-plan':
        report = vfx_pack_plan(args.pack); dump(args.out, report); return 1 if report['errors'] else 0
    if args.command == 'vfx-pack-bundle-check':
        report = vfx_pack_bundle_check(args.pack, args.dir); dump(args.out, report); return 1 if report['errors'] else 0
    if args.command == 'vfx-pack-release-check':
        report = vfx_pack_release_check(args.pack, args.dir); dump(args.out, report); return 1 if report['errors'] else 0
    if args.command == 'ui-review-template':
        dump(args.out, ui_review_template(args.contract, args.evidence, args.out)); return 0
    if args.command == 'ui-qa':
        report = ui_qa(args.contract, args.review); dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'ui-runtime-template':
        dump(args.out, ui_runtime_template(args.contract, args.visual_review, args.evidence, args.out)); return 0
    if args.command == 'ui-runtime-verify':
        report = ui_runtime_verify(args.contract, args.visual_review, args.review); dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'ui-check':
        report = ui_check(args.contract)
        dump(args.out, report)
        return 1 if report['errors'] else 0
    if args.command == 'ui-slice':
        report = ui_slice(args.contract, args.out)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    from PIL import Image, ImageSequence
    if args.command == 'pad':
        if any(v < 0 for v in args.padding):
            raise ValueError('Padding must be nonnegative')
        target = Path(args.out)
        if target.exists() or target.resolve() == Path(args.source).resolve():
            raise ValueError('Refusing to overwrite source/output')
        with Image.open(args.source) as src:
            if getattr(src, 'n_frames', 1) != 1:
                raise ValueError('Extract animated input first')
            im = src.convert('RGBA')
        l, t, r, b = args.padding
        canvas = Image.new('RGBA', (im.width + l + r, im.height + t + b))
        canvas.paste(im, (l, t))
        target.parent.mkdir(parents=True, exist_ok=True); canvas.save(target)
        print(json.dumps({'size': list(canvas.size), 'origin_translation': [l, t]}))
        return 0
    if args.command == 'extract':
        if args.duration_ms is not None and not positive_int(args.duration_ms):
            raise ValueError('duration-ms must be positive')
        out = Path(args.out)
        with Image.open(args.source) as src:
            if args.cell:
                cw, ch = args.cell
                if not positive_int(cw) or not positive_int(ch) or src.width % cw or src.height % ch or getattr(src, 'n_frames', 1) != 1:
                    raise ValueError('Static sheet must divide exactly into positive cell dimensions')
                if args.duration_ms is None:
                    raise ValueError('Raster sheets have no timing; supply explicitly designed duration-ms')
                items = [(src.convert('RGBA').crop((x, y, x + cw, y + ch)), args.duration_ms)
                         for y in range(0, src.height, ch) for x in range(0, src.width, cw)]
            else:
                items = [(im.convert('RGBA').copy(), im.info.get('duration', args.duration_ms)) for im in ImageSequence.Iterator(src)]
                if not all(positive_int(d) for _, d in items):
                    raise ValueError('Missing/invalid authored duration; provide duration-ms for missing values')
        new_dir(out)
        extracted = []
        for i, (im, duration) in enumerate(items):
            name = f'frame_{i:04d}.png'; im.save(out / name)
            extracted.append({'id': f'frame_{i:04d}', 'path': name, 'duration_ms': duration})
        dump(out / 'extracted-frames.json', {'source': str(Path(args.source).resolve()), 'frames': extracted,
                                           'timing': 'designed' if args.cell else 'source_or_explicit_fallback'})
        return 0
    m, root = load_manifest(args.manifest)
    if args.command == 'validate':
        print('Contract valid; image, visual and runtime gates have not been evaluated')
        return 0
    if args.command == 'inspect':
        r = inspect(m, root); dump(args.out, r); return 1 if r['errors'] else 0
    if args.command == 'review-template':
        r = inspect(m, root)
        dump(args.out, {'schema_version': 2, 'binding': r['binding'], 'reviewer': '', 'evidence_files': bind_evidence(args.evidence, args.out), 'clips': {c['name']: {k: {'verdict': 'unknown', 'observation': '', 'evidence': []} for k in CHECKS} for c in m['clips']}, 'finding_reviews': {f['id']: {'verdict': 'unknown', 'observation': '', 'evidence': []} for f in r['dependencies']['findings']}})
        return 0
    if args.command == 'preview':
        r = inspect(m, root)
        if r['errors']:
            raise ValueError('Preview blocked: ' + '; '.join(r['errors']))
        preview(m, root, args.out); return 0
    if args.command == 'qa':
        r = assess(m, root, args.review); dump(args.out, r); return 0 if r['status'] == 'approved' else 1
    pack(m, root, args.review, args.out)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except ApprovalBlocked as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except (ValueError, OSError, KeyError, TypeError, ImportError) as e:
        print(f'Invalid input or I/O: {e}', file=sys.stderr)
        sys.exit(2)
