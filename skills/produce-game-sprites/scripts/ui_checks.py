#!/usr/bin/env python3
"""Provider-independent UI structure, evidence-bound review and deterministic slicing."""
import hashlib
import json
import math
from pathlib import Path

from path_utils import is_safe_relative_path, resolve_under
from production_support import bind_evidence, digest, evidence_errors

UI_VISUAL_CHECKS = (
    'hierarchy_readability', 'state_distinction', 'style_consistency',
    'text_localization_fit', 'safe_area_layout', 'nine_slice_scaling',
)
UI_RUNTIME_CHECKS = (
    'screen_import', 'responsive_layout', 'safe_area', 'touch_input',
    'state_transitions', 'localization_overflow', 'nine_slice_runtime', 'performance',
)


def _safe(value):
    return isinstance(value, str) and value and all(c.isascii() and (c.isalnum() or c in '_-') for c in value)


def _positive_pair(value):
    return isinstance(value, list) and len(value) == 2 and all(type(v) is int and v > 0 for v in value)


def _nonneg_number(v):
    return type(v) in (int, float) and math.isfinite(v) and v >= 0


def _rect(value):
    return isinstance(value, list) and len(value) == 4 and all(type(v) is int for v in value) and value[0] >= 0 and value[1] >= 0 and value[2] > 0 and value[3] > 0


def load_ui_contract(path):
    p = Path(path).resolve()
    data = json.loads(p.read_text())
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('UI contract must be a schema_version 1 object')
    return data, p.parent


def _ui_binding(contract, file_hashes):
    canonical = json.dumps({'contract': contract, 'files': file_hashes}, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(canonical).hexdigest()


def ui_check(path):
    from PIL import Image

    contract, root = load_ui_contract(path)
    errors, warnings, components_report, file_hashes = [], [], [], {}

    if not _safe(contract.get('ui_system_id')):
        errors.append('ui_system_id must be a nonempty ASCII name')
    if contract.get('representation') not in ('pixel', 'hd'):
        errors.append('representation must be pixel or hd')
    canvas = contract.get('reference_canvas')
    if not _positive_pair(canvas):
        errors.append('reference_canvas must contain two positive integers')
    if contract.get('text_policy') not in ('runtime_text', 'baked_text_allowed'):
        errors.append('text_policy must be runtime_text or baked_text_allowed')
    if not _positive_pair(contract.get('minimum_touch_size')):
        errors.append('minimum_touch_size must contain two positive integers')

    safe = contract.get('safe_area', {})
    if not isinstance(safe, dict) or any(k not in safe for k in ('top', 'right', 'bottom', 'left')) or any(not _nonneg_number(safe.get(k)) for k in ('top', 'right', 'bottom', 'left')):
        errors.append('safe_area must explicitly contain nonnegative top/right/bottom/left values')
    elif _positive_pair(canvas):
        if safe.get('left', 0) + safe.get('right', 0) >= canvas[0] or safe.get('top', 0) + safe.get('bottom', 0) >= canvas[1]:
            errors.append('safe_area leaves no positive reference content area')

    runtime = contract.get('runtime', {})
    if runtime and not isinstance(runtime, dict):
        errors.append('runtime must be an object')
        runtime = {}
    if contract.get('representation') == 'pixel':
        if runtime.get('pixel_snap') is False:
            warnings.append('pixel UI declares pixel_snap=false; inspect runtime sampling/alignment')
        if runtime.get('integer_scale_preferred') is False:
            warnings.append('pixel UI declares integer_scale_preferred=false; inspect blur and uneven borders')

    matrix = contract.get('runtime_test_matrix', {})
    if matrix and not isinstance(matrix, dict):
        errors.append('runtime_test_matrix must be an object')
        matrix = {}
    if isinstance(matrix, dict):
        for key in ('viewports', 'locales', 'input_modes'):
            if key in matrix and (not isinstance(matrix[key], list) or not matrix[key] or not all(isinstance(v, str) and v.strip() for v in matrix[key]) or len(matrix[key]) != len(set(matrix[key]))):
                errors.append(f'runtime_test_matrix/{key} must be a nonempty unique string array when declared')

    comps = contract.get('components')
    if not isinstance(comps, list) or not comps:
        errors.append('components must be a nonempty array')
        comps = []

    ids, groups = set(), {}
    min_touch = contract.get('minimum_touch_size') if _positive_pair(contract.get('minimum_touch_size')) else [1, 1]
    interactive_roles = {'button', 'tab', 'slot', 'skill', 'toggle', 'slider', 'menu_item', 'drag_handle'}

    for comp in comps:
        if not isinstance(comp, dict):
            errors.append('Each component must be an object')
            continue
        cid = comp.get('id')
        if not _safe(cid) or cid in ids:
            errors.append('Each component needs a unique safe id')
            continue
        ids.add(cid)
        group, state, role = comp.get('group'), comp.get('state'), comp.get('role')
        if not _safe(group) or not _safe(state) or not _safe(role):
            errors.append(f'{cid}: group, role and state must be safe names')
        else:
            groups.setdefault(group, set()).add(state)
        if not is_safe_relative_path(comp.get('path')):
            errors.append(f'{cid}: safe project-relative path required')
            continue
        if not _positive_pair(comp.get('logical_size')):
            errors.append(f'{cid}: logical_size must contain two positive integers')
        if role in interactive_roles:
            if not _positive_pair(comp.get('touch_size')):
                errors.append(f'{cid}: interactive component requires touch_size')
            else:
                tw, th = comp['touch_size']
                if tw < min_touch[0] or th < min_touch[1]:
                    errors.append(f'{cid}: declared touch_size is below project minimum_touch_size')
        if contract.get('text_policy') == 'runtime_text' and comp.get('text_baked') is True:
            errors.append(f'{cid}: baked text violates runtime_text policy')

        try:
            p = resolve_under(root, comp['path'])
        except ValueError as exc:
            errors.append(f'{cid}: {exc}')
            continue
        row = {'id': cid, 'path': comp['path'], 'exists': p.exists()}
        if not p.exists():
            errors.append(f'{cid}: file not found: {comp["path"]}')
            components_report.append(row)
            continue
        try:
            with Image.open(p) as src:
                im = src.convert('RGBA')
                row['image_size'] = list(im.size)
                alpha = im.getchannel('A')
                row['alpha_bounds'] = alpha.getbbox()
                file_hashes[comp['path']] = digest(p)
                if comp.get('alpha_required') is True and alpha.getextrema()[0] == 255:
                    warnings.append(f'{cid}: alpha_required but image has no transparent pixels')
                ns = comp.get('nine_slice')
                if ns is not None:
                    if not isinstance(ns, list) or len(ns) != 4 or not all(type(v) is int and v >= 0 for v in ns):
                        errors.append(f'{cid}: nine_slice must be [left, top, right, bottom] nonnegative integers')
                    else:
                        left, top, right, bottom = ns
                        if left + right >= im.width or top + bottom >= im.height:
                            errors.append(f'{cid}: nine_slice margins leave no stretchable source center')
                        logical = comp.get('logical_size')
                        if _positive_pair(logical) and (left + right > logical[0] or top + bottom > logical[1]):
                            errors.append(f'{cid}: logical_size is smaller than fixed nine-slice borders')
        except OSError as exc:
            errors.append(f'{cid}: unreadable image: {exc}')
        components_report.append(row)

    req = contract.get('required_state_groups', {})
    if req and not isinstance(req, dict):
        errors.append('required_state_groups must be an object')
        req = {}
    if isinstance(req, dict):
        for group, states in req.items():
            if not _safe(group) or not isinstance(states, list) or not states or not all(_safe(s) for s in states) or len(states) != len(set(states)):
                errors.append('required_state_groups entries need safe group and unique nonempty safe state list')
                continue
            missing = set(states) - groups.get(group, set())
            if missing:
                errors.append(f'{group}: missing required UI states: ' + ', '.join(sorted(missing)))

    flows = contract.get('screen_flows', [])
    if flows and not isinstance(flows, list):
        errors.append('screen_flows must be an array')
        flows = []
    seen_screens = set()
    for flow in flows:
        if not isinstance(flow, dict) or not _safe(flow.get('screen')):
            errors.append('Each screen_flow requires a safe screen name')
            continue
        if flow['screen'] in seen_screens:
            errors.append(f'{flow["screen"]}: duplicate screen_flow')
        seen_screens.add(flow['screen'])
        refs = flow.get('components', [])
        if not isinstance(refs, list) or not all(isinstance(v, str) for v in refs):
            errors.append(f'{flow.get("screen", "screen")}: components must be an array of component ids')
        else:
            unknown = set(refs) - ids
            if unknown:
                errors.append(f'{flow["screen"]}: unknown component ids: ' + ', '.join(sorted(unknown)))

    slices = contract.get('slices', [])
    if slices and not isinstance(slices, list):
        errors.append('slices must be an array')
        slices = []
    slice_ids, outputs = set(), set()
    for sl in slices:
        if not isinstance(sl, dict) or not _safe(sl.get('id')) or not _rect(sl.get('rect')):
            errors.append('Each slice needs safe id and rect [x,y,w,h]')
            continue
        sid = sl['id']
        if sid in slice_ids:
            errors.append(f'{sid}: duplicate slice id')
        slice_ids.add(sid)
        if not is_safe_relative_path(sl.get('source_sheet')):
            errors.append(f'{sid}: safe project-relative source_sheet required')
        if not is_safe_relative_path(sl.get('output')):
            errors.append(f'{sid}: safe relative output required')
        else:
            try:
                target = resolve_under(root, sl['output'])
                reserved = root / 'ui-slices.json'
                if target == reserved or reserved in target.parents:
                    errors.append(f'{sid}: reserved ui-slices.json output')
                elif any(target == old or target in old.parents or old in target.parents for old in outputs):
                    errors.append(f'{sid}: duplicate or conflicting slice output')
                outputs.add(target)
            except ValueError as exc:
                errors.append(f'{sid}: {exc}')


    return {
        'status': 'blocked' if errors else 'review_required',
        'ux_approval': 'not_evaluated',
        'binding': _ui_binding(contract, file_hashes),
        'errors': errors,
        'warnings': warnings,
        'components': components_report,
        'runtime_test_matrix': matrix if isinstance(matrix, dict) else {},
        'limitation': 'Structural UI checks do not establish visual hierarchy, readability, touch usability, localization fit, safe-area behavior or runtime UX.'
    }


def ui_slice(path, out_dir):
    """Two-phase validate then crop. No partial output for declaration/bounds failures."""
    from PIL import Image

    contract, root = load_ui_contract(path)
    slices = contract.get('slices')
    if not isinstance(slices, list) or not slices:
        raise ValueError('UI contract has no slices')
    out = Path(out_dir).resolve()
    if out.exists():
        raise ValueError(f'Refusing to overwrite directory: {out}')

    planned, ids, outputs = [], set(), set()
    for sl in slices:
        if not isinstance(sl, dict) or not _safe(sl.get('id')) or not _rect(sl.get('rect')):
            raise ValueError('Invalid slice declaration')
        sid = sl['id']
        if sid in ids:
            raise ValueError(f'{sid}: duplicate slice id')
        ids.add(sid)
        if not is_safe_relative_path(sl.get('source_sheet')):
            raise ValueError(f'{sid}: unsafe source_sheet')
        if not is_safe_relative_path(sl.get('output')):
            raise ValueError(f'{sid}: unsafe output path')
        dest = resolve_under(out, sl['output'])
        reserved = out / 'ui-slices.json'
        if dest == reserved or reserved in dest.parents:
            raise ValueError(f'{sid}: output conflicts with reserved ui-slices.json manifest')
        if any(dest == old or dest in old.parents or old in dest.parents for old in outputs):
            raise ValueError(f'{sid}: duplicate or conflicting output path')
        outputs.add(dest)
        src_path = resolve_under(root, sl['source_sheet'])
        if not src_path.exists():
            raise ValueError(f'Missing source sheet: {sl["source_sheet"]}')
        x, y, w, h = sl['rect']
        with Image.open(src_path) as src:
            if x + w > src.width or y + h > src.height:
                raise ValueError(f'{sid}: slice exceeds source sheet')
        planned.append((sl, src_path))

    out.mkdir(parents=True)
    saved = []
    for sl, src_path in planned:
        x, y, w, h = sl['rect']
        with Image.open(src_path) as src:
            crop = src.convert('RGBA').crop((x, y, x + w, y + h))
        rel = Path(sl['output'])
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        crop.save(dest)
        saved.append({'id': sl['id'], 'path': rel.as_posix(), 'size': [w, h], 'sha256': digest(dest)})
    manifest = out / 'ui-slices.json'
    manifest.write_text(json.dumps({'schema_version': 1, 'slices': saved}, ensure_ascii=False, indent=2) + '\n')
    return {'status': 'sliced', 'output_dir': str(out), 'count': len(saved), 'manifest': str(manifest)}


def _review_rows(review, keys):
    checks = review.get('checks', {}) if isinstance(review, dict) else {}
    rows = []
    for key in keys:
        row = checks.get(key, {}) if isinstance(checks, dict) else {}
        if not isinstance(row, dict):
            row = {}
        rows.append((key, row))
    return rows


def ui_review_template(contract_path, evidence, out_path):
    report = ui_check(contract_path)
    if report['errors']:
        raise ValueError('UI review template blocked by structural errors: ' + '; '.join(report['errors']))
    return {
        'schema_version': 1, 'status': 'not_reviewed', 'binding': report['binding'], 'reviewer': '',
        'evidence_files': bind_evidence(evidence, out_path),
        'checks': {k: {'verdict': 'unknown', 'observation': '', 'evidence': []} for k in UI_VISUAL_CHECKS},
    }


def ui_qa(contract_path, review_path):
    report = ui_check(contract_path)
    p = Path(review_path).resolve()
    review = json.loads(p.read_text())
    errors = list(report['errors'])
    if not isinstance(review, dict) or review.get('schema_version') != 1:
        errors.append('UI visual review schema 1 required')
        review = review if isinstance(review, dict) else {}
    if review.get('binding') != report['binding']:
        errors.append('UI visual review is stale or bound to different assets')
    if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip():
        errors.append('Actual UI visual reviewer identity is required')
    rows = _review_rows(review, UI_VISUAL_CHECKS)
    for key, row in rows:
        if row.get('verdict') != 'pass' or not isinstance(row.get('observation'), str) or not row['observation'].strip():
            errors.append(f'{key}: incomplete or failing UI visual review')
    errors += evidence_errors(review, p.parent, rows)
    return {
        **report,
        'status': 'approved' if not errors else 'blocked',
        'ux_approval': 'approved' if not errors else 'not_approved',
        'errors': errors,
        'runtime_status': 'not_tested',
        'limitation': 'Validates current bound evidence and reviewer assertions; it does not independently perceive or operate the UI.'
    }


def ui_runtime_template(contract_path, visual_review_path, evidence, out_path):
    visual = ui_qa(contract_path, visual_review_path)
    if visual['errors']:
        raise ValueError('UI runtime template requires approved current visual review')
    return {
        'schema_version': 1, 'status': 'not_tested', 'binding': visual['binding'],
        'visual_review_sha256': digest(visual_review_path),
        'engine': '', 'version': '', 'project_or_scene': '', 'reviewer': '',
        'viewports_tested': [], 'locales_tested': [], 'input_modes_tested': [], 'devices_or_browsers': [],
        'evidence_files': bind_evidence(evidence, out_path),
        'checks': {k: {'verdict': 'unknown', 'mode': '', 'observation': '', 'evidence': []} for k in UI_RUNTIME_CHECKS},
    }


def ui_runtime_verify(contract_path, visual_review_path, runtime_review_path):
    visual = ui_qa(contract_path, visual_review_path)
    p = Path(runtime_review_path).resolve()
    review = json.loads(p.read_text())
    errors = list(visual['errors'])
    if not isinstance(review, dict) or review.get('schema_version') != 1:
        errors.append('UI runtime review schema 1 required')
        review = review if isinstance(review, dict) else {}
    if review.get('binding') != visual['binding'] or review.get('visual_review_sha256') != digest(visual_review_path):
        errors.append('UI runtime review is stale or bound to different visual/assets')
    for key in ('engine', 'version', 'project_or_scene', 'reviewer'):
        if not isinstance(review.get(key), str) or not review[key].strip():
            errors.append(f'Missing actual UI runtime {key}')
    for key in ('viewports_tested', 'locales_tested', 'input_modes_tested', 'devices_or_browsers'):
        if not isinstance(review.get(key), list) or not review[key] or not all(isinstance(v, str) and v.strip() for v in review[key]):
            errors.append(f'{key}: record at least one concrete runtime case')
    matrix = visual.get('runtime_test_matrix', {})
    for contract_key, review_key in (('viewports', 'viewports_tested'), ('locales', 'locales_tested'), ('input_modes', 'input_modes_tested')):
        required = set(matrix.get(contract_key, [])) if isinstance(matrix, dict) else set()
        actual = set(review.get(review_key, [])) if isinstance(review.get(review_key), list) else set()
        missing = sorted(required - actual)
        if missing:
            errors.append(f'{review_key}: missing contract-required cases: ' + ', '.join(missing))
    rows = _review_rows(review, UI_RUNTIME_CHECKS)
    visual_required = {'responsive_layout', 'safe_area', 'touch_input', 'state_transitions', 'localization_overflow', 'nine_slice_runtime'}
    for key, row in rows:
        if row.get('verdict') != 'pass' or not isinstance(row.get('observation'), str) or not row['observation'].strip():
            errors.append(f'{key}: incomplete or failing UI runtime assertion')
        if row.get('mode') not in ('visual', 'headless', 'automated'):
            errors.append(f'{key}: identify visual/headless/automated check mode')
        if key in visual_required and row.get('mode') != 'visual':
            errors.append(f'{key}: actual runtime visual/interaction evidence is required')
    errors += evidence_errors(review, p.parent, rows)
    return {
        'status': 'runtime_assertions_pass' if not errors else 'blocked', 'errors': errors,
        'binding': visual['binding'], 'visual_review_sha256': digest(visual_review_path),
        'limitation': 'Validates current assets plus bound reviewer runtime assertions; it does not independently launch the engine or prove device performance.'
    }
