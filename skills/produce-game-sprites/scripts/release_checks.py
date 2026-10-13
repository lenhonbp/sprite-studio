"""Final release gates, separate from export and structural bundle readiness."""
import json
from pathlib import Path
from production_support import digest, runtime_verify, verify_release
from path_utils import resolve_under, is_safe_relative_path


def sprite_release_check(manifest_path, visual_path, release, runtime_path, load_manifest, assess):
    m, root = load_manifest(manifest_path)
    visual = assess(m, root, visual_path)
    exported, identity = verify_release(release)
    errors = list(visual['errors'])
    if visual['binding'] != exported.get('binding'):
        errors.append('Export is stale relative to current source/dependencies')
    if exported.get('visual_review_sha256') != digest(visual_path):
        errors.append('Export is bound to another visual review')
    runtime = runtime_verify(release, runtime_path)
    errors.extend(runtime['errors'])
    return {'status': 'release_approved' if not errors else 'blocked', 'errors': errors,
            'binding': visual['binding'], 'export_manifest_sha256': identity,
            'limitation': 'Checks current source, release and bound engine-review assertions; does not independently judge art.'}


def vfx_pack_release_check(pack_path, bundle_dir):
    from vfx_pack import vfx_pack_bundle_check
    from artifact_checks import vfx_qa, vfx_runtime_verify
    pack = Path(pack_path).resolve()
    spec = json.loads(pack.read_text())
    structural = vfx_pack_bundle_check(pack_path, bundle_dir)
    errors = list(structural['errors'])
    rows = []
    effects = spec.get('effects', []) if isinstance(spec, dict) else []
    if not isinstance(effects, list):
        effects = []
    if not effects:
        errors.append('No effects available for release verification')
    for effect in effects:
        if not isinstance(effect, dict):
            continue
        vid = effect.get('vfx_id', 'unknown')
        try:
            paths = {}
            for key in ('vfx_contract', 'visual_review', 'runtime_review'):
                if not is_safe_relative_path(effect.get(key)):
                    raise ValueError(f'{key} is required as a safe pack-relative path for release')
                paths[key] = resolve_under(pack.parent, effect[key])
            visual = vfx_qa(paths['vfx_contract'], paths['visual_review'])
            runtime = vfx_runtime_verify(paths['vfx_contract'], paths['visual_review'], paths['runtime_review'])
            errors.extend(f'{vid}: {e}' for e in visual['errors'] + runtime['errors'])
            rows.append({'vfx_id': vid, 'visual_status': visual['status'], 'runtime_status': runtime['status']})
        except (ValueError, OSError, KeyError, TypeError) as exc:
            errors.append(f'{vid}: {exc}')
    return {**structural, 'status': 'release_approved' if not errors else 'blocked',
            'art_approval': 'approved' if not errors else 'not_approved', 'errors': errors,
            'effect_gates': rows,
            'limitation': 'Approval applies to unchanged bundle/spec/sources and bound per-effect reviews; it does not upload a marketplace listing.'}
