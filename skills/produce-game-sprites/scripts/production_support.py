"""Strict evidence binding, pose preflight and runtime assertion checks."""
import hashlib
import json
from pathlib import Path
from path_utils import is_safe_relative_path, resolve_under

RUNTIME_CHECKS = ('import', 'playback', 'facing_origin', 'filter_scale', 'transitions_events', 'texture_budget')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind_evidence(paths, review_path):
    base = Path(review_path).resolve().parent
    result = {}
    for raw in paths:
        p = Path(raw).resolve()
        if not p.is_file():
            raise ValueError(f'Missing evidence file: {p}')
        import os
        name = os.path.relpath(p, base)
        result[name] = digest(p)
    return result


def evidence_errors(review, base, rows):
    errors = []
    bound = review.get('evidence_files')
    if not isinstance(bound, dict):
        return ['Missing bound evidence_files; create a fresh template with --evidence']
    for label, row in rows:
        ev = row.get('evidence', []) if isinstance(row, dict) else []
        if not isinstance(ev, list) or not ev:
            errors.append(f'{label}: evidence references required')
            continue
        for name in ev:
            if not isinstance(name, str) or name not in bound:
                errors.append(f'{label}: evidence is not prebound: {name}')
                continue
            p = Path(base) / name
            if not p.is_file() or digest(p) != bound[name]:
                errors.append(f'{label}: evidence missing or changed: {name}')
    return errors


def keypose_check(plan_path):
    from PIL import Image
    p = Path(plan_path).resolve()
    plan = json.loads(p.read_text())
    if not isinstance(plan, dict):
        raise ValueError('Pose plan must be an object')
    n = plan.get('total_frames')
    size, origin = plan.get('cell_size'), plan.get('origin')
    if type(n) is not int or n < 2:
        raise ValueError('total_frames must be an integer >= 2')
    if not isinstance(size, list) or len(size) != 2 or not all(type(v) is int and v > 0 for v in size):
        raise ValueError('cell_size must contain two positive integers')
    import math
    if not isinstance(origin, list) or len(origin) != 2 or not all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= size[i] for i, v in enumerate(origin)):
        raise ValueError('origin must contain finite cell-local coordinates')
    poses = plan.get('keyframes')
    if not isinstance(poses, list) or len(poses) < 2:
        raise ValueError('At least two key poses required')
    seen, errors, bindings = set(), [], {}
    for pose in poses:
        if not isinstance(pose, dict):
            raise ValueError('Each key pose must be an object')
        index = pose.get('index')
        if type(index) is not int or not 0 <= index < n or index in seen:
            raise ValueError('Key pose indices must be unique and inside total_frames')
        seen.add(index)
        raw = pose.get('path')
        if not is_safe_relative_path(raw):
            raise ValueError('Key pose path must be safe and relative to plan')
        source = resolve_under(p.parent, raw)
        if pose.get('origin') != origin:
            errors.append(f'{index}: origin differs from common pose origin')
        if not isinstance(pose.get('role'), str) or not pose['role'].strip():
            errors.append(f'{index}: describe action-ready pose role')
        try:
            with Image.open(source) as image:
                if list(image.size) != size or getattr(image, 'n_frames', 1) != 1:
                    errors.append(f'{index}: static canvas dimensions do not match')
            bindings[str(index)] = digest(source)
        except OSError as e:
            errors.append(f'{index}: {e}')
    if 0 not in seen:
        errors.append('Key pose 0 is required')
    return {'status': 'structural_pass' if not errors else 'blocked', 'errors': errors,
            'files': bindings, 'visual_status': 'not_reviewed'}


def verify_release(release):
    release = Path(release).resolve()
    manifest_path = release / 'export-manifest.json'
    m = json.loads(manifest_path.read_text())
    if not isinstance(m, dict) or not isinstance(m.get('files'), dict) or not m['files']:
        raise ValueError('Invalid export manifest')
    for name, expected in m['files'].items():
        if not isinstance(name, str) or Path(name).name != name:
            raise ValueError('Export manifest paths must be simple file names')
        p = release / name
        if not p.is_file() or digest(p) != expected:
            raise ValueError(f'Export file missing or changed: {name}')
    return m, digest(manifest_path)


def runtime_template(release, evidence, out):
    m, identity = verify_release(release)
    return {'schema_version': 2, 'status': 'not_tested', 'binding': m['binding'],
            'export_manifest_sha256': identity, 'engine': '', 'version': '',
            'project_or_scene': '', 'reviewer': '', 'evidence_files': bind_evidence(evidence, out),
            'checks': {k: {'verdict': 'unknown', 'mode': '', 'observation': '', 'evidence': []} for k in RUNTIME_CHECKS}}


def runtime_verify(release, review_path):
    m, identity = verify_release(release)
    p = Path(review_path).resolve()
    review = json.loads(p.read_text())
    if not isinstance(review, dict) or not isinstance(review.get('checks'), dict):
        raise ValueError('Runtime review must contain checks')
    errors = []
    if review.get('schema_version') != 2:
        errors.append('Runtime review schema 2 required')
    if review.get('binding') != m['binding'] or review.get('export_manifest_sha256') != identity:
        errors.append('Runtime review is stale or bound to another export')
    for key in ('engine', 'version', 'project_or_scene', 'reviewer'):
        if not isinstance(review.get(key), str) or not review[key].strip():
            errors.append(f'Missing actual {key}')
    target = m.get('engine_target')
    if target:
        if not isinstance(target, dict):
            errors.append('Invalid engine_target in export')
        else:
            normalize = lambda s: str(s).lower().replace('js', '').replace(' ', '')
            if normalize(target.get('name')) != normalize(review.get('engine')):
                errors.append('Runtime engine differs from declared engine_target')
            if target.get('version') and str(review.get('version')) != str(target['version']):
                errors.append('Runtime version differs from declared engine_target')
    rows = []
    for key in RUNTIME_CHECKS:
        row = review['checks'].get(key, {})
        if not isinstance(row, dict):
            row = {}
        if row.get('verdict') != 'pass' or not isinstance(row.get('observation'), str) or not row['observation'].strip():
            errors.append(f'{key}: incomplete or failing runtime assertion')
        if row.get('mode') not in ('visual', 'headless', 'automated'):
            errors.append(f'{key}: identify visual/headless/automated check mode')
        if key in ('playback', 'facing_origin', 'filter_scale') and row.get('mode') != 'visual':
            errors.append(f'{key}: actual engine visual evidence is required')
        rows.append((key, row))
    errors += evidence_errors(review, p.parent, rows)
    return {'status': 'runtime_assertions_pass' if not errors else 'blocked', 'errors': errors,
            'binding': m['binding'], 'export_manifest_sha256': identity,
            'limitation': 'Validates unchanged exports and bound reviewer assertions, not independent engine/artistic truth.'}
