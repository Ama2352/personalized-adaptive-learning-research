"""Kiểm integrity evidence bundle, không thực thi nội dung artifact."""

import hashlib
import json
from pathlib import Path


def verify_evidence_bundle(directory: Path) -> dict:
    directory = Path(directory).resolve()
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('status') != 'completed' or not manifest.get('outputs_sha256'):
        raise ValueError('evidence bundle is incomplete')
    for name, expected in manifest['outputs_sha256'].items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory) or path == directory or path.is_symlink():
            raise ValueError('unsafe evidence artifact path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'evidence hash mismatch: {name}')
    return {'status': 'verified', 'artifacts': len(manifest['outputs_sha256']),
            'kind': manifest.get('kind'),
            'scope': 'Output integrity only, scientific validity requires research review'}
