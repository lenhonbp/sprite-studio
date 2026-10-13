"""Sellable VFX pack planning and bundle validation.

Structural checks only: they validate declared pack specs, marketplace policy
gates and sales-bundle completeness. They never approve art, and they never
call a network generation API.
"""
import csv
import json
import hashlib
from pathlib import Path

from artifact_checks import _finite, _load, _positive_pair, _safe, vfx_check
from path_utils import is_safe_relative_path, resolve_under

TAXONOMY = (
    'hit-spark', 'impact-burst', 'slash-arc', 'muzzle-flash', 'explode-burst',
    'status-aura', 'projectile-trail', 'ground-crack', 'magic-circle',
    'heal-glow', 'smoke-plume', 'portal-gate',
)

ADAPTERS = ('pixellab', 'retro_diffusion', 'scenario', 'embergen', 'native', 'other')

MARKETS = ('itch.io', 'unity-asset-store', 'gamedev-market', 'craftpix', 'opengameart', 'other')

LOG_FIELDS = ('model', 'seed', 'prompt', 'date')


def _spec_effects(c, errors):
    effects = c.get('effects')
    if not isinstance(effects, list) or not effects:
        errors.append('effects must be a nonempty array')
        return []
    return effects


def vfx_pack_plan(pack_path):
    """Validate a vfx-pack spec and compute the production plan."""
    errors, warnings = [], []
    try:
        c, root = _load(pack_path, 'VFX pack')
    except (OSError, ValueError) as exc:
        return {'status': 'blocked', 'errors': [str(exc)], 'warnings': [],
                'limitation': 'Pack spec unreadable; nothing planned.'}
    if type(c.get('schema_version')) is not int:
        errors.append('schema_version must be integer 1')
    if not _safe(c.get('pack_id')):
        errors.append('pack_id must be a safe nonempty ASCII name')
    title = c.get('title')
    if not isinstance(title, str) or not title.strip():
        errors.append('title must be a declared nonempty string')
    if c.get('representation') not in ('pixel', 'hd'):
        errors.append('representation must be pixel or hd')
    default_cell = c.get('default_cell_size')
    if default_cell is not None and not _positive_pair(default_cell):
        errors.append('default_cell_size must contain two positive integers when declared')

    gen = c.get('generation', {})
    if not isinstance(gen, dict):
        errors.append('generation must be an object')
        gen = {}
    adapter = gen.get('adapter')
    if adapter not in ADAPTERS:
        errors.append('generation/adapter must be one of: ' + ', '.join(ADAPTERS))
    cost = gen.get('cost_per_effect_usd')
    if cost is not None and (not _finite(cost) or cost < 0):
        errors.append('generation/cost_per_effect_usd must be a finite non-negative number')
    if 'fixed_seed' not in gen:
        warnings.append('no fixed_seed declared; frame-to-frame consistency is at risk')
    elif type(gen.get('fixed_seed')) is not int:
        errors.append('generation/fixed_seed must be an integer when declared')
    log_fields = gen.get('log_fields', [])
    if not isinstance(log_fields, list) or any(not isinstance(x, str) for x in log_fields):
        errors.append('generation/log_fields must be an array of strings')
        log_fields = []
    missing_log = [f for f in LOG_FIELDS if f not in log_fields]
    if missing_log:
        warnings.append('generation/log_fields missing: ' + ', '.join(missing_log)
                        + '; keep a generation log for license safety')

    market = c.get('marketplace', {})
    if not isinstance(market, dict):
        errors.append('marketplace must be an object')
        market = {}
    target = market.get('target')
    if target not in MARKETS:
        errors.append('marketplace/target must be one of: ' + ', '.join(MARKETS))
    ai_generated = market.get('ai_generated', False)
    if type(ai_generated) is not bool:
        errors.append('marketplace/ai_generated must be boolean')
        ai_generated = False
    if 'ai_disclosure' in market and type(market['ai_disclosure']) is not bool:
        errors.append('marketplace/ai_disclosure must be boolean')
    if target == 'gamedev-market' and ai_generated:
        errors.append('gamedev-market bans AI-generated assets; pick another marketplace or drop AI generation')
    if target == 'itch.io' and ai_generated and not market.get('ai_disclosure'):
        errors.append('itch.io requires an AI disclosure for AI-generated assets; set marketplace/ai_disclosure')
    if target == 'unity-asset-store' and ai_generated:
        warnings.append('unity-asset-store reviews AI-generated assets strictly; disclose AI use and keep the generation log')
    price = market.get('price_usd')
    if price is not None and (not _finite(price) or price < 0):
        errors.append('marketplace/price_usd must be a finite non-negative number when declared')

    effect_rows, total_frames, total_ms, total_cost = [], 0, 0, 0.0
    seen = set()
    for effect in _spec_effects(c, errors):
        if not isinstance(effect, dict):
            errors.append('Each effect must be an object')
            continue
        vid = effect.get('vfx_id')
        if not _safe(vid) or vid in seen:
            errors.append('Each effect needs a unique safe vfx_id')
            continue
        seen.add(vid)
        if effect.get('taxonomy') not in TAXONOMY:
            errors.append(f'{vid}: taxonomy must be one of: ' + ', '.join(TAXONOMY))
        if type(effect.get('loop')) is not bool:
            errors.append(f'{vid}: loop must be boolean')
        if not isinstance(effect.get('blend_intent'), str) or not effect['blend_intent'].strip():
            errors.append(f'{vid}: blend_intent must be declared')
        if effect.get('alpha_policy') not in ('binary', 'soft'):
            errors.append(f'{vid}: alpha_policy must be binary or soft')
        cell = effect.get('cell_size', default_cell)
        if not _positive_pair(cell):
            errors.append(f'{vid}: cell_size must contain two positive integers (effect or default_cell_size)')
            cell = None
        frames = effect.get('frames')
        if not isinstance(frames, list) or not frames:
            errors.append(f'{vid}: frames must be a nonempty array')
            frames = []
        fids, source_paths, dur = set(), set(), 0
        for frame in frames:
            if not isinstance(frame, dict):
                errors.append(f'{vid}: each frame must be an object')
                continue
            fid = frame.get('id')
            if not _safe(fid) or fid in fids:
                errors.append(f'{vid}: each frame needs a unique safe id')
                continue
            fids.add(fid)
            if not is_safe_relative_path(frame.get('path')):
                errors.append(f'{vid}/{fid}: safe project-relative frame path required')
            else:
                normalized = Path(frame['path']).as_posix()
                if normalized in source_paths:
                    errors.append(f'{vid}/{fid}: duplicate normalized frame path')
                source_paths.add(normalized)
            d = frame.get('duration_ms')
            if type(d) is not int or d <= 0:
                errors.append(f'{vid}/{fid}: duration_ms must be a positive integer')
            else:
                dur += d
        events = effect.get('events', {})
        if not isinstance(events, dict):
            errors.append(f'{vid}: events must be an object')
        if isinstance(events, dict):
            for key in ('visual_peak_ms', 'gameplay_hit_ms'):
                if key in events and (type(events[key]) is not int or not 0 <= events[key] <= dur):
                    errors.append(f'{vid}: events/{key} is outside the effect duration')
        contract = effect.get('vfx_contract')
        if contract is not None and not is_safe_relative_path(contract):
            errors.append(f'{vid}: vfx_contract must be a safe project-relative path when declared')
        effect_cost = cost if _finite(cost) and cost else 0.0
        total_frames += len(frames)
        total_ms += dur
        total_cost += effect_cost
        effect_rows.append({
            'vfx_id': vid, 'taxonomy': effect.get('taxonomy'), 'loop': effect.get('loop'),
            'frames': len(frames), 'total_duration_ms': dur,
            'cell_size': list(cell) if cell else None,
            'cost_estimate_usd': round(effect_cost, 4),
            'deliverables': [f'sheets/{vid}.png', f'previews/{vid}.gif', f'meta/{vid}.json'],
        })

    bundle_manifest = ['LICENSE', 'README.md', 'pack-manifest.json']
    if ai_generated:
        bundle_manifest.append('AI_DISCLOSURE.txt')
    if gen:
        bundle_manifest.append('generation-log.csv')
    for row in effect_rows:
        bundle_manifest.extend(row['deliverables'])

    return {
        'status': 'blocked' if errors else 'ready',
        'art_approval': 'not_evaluated',
        'errors': errors, 'warnings': warnings,
        'pack_id': c.get('pack_id'),
        'effects': effect_rows,
        'totals': {
            'effects': len(effect_rows), 'frames': total_frames,
            'duration_ms': total_ms,
            'cost_estimate_usd': round(total_cost, 4),
        },
        'bundle_manifest': bundle_manifest,
        'limitation': ('Pack planning validates spec structure, marketplace policy gates and '
                        'bundle completeness only. Per-effect visual approval still requires '
                        'vfx-review-template/vfx-qa and runtime acceptance requires the '
                        'target-engine gates from vfx-production.md.'),
    }


def _check_image(path, label, errors, warnings):
    from PIL import Image
    try:
        with Image.open(path) as src:
            if getattr(src, 'n_frames', 1) != 1:
                errors.append(f'{label}: animated source must be extracted to explicit frames')
            im = src.convert('RGBA')
            if im.getchannel('A').getbbox() is None:
                errors.append(f'{label}: fully transparent image')
            return list(im.size)
    except OSError as exc:
        errors.append(f'{label}: unreadable image: {exc}')
        return None


def vfx_pack_bundle_check(pack_path, bundle_dir):
    """Validate structure and bind every ordered sheet cell to source RGBA.

    Ready means structural readiness only; this function cannot approve art.
    GIF is lossy and binary-alpha: its preview must declare a compositing mode.
    """
    from PIL import Image, ImageChops, ImageStat
    errors, warnings, effect_rows, binding, artifacts = [], [], [], {}, {}
    try:
        c, root = _load(pack_path, 'VFX pack')
    except (OSError, ValueError) as exc:
        return {'status': 'blocked', 'structural_ready': False, 'art_approval': 'not_evaluated',
                'errors': [str(exc)], 'warnings': []}
    plan = vfx_pack_plan(pack_path)
    errors.extend('spec: ' + e for e in plan['errors'])
    if errors:
        return {'status': 'blocked', 'structural_ready': False, 'art_approval': 'not_evaluated', 'errors': errors, 'warnings': warnings}
    bundle = Path(bundle_dir).resolve()

    def need(rel, label):
        try:
            p = resolve_under(bundle, rel)
            if not p.is_file():
                raise ValueError(f'missing {label}: {rel}')
            artifacts[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
            return p
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
            return None

    def load_json(p, label):
        if p is None:
            return None
        try:
            return json.loads(p.read_text())
        except (OSError, ValueError) as exc:
            errors.append(f'{label}: invalid JSON: {exc}')

    def nonempty_text(p, name):
        if p:
            try:
                if not p.read_text().strip():
                    errors.append(f'{name}: must be nonempty')
            except (OSError, ValueError) as exc:
                errors.append(f'{name}: unreadable text: {exc}')

    for name in ('LICENSE', 'README.md'):
        nonempty_text(need(name, name), name)
    market = c.get('marketplace', {})
    if isinstance(market, dict) and market.get('ai_generated') is True:
        p = need('AI_DISCLOSURE.txt', 'AI disclosure')
        nonempty_text(p, 'AI_DISCLOSURE.txt')
    ids = [e['vfx_id'] for e in plan['effects']]
    manifest = load_json(need('pack-manifest.json', 'pack manifest'), 'pack-manifest.json')
    manifest_rows = {}
    if not isinstance(manifest, dict) or manifest.get('pack_id') != c.get('pack_id'):
        errors.append('pack-manifest.json: must be an object with matching pack_id')
    else:
        entries = manifest.get('effects')
        if not isinstance(entries, list):
            errors.append('pack-manifest.json: effects must be an array')
        else:
            for entry in entries:
                if not isinstance(entry, dict) or not _safe(entry.get('vfx_id')):
                    errors.append('pack-manifest.json: each effect must be an object with safe vfx_id')
                    continue
                vid = entry['vfx_id']
                if vid in manifest_rows or vid not in ids:
                    errors.append(f'pack-manifest.json: duplicate or undeclared effect: {vid}')
                manifest_rows[vid] = entry
            for vid in ids:
                if vid not in manifest_rows:
                    errors.append(f'pack-manifest.json missing effect: {vid}')

    gen = c.get('generation', {})
    if isinstance(gen, dict) and gen:
        p = need('generation-log.csv', 'generation log')
        if p:
            try:
                with p.open(newline='') as f:
                    reader = csv.DictReader(f)
                    fields = reader.fieldnames or []
                    required = ('vfx_id',) + LOG_FIELDS
                    if any(k not in fields for k in required) or len(fields) != len(set(fields)):
                        errors.append('generation-log.csv: unique columns vfx_id, model, seed, prompt, date required')
                    rows = list(reader)
                logged = set()
                for row in rows:
                    if None in row or any(not isinstance(row.get(k), str) or not row[k].strip() for k in required):
                        errors.append('generation-log.csv: incomplete or malformed data row')
                    vid = row.get('vfx_id')
                    if vid not in ids:
                        errors.append('generation-log.csv: undeclared effect identity')
                    logged.add(vid)
                for vid in ids:
                    if vid not in logged:
                        errors.append(f'generation-log.csv: missing data row for {vid}')
            except (OSError, ValueError, csv.Error) as exc:
                errors.append(f'generation-log.csv: {exc}')

    specs = {e['vfx_id']: e for e in c.get('effects', [])
             if isinstance(e, dict) and _safe(e.get('vfx_id'))}
    for row in plan['effects']:
        vid = row['vfx_id']
        effect = specs[vid]
        paths = {'sheet': f'sheets/{vid}.png', 'gif': f'previews/{vid}.gif', 'meta': f'meta/{vid}.json'}
        entry = manifest_rows.get(vid, {})
        for key, rel in paths.items():
            if entry.get(key) != rel:
                errors.append(f'{vid}: manifest {key} must equal {rel}')
        sources = []
        for frame in effect['frames']:
            try:
                p = resolve_under(root, frame['path'])
                with Image.open(p) as im:
                    if getattr(im, 'n_frames', 1) != 1:
                        raise ValueError('animated source requires explicit frames')
                    src = im.convert('RGBA')
                    if list(src.size) != row['cell_size']:
                        raise ValueError('source size does not match cell_size')
                    if src.getchannel('A').getbbox() is None:
                        raise ValueError('fully transparent source frame')
                    if effect['alpha_policy'] == 'binary' and any(v not in (0, 255) for v in src.getchannel('A').getdata()):
                        raise ValueError('source violates binary alpha_policy')
                    sources.append(src.copy())
                binding[f"{vid}/{frame['id']}"] = hashlib.sha256(p.read_bytes()).hexdigest()
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append(f'{vid}: source frame invalid: {exc}')
        sheet_p = need(paths['sheet'], 'effect sheet')
        if sheet_p and row['cell_size']:
            try:
                with Image.open(sheet_p) as im:
                    sheet = im.convert('RGBA')
                cw, ch = row['cell_size']
                cols = sheet.width // cw
                if sheet.width % cw or sheet.height % ch or cols * (sheet.height // ch) != row['frames']:
                    errors.append(f'{vid}: sheet grid does not match declared cells')
                elif len(sources) == row['frames']:
                    for i, src in enumerate(sources):
                        x, y = (i % cols) * cw, (i // cols) * ch
                        cell = sheet.crop((x, y, x + cw, y + ch))
                        if cell.tobytes() != src.tobytes():
                            errors.append(f'{vid}: sheet cell {i} RGBA does not match ordered source')
            except (OSError, ValueError) as exc:
                errors.append(f'{vid}: unreadable sheet: {exc}')
        meta = load_json(need(paths['meta'], 'effect metadata'), paths['meta'])
        if not isinstance(meta, dict):
            errors.append(f'{vid}: metadata must be an object')
            meta = {}
        for key in ('vfx_id', 'loop', 'blend_intent', 'alpha_policy'):
            if type(meta.get(key)) is not type(effect.get(key)) or meta.get(key) != effect.get(key):
                errors.append(f'{vid}: metadata {key} differs from spec')
        if meta.get('events', {}) != effect.get('events', {}):
            errors.append(f'{vid}: metadata events differ from spec')
        if meta.get('frames') != effect.get('frames'):
            errors.append(f'{vid}: metadata ordered frames must match spec IDs, paths and durations')
        preview = meta.get('gif_preview')
        mode = preview.get('mode') if isinstance(preview, dict) else None
        background = preview.get('background_rgb') if isinstance(preview, dict) else None
        if mode not in ('binary-alpha', 'composite'):
            errors.append(f'{vid}: gif_preview mode must declare binary-alpha or composite')
        if mode == 'binary-alpha' and effect['alpha_policy'] == 'soft':
            errors.append(f'{vid}: soft alpha requires a composite GIF preview; GIF cannot preserve soft alpha')
        if mode == 'composite' and (not isinstance(background, list) or len(background) != 3 or any(type(x) is not int or not 0 <= x <= 255 for x in background)):
            errors.append(f'{vid}: composite GIF requires background_rgb byte triple')
            mode = None
        gif_p = need(paths['gif'], 'effect preview GIF')
        if gif_p:
            try:
                with Image.open(gif_p) as gif:
                    if gif.format != 'GIF' or gif.n_frames != row['frames']:
                        errors.append(f'{vid}: GIF frames/format do not match spec')
                    if (effect['loop'] and gif.info.get('loop') != 0) or (not effect['loop'] and 'loop' in gif.info):
                        errors.append(f'{vid}: GIF loop differs from spec')
                    for i in range(gif.n_frames):
                        gif.seek(i)
                        if i >= len(effect['frames']):
                            continue
                        d = gif.info.get('duration', 0)
                        expected = effect['frames'][i]['duration_ms']
                        if not isinstance(d, int) or d <= 0 or abs(d - expected) >= 10:
                            errors.append(f'{vid}: GIF frame {i} duration differs beyond centisecond rounding')
                        if i < len(sources) and mode:
                            src = sources[i]
                            actual = gif.convert('RGBA')
                            if actual.size != src.size:
                                errors.append(f'{vid}: GIF frame {i} size differs from source')
                                continue
                            if mode == 'composite':
                                expected_im = Image.new('RGBA', src.size, tuple(background) + (255,))
                                expected_im.alpha_composite(src)
                            else:
                                expected_im = src
                            if actual.getchannel('A').tobytes() != expected_im.getchannel('A').tobytes():
                                errors.append(f'{vid}: GIF frame {i} alpha differs from declared preview')
                            if mode == 'binary-alpha':
                                # Hidden transparent RGB is not displayed and GIF cannot preserve it.
                                visible_actual = Image.new('RGBA', src.size, (0, 0, 0, 255))
                                visible_expected = visible_actual.copy()
                                visible_actual.alpha_composite(actual)
                                visible_expected.alpha_composite(expected_im)
                                actual, expected_im = visible_actual, visible_expected
                            diff = ImageChops.difference(actual.convert('RGB'), expected_im.convert('RGB'))
                            if max(ImageStat.Stat(diff).mean) > 8:
                                errors.append(f'{vid}: GIF frame {i} pixels differ from declared preview')
            except (OSError, ValueError, EOFError) as exc:
                errors.append(f'{vid}: unreadable GIF: {exc}')
        contract = effect.get('vfx_contract')
        if contract:
            try:
                cp = resolve_under(root, contract)
                cc, contract_root = _load(cp, 'VFX')
                for key in ('vfx_id', 'frames', 'loop', 'blend_intent', 'alpha_policy'):
                    if cc.get(key) != effect.get(key):
                        errors.append(f'{vid}: contract {key} differs from pack spec')
                if cc.get('events', {}) != effect.get('events', {}):
                    errors.append(f'{vid}: contract events differ from pack spec')
                if cc.get('cell_size') != effect.get('cell_size', c.get('default_cell_size')) or cc.get('representation') != c.get('representation'):
                    errors.append(f'{vid}: contract canvas/representation differs from pack spec')
                for pack_frame, contract_frame in zip(effect['frames'], cc.get('frames', [])):
                    pack_source = resolve_under(root, pack_frame['path'])
                    contract_source = resolve_under(contract_root, contract_frame['path'])
                    if hashlib.sha256(pack_source.read_bytes()).digest() != hashlib.sha256(contract_source.read_bytes()).digest():
                        errors.append(f'{vid}/{pack_frame["id"]}: contract source identity differs from pack source')
                report = vfx_check(str(cp))
                errors.extend(f'{vid}: contract: {e}' for e in report.get('errors', []))
                warnings.extend(f'{vid}: contract: {w}' for w in report.get('warnings', []))
            except (OSError, ValueError, TypeError, KeyError) as exc:
                errors.append(f'{vid}: contract invalid: {exc}')
        effect_rows.append({'vfx_id': vid})
    return {'status': 'blocked' if errors else 'ready', 'structural_ready': not errors,
            'art_approval': 'not_evaluated', 'runtime_approval': 'not_evaluated',
            'errors': errors, 'warnings': warnings, 'pack_id': c.get('pack_id'),
            'bundle': str(bundle), 'effects': effect_rows, 'source_binding': binding, 'artifact_binding': artifacts,
            'spec_binding': hashlib.sha256(Path(pack_path).read_bytes()).hexdigest(),
            'limitation': 'Structural readiness only. Source hashes bind this check to inputs; visual and target-runtime gates remain required before release.'}
