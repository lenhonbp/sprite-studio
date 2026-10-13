"""Verify exact source reconstruction; not slicing or artistic approval."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image
from path_utils import resolve_under, is_safe_relative_path


def verify(path):
    path = Path(path).resolve()
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Expected provenance schema 1')
    def image(name):
        if not is_safe_relative_path(name):
            raise ValueError('Unsafe image path')
        with Image.open(resolve_under(path.parent, name)) as im:
            return im.convert('RGBA')
    src = image(data.get('source'))
    errors = []
    if data.get('source_rgba_sha256') != hashlib.sha256(src.tobytes()).hexdigest():
        errors.append('Source RGBA identity mismatch')
    frames = data.get('frames')
    if not isinstance(frames, list) or not frames:
        raise ValueError('frames must be nonempty')
    ids, outputs, bindings = [], set(), {}
    shared = None
    def ints(v, n):
        return isinstance(v, list) and len(v) == n and all(type(x) is int for x in v)
    for f in frames:
        if not isinstance(f, dict):
            raise ValueError('frame must be object')
        fid, out = f.get('id'), f.get('output')
        if not isinstance(fid, str) or not fid or fid in ids:
            raise ValueError('Missing/duplicate frame ID')
        ids.append(fid)
        if not is_safe_relative_path(out):
            raise ValueError('Unsafe output path')
        target = str(resolve_under(path.parent, out))
        if target in outputs or target == str(resolve_under(path.parent, data['source'])):
            raise ValueError('Duplicate output or output aliases source')
        outputs.add(target)
        rect, offset, origin = f.get('source_rect'), f.get('offset'), f.get('origin')
        if not ints(rect, 4) or not ints(offset, 2) or not ints(origin, 2):
            raise ValueError('Invalid rectangle/offset/origin')
        x, y, w, h = rect
        if min(x, y) < 0 or min(w, h) <= 0 or x+w > src.width or y+h > src.height:
            raise ValueError('Rectangle outside source')
        if not (0 <= origin[0] <= w and 0 <= origin[1] <= h):
            raise ValueError('Origin outside canvas')
        if type(f.get('duration_ms')) is not int or f['duration_ms'] <= 0:
            raise ValueError('Invalid duration')
        signature = (w, h, tuple(origin))
        if shared is not None and signature != shared:
            errors.append(fid + ': shared canvas/origin mismatch')
        shared = signature
        im = image(out)
        bindings[fid] = {'output': out, 'rgba_sha256': hashlib.sha256(im.tobytes()).hexdigest(),
                         'size': list(im.size)}
        ox, oy = offset
        if min(ox, oy) < 0 or ox+im.width > w or oy+im.height > h:
            raise ValueError('Output/offset outside canvas')
        restored = Image.new('RGBA', (w, h))
        restored.paste(im, (ox, oy))
        if restored.tobytes() != src.crop((x, y, x+w, y+h)).tobytes():
            errors.append(fid + ': RGBA reconstruction mismatch')
    if data.get('expected_ids') != ids:
        errors.append('Expected frame coverage/order mismatch')
    return {'status': 'blocked' if errors else 'pass', 'errors': errors,
            'frames_checked': len(ids), 'visual_approval': 'not_evaluated',
            'output_bindings': bindings,
            'manifest_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == '__main__':
    try:
        result = verify(sys.argv[1])
        print(json.dumps(result, indent=2))
        sys.exit(1 if result['errors'] else 0)
    except (ValueError, OSError, KeyError, IndexError, TypeError) as exc:
        print(json.dumps({'status': 'invalid_input', 'error': str(exc)}))
        sys.exit(2)
