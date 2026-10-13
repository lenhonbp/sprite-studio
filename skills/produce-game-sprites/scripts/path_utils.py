"""Portable path validation for project-relative skill contracts."""
from pathlib import Path


def is_safe_relative_path(raw):
    if not isinstance(raw, str) or not raw.strip() or '\x00' in raw or '\\' in raw:
        return False
    p = Path(raw)
    if p.is_absolute() or any(part == '..' for part in p.parts):
        return False
    return p.as_posix() not in ('.', '')


def resolve_under(root, raw):
    """Resolve a declared relative path and refuse parent/symlink escape."""
    if not is_safe_relative_path(raw):
        raise ValueError(f'Unsafe relative path: {raw!r}')
    base = Path(root).resolve()
    target = (base / raw).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError(f'Path escapes contract root: {raw!r}') from exc
    return target
