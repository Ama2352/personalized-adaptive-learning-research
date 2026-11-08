"""Xác minh nguồn AKT và danh tính thí nghiệm."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess

from .config import AKTConfig

SOURCE_URL = 'https://github.com/arghosh/AKT.git'


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def verify_upstream(root: Path, expected_commit: str) -> dict:
    root = root.resolve()
    commit = _git(root, 'rev-parse', 'HEAD')
    if commit != expected_commit:
        raise ValueError('source commit mismatch')
    if _git(root, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('dirty source checkout')
    if _git(root, 'remote', 'get-url', 'origin') != SOURCE_URL:
        raise ValueError('source remote mismatch')
    paths = {name: root / name for name in ('akt.py', 'README.md', 'LICENSE')}
    if not all(path.is_file() for path in paths.values()):
        raise ValueError('source file missing')
    for name in paths:
        if _git(root, 'hash-object', name) != _git(root, 'rev-parse', f'HEAD:{name}'):
            raise ValueError(f'source content mismatch: {name}')
    if 'MIT License' not in paths['LICENSE'].read_text(encoding='utf-8'):
        raise ValueError('unexpected source license')
    return {
        'commit': commit,
        'tree': _git(root, 'rev-parse', 'HEAD^{tree}'),
        'remote': SOURCE_URL,
        'files': {name: sha256_file(path) for name, path in paths.items()},
    }


def make_run_identity(config: AKTConfig, input_hashes: dict) -> dict:
    payload = json.loads(json.dumps(asdict(config), default=str))
    return {'config': payload, 'input_hashes': dict(input_hashes)}
