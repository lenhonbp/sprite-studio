"""Project scaffolding and resumable input identity; never generate placeholder art."""
import json
from pathlib import Path


def init_animation(asset_id, actions, directions, size, origin, representation, output, load_manifest):
    out = Path(output)
    if out.exists():
        raise ValueError('Refusing to overwrite scaffold directory')
    if len(actions) != len(set(actions)) or len(directions) != len(set(directions)):
        raise ValueError('Actions and directions must be unique')
    clips = []
    for action in actions:
        for direction in directions:
            name = action + '_' + direction
            clips.append({'name': name, 'action': action, 'direction': direction,
                          'loop': action in ('idle', 'walk', 'run'), 'events': [],
                          'frames': [{'id': name + '_00', 'path': f'frames/{name}_00.png', 'duration_ms': 100}]})
    m = {'schema_version': 1, 'asset_id': asset_id, 'representation': representation,
         'cell_size': list(size), 'origin': list(origin), 'alpha_required': True,
         'required_clips': [c['name'] for c in clips], 'clips': clips,
         'coverage': {'actions': actions, 'directions': directions, 'exceptions': []},
         'atlas_policy': {'multipage': True, 'trim': False, 'extrude': False},
         'production_contracts': {'art_contract': 'art-contract.md'}}
    # Validate before touching user's output path.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        check = Path(d) / 'animation-set.json'
        check.write_text(json.dumps(m))
        load_manifest(check)
    out.mkdir(parents=True)
    (out / 'animation-set.json').write_text(json.dumps(m, indent=2) + '\n')
    (out / 'art-contract.md').write_text('# Unapproved art contract\n\nDeclare camera/projection, identity master, '
                                       'handedness, scale, palette/materials, origin and runtime sampling before production.\n'
                                       'Frame counts/timing are starter values; adapt them to the actual motion proof.\n')
    return {'status': 'scaffold_created', 'manifest': str(out / 'animation-set.json'),
            'required_clips': len(clips), 'art_approval': 'not_evaluated', 'runtime_status': 'not_tested',
            'limitation': 'No images generated. Replace starter timing and create approved motion before expansion.'}


def checkpoint(manifest, root, inspect, previous=None):
    current = inspect(manifest, root)
    frame_hashes = {r['id']: r['pixel_hash'] for r in current['frames']}
    report = {'schema_version': 1, 'binding': current['binding'], 'frame_pixels': frame_hashes,
              'dependency_files': current['dependencies']['files'], 'errors': current['errors'],
              'status': 'checkpoint' if not current['errors'] else 'blocked'}
    if previous:
        old = json.loads(Path(previous).read_text())
        if not isinstance(old, dict) or old.get('schema_version') != 1 or not isinstance(old.get('frame_pixels'), dict):
            raise ValueError('Invalid previous checkpoint')
        changed = sorted(fid for fid in set(frame_hashes) | set(old['frame_pixels']) if frame_hashes.get(fid) != old['frame_pixels'].get(fid))
        dependencies_changed = old.get('dependency_files') != report['dependency_files']
        report.update({'changed_frames': changed, 'dependencies_changed': dependencies_changed,
                       'review_invalidated': old.get('binding') != report['binding'],
                       'clips_to_reinspect': [c['name'] for c in manifest['clips'] if dependencies_changed or any(f['id'] in changed for f in c['frames'])]})
        if report['review_invalidated'] and not report['clips_to_reinspect']:
            report['clips_to_reinspect'] = [c['name'] for c in manifest['clips']] # timing/order/contract revision
    return report
