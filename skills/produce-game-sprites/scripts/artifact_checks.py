"""Structural checks for non-character game-art contracts.

These checks validate declared geometry/files/timing only. They never approve art.
"""
import json
import math
from pathlib import Path

from path_utils import is_safe_relative_path, resolve_under
from production_support import digest


def _safe(v):
    return isinstance(v, str) and v and all(c.isascii() and (c.isalnum() or c in '_-') for c in v)


def _finite(v):
    return type(v) in (int, float) and math.isfinite(v)


def _positive_pair(v):
    return isinstance(v, list) and len(v) == 2 and all(type(x) is int and x > 0 for x in v)


def _point(v):
    return isinstance(v, list) and len(v) == 2 and all(_finite(x) for x in v)


def _rect(v):
    return isinstance(v, list) and len(v) == 4 and all(_finite(x) for x in v) and v[0] >= 0 and v[1] >= 0 and v[2] > 0 and v[3] > 0


def _load(path, kind):
    p = Path(path).resolve()
    data = json.loads(p.read_text())
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError(f'{kind} contract must be a schema_version 1 object')
    return data, p.parent


def environment_check(path):
    from PIL import Image

    c, root = _load(path, 'Environment')
    errors, warnings, props_report = [], [], []
    if not _safe(c.get('environment_id')):
        errors.append('environment_id must be a safe nonempty ASCII name')
    if not _safe(c.get('projection')):
        errors.append('projection must be a declared safe name')
    if c.get('representation') not in ('pixel', 'hd'):
        errors.append('representation must be pixel or hd')
    if not _positive_pair(c.get('world_tile')):
        errors.append('world_tile must contain two positive integers')
    if not _safe(c.get('depth_sort')):
        errors.append('depth_sort must be declared')
    if not _safe(c.get('sampling')):
        errors.append('sampling must be declared')

    terrain = c.get('terrain', {})
    if terrain and not isinstance(terrain, dict):
        errors.append('terrain must be an object')
        terrain = {}
    if isinstance(terrain, dict):
        if 'seam_test_repeat' in terrain and not _positive_pair(terrain['seam_test_repeat']):
            errors.append('terrain/seam_test_repeat must contain two positive integers')
        if 'collision_is_separate_from_visible_bounds' in terrain and type(terrain['collision_is_separate_from_visible_bounds']) is not bool:
            errors.append('terrain/collision_is_separate_from_visible_bounds must be boolean')

    props = c.get('props', [])
    if not isinstance(props, list):
        errors.append('props must be an array')
        props = []
    ids = set()
    for prop in props:
        if not isinstance(prop, dict):
            errors.append('Each prop must be an object')
            continue
        pid = prop.get('id')
        if not _safe(pid) or pid in ids:
            errors.append('Each prop needs a unique safe id')
            continue
        ids.add(pid)
        if not is_safe_relative_path(prop.get('path')):
            errors.append(f'{pid}: safe project-relative image path required')
            continue
        footprint = prop.get('footprint_cells')
        if not isinstance(footprint, list) or not footprint or not all(isinstance(x, list) and len(x) == 2 and all(type(n) is int for n in x) for x in footprint):
            errors.append(f'{pid}: footprint_cells must be a nonempty array of integer [x,y] cells')
        if not _point(prop.get('base_pivot')):
            errors.append(f'{pid}: base_pivot must be [x,y] finite image-local coordinates')
        if 'collision_rect' in prop and not _rect(prop['collision_rect']):
            errors.append(f'{pid}: collision_rect must be [x,y,w,h] with positive size')
        if 'occluder' in prop and type(prop['occluder']) is not bool:
            errors.append(f'{pid}: occluder must be boolean')
        try:
            p = resolve_under(root, prop['path'])
        except ValueError as exc:
            errors.append(f'{pid}: {exc}')
            continue
        row = {'id': pid, 'path': prop['path'], 'exists': p.exists()}
        if not p.exists():
            errors.append(f'{pid}: file not found: {prop["path"]}')
            props_report.append(row)
            continue
        try:
            with Image.open(p) as src:
                im = src.convert('RGBA')
                row['image_size'] = list(im.size)
                row['sha256'] = digest(p)
                pivot = prop.get('base_pivot')
                if _point(pivot) and not (0 <= pivot[0] <= im.width and 0 <= pivot[1] <= im.height):
                    errors.append(f'{pid}: base_pivot lies outside image bounds')
                rect = prop.get('collision_rect')
                if _rect(rect) and (rect[0] + rect[2] > im.width or rect[1] + rect[3] > im.height):
                    warnings.append(f'{pid}: collision_rect extends outside image; confirm logical coordinate intent')
                alpha_bounds = im.getchannel('A').getbbox()
                row['alpha_bounds'] = alpha_bounds
                if alpha_bounds is None:
                    errors.append(f'{pid}: fully transparent prop image')
        except OSError as exc:
            errors.append(f'{pid}: unreadable image: {exc}')
        props_report.append(row)

    return {
        'status': 'blocked' if errors else 'review_required', 'art_approval': 'not_evaluated',
        'errors': errors, 'warnings': warnings, 'props': props_report,
        'limitation': 'Environment checks validate declared files/geometry only; seam quality, depth readability, collision feel and assembled-map appearance require visual/runtime field tests.'
    }


def vfx_check(path):
    from PIL import Image

    c, root = _load(path, 'VFX')
    errors, warnings, frames_report = [], [], []
    if not _safe(c.get('vfx_id')):
        errors.append('vfx_id must be a safe nonempty ASCII name')
    if c.get('representation') not in ('pixel', 'hd'):
        errors.append('representation must be pixel or hd')
    space = c.get('attachment_space')
    if space not in ('socket', 'world', 'screen', 'actor'):
        errors.append('attachment_space must be socket, world, screen or actor')
    if space == 'socket' and not _safe(c.get('socket')):
        errors.append('socket attachment requires a safe socket name')
    if type(c.get('loop')) is not bool:
        errors.append('loop must be boolean')
    if not isinstance(c.get('blend_intent'), str) or not c['blend_intent'].strip():
        errors.append('blend_intent must be declared')
    if c.get('alpha_policy') not in ('binary', 'soft'):
        errors.append('alpha_policy must be binary or soft')
    if 'cell_size' in c and not _positive_pair(c['cell_size']):
        errors.append('cell_size must contain two positive integers when declared')

    frames = c.get('frames')
    if not isinstance(frames, list) or not frames:
        errors.append('frames must be a nonempty array')
        frames = []
    ids, expected_size, total_ms, total_rgba = set(), None, 0, 0
    for frame in frames:
        if not isinstance(frame, dict):
            errors.append('Each VFX frame must be an object')
            continue
        fid = frame.get('id')
        if not _safe(fid) or fid in ids:
            errors.append('Each VFX frame needs a unique safe id')
            continue
        ids.add(fid)
        if not is_safe_relative_path(frame.get('path')):
            errors.append(f'{fid}: safe project-relative frame path required')
            continue
        duration = frame.get('duration_ms')
        if type(duration) is not int or duration <= 0:
            errors.append(f'{fid}: duration_ms must be a positive integer')
        else:
            total_ms += duration
        try:
            p = resolve_under(root, frame['path'])
        except ValueError as exc:
            errors.append(f'{fid}: {exc}')
            continue
        row = {'id': fid, 'path': frame['path'], 'exists': p.exists()}
        if not p.exists():
            errors.append(f'{fid}: file not found: {frame["path"]}')
            frames_report.append(row)
            continue
        try:
            with Image.open(p) as src:
                if getattr(src, 'n_frames', 1) != 1:
                    errors.append(f'{fid}: animated source must be extracted to explicit frames')
                im = src.convert('RGBA')
                row['image_size'] = list(im.size)
                row['sha256'] = digest(p)
                if expected_size is None:
                    expected_size = im.size
                elif im.size != expected_size:
                    errors.append(f'{fid}: frame canvas differs from earlier VFX frames')
                if _positive_pair(c.get('cell_size')) and list(im.size) != c['cell_size']:
                    errors.append(f'{fid}: frame size does not match declared cell_size')
                alpha = im.getchannel('A')
                bounds = alpha.getbbox()
                row['alpha_bounds'] = bounds
                if bounds is None:
                    errors.append(f'{fid}: fully transparent VFX frame')
                if alpha.getextrema()[0] == 255:
                    warnings.append(f'{fid}: VFX frame has no transparency; confirm intended full-screen/opaque effect')
                if c.get('alpha_policy') == 'binary' and sum(alpha.histogram()[1:255]):
                    errors.append(f'{fid}: soft alpha violates binary alpha policy')
                total_rgba += im.width * im.height * 4
        except OSError as exc:
            errors.append(f'{fid}: unreadable image: {exc}')
        frames_report.append(row)

    events = c.get('events', {})
    if events and not isinstance(events, dict):
        errors.append('events must be an object')
        events = {}
    if isinstance(events, dict):
        for key, value in events.items():
            if not _safe(key) or not _finite(value) or value < 0 or (total_ms and value >= total_ms):
                errors.append(f'events/{key}: time must be finite and inside total VFX duration')

    perf = c.get('performance_budget', {})
    if perf and not isinstance(perf, dict):
        errors.append('performance_budget must be an object')
        perf = {}
    if isinstance(perf, dict):
        sim = perf.get('max_simultaneous_instances')
        if sim is not None and (type(sim) is not int or sim <= 0):
            errors.append('performance_budget/max_simultaneous_instances must be a positive integer')
        if 'allow_large_transparent_canvas' in perf and type(perf['allow_large_transparent_canvas']) is not bool:
            errors.append('performance_budget/allow_large_transparent_canvas must be boolean')

    simultaneous = perf.get('max_simultaneous_instances', 1) if isinstance(perf, dict) else 1
    estimate = total_rgba * simultaneous if type(simultaneous) is int and simultaneous > 0 else total_rgba
    return {
        'status': 'blocked' if errors else 'review_required', 'art_approval': 'not_evaluated',
        'errors': errors, 'warnings': warnings, 'frames': frames_report, 'total_duration_ms': total_ms,
        'raw_rgba_frame_bytes': total_rgba, 'raw_rgba_simultaneous_estimate': estimate,
        'limitation': 'VFX checks validate timing/canvas/alpha/socket declarations only; perceived impact, blend result, overdraw and gameplay-hit alignment require visual/runtime field tests.'
    }

# Evidence-bound review profiles for environment and VFX. These mirror the
# sprite/UI three-gate policy without claiming independent visual truth.
from production_support import bind_evidence, evidence_errors

ENV_VISUAL_CHECKS = (
    'style_scale_projection', 'seams_transitions', 'pivot_depth_occlusion',
    'collision_footprint_readability', 'assembled_composition', 'sampling_edges',
)
ENV_RUNTIME_CHECKS = (
    'import_sampling', 'assembled_seams', 'depth_sort_occlusion',
    'collision_walkability', 'camera_scale', 'performance',
)
VFX_VISUAL_CHECKS = (
    'phase_readability', 'shape_direction', 'alpha_edges',
    'socket_alignment', 'light_dark_readability', 'loop_or_terminal',
)
VFX_RUNTIME_CHECKS = (
    'import_blend', 'playback_timing', 'socket_transform',
    'gameplay_hit_alignment', 'multi_instance_readability', 'performance_overdraw',
)


def _binding(contract, file_hashes):
    canonical = json.dumps({'contract': contract, 'files': file_hashes}, sort_keys=True, separators=(',', ':')).encode()
    import hashlib
    return hashlib.sha256(canonical).hexdigest()


def _ensure_binding(report, contract_path, rows):
    contract, root = _load(contract_path, 'Asset')
    hashes = {}
    for rel in rows:
        try:
            p = resolve_under(root, rel)
            if p.is_file():
                hashes[rel] = digest(p)
        except ValueError:
            pass
    report['binding'] = _binding(contract, hashes)
    return report


def environment_check_bound(path):
    report = environment_check(path)
    contract, _ = _load(path, 'Environment')
    rows = [p.get('path') for p in contract.get('props', []) if isinstance(p, dict) and isinstance(p.get('path'), str)]
    return _ensure_binding(report, path, rows)


def vfx_check_bound(path):
    report = vfx_check(path)
    contract, _ = _load(path, 'VFX')
    rows = [f.get('path') for f in contract.get('frames', []) if isinstance(f, dict) and isinstance(f.get('path'), str)]
    return _ensure_binding(report, path, rows)


def _rows(review, keys):
    checks = review.get('checks', {}) if isinstance(review, dict) else {}
    out = []
    for key in keys:
        row = checks.get(key, {}) if isinstance(checks, dict) else {}
        out.append((key, row if isinstance(row, dict) else {}))
    return out


def _visual_template(check_fn, contract_path, checks, evidence, out_path):
    report = check_fn(contract_path)
    if report['errors']:
        raise ValueError('Visual review template blocked by structural errors: ' + '; '.join(report['errors']))
    return {'schema_version': 1, 'status': 'not_reviewed', 'binding': report['binding'], 'reviewer': '',
            'evidence_files': bind_evidence(evidence, out_path),
            'checks': {k: {'verdict': 'unknown', 'observation': '', 'evidence': []} for k in checks}}


def _visual_qa(check_fn, contract_path, review_path, checks, approval_key='art_approval'):
    report = check_fn(contract_path)
    p = Path(review_path).resolve()
    review = json.loads(p.read_text())
    errors = list(report['errors'])
    if not isinstance(review, dict) or review.get('schema_version') != 1:
        errors.append('Visual review schema 1 required')
        review = review if isinstance(review, dict) else {}
    if review.get('binding') != report['binding']:
        errors.append('Visual review is stale or bound to different assets')
    if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip():
        errors.append('Actual visual reviewer identity is required')
    rows = _rows(review, checks)
    for key, row in rows:
        if row.get('verdict') != 'pass' or not isinstance(row.get('observation'), str) or not row['observation'].strip():
            errors.append(f'{key}: incomplete or failing visual review')
    errors += evidence_errors(review, p.parent, rows)
    report['status'] = 'approved' if not errors else 'blocked'
    report[approval_key] = 'approved' if not errors else 'not_approved'
    report['errors'] = errors
    report['runtime_status'] = 'not_tested'
    report['limitation'] = 'Validates current bound evidence and reviewer assertions; it does not independently perceive the art.'
    return report


def _runtime_template(check_fn, contract_path, visual_path, visual_checks, evidence, out_path):
    visual = _visual_qa(check_fn, contract_path, visual_path, visual_checks)
    if visual['errors']:
        raise ValueError('Runtime template requires approved current visual review')
    return {'schema_version': 1, 'status': 'not_tested', 'binding': visual['binding'],
            'visual_review_sha256': digest(visual_path), 'engine': '', 'version': '', 'project_or_scene': '', 'reviewer': '',
            'evidence_files': bind_evidence(evidence, out_path)}


def _runtime_verify(check_fn, contract_path, visual_path, visual_checks, runtime_path, runtime_checks, visual_required):
    visual = _visual_qa(check_fn, contract_path, visual_path, visual_checks)
    p = Path(runtime_path).resolve()
    review = json.loads(p.read_text())
    errors = list(visual['errors'])
    if not isinstance(review, dict) or review.get('schema_version') != 1:
        errors.append('Runtime review schema 1 required')
        review = review if isinstance(review, dict) else {}
    if review.get('binding') != visual['binding'] or review.get('visual_review_sha256') != digest(visual_path):
        errors.append('Runtime review is stale or bound to different visual/assets')
    for key in ('engine', 'version', 'project_or_scene', 'reviewer'):
        if not isinstance(review.get(key), str) or not review[key].strip():
            errors.append(f'Missing actual runtime {key}')
    rows = _rows(review, runtime_checks)
    for key, row in rows:
        if row.get('verdict') != 'pass' or not isinstance(row.get('observation'), str) or not row['observation'].strip():
            errors.append(f'{key}: incomplete or failing runtime assertion')
        if row.get('mode') not in ('visual', 'headless', 'automated'):
            errors.append(f'{key}: identify visual/headless/automated check mode')
        if key in visual_required and row.get('mode') != 'visual':
            errors.append(f'{key}: actual runtime visual evidence is required')
    errors += evidence_errors(review, p.parent, rows)
    return {'status': 'runtime_assertions_pass' if not errors else 'blocked', 'errors': errors,
            'binding': visual['binding'], 'visual_review_sha256': digest(visual_path),
            'limitation': 'Validates current assets plus bound runtime assertions; it does not independently launch the target engine or measure hardware.'}


def environment_review_template(contract_path, evidence, out_path):
    return _visual_template(environment_check_bound, contract_path, ENV_VISUAL_CHECKS, evidence, out_path)


def environment_qa(contract_path, review_path):
    return _visual_qa(environment_check_bound, contract_path, review_path, ENV_VISUAL_CHECKS)


def environment_runtime_template(contract_path, visual_path, evidence, out_path):
    data = _runtime_template(environment_check_bound, contract_path, visual_path, ENV_VISUAL_CHECKS, evidence, out_path)
    data['checks'] = {k: {'verdict': 'unknown', 'mode': '', 'observation': '', 'evidence': []} for k in ENV_RUNTIME_CHECKS}
    return data


def environment_runtime_verify(contract_path, visual_path, runtime_path):
    return _runtime_verify(environment_check_bound, contract_path, visual_path, ENV_VISUAL_CHECKS, runtime_path,
                           ENV_RUNTIME_CHECKS, {'assembled_seams', 'depth_sort_occlusion', 'collision_walkability', 'camera_scale'})


def vfx_review_template(contract_path, evidence, out_path):
    return _visual_template(vfx_check_bound, contract_path, VFX_VISUAL_CHECKS, evidence, out_path)


def vfx_qa(contract_path, review_path):
    return _visual_qa(vfx_check_bound, contract_path, review_path, VFX_VISUAL_CHECKS)


def vfx_runtime_template(contract_path, visual_path, evidence, out_path):
    data = _runtime_template(vfx_check_bound, contract_path, visual_path, VFX_VISUAL_CHECKS, evidence, out_path)
    data['checks'] = {k: {'verdict': 'unknown', 'mode': '', 'observation': '', 'evidence': []} for k in VFX_RUNTIME_CHECKS}
    return data


def vfx_runtime_verify(contract_path, visual_path, runtime_path):
    return _runtime_verify(vfx_check_bound, contract_path, visual_path, VFX_VISUAL_CHECKS, runtime_path,
                           VFX_RUNTIME_CHECKS, {'import_blend', 'playback_timing', 'socket_transform', 'gameplay_hit_alignment', 'multi_instance_readability'})
