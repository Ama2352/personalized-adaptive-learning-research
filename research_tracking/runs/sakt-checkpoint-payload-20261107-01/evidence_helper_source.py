"""Kiểm integrity evidence bundle, không thực thi nội dung artifact."""

import hashlib
import json
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone
import re
import subprocess
import sys
import time
import traceback


@contextmanager
def record_evidence_run(root: Path, run_id: str, *, metadata: dict, sources: list[Path], note: str):
    """Lưu run mới bất biến, kể cả failure; caller ghi outputs trong context."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_id):
        raise ValueError('invalid evidence run ID')
    directory = root / 'research_tracking/runs' / run_id
    directory.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    manifest = {**metadata, 'status': 'running', 'started_utc': datetime.now(timezone.utc).isoformat(),
                'python': sys.executable, 'command': [sys.executable, *sys.argv],
                'git_head_before_run': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                'sources_sha256': {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                                   for path in sources}}
    def persist():
        (directory / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (directory / 'README.md').write_text(note, encoding='utf-8')
    persist()
    with (directory / 'execution.log').open('x', encoding='utf-8') as log:
        log.write('Bắt đầu run với workload đã ghi trong manifest.\n')
        log.flush()
        try:
            yield directory
            if any(hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
                   for name, digest in manifest['sources_sha256'].items()):
                raise ValueError('evidence source changed during execution')
            manifest['status'] = 'completed'
            log.write('Run hoàn tất, outputs được hash riêng.\n')
        except BaseException as error:
            manifest.update(status='failed', error_type=type(error).__name__, error=str(error))
            traceback.print_exc(file=log)
            raise
        finally:
            log.flush()
            manifest['elapsed_seconds'] = time.perf_counter() - started
            manifest['outputs_sha256'] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                         for path in directory.iterdir() if path.name != 'manifest.json'}
            persist()


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
