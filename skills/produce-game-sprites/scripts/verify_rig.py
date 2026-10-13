#!/usr/bin/env python3
"""Reassembly gate for rig-first workflows: composite cut parts at their rig
pivots and verify the result matches the neutral master numerically.

Usage:
    verify_rig.py rig.json master.png parts_dir/ [--ncc-threshold 0.99]

Part files are named <part name>.png. Each may be a full cell-size canvas or a
crop exactly matching the part rect; crops are placed at the rect origin.
Exit 0 when the composite exactly matches the master RGBA (NCC is diagnostic) and every
pivot lands on its part's opaque pixels. Exit 1 on verification failure,
exit 2 on invalid input or I/O.
"""
import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image


def load_rig(path):
    try:
        rig = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f'cannot read rig: {e}')
    if not isinstance(rig, dict):
        raise ValueError('rig must be an object')
    size = rig.get('cell_size')
    if not isinstance(size, list) or len(size) != 2 or not all(type(v) is int and v > 0 for v in size):
        raise ValueError('cell_size must be two positive integers')
    def point(v):
        return isinstance(v, list) and len(v) == 2 and all(type(x) is int for x in v) and 0 <= v[0] < size[0] and 0 <= v[1] < size[1]
    def name(v):
        return isinstance(v, str) and v not in ('.', '..') and bool(v) and all(c.isascii() and (c.isalnum() or c in '._-') for c in v)
    joints = rig.get('joints')
    if not isinstance(joints, dict) or not all(name(k) and point(v) for k,v in joints.items()):
        raise ValueError('joints must map safe names to in-cell integer points')
    parts = rig.get('parts')
    if not isinstance(parts, list) or not parts:
        raise ValueError('parts must be a nonempty array')
    seen = set()
    for part in parts:
        if not isinstance(part, dict) or not name(part.get('name')) or part['name'] in seen:
            raise ValueError('parts require unique safe names')
        seen.add(part['name'])
        rect = part.get('rect')
        if not isinstance(rect, list) or len(rect) != 4 or not all(type(v) is int for v in rect) or min(rect[:2]) < 0 or min(rect[2:]) <= 0 or rect[0]+rect[2] > size[0] or rect[1]+rect[3] > size[1]:
            raise ValueError('part rect must be an in-cell [x,y,w,h]')
        if not point(part.get('pivot_body')) or type(part.get('draw_order', 0)) is not int:
            raise ValueError('part requires in-cell integer pivot_body and integer draw_order')
        if 'pivot_joint' in part and (not isinstance(part['pivot_joint'], str) or part['pivot_joint'] not in joints or part['pivot_body'] != joints[part['pivot_joint']]):
            raise ValueError('pivot_body must equal its declared pivot_joint; no inferred joint mapping')
    return rig


def place_part(canvas, part_img, rect):
    """Paste a part onto the canvas. Full-canvas parts go at (0,0); crops
    matching the rect size go at the rect origin."""
    x, y, w, h = rect
    if part_img.size == canvas.size:
        canvas.alpha_composite(part_img)
    elif part_img.size == (w, h):
        canvas.alpha_composite(part_img, (x, y))
    else:
        raise ValueError(
            f'part size {part_img.size} matches neither canvas {canvas.size} '
            f'nor rect {(w, h)}')


def ncc(a, b):
    """Normalized cross-correlation of two equal-size grayscale images."""
    import statistics
    pa = list(a.getdata())
    pb = list(b.getdata())
    ma = statistics.fmean(pa)
    mb = statistics.fmean(pb)
    num = sum((x - ma) * (y - mb) for x, y in zip(pa, pb))
    da = math.sqrt(sum((x - ma) ** 2 for x in pa))
    db = math.sqrt(sum((y - mb) ** 2 for y in pb))
    if da == 0 or db == 0:
        return 1.0 if pa == pb else 0.0
    return num / (da * db)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rig', help='rig.json path')
    parser.add_argument('master', help='neutral master image path')
    parser.add_argument('parts_dir', help='directory with <part name>.png files')
    parser.add_argument('--ncc-threshold', type=float, default=0.99)
    args = parser.parse_args()

    try:
        rig = load_rig(args.rig)
        master = Image.open(args.master).convert('RGBA')
    except (OSError, ValueError) as e:
        print(f'error: {e}', file=sys.stderr)
        return 2

    cw, ch = rig['cell_size']
    if master.size != (cw, ch):
        print(f'error: master size {master.size} != rig cell_size {(cw, ch)}',
              file=sys.stderr)
        return 2

    parts_dir = Path(args.parts_dir).resolve()
    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    errors = []
    ordered = sorted(rig['parts'], key=lambda p: p.get('draw_order', 0))
    for part in ordered:
        name = part['name']
        rect = part['rect']
        ppath = parts_dir / f'{name}.png'
        try:
            ppath.resolve().relative_to(parts_dir)
        except ValueError:
            errors.append(f'{name}: part file escapes parts directory')
            continue
        if not ppath.exists():
            errors.append(f"missing part file: {ppath.name}")
            continue
        try:
            img = Image.open(ppath).convert('RGBA')
            place_part(canvas, img, rect)
        except (OSError, ValueError) as e:
            errors.append(f'{name}: {e}')
            continue
        # pivot must land on the part's own opaque pixels (in canvas space)
        px, py = part['pivot_body']
        alpha = img.getchannel('A') if img.size == canvas.size else None
        if alpha is not None:
            if not (0 <= px < cw and 0 <= py < ch and alpha.getpixel((px, py)) > 0):
                errors.append(f'{name}: pivot_body {part["pivot_body"]} is not on opaque part pixels')
        else:
            lx, ly = px - rect[0], py - rect[1]
            a = img.getchannel('A')
            if not (0 <= lx < rect[2] and 0 <= ly < rect[3] and a.getpixel((lx, ly)) > 0):
                errors.append(f'{name}: pivot_body {part["pivot_body"]} is not on opaque part pixels')

    score = ncc(canvas.convert('L'), master.convert('L'))
    actual, expected = canvas.tobytes(), master.tobytes()
    changed_pixels = sum(actual[i:i+4] != expected[i:i+4] for i in range(0, len(actual), 4))
    if changed_pixels:
        errors.append(f'lossless RGBA reassembly differs at {changed_pixels} pixels')
    result = {
        'status': 'pass' if not errors and score >= args.ncc_threshold else 'fail',
        'ncc': round(score, 5),
        'rgba_changed_pixels': changed_pixels,
        'rgba_exact': changed_pixels == 0,
        'ncc_threshold': args.ncc_threshold,
        'parts_checked': len(ordered),
        'errors': errors,
    }
    print(json.dumps(result, indent=1))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
