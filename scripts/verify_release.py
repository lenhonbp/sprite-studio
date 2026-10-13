"""Verify archive names, inventory, release metadata and every SHA-256; never extract."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import stat
import sys
import zipfile


def verify(file):
    with zipfile.ZipFile(file) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if not names or len(names) != len(set(names)) or len(names) > 20000:
            raise ValueError('Empty, duplicated or excessive ZIP inventory')
        roots = set()
        for i in infos:
            n = i.filename
            p = PurePosixPath(n)
            if ('\\' in n or ':' in n or '\x00' in n or p.is_absolute() or '..' in p.parts
                    or str(p) != n or len(p.parts) < 2 or i.is_dir()
                    or stat.S_ISLNK(i.external_attr >> 16) or i.flag_bits & 1):
                raise ValueError('Unsafe ZIP entry: ' + n)
            roots.add(p.parts[0])
        if len(roots) != 1 or sum(i.file_size for i in infos) > 1024**3:
            raise ValueError('Invalid root or archive exceeds 1 GiB uncompressed')
        prefix = next(iter(roots)) + '/'
        sums = z.read(prefix + 'SHA256SUMS.txt').decode()
        checks = {}
        for line in sums.splitlines():
            if not re.fullmatch(r'[a-f0-9]{64}  .+', line):
                raise ValueError('Malformed checksum line')
            digest, name = line.split('  ', 1)
            if name in checks:
                raise ValueError('Duplicate checksum path')
            checks[name] = digest
        actual = {n[len(prefix):] for n in names} - {'SHA256SUMS.txt'}
        if set(checks) != actual:
            raise ValueError('Checksum inventory differs from archive')
        for name, digest in checks.items():
            if hashlib.sha256(z.read(prefix + name)).hexdigest() != digest:
                raise ValueError('SHA-256 mismatch: ' + name)
        release = json.loads(z.read(prefix + 'release.json'))
        package = json.loads(z.read(prefix + 'package.json'))
        if release['version'] != package['version'] or prefix != 'Nhon-Le-Sprite-Studio-v' + package['version'] + '/':
            raise ValueError('Release version differs from package/root')
        content_lines = [line for line in sums.splitlines() if not line.endswith('  release.json')]
        tree_hash = hashlib.sha256(('\n'.join(content_lines) + '\n').encode()).hexdigest()
        if release['source_tree_sha256'] != tree_hash or release['files'] != len(actual) - 1:
            raise ValueError('Release tree identity differs')
        for name in ['Nhon-Le-Sprite-Studio.html', 'skills/produce-game-sprites/SKILL.md', 'local/server.mjs']:
            if name not in actual:
                raise ValueError('Missing required release entry: ' + name)
        return {'status': 'passed', 'version': release['version'], 'entries': len(names), 'source_tree_sha256': tree_hash}


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('Usage: python3 scripts/verify_release.py ARCHIVE.zip')
        print(json.dumps(verify(Path(sys.argv[1]))))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}), file=sys.stderr)
        sys.exit(1)
