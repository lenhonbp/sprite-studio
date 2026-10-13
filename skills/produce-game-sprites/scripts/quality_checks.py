"""Production v3.3 structural/temporal/family checks.

These checks surface suspicious changes and contract omissions. They never decide
artistic quality. Visual and runtime approval remain separate gates.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from path_utils import is_safe_relative_path, resolve_under


def _finite_number(v):
    return type(v) in (int, float) and math.isfinite(v)


def _point(v):
    return isinstance(v, list) and len(v) == 2 and all(_finite_number(x) for x in v)


def _rect(v):
    return isinstance(v, list) and len(v) == 4 and all(type(x) is int and x >= 0 for x in v) and v[2] > 0 and v[3] > 0


def _safe(v):
    return isinstance(v, str) and bool(v) and all(c.isascii() and (c.isalnum() or c in '_-') for c in v)


def load_contract(path, asset_id=None):
    p = Path(path).resolve()
    data = json.loads(p.read_text())
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Production metadata must be a schema_version 1 object')
    if asset_id is not None and data.get('asset_id') != asset_id:
        raise ValueError('Production metadata asset_id does not match animation manifest')
    if data.get('coordinate_space', 'cell_pixels') != 'cell_pixels':
        raise ValueError('Only cell_pixels coordinate_space is supported')
    return data, p.parent


def _visible_stats(image):
    alpha = image.getchannel('A')
    bbox = alpha.getbbox()
    hist = alpha.histogram()
    area = sum(hist[1:])
    if bbox:
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
    else:
        cx = cy = 0.0
    rgba = image.tobytes()
    colors = {tuple(rgba[i:i+3]) for i in range(0, len(rgba), 4) if rgba[i+3] > 0}
    return {'visible_pixels': area, 'bbox': list(bbox) if bbox else None, 'bbox_center': [cx, cy], 'colors': colors}


def _jaccard(a, b):
    if not a and not b:
        return 1.0
    union = len(a | b)
    return len(a & b) / union if union else 1.0


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _frame_lookup(manifest):
    result = {}
    clips = {}
    for clip in manifest['clips']:
        clips[clip['name']] = clip
        for frame in clip['frames']:
            result[frame['id']] = (clip, frame)
    return result, clips


def _validate_point_map(label, mapping, frame_ids, size, errors):
    if mapping is None:
        return
    if not isinstance(mapping, dict):
        errors.append(f'{label} must be an object keyed by frame ID')
        return
    w, h = size
    for frame_id, points in mapping.items():
        if frame_id not in frame_ids:
            errors.append(f'{label}: unknown frame ID {frame_id}')
            continue
        if not isinstance(points, dict):
            errors.append(f'{label}/{frame_id}: expected an object of named points')
            continue
        for name, point in points.items():
            if not _safe(name) or not _point(point):
                errors.append(f'{label}/{frame_id}: invalid point {name!r}')
            elif not (0 <= point[0] <= w and 0 <= point[1] <= h):
                errors.append(f'{label}/{frame_id}/{name}: point outside cell')


def motion_check(manifest, root, contract_path):
    from PIL import Image, ImageChops

    contract, _ = load_contract(contract_path, manifest['asset_id'])
    lookup, clips = _frame_lookup(manifest)
    frame_ids = set(lookup)
    errors, warnings, findings = [], [], []
    size = manifest['cell_size']

    landmarks = contract.get('landmarks')
    sockets = contract.get('sockets')
    _validate_point_map('landmarks', landmarks, frame_ids, size, errors)
    _validate_point_map('sockets', sockets, frame_ids, size, errors)

    required_landmarks = contract.get('required_landmarks', [])
    if not isinstance(required_landmarks, list) or not all(_safe(v) for v in required_landmarks):
        errors.append('required_landmarks must be an array of safe names')
    elif required_landmarks:
        for frame_id in sorted(frame_ids):
            actual = set(landmarks.get(frame_id, {})) if isinstance(landmarks, dict) and isinstance(landmarks.get(frame_id, {}), dict) else set()
            missing = sorted(set(required_landmarks) - actual)
            if missing:
                warnings.append(f'{frame_id}: missing required landmarks: {", ".join(missing)}')

    required_sockets = contract.get('required_sockets_by_action', {})
    if not isinstance(required_sockets, dict):
        errors.append('required_sockets_by_action must be an object')
    else:
        for action, names in required_sockets.items():
            if not _safe(action) or not isinstance(names, list) or not all(_safe(v) for v in names):
                errors.append(f'required_sockets_by_action/{action}: invalid declaration')
                continue
            for clip in manifest['clips']:
                if clip['action'] != action:
                    continue
                for f in clip['frames']:
                    actual = set(sockets.get(f['id'], {})) if isinstance(sockets, dict) and isinstance(sockets.get(f['id'], {}), dict) else set()
                    missing = sorted(set(names) - actual)
                    if missing:
                        errors.append(f'{f["id"]}: missing action sockets: {", ".join(missing)}')

    # Invalid point maps must not reach temporal arithmetic.
    landmarks = {k:v for k,v in (landmarks.items() if isinstance(landmarks, dict) else []) if isinstance(v,dict)}
    sockets = {k:v for k,v in (sockets.items() if isinstance(sockets, dict) else []) if isinstance(v,dict)}
    landmarks = {k:{n:p for n,p in v.items() if _point(p)} for k,v in landmarks.items()}
    sockets = {k:{n:p for n,p in v.items() if _point(p)} for k,v in sockets.items()}

    depth = contract.get('depth_profiles', {})
    if depth and not isinstance(depth, dict):
        errors.append('depth_profiles must be an object keyed by direction/profile name')
    elif isinstance(depth, dict):
        for name, layers in depth.items():
            if not _safe(name) or not isinstance(layers, list) or not all(_safe(v) for v in layers) or len(layers) != len(set(layers)):
                errors.append(f'depth_profiles/{name}: layers must be unique safe names')
    if not isinstance(depth, dict):
        depth = {}
    clip_depth = contract.get('clip_depth_profile', {})
    if clip_depth and not isinstance(clip_depth, dict):
        errors.append('clip_depth_profile must be an object')
    elif isinstance(clip_depth, dict):
        for clip_name, profile in clip_depth.items():
            if clip_name not in clips:
                errors.append(f'clip_depth_profile: unknown clip {clip_name}')
            elif not isinstance(profile, str) or profile not in depth:
                errors.append(f'clip_depth_profile/{clip_name}: unknown depth profile {profile}')

    collision = contract.get('collision', {})
    if collision and not isinstance(collision, dict):
        errors.append('collision must be an object keyed by frame ID')
    elif isinstance(collision, dict):
        w, h = size
        for frame_id, groups in collision.items():
            if frame_id not in frame_ids or not isinstance(groups, dict):
                errors.append(f'collision/{frame_id}: unknown frame or invalid group object')
                continue
            for kind in ('hurtboxes', 'hitboxes'):
                boxes = groups.get(kind, [])
                if not isinstance(boxes, list) or not all(_rect(v) for v in boxes):
                    errors.append(f'collision/{frame_id}/{kind}: expected [x,y,w,h] boxes')
                    continue
                for x, y, bw, bh in boxes:
                    if x + bw > w or y + bh > h:
                        errors.append(f'collision/{frame_id}/{kind}: box exceeds cell')

    transitions = contract.get('transitions', [])
    if not isinstance(transitions, list):
        errors.append('transitions must be an array')
    else:
        for row in transitions:
            if not isinstance(row, dict) or not isinstance(row.get('from'), str) or not isinstance(row.get('to'), str) or row['from'] not in clips or row['to'] not in clips:
                errors.append('Each transition must reference existing from/to clips')

    static_regions = contract.get('static_regions', [])
    if not isinstance(static_regions, list):
        errors.append('static_regions must be an array')
        static_regions = []
    for region in static_regions:
        if not isinstance(region, dict) or not _safe(region.get('name')) or not _rect(region.get('rect')):
            errors.append('Each static_region needs safe name and rect [x,y,w,h]')
            continue
        x, y, rw, rh = region['rect']
        if x + rw > size[0] or y + rh > size[1]:
            errors.append(f'static_region/{region["name"]}: rectangle exceeds cell')
        if 'clips' in region and (not isinstance(region['clips'], list) or not all(isinstance(v,str) and v in clips for v in region['clips'])):
            errors.append(f'static_region/{region["name"]}: clips must reference known clip names')
        if 'max_changed_ratio' in region and (not _finite_number(region['max_changed_ratio']) or not 0 <= region['max_changed_ratio'] <= 1):
            errors.append(f'static_region/{region["name"]}: max_changed_ratio must be 0..1')

    thresholds = contract.get('temporal_thresholds', {})
    if not isinstance(thresholds, dict):
        errors.append('temporal_thresholds must be an object')
        thresholds = {}
    defaults = {'silhouette_area_ratio': 0.22, 'bbox_center_px': 6.0, 'palette_jaccard_min': 0.45, 'landmark_step_px': 16.0, 'socket_step_px': 16.0}
    for k, default in defaults.items():
        thresholds.setdefault(k, default)
        if not _finite_number(thresholds[k]) or thresholds[k] < 0 or (k in ('silhouette_area_ratio', 'palette_jaccard_min') and thresholds[k] > 1):
            errors.append(f'temporal_thresholds/{k}: expected nonnegative finite threshold (ratios at most 1)')
            thresholds[k] = default

    if errors:
        return {'status': 'blocked', 'art_approval': 'not_evaluated', 'errors': errors, 'warnings': warnings, 'temporal_findings': [], 'flagged_findings': 0}

    cache = {}
    for frame_id, (_, frame) in lookup.items():
        p = resolve_under(root, frame['path'])
        with Image.open(p) as src:
            im = src.convert('RGBA')
        cache[frame_id] = (im, _visible_stats(im))

    for clip in manifest['clips']:
        fs = clip['frames']
        pairs = list(zip(fs, fs[1:]))
        if clip.get('loop') and len(fs) > 1:
            pairs.append((fs[-1], fs[0]))
        for a_frame, b_frame in pairs:
            a_id, b_id = a_frame['id'], b_frame['id']
            a_im, a = cache[a_id]
            b_im, b = cache[b_id]
            denom = max(a['visible_pixels'], b['visible_pixels'], 1)
            area_ratio = abs(a['visible_pixels'] - b['visible_pixels']) / denom
            center_delta = _distance(a['bbox_center'], b['bbox_center'])
            palette = _jaccard(a['colors'], b['colors']) if manifest['representation'] == 'pixel' else None
            row = {'clip': clip['name'], 'from': a_id, 'to': b_id,
                   'silhouette_area_ratio': round(area_ratio, 4), 'bbox_center_delta_px': round(center_delta, 3)}
            if palette is not None:
                row['palette_jaccard'] = round(palette, 4)
            landmark_steps = {}
            for name in set((landmarks or {}).get(a_id, {})) & set((landmarks or {}).get(b_id, {})):
                landmark_steps[name] = round(_distance(landmarks[a_id][name], landmarks[b_id][name]), 3)
            if landmark_steps:
                row['landmark_step_px'] = landmark_steps
            socket_steps = {name: round(_distance(sockets[a_id][name], sockets[b_id][name]), 3)
                            for name in set(sockets.get(a_id, {})) & set(sockets.get(b_id, {}))}
            if socket_steps:
                row['socket_step_px'] = socket_steps
            flags = []
            if any(v > thresholds['socket_step_px'] for v in socket_steps.values()):
                flags.append('socket_jump')
            if area_ratio > thresholds['silhouette_area_ratio']:
                flags.append('silhouette_area_jump')
            if center_delta > thresholds['bbox_center_px']:
                flags.append('bbox_center_jump')
            if palette is not None and palette < thresholds['palette_jaccard_min']:
                flags.append('palette_drift')
            if any(v > thresholds['landmark_step_px'] for v in landmark_steps.values()):
                flags.append('landmark_jump')
            row['flags'] = flags
            findings.append(row)

        for region in static_regions:
            if clip['name'] not in region.get('clips', [clip['name']]):
                continue
            x, y, rw, rh = region['rect']
            max_ratio = region.get('max_changed_ratio', 0.0)
            for a_frame, b_frame in pairs:
                a_id, b_id = a_frame['id'], b_frame['id']
                aa = cache[a_id][0].crop((x, y, x+rw, y+rh))
                bb = cache[b_id][0].crop((x, y, x+rw, y+rh))
                diff = ImageChops.difference(aa, bb).convert('RGBA')
                raw = diff.tobytes()
                changed = sum(1 for i in range(0, len(raw), 4) if any(raw[i:i+4]))
                ratio = changed / max(1, rw * rh)
                if ratio > max_ratio:
                    findings.append({'clip': clip['name'], 'from': a_id, 'to': b_id, 'static_region': region['name'],
                                     'changed_ratio': round(ratio, 4), 'flags': ['static_region_drift']})

    locomotion_results = []
    locomotion = contract.get('locomotion', {})
    if locomotion and not isinstance(locomotion, dict):
        errors.append('locomotion must be an object keyed by clip name')
    elif isinstance(locomotion, dict):
        for clip_name, spec in locomotion.items():
            if clip_name not in clips or not isinstance(spec, dict):
                errors.append(f'locomotion/{clip_name}: unknown clip or invalid object')
                continue
            required = ('stride_pixels', 'pixels_per_world_unit', 'world_speed_units_per_s')
            if not all(_finite_number(spec.get(k)) and spec.get(k) > 0 for k in required):
                errors.append(f'locomotion/{clip_name}: positive stride_pixels, pixels_per_world_unit and world_speed_units_per_s required')
                continue
            cycle_ms = spec.get('cycle_ms', sum(f['duration_ms'] for f in clips[clip_name]['frames']))
            if not _finite_number(cycle_ms) or cycle_ms <= 0:
                errors.append(f'locomotion/{clip_name}: cycle_ms must be positive')
                continue
            authored_speed = (spec['stride_pixels'] / spec['pixels_per_world_unit']) / (cycle_ms / 1000.0)
            target = spec['world_speed_units_per_s']
            error_ratio = abs(authored_speed - target) / target
            tolerance = spec.get('speed_tolerance_ratio', 0.15)
            if not _finite_number(tolerance) or tolerance < 0:
                errors.append(f'locomotion/{clip_name}: invalid speed_tolerance_ratio')
                continue
            locomotion_results.append({'clip': clip_name, 'cycle_ms': cycle_ms,
                                       'calibrated_speed_units_per_s': round(authored_speed, 4),
                                       'target_speed_units_per_s': target, 'error_ratio': round(error_ratio, 4),
                                       'within_declared_tolerance': error_ratio <= tolerance,
                                       'planted_foot_tolerance_px': spec.get('planted_foot_tolerance_px')})
            if error_ratio > tolerance:
                warnings.append(f'{clip_name}: stride/timing implies {authored_speed:.3f} units/s, outside target tolerance')

    provenance = contract.get('provenance', {})
    if provenance:
        if not isinstance(provenance, dict) or not isinstance(provenance.get('frames'), dict):
            errors.append('provenance.frames must be an object keyed by frame ID')
        else:
            unknown = set(provenance['frames']) - frame_ids
            if unknown:
                errors.append('provenance has unknown frame IDs: ' + ', '.join(sorted(unknown)))
            missing = frame_ids - set(provenance['frames'])
            if missing:
                warnings.append('provenance missing for frames: ' + ', '.join(sorted(missing)))

    perf = contract.get('performance_budget', {})
    performance = {}
    if perf:
        if not isinstance(perf, dict):
            errors.append('performance_budget must be an object')
        else:
            frame_count = len(frame_ids)
            raw_bytes = frame_count * size[0] * size[1] * 4
            performance = {'frame_count': frame_count, 'raw_rgba_bytes': raw_bytes,
                           'simultaneous_actor_raw_rgba_bytes': raw_bytes * int(perf.get('max_simultaneous_actors', 1)) if type(perf.get('max_simultaneous_actors', 1)) is int and perf.get('max_simultaneous_actors', 1) > 0 else None}
            limit = perf.get('max_total_rgba_bytes')
            if limit is not None and (type(limit) is not int or limit <= 0):
                errors.append('performance_budget/max_total_rgba_bytes must be a positive integer')
            elif limit is not None and raw_bytes > limit:
                warnings.append(f'Raw frame RGBA estimate {raw_bytes} exceeds declared budget {limit}')

    flagged_pairs = sum(bool(r.get('flags')) for r in findings)
    return {'status': 'blocked' if errors else 'review_required', 'art_approval': 'not_evaluated',
            'errors': errors, 'warnings': warnings, 'thresholds': thresholds,
            'temporal_findings': findings, 'flagged_findings': flagged_pairs,
            'locomotion': locomotion_results, 'performance': performance,
            'limitation': 'Automatic metrics surface suspicious changes; they do not establish visual quality or runtime correctness.'}


def family_check(family_path, load_manifest_fn):
    from PIL import Image

    p = Path(family_path).resolve()
    family = json.loads(p.read_text())
    if not isinstance(family, dict) or family.get('schema_version') != 1:
        raise ValueError('Family contract must be a schema_version 1 object')
    members = family.get('members')
    inv = family.get('invariants', {})
    if not isinstance(members, list) or len(members) < 2:
        raise ValueError('Family contract requires at least two members')
    if not isinstance(inv, dict):
        raise ValueError('Family invariants must be an object')
    errors, warnings, observations = [], [], []
    seen_members = set()
    seen_asset_ids = set()
    for field in ('required_actions', 'required_directions'):
        values = inv.get(field, [])
        if not isinstance(values, list) or not all(_safe(v) for v in values) or len(values) != len(set(values)):
            raise ValueError(f'{field} must be a unique safe-name array')
    exceptions = inv.get('allowed_missing_pairs', [])
    if not isinstance(exceptions, list) or not all(isinstance(v, dict) and _safe(v.get('action')) and _safe(v.get('direction')) and isinstance(v.get('reason'), str) and v['reason'].strip() for v in exceptions):
        raise ValueError('allowed_missing_pairs requires action, direction and nonempty reason')
    allowed_missing = {(v['action'], v['direction']) for v in exceptions}
    expected_pairs = {(a,d) for a in inv.get('required_actions', []) for d in inv.get('required_directions', [])}
    if len(allowed_missing) != len(exceptions) or allowed_missing - expected_pairs:
        raise ValueError('allowed_missing_pairs must be unique combinations inside the required matrix')
    baseline = None
    for member in members:
        if not isinstance(member, dict) or not isinstance(member.get('manifest'), str) or not isinstance(member.get('reference_frame_id'), str):
            errors.append('Each family member needs manifest and reference_frame_id')
            continue

        if not is_safe_relative_path(member['manifest']):
            errors.append('Family member manifest path must be safe and project-relative')
            continue
        manifest_path = resolve_under(p.parent, member['manifest'])
        if manifest_path in seen_members:
            errors.append('Duplicate family manifest member: ' + member['manifest'])
            continue
        seen_members.add(manifest_path)
        m, root = load_manifest_fn(manifest_path)
        if m['asset_id'] in seen_asset_ids:
            errors.append('Duplicate family asset_id: ' + m['asset_id'])
            continue
        seen_asset_ids.add(m['asset_id'])
        lookup, _ = _frame_lookup(m)
        ref = member['reference_frame_id']
        if ref not in lookup:
            errors.append(f'{m["asset_id"]}: missing reference frame {ref}')
            continue
        with Image.open(resolve_under(root, lookup[ref][1]['path'])) as src:
            im = src.convert('RGBA')
            bbox = im.getchannel('A').getbbox()
        visible_height = (bbox[3] - bbox[1]) if bbox else 0
        row = {'asset_id': m['asset_id'], 'representation': m['representation'], 'cell_size': m['cell_size'],
               'origin': m['origin'], 'reference_frame_id': ref, 'visible_height_px': visible_height,
               'actions': sorted(set(c['action'] for c in m['clips'])), 'directions': sorted(set(c['direction'] for c in m['clips']))}
        observations.append(row)
        if baseline is None:
            baseline = row
        expected_rep = inv.get('representation')
        if expected_rep and m['representation'] != expected_rep:
            errors.append(f'{m["asset_id"]}: representation differs from family invariant')
        expected_cell = inv.get('cell_size')
        if expected_cell and m['cell_size'] != expected_cell:
            errors.append(f'{m["asset_id"]}: cell_size differs from family invariant')
        req_actions = inv.get('required_actions', [])
        req_dirs = inv.get('required_directions', [])
        actual_pairs = {(c['action'], c['direction']) for c in m['clips']}
        missing_pairs = {(a,d) for a in req_actions for d in req_dirs} - actual_pairs - allowed_missing
        if missing_pairs:
            errors.append(f'{m["asset_id"]}: missing action-direction pairs: ' + ', '.join(f'{a}/{d}' for a,d in sorted(missing_pairs)))
        missing_actions = set(req_actions) - set(row['actions'])
        missing_dirs = set(req_dirs) - set(row['directions'])
        if missing_actions:
            errors.append(f'{m["asset_id"]}: missing actions: {", ".join(sorted(missing_actions))}')
        if missing_dirs:
            errors.append(f'{m["asset_id"]}: missing directions: {", ".join(sorted(missing_dirs))}')

    if observations:
        origin_tol = inv.get('origin_y_tolerance_px', 2)
        height_tol = inv.get('visible_height_tolerance_ratio', 0.12)
        if not _finite_number(origin_tol) or origin_tol < 0 or not _finite_number(height_tol) or height_tol < 0:
            errors.append('Family tolerances must be nonnegative numbers')
        else:
            base_y = observations[0]['origin'][1]
            base_h = max(1, observations[0]['visible_height_px'])
            for row in observations[1:]:
                if abs(row['origin'][1] - base_y) > origin_tol:
                    warnings.append(f'{row["asset_id"]}: origin_y differs from family reference by more than tolerance')
                if abs(row['visible_height_px'] - base_h) / base_h > height_tol:
                    warnings.append(f'{row["asset_id"]}: visible reference height differs from family reference by more than tolerance')

    return {'status': 'blocked' if errors else 'review_required', 'art_approval': 'not_evaluated',
            'errors': errors, 'warnings': warnings, 'members': observations,
            'limitation': 'Family checks compare declared invariants/reference geometry only; visual style cohesion still requires side-by-side review.'}
