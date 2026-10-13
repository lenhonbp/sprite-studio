"""Bind declared production dependencies and run their structural gates.

Metrics remain review prompts. Invalid authored geometry blocks export.
"""
import hashlib
import json
from pathlib import Path
from path_utils import resolve_under, is_safe_relative_path

ROLES = ('art_contract', 'metadata', 'keyposes', 'family', 'slice_provenance')
CONVENTIONAL = {'art_contract': 'art-contract.md', 'metadata': 'production-metadata.json',
                'family': 'family-contract.json', 'slice_provenance': 'slice-provenance.json'}


def dependency_paths(manifest, root):
    declared = manifest.get('production_contracts', {})
    if not isinstance(declared, dict) or set(declared) - set(ROLES):
        raise ValueError('production_contracts must map supported roles to safe relative paths')
    result = dict(declared)
    for role, name in CONVENTIONAL.items():
        if role not in result and (Path(root) / name).exists():
            result[role] = name
    for role, name in result.items():
        if not is_safe_relative_path(name):
            raise ValueError(f'production_contracts/{role}: safe relative path required')
    return result


def check_dependencies(manifest, root, load_manifest):
    from quality_checks import motion_check, family_check
    from production_support import keypose_check
    from verify_slices import verify
    hashes, reports, findings, errors, frame_aliases = {}, {}, [], [], {}

    def bind(label, path):
        path = Path(path)
        hashes[label] = hashlib.sha256(path.read_bytes()).hexdigest()

    for role, raw in dependency_paths(manifest, root).items():
        try:
            p = resolve_under(root, raw)
            bind(role, p)
            if role == 'art_contract':
                if not p.read_text().strip():
                    raise ValueError('art contract cannot be empty')
                report = {'status': 'declared', 'errors': []}
            elif role == 'metadata':
                report = motion_check(manifest, root, p)
                for i, row in enumerate(report.get('temporal_findings', [])):
                    if row.get('flags'):
                        findings.append({'id': f'metadata_temporal_{i}', **row})
                for i, warning in enumerate(report.get('warnings', [])):
                    findings.append({'id': f'metadata_warning_{i}', 'observation': warning})
            elif role == 'keyposes':
                report = keypose_check(p)
                data = json.loads(p.read_text())
                if data.get('cell_size') != manifest['cell_size'] or data.get('origin') != manifest['origin']:
                    raise ValueError('keypose canvas/origin differs from current animation manifest')
                for pose in data['keyframes']:
                    bind(f'keypose/{pose["index"]}', resolve_under(p.parent, pose['path']))
            elif role == 'family':
                report = family_check(p, load_manifest)
                data = json.loads(p.read_text())
                matched_current = False
                def identity(candidate, base):
                    candidate = json.loads(json.dumps(candidate))
                    for clip in candidate['clips']:
                        for frame in clip['frames']:
                            frame['path'] = str(resolve_under(base, frame['path']))
                    return candidate
                for i, member in enumerate(data['members']):
                    mp = resolve_under(p.parent, member['manifest'])
                    bind(f'family/{i}/manifest', mp)
                    m, base = load_manifest(mp)
                    if m['asset_id'] == manifest['asset_id']:
                        if identity(m, base) != identity(manifest, root):
                            raise ValueError('family member with this asset_id does not match the current manifest and frame paths')
                        matched_current = True
                    for clip in m['clips']:
                        for frame in clip['frames']:
                            label = f'family/{i}/{frame["id"]}'
                            bind(label, resolve_under(base, frame['path']))
                            if m['asset_id'] == manifest['asset_id']:
                                frame_aliases[label] = frame['id']
                if not matched_current:
                    raise ValueError('family contract does not contain this asset_id')
                for i, warning in enumerate(report.get('warnings', [])):
                    findings.append({'id': f'family_warning_{i}', 'observation': warning})
            else:
                report = verify(p)
                data = json.loads(p.read_text())
                bind('slice/source', resolve_under(p.parent, data['source']))
                current_frames = [f for clip in manifest['clips'] for f in clip['frames']]
                if [f['id'] for f in data['frames']] != [f['id'] for f in current_frames]:
                    raise ValueError('slice provenance does not match current frame coverage/order')
                for frame, current in zip(data['frames'], current_frames):
                    if resolve_under(p.parent, frame['output']) != resolve_under(root, current['path']):
                        raise ValueError('slice provenance output is not the current frame: ' + current['id'])
                    if frame['source_rect'][2:] != manifest['cell_size'] or frame['origin'] != manifest['origin'] or frame['duration_ms'] != current['duration_ms'] or frame['offset'] != [0, 0]:
                        raise ValueError('slice provenance geometry/origin/timing differs from current full-canvas frame: ' + current['id'])
                    bind('slice/' + frame['id'], resolve_under(p.parent, frame['output']))
            reports[role] = report
            errors.extend(f'{role}: {e}' for e in report.get('errors', []))
        except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            errors.append(f'{role}: {exc}')
    return {'files': hashes, 'current_frame_aliases': frame_aliases, 'reports': reports, 'findings': findings, 'errors': errors}
