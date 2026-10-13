"""Build a complete portable archive atomically, with or without a Git checkout."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST = ['.gitignore', 'AGENTS.md', 'local', 'config', 'skills', 'projects',
             'README.md', 'package.json', 'build-offline.py', 'Nhon-Le-Sprite-Studio.html',
             'web', 'server', 'scripts', 'cli', 'docs', 'authoring-source', 'worker',
             'dist', '.openai/hosting.json']
SKIP = {'__pycache__', 'node_modules', '.git', '.pytest_cache'}


def collect(root):
    files = []
    def walk(p):
        if p.name in SKIP:
            return
        if p.is_symlink():
            raise ValueError('Refusing symlink in release: ' + str(p.relative_to(root)))
        name = p.name.lower()
        if (name.startswith('.env') or name in {'credentials.json', 'write.lock', 'state.json', 'id_rsa', 'id_ed25519'}
                or p.suffix.lower() in {'.pem', '.key', '.p12', '.pfx'} or name == '.studio'):
            raise ValueError('Private file is not allowed in release: ' + str(p.relative_to(root)))
        if p.is_dir():
            for child in sorted(p.iterdir()):
                walk(child)
        elif p.is_file():
            files.append(p)
        else:
            raise ValueError('Missing/nonregular release entry: ' + str(p.relative_to(root)))
    for name in ALLOWLIST:
        walk(root / name)
    for p in sorted(root.glob('test-*.mjs')):
        walk(p)
    return sorted(set(files))


def package(root, out):
    root, out = root.resolve(), out.absolute()
    if out.exists() or out.is_symlink():
        raise FileExistsError('Choose a new archive path: ' + str(out))
    subprocess.run([sys.executable, str(root / 'scripts/audit-bundle.py')], check=True, cwd=root)
    files = collect(root)
    version = json.loads((root / 'package.json').read_text())['version']
    prefix = 'Nhon-Le-Sprite-Studio-v' + version + '/'
    checks = []
    git = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=root, capture_output=True, text=True) if __import__('shutil').which('git') else None
    own_git = git is not None and git.returncode == 0 and Path(git.stdout.strip()).resolve() == root
    head = subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], cwd=root, capture_output=True, text=True) if own_git else None
    commit = head.stdout.strip() if head is not None and head.returncode == 0 else None
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip()) if own_git else None
    fd, temporary = tempfile.mkstemp(prefix='.studio-release-', suffix='.zip', dir=out.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            def put(name, data):
                info = zipfile.ZipInfo(prefix + name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, data)
            for p in files:
                rel = p.relative_to(root).as_posix()
                data = p.read_bytes()
                put(rel, data)
                checks.append(hashlib.sha256(data).hexdigest() + '  ' + rel)
            tree_hash = hashlib.sha256(('\n'.join(checks) + '\n').encode()).hexdigest()
            release = {'name': 'Nhon Le Sprite Studio', 'version': version, 'source_commit': commit,
                       'source_git_dirty': dirty, 'source_tree_sha256': tree_hash,
                       'made_by': 'Nhon Le', 'bundled_skill': 'produce-game-sprites v3.8',
                       'rig_module': '2.2.0', 'files': len(files),
                       'private_cloud_projects_included': False, 'qa': 'See docs/QA.md'}
            metadata = (json.dumps(release, indent=2) + '\n').encode()
            put('release.json', metadata)
            checks.append(hashlib.sha256(metadata).hexdigest() + '  release.json')
            put('SHA256SUMS.txt', ('\n'.join(checks) + '\n').encode())
        from verify_release import verify
        result = verify(Path(temporary))
        # Same filesystem: link creation is atomic and cannot replace an existing path.
        os.link(temporary, out)
        return {**result, 'file': str(out), 'bytes': out.stat().st_size,
                'sha256': hashlib.sha256(out.read_bytes()).hexdigest()}
    finally:
        Path(temporary).unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        version = json.loads((ROOT / 'package.json').read_text())['version']
        destination = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / f'Nhon-Le-Sprite-Studio-v{version}-Full-Skill-Nhon-Le.zip'
        print(json.dumps(package(ROOT, destination)))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}), file=sys.stderr)
        sys.exit(1)
