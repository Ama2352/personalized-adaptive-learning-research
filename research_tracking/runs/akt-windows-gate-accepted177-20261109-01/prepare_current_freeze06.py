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
SNAPSHOT = PREP/'gate_source_snapshot06.json'
SNAPSHOT_SHA = 'c88fcc9387a1bd64114126d333651d84e92c9c30e4c8871dc6d99cd7f86600c1'
OUTER = PREP/'run_gate_collection11.py'


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
    revision = snapshot['source_revision_provenance']
    need(revision['kind'] == 'TWO_SOURCE_JUNIT_PHYSICAL_ITEM_FIX_ONLY_NOT_GATE_ACCEPTANCE'
         and revision['failed_gate04_remains_rejected'] is True
         and revision['new_collection_case_count'] is None, 'source revision is not Gate acceptance')
    expected_changes = {
        'scripts/akt/refresh_gate2.py': (
            '9608ddfe1450b2d78699d5ec95d26b8cd65d4439fcc7bda209f698b2e4a7f9ef',
            '8689c5b4737f4eae00459f4a3bc85c22206f58974274304fa4411e36f9acc055'),
        'tests/akt/test_gate2_refresh.py': (
            '255c07a3a1af2d458c8586bd206a3151baadeae76d1fa0a2ce3362409da8d5df',
            '268ace8716285c35db15caaae1efc819776795e3ef931f2e14f41b9cbe2a1e3c'),
    }
    need(len(revision['changed_sources']) == 2 and {
        row['path']: (row['before_sha256'], row['after_sha256'])
        for row in revision['changed_sources']} == expected_changes, 'exact reviewed two-source delta')
    for ref in revision['evidence_refs']:
        path = ROOT/ref['path']
        need(path.is_relative_to(PREP) and '..' not in Path(ref['path']).parts
             and sha(path) == ref['sha256'], 'historical evidence unchanged')
    parent = revision['parent_snapshot']
    need(parent['path'] == (PREP/'gate_source_snapshot05.json').relative_to(ROOT).as_posix()
         and parent['sha256'] == '743c715d2bc711b169d32277443f1c88cd6fdf8954b09dc523fb2860f02afa4d'
         and sha(ROOT/parent['path']) == parent['sha256'], 'exact old native-ordered snapshot preserved')
    previous = json.loads((ROOT/parent['path']).read_bytes())
    changed = {name for name in previous['gate_build_hashes']
               if previous['gate_build_hashes'][name] != snapshot['gate_build_hashes'].get(name)}
    need(set(previous['gate_build_hashes']) == set(snapshot['gate_build_hashes'])
         and changed == set(expected_changes) and previous['module_groups'] == snapshot['module_groups'],
         'whole source population/order unchanged outside exact two patches')
    need(revision['immediate_parent_delta'] == dict(
        added=[], removed=[], changed=list(expected_changes)), 'immediate05 delta2/0/0')
    historical_ref = snapshot['parent_collection_input']
    historical_path = ROOT/historical_ref['path']
    need(historical_path.is_relative_to(PREP) and '..' not in Path(historical_ref['path']).parts
         and sha(historical_path) == historical_ref['sha256'], 'historical154 source packet binding')
    historical = json.loads(historical_path.read_bytes())['gate_build_hashes']
    current = snapshot['gate_build_hashes']
    historical_changed = {name for name in historical if name in current and historical[name] != current[name]}
    need(len(historical) == 154 and len(historical_changed) == 4
         and set(snapshot['delta']['changed']) == historical_changed
         and set(snapshot['delta']['added']) == set(current)-set(historical)
         and len(snapshot['delta']['added']) == 23
         and snapshot['delta']['removed'] == [] and not set(historical)-set(current),
         'historical154 delta23added/4changed/0removed, distinct from immediate05')
    fixture = json.loads((PREP/'gate-junit-items01-owned/final.json').read_bytes())
    need(sha(PREP/'gate-junit-items01-owned/final.json') ==
         '4f7b109e7b927116d78fd7293b2528366796f0f58f44cbdbe6ad7e4e553b15a7'
         and fixture['status'] == 'ACCEPTED_GATE_JUNIT_ITEM_FIXTURES_ONLY'
         and fixture['counts'] == dict(tests=99, failures=0, errors=0, skipped=0)
         and fixture['errors'] == [] and fixture['owned_receipt']['accepted'] is True
         and fixture['owned_receipt']['cleanup_accepted'] is True
         and fixture['owned_receipt']['job_active_after_cleanup'] == 0
         and fixture['source_pins'] == {name: pair[1] for name, pair in expected_changes.items()},
         'actual targeted99 scoped acceptance, not fresh full Gate')
    old_gate = json.loads((PREP/'win-current-gate-20261109-04-child/result.json').read_bytes())
    need(old_gate['status'] == 'REJECTED_NATIVE_GATE' and old_gate['native_returncode'] != 0,
         'old Gate04 rejection remains historical')
    need(sha(OUTER) == args.collection_outer_sha256, 'ROOT reviewed collection outer source')
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import safe
    outer = load(OUTER,'current_freeze_collection_outer11')
    outer.safe = safe  # Existing definitions-only outer uses helper after main().
    packet = {key:snapshot[key] for key in ('gate_build_hashes','test_module_sha256','module_groups',
        'lock_file','lock_sha256','upstream_file_sha256','support_document_sha256')}
    packet.update(schema_version=1,kind='ROOT_FROZEN_GATE2_COLLECTION_INPUT',
        root_freeze_reference=args.root_freeze_reference,
        metadata_snapshot=dict(path=SNAPSHOT.relative_to(ROOT).as_posix(),sha256=SNAPSHOT_SHA))
    packet['ordered_partition_provenance'] = provenance
    packet['source_revision_provenance'] = revision
    outer.validate_packet(packet)
    before = outer.snapshot(packet)
    native = load(ROOT/'scripts/akt/refresh_gate2.py','current_freeze_native_refresh06')
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
