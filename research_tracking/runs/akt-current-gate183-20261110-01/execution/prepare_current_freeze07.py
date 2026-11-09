"""ROOT-only source freeze metadata; không collect, chạy test hoặc cấp Gate PASS."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys


ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
SNAPSHOT = PREP/'gate_source_snapshot07.json'
SNAPSHOT_SHA = '00f0e3afceccb7ae6e206d62efe21760451d4f55250e061d0ebb73951f198838'
WORKER = PREP/'gate_collection_worker12.py'
OUTER = PREP/'run_gate_collection12.py'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--helper-sha256', required=True)
    parser.add_argument('--snapshot-sha256', required=True)
    parser.add_argument('--collection-worker-sha256', required=True)
    parser.add_argument('--collection-outer-sha256', required=True)
    parser.add_argument('--root-freeze-reference', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    need(Path(sys.executable).absolute() == ROOT/'.venv/Scripts/python.exe'
         and Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv required')
    need(sha(Path(__file__)) == args.helper_sha256 and args.snapshot_sha256 == SNAPSHOT_SHA
         and sha(SNAPSHOT) == SNAPSHOT_SHA and sha(WORKER) == args.collection_worker_sha256
         and sha(OUTER) == args.collection_outer_sha256
         and args.root_freeze_reference.strip(), 'ROOT reviewed source/snapshot/reference pins')
    raw = SNAPSHOT.read_bytes()
    need(len(raw) <= 2*1024**2, 'bounded metadata snapshot')
    snapshot = json.loads(raw)
    need(snapshot['kind'] == 'SOURCE_METADATA_SNAPSHOT_NOT_ROOT_FREEZE_OR_GATE'
         and snapshot['execution_authority'] is False and snapshot['collected_case_count'] is None,
         'source snapshot cannot be collection or execution proof')
    for name, digest in snapshot['reused_source_sha256'].items():
        need(sha(ROOT/name) == digest, 'reused original source/proof changed')
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import safe
    outer = load(OUTER, 'reviewed_collection12_metadata_definitions')
    outer.safe = safe
    packet = {key:snapshot[key] for key in ('gate_build_hashes', 'test_module_sha256', 'module_groups',
        'lock_file', 'lock_sha256', 'upstream_file_sha256', 'support_document_sha256')}
    packet.update(schema_version=1, kind='ROOT_FROZEN_GATE2_COLLECTION_INPUT',
        root_freeze_reference=args.root_freeze_reference,
        metadata_snapshot=dict(path=SNAPSHOT.relative_to(ROOT).as_posix(), sha256=SNAPSHOT_SHA))
    outer.validate_packet(packet)
    before = outer.snapshot(packet)
    native = load(ROOT/'scripts/akt/refresh_gate2.py', 'reviewed_source_freeze07_native_definitions')
    need(native.gate2_build_hashes() == packet['gate_build_hashes']
         and [dict(name=name, modules=modules) for name, modules in native.test_partition(ROOT)]
         == packet['module_groups'], 'whole exact canonical build map and ordered partition required')
    forbidden = ('torch', 'numpy', 'pandas', 'sklearn', 'scipy', 'modal', 'boto3')
    need(not any(name.split('.')[0] in forbidden for name in sys.modules), 'metadata-only definitions required')
    output = safe(args.output)
    need(output.parent == PREP and not output.exists(), 'new exclusive packet in prep')
    payload = (json.dumps(packet, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    need(len(payload) <= 2*1024**2, 'bounded finalized source packet')
    with output.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    need(output.read_bytes() == payload and outer.snapshot(packet) == before
         and SNAPSHOT.read_bytes() == raw and sha(Path(__file__)) == args.helper_sha256
         and sha(WORKER) == args.collection_worker_sha256 and sha(OUTER) == args.collection_outer_sha256,
         'source/controller/readback drift after freeze')
    for name, digest in snapshot['reused_source_sha256'].items():
        need(sha(ROOT/name) == digest, 'reused source/proof drift after freeze')
    print(json.dumps(dict(status='ROOT_SOURCE_IDENTITY_FROZEN_NOT_GATE_OR_EXECUTION_APPROVAL',
        path=str(output), sha256=hashlib.sha256(payload).hexdigest(),
        source_count=len(packet['gate_build_hashes']), module_count=len(packet['test_module_sha256']),
        collected_case_count=None, test_bodies_executed=False)))


if __name__ == '__main__':
    main()
