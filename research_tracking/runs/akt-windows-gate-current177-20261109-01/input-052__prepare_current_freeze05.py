"""ROOT-only metadata preparation; không collect/test/Gate approval/source export."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
SNAPSHOT = PREP/'gate_source_snapshot05.json'
SNAPSHOT_SHA = '743c715d2bc711b169d32277443f1c88cd6fdf8954b09dc523fb2860f02afa4d'
OUTER = PREP/'run_gate_collection10.py'


def need(ok, reason):
    if not ok: raise ValueError(reason)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot-sha256',required=True)
    parser.add_argument('--collection-outer-sha256',required=True)
    parser.add_argument('--root-freeze-reference',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    need(sys.executable.lower() == str(ROOT/'.venv/Scripts/python.exe').lower()
         and Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    need(args.snapshot_sha256 == SNAPSHOT_SHA and args.root_freeze_reference.strip(), 'reviewed snapshot and ROOT freeze reference')
    raw = SNAPSHOT.read_bytes()
    need(len(raw) <= 2*1024**2 and hashlib.sha256(raw).hexdigest() == SNAPSHOT_SHA, 'bounded exact metadata snapshot')
    snapshot = json.loads(raw)
    provenance = snapshot['ordered_partition_provenance']
    diagnostic_path = PREP/'root_gate_freeze04_metadata_diagnostic01.json'
    need(provenance['diagnostic_path'] == diagnostic_path.relative_to(ROOT).as_posix()
         and provenance['diagnostic_sha256'] == 'fe568bca3187f9d9f7336c3cd788bc25f3fb89d78dfe0409a6ce6f69d0bd67bb'
         and sha(diagnostic_path) == provenance['diagnostic_sha256']
         and provenance['operation'] == 'COPY_EXACT_ROOT_ACTUAL_NATIVE_GROUP_ORDER', 'ROOT actual diagnostic binding')
    diagnostic = json.loads(diagnostic_path.read_bytes())
    need(diagnostic['build_equal'] is True and diagnostic['groups_equal'] is False
         and snapshot['module_groups'] == diagnostic['groups'], 'whole ordered native group population from actual diagnostic')
    need(snapshot['kind'] == 'SOURCE_METADATA_SNAPSHOT_NOT_ROOT_FREEZE_OR_GATE'
         and snapshot['execution_authority'] is False and snapshot['collected_case_count'] is None,
         'metadata snapshot is not actual collection or authority')
    need(sha(OUTER) == args.collection_outer_sha256, 'ROOT reviewed collection outer source')
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import safe
    outer = load(OUTER,'current_freeze_collection_outer10')
    outer.safe = safe  # Existing definitions-only outer uses helper after main().
    packet = {key:snapshot[key] for key in ('gate_build_hashes','test_module_sha256','module_groups',
        'lock_file','lock_sha256','upstream_file_sha256','support_document_sha256')}
    packet.update(schema_version=1,kind='ROOT_FROZEN_GATE2_COLLECTION_INPUT',
        root_freeze_reference=args.root_freeze_reference,
        metadata_snapshot=dict(path=SNAPSHOT.relative_to(ROOT).as_posix(),sha256=SNAPSHOT_SHA))
    packet['ordered_partition_provenance'] = provenance
    outer.validate_packet(packet)
    before = outer.snapshot(packet)
    native = load(ROOT/'scripts/akt/refresh_gate2.py','current_freeze_native_refresh05')
    need(native.gate2_build_hashes() == packet['gate_build_hashes']
         and [dict(name=name,modules=modules) for name,modules in native.test_partition(ROOT)] == packet['module_groups'],
         'actual canonical functions match metadata mirror before ROOT freeze')
    need(len(packet['gate_build_hashes']) == 177 and len(packet['test_module_sha256']) == 81
         and 'torch' not in sys.modules, 'exact current population; lightweight preparation')
    output = safe(args.output)
    need(output.parent == PREP and not output.exists(), 'exclusive finalized packet in existing prep')
    payload = (json.dumps(packet,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    with output.open('xb') as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    need(output.read_bytes() == payload and outer.snapshot(packet) == before and SNAPSHOT.read_bytes() == raw
         and sha(OUTER) == args.collection_outer_sha256 and 'torch' not in sys.modules, 'readback/source prepost')
    print(json.dumps(dict(status='ROOT_SOURCE_IDENTITY_FROZEN_NOT_GATE_OR_EXECUTION_APPROVAL',
        path=str(output),sha256=hashlib.sha256(payload).hexdigest(),sources=177,modules=81,
        collected_case_count=None,test_bodies_executed=False)))


if __name__ == '__main__': main()
