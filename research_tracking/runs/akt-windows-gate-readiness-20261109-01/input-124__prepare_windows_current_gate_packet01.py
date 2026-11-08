"""ROOT metadata-only preparation; no test collection/body, Job, Torch or native CLI."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'windows_current_gate_worker01.py'
OUTER = PREP/'windows_current_gate_outer01.py'


def need(ok, reason):
    if not ok: raise ValueError(reason)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def module(path,name):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker-sha256',required=True); parser.add_argument('--outer-sha256',required=True)
    parser.add_argument('--runtime-report',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True); parser.add_argument('--root-review-reference',required=True)
    args = parser.parse_args()
    need(sys.executable.lower() == str(ROOT/'.venv/Scripts/python.exe').lower()
         and Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    need(sha(WORKER) == args.worker_sha256 and sha(OUTER) == args.outer_sha256
         and args.root_review_reference.strip(), 'ROOT reviewed exact source pins')
    worker = module(WORKER,'current_gate_packet_worker')
    outer = module(OUTER,'current_gate_packet_outer')
    worker.safe(args.output); worker.safe(args.runtime_report)
    need(args.output.parent == PREP and not args.output.exists(), 'exclusive packet in existing prep')
    actual = PREP/'gate-collection07-outer/final.json'
    original = PREP/'gate_collection01_packet.ROOT.json'
    need(sha(actual) == '88ea96dfe1b601b73c8fd7fbc85def3942a7ed9c4321782dc094d9fbe7dc6dbe', 'ROOT-accepted actual07 only')
    def ref(path): return dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path))
    packet = dict(schema_version=1,kind='ACCEPTED_CURRENT_COLLECTION',root_review_reference=args.root_review_reference,
        collection_input=ref(original),collection_result=ref(actual),runtime_report=ref(args.runtime_report),
        controller_source_pins={WORKER.relative_to(ROOT).as_posix():args.worker_sha256,
            OUTER.relative_to(ROOT).as_posix():args.outer_sha256,
            outer.HELPER.relative_to(ROOT).as_posix():outer.HELPER_SHA,
            outer.JUNIT.relative_to(ROOT).as_posix():outer.JUNIT_SHA})
    need(all(sha(worker.safe(ROOT/name)) == digest for name,digest in packet['controller_source_pins'].items()), 'controller/runtime mapper exact bytes')
    # Read actual3childresults and union without writing a provisional packet.
    _,final = worker.reference(packet['collection_result'])
    _,inputs = worker.reference(packet['collection_input'])
    need(final['status'] == 'ACCEPTED_COLLECTION_ONLY_NOT_GATE_PASS' and final['errors'] == []
         and final['packet_sha256'] == packet['collection_input']['sha256'], 'actual collection accepted, not GatePASS')
    from _pytest import junitxml as utility
    import pytest
    need(Path(utility.__file__).resolve() == outer.JUNIT.resolve()
         and Path(pytest.__file__).resolve().is_relative_to((ROOT/'.venv').resolve())
         and 'torch' not in sys.modules, 'isolated installed pytest utility only')
    nodes = {}
    for group,stage in zip(inputs['module_groups'],final['stages']):
        need(group['name'] == stage['group'], 'actual group ordering')
        _,child = worker.reference(dict(path=stage['child_result_relative'],sha256=stage['child_result_sha256']))
        nodes[group['name']] = child['nodeids']
    need(list(nodes) == ['stdlib','no-torch','remaining'] and len(nodes) == len(final['stages']) == 3, 'exactthreegroups')
    merged = [node for values in nodes.values() for node in values]
    need(merged == final['nodeids'] and len(merged) == len(set(merged)) == final['collected_count'], 'actual exact union')
    packet['expected_JUnit_ids'] = {name:outer.mapped_ids(values,utility) for name,values in nodes.items()}
    packet['expected_JUnit_ids']['merged'] = outer.mapped_ids(merged,utility)
    packet['expected_native_counts'] = {name:len(values) for name,values in packet['expected_JUnit_ids'].items()}
    packet['preparation_source_sha256'] = sha(Path(__file__))
    raw = (json.dumps(packet,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    need(len(raw) <= 2*1024**2, 'bounded metadata packet')
    # All validation in load_collection requires a file. Publish exclusively,
    # then validate readback; on failure keep the rejected packet for evidence.
    with args.output.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    digest = hashlib.sha256(raw).hexdigest()
    worker.load_collection(args.output,digest)
    need(all(sha(ROOT/name) == expected for name,expected in packet['controller_source_pins'].items())
         and sha(actual) == packet['collection_result']['sha256'] and sha(original) == packet['collection_input']['sha256'], 'postpreparation source/inputs drift')
    print(json.dumps(dict(status='PREPARED_COLLECTION_BOUND_FULL_GATE_PACKET_NOT_EXECUTED',
        path=str(args.output),sha256=digest,expected_native_counts=packet['expected_native_counts'],test_bodies_executed=False)))


if __name__ == '__main__': main()
