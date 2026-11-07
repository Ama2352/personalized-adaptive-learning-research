"""Bộ Colab phải đủ fixture và không mang outputs notebook lịch sử."""

import hashlib
import json
from pathlib import Path
import runpy


def test_bundle_contains_current_test_dependencies_and_source_only_notebooks():
    collect = runpy.run_path('scripts/akt/build_colab_bundle.py')['bundle_contents']
    contents, transforms = collect()
    for name in ('scripts/akt/refresh_gate2.py','scripts/research/run_cpu_diagnostics.py',
                 'src/knowledge_tracing/paper2_reference.py'):
        assert name in contents
    assert 'requirements-akt.lock.txt' in contents
    assert not any(name.startswith(('dataset/','artifacts/')) or '/results/' in name for name in contents)
    assert len(transforms) == 3
    for name, metadata in transforms.items():
        original_bytes = Path(name).read_bytes()
        assert hashlib.sha256(original_bytes).hexdigest() == metadata['original_sha256']
        original, copied = json.loads(original_bytes), json.loads(contents[name])
        assert [cell['source'] for cell in original['cells']] == [cell['source'] for cell in copied['cells']]
        assert all(not cell.get('outputs') and cell.get('execution_count') is None
                   for cell in copied['cells'] if cell['cell_type']=='code')
