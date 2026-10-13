"""Deterministic shelf packing with lossless trim, pages and edge extrusion."""
import math
from pathlib import Path
from PIL import Image


def build_atlases(manifest, root, ordered_frames, resolve):
    w, h = manifest['cell_size']
    policy = manifest.get('atlas_policy', {})
    maximum, gutter = manifest.get('max_texture_size', 2048), manifest.get('gutter', 2)
    entries = []
    for _, frame in ordered_frames:
        with Image.open(resolve(root, frame['path'])) as src:
            im = src.convert('RGBA')
        rect = im.getchannel('A').getbbox() if policy.get('trim', False) else (0, 0, w, h)
        if rect is None:
            rect = (0, 0, w, h)
        x0, y0, x1, y1 = rect
        cropped = im.crop(rect)
        if cropped.width + 2 * gutter > maximum or cropped.height + 2 * gutter > maximum:
            raise ValueError(f'{frame["id"]}: one frame exceeds max_texture_size including gutters')
        restored = Image.new('RGBA', (w, h))
        restored.paste(cropped, (x0, y0))
        if restored.tobytes() != im.tobytes():
            # Invisible RGB is authored data too. Do not silently discard it.
            raise ValueError(f'{frame["id"]}: trim would discard nonzero RGBA; clean hidden RGB or disable trim')
        entries.append((frame, cropped, rect))

    # Fixed cells retain the previous compact grid layout for one-page users.
    if not policy.get('trim', False):
        cw, ch = w + 2 * gutter, h + 2 * gutter
        mc, mr = maximum // cw, maximum // ch
        if len(entries) > mc * mr and policy.get('multipage', True) is False:
            raise ValueError('Set exceeds single-atlas texture budget; enable atlas_policy.multipage')
        assignments = []
        for base in range(0, len(entries), mc * mr):
            subset = entries[base:base + mc * mr]
            cols = min(mc, max(1, math.ceil(math.sqrt(len(subset) * ch / cw))))
            rows = math.ceil(len(subset) / cols)
            if rows > mr:
                cols, rows = mc, math.ceil(len(subset) / mc)
            assignments.append((cols * cw, rows * ch,
                                [(e, (i % cols) * cw + gutter, (i // cols) * ch + gutter)
                                 for i, e in enumerate(subset)]))
    else:
        assignments, placed = [], []
        x = y = row_h = used_w = 0
        for entry in entries:
            pw, ph = entry[1].width + 2 * gutter, entry[1].height + 2 * gutter
            if x + pw > maximum:
                x, y, row_h = 0, y + row_h, 0
            if y + ph > maximum:
                assignments.append((used_w, y + row_h, placed))
                if policy.get('multipage', True) is False:
                    raise ValueError('Trimmed set exceeds single-atlas texture budget')
                placed, x, y, row_h, used_w = [], 0, 0, 0, 0
            placed.append((entry, x + gutter, y + gutter))
            x += pw
            used_w, row_h = max(used_w, x), max(row_h, ph)
        if placed:
            assignments.append((used_w, y + row_h, placed))

    pages, mapping = [], {}
    for index, (pw, ph, placed) in enumerate(assignments):
        atlas = Image.new('RGBA', (pw, ph))
        local = {}
        for (frame, im, rect), x, y in placed:
            if policy.get('extrude', False) and gutter:
                for n in range(1, gutter + 1):
                    atlas.paste(im.crop((0, 0, im.width, 1)), (x, y - n))
                    atlas.paste(im.crop((0, im.height - 1, im.width, im.height)), (x, y + im.height - 1 + n))
                    atlas.paste(im.crop((0, 0, 1, im.height)), (x - n, y))
                    atlas.paste(im.crop((im.width - 1, 0, im.width, im.height)), (x + im.width - 1 + n, y))
                for dx in range(gutter):
                    for dy in range(gutter):
                        for px, py, sx, sy in [(x-1-dx,y-1-dy,0,0), (x+im.width+dx,y-1-dy,im.width-1,0),
                                               (x-1-dx,y+im.height+dy,0,im.height-1),
                                               (x+im.width+dx,y+im.height+dy,im.width-1,im.height-1)]:
                            atlas.putpixel((px, py), im.getpixel((sx, sy)))
            atlas.paste(im, (x, y))
            meta = {'frame': {'x': x, 'y': y, 'w': im.width, 'h': im.height}, 'rotated': False,
                    'trimmed': rect != (0, 0, w, h),
                    'spriteSourceSize': {'x': rect[0], 'y': rect[1], 'w': im.width, 'h': im.height},
                    'sourceSize': {'w': w, 'h': h},
                    'anchor': {'x': manifest['origin'][0] / w, 'y': manifest['origin'][1] / h}}
            local[frame['id']] = meta
            mapping[frame['id']] = {**meta, 'page': index}
        pages.append({'image': atlas, 'frames': local})
    return pages, mapping
