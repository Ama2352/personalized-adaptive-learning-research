"""Ghim nguồn hiện hành bằng API thật, chỉ chuẩn bị collect-only có giới hạn."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == root / '.venv' and sys.dont_write_bytecode
sys.path.insert(0, str(root / 'src'))
from knowledge_tracing.akt.authorization import gate2_build_hashes


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


spec = importlib.util.spec_from_file_location('current_gate195_native', root / 'scripts/akt/refresh_gate2.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
build = gate2_build_hashes()
groups = [dict(name=name, modules=modules) for name, modules in native.test_partition(root)]
modules = [name for group in groups for name in group['modules']]
assert len(build) == 195 and len(modules) == len(set(modules)) == 91
old = json.loads((prep / 'gate_collection07_packet.ROOT.json').read_bytes())
fields = dict(gate_build_hashes=build, test_module_sha256={name: sha(root / name) for name in modules},
    module_groups=groups, lock_file=old['lock_file'], lock_sha256=old['lock_sha256'],
    upstream_file_sha256=old['upstream_file_sha256'], support_document_sha256=old['support_document_sha256'])
assert all(sha(root / name) == digest for name, digest in fields['support_document_sha256'].items())
assert sha(root / fields['lock_file']) == fields['lock_sha256']
assert all(sha(root / 'artifacts/akt/dependencies/upstream' / name) == digest
           for name, digest in fields['upstream_file_sha256'].items())
snapshot_path = prep / 'gate_source_snapshot08.json'
snapshot = dict(schema_version=1, kind='SOURCE_METADATA_SNAPSHOT_NOT_GATE', execution_authority=False,
    collected_case_count=None, source_count=195, test_module_count=91, **fields)
with snapshot_path.open('x', encoding='utf-8') as stream:
    json.dump(snapshot, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
packet_path = prep / 'gate_collection08_packet.ROOT.json'
packet = dict(schema_version=1, kind='ROOT_FROZEN_GATE2_COLLECTION_INPUT',
    root_freeze_reference='ROOT_20261110_CURRENT195_91_EXACT_NATIVE_API_COLLECTION_ONLY_NO_TEST_PASS',
    metadata_snapshot=dict(path=snapshot_path.relative_to(root).as_posix(), sha256=sha(snapshot_path)), **fields)
source = (prep / 'run_gate_collection12.py').read_text(encoding='utf-8')
outer_path = prep / 'run_gate_collection13.py'
with outer_path.open('x', encoding='utf-8') as stream:
    stream.write(source.replace('gate-collection12', 'gate-collection13'))
controller_spec = importlib.util.spec_from_file_location('current_gate195_collection_controller', outer_path)
controller = importlib.util.module_from_spec(controller_spec)
controller_spec.loader.exec_module(controller)
sys.path.insert(0, str(root / 'scripts/research'))
from windows_owned_worker import safe
controller.safe = safe
controller.validate_packet(packet)
controller.snapshot(packet)
with packet_path.open('x', encoding='utf-8') as stream:
    json.dump(packet, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
assert build == gate2_build_hashes() and not {'torch', 'numpy', 'pandas', 'modal'}.intersection(sys.modules)
dispatch = dict(packet=packet_path.relative_to(root).as_posix(), packet_sha256=sha(packet_path),
    outer=outer_path.relative_to(root).as_posix(), outer_sha256=sha(outer_path),
    worker_sha256=sha(prep / 'gate_collection_worker12.py'), source_count=195, modules=91,
    approval_reference='ROOT_CURRENT195_COLLECTION13_REVIEW_60S_NO_MODEL_BODY',
    changes_vi='Chỉ đổi output namespace12→13. Worker/helpers/guards/caps giữ nguyên.')
with (prep / 'gate195_collection13_dispatch.json').open('x', encoding='utf-8') as stream:
    json.dump(dispatch, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dispatch))
