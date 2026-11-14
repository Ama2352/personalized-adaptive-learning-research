"""Kiểm join selection đầy đủ trên CPU và ghi admission cho staged A2/A3."""
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'src'))

from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
from knowledge_tracing.akt.research_junyi_selection_cache import SelectionCacheSession, write_selection_cpu_admission
from knowledge_tracing.akt.research_junyi_engineering import file_sha

started = time.monotonic()
data = json.loads((HERE/'selection-cache-request02.json').read_text())
inputs = load_full_selected_cache(ROOT/data['selected_cache_root'], ROOT/data['roles_file'],
    expected_manifest_sha256=data['selected_manifest_sha256'], expected_roles_sha256=data['roles_sha256'])
encoding = load_prepared_junyi_encoding(ROOT/data['encoding_file'], ROOT/data['encoding_receipt'],
    view=inputs.train, source_data_sha256=inputs.source_identity,
    expected_file_sha256=data['encoding_sha256'], expected_receipt_sha256=data['encoding_receipt_sha256'])
folder = ROOT/data['output_root']
session = SelectionCacheSession(folder, view=inputs.selection, encoding=encoding,
    source_sha256=inputs.source_identity, expected_targets=inputs.selection_targets,
    expected_manifest_sha256=file_sha(folder/'manifest.json'))
output = ROOT/'artifacts/akt/graph-context-cache/full-train80-staged-20261114-01'
output.mkdir(parents=True, exist_ok=True)
join = output/'selection-admission.json'
window = output/'selection-window-admission.json'
write_selection_cpu_admission(session, join, window)
receipt = dict(status='FULL_SELECTION_CPU_ADMITTED', targets=inputs.selection_targets,
    population_sha256=session.manifest['population_sha256'], seconds=time.monotonic()-started,
    inputs={str(path.relative_to(ROOT)):file_sha(path) for path in (folder/'manifest.json', join, window)})
with (HERE/'selection-admission-acceptance.json').open('x', encoding='utf-8') as stream:
    json.dump(receipt, stream, indent=2)
    stream.write('\n')
print(json.dumps(receipt), flush=True)
