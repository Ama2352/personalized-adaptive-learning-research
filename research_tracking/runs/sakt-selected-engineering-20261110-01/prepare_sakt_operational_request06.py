"""Root-only derivative request sau NO-GO4GiB, không ghi hoặc thay authorization."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OLD = PREP/'sakt_selected_fit04_request.ROOT.json'
OLD_SHA = 'be63bb6bb29b3ffbee6b8bccca2422376f8f0aebc435c5be72eceafdc1cc6793'
NO_GO = PREP/'sakt-selected-fit04/result.json'
NO_GO_SHA = '8963650d0aaea07b89a06c96f1869db3fed7399832103a70956157a14f889bff'
OUTER_NO_GO = PREP/'sakt-selected-fit04/outer-final.json'
OUTER_NO_GO_SHA = '32f25fc0a8b8c537b16a0e7cca9afd20852079ee1b509659a91ac660557011ff'
WORKER = PREP/'check_sakt_selected_fit05.py'
OUTER = PREP/'run_sakt_selected_fit05.py'
REQUEST = PREP/'sakt_selected_fit05_request.ROOT.json'
OUT = PREP/'sakt-selected-operational-request05'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def valid_sha(value):
    need(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'full lowercase SHA256')


def sha(path):
    need(path.is_file() and path.stat().st_size <= 8*2**20, 'bounded source/metadata')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)+'\n').encode()


def publish(path, value):
    payload = raw(value); need(len(payload) <= 2**20, 'small request/receipt')
    with path.open('xb') as stream:
        need(stream.write(payload) == len(payload), 'complete write')
        stream.flush(); os.fsync(stream.fileno())
    need(sha(path) == hashlib.sha256(payload).hexdigest(), 'byte readback')


def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    for n in ('self-sha256', 'worker-sha256', 'outer-sha256', 'approval-reference'):
        parser.add_argument('--'+n, required=True)
    args = parser.parse_args()
    for h in (args.self_sha256, args.worker_sha256, args.outer_sha256): valid_sha(h)
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import entry, safe
    entry()
    need(sha(Path(__file__)) == args.self_sha256 and sha(WORKER) == args.worker_sha256
         and sha(OUTER) == args.outer_sha256 and args.approval_reference.strip(), 'Root exact derivative review')
    need(sha(OLD) == OLD_SHA and sha(NO_GO) == NO_GO_SHA and sha(OUTER_NO_GO) == OUTER_NO_GO_SHA, 'actual immutable NO-GO proofs')
    previous = json.loads(OLD.read_bytes()); failed = json.loads(NO_GO.read_bytes()); outer = json.loads(OUTER_NO_GO.read_bytes())
    need(failed['status'] == 'REJECTED_SAKT_KEEP_PARTIAL' and failed['native_outputs'] == {}
         and failed['error'] == dict(type='ValueError', message='SAKT preallocation RAM floor'), 'exact preallocation refusal')
    observer = failed['observer']
    need(observer['counts']['lazy_tools'] == dict(started=0, returned=0, exceptions=0)
         and observer['training_targets'] == observer['selection_targets'] == 0
         and observer['constructor_metadata'] == observer['epochs'] == []
         and observer['installed_after_actual_lazy_tools'] is False, 'no native allocation or work')
    need(failed['source_before'] == failed['source_after'] == previous['source_pins']
         and failed['input_before'] == failed['input_after'] == previous['input_pins']
         and failed['runtime_before'] == failed['runtime_after'] == previous['runtime_pins'], 'NO-GO source stability')
    need(outer['status'] == 'REJECTED_SAKT_KEEP_PARTIAL'
         and outer['owned_receipt']['cleanup_accepted'] is True and outer['owned_receipt']['job_active_after_cleanup'] == 0, 'actual Job0 cleanup')
    need(previous['specification']['run_id'] == 'sakt-selected-engineering10x84-20261110-03', 'same unallocated native run')
    auth = safe(ROOT/previous['authorization_file'])
    need(sha(auth) == previous['authorization_sha256'], 'same exact authorization bytes')
    native = ROOT/'experiments/sakt/results/sakt-selected-engineering10x84-20261110-03'
    need(not native.exists() and not REQUEST.exists() and not OUT.exists()
         and not (PREP/'sakt-selected-fit05').exists() and not (PREP/'sakt-selected-fit05-owned').exists(), 'new operational attempt, native remains absent')
    for field in ('source_pins', 'input_pins', 'runtime_pins'):
        for name, digest in previous[field].items():
            valid_sha(digest); path = Path(name) if Path(name).is_absolute() else ROOT/name
            need(sha(safe(path)) == digest, 'unchanged previous source/input/runtime')
    request = json.loads(raw(previous))
    for path, digest in ((Path(__file__).resolve(), args.self_sha256), (WORKER, args.worker_sha256), (OUTER, args.outer_sha256)):
        request['source_pins'][path.relative_to(ROOT).as_posix()] = digest
    for path, digest in ((OLD, OLD_SHA), (NO_GO, NO_GO_SHA), (OUTER_NO_GO, OUTER_NO_GO_SHA)):
        request['input_pins'][path.relative_to(ROOT).as_posix()] = digest
    request['approval_reference'] = args.approval_reference
    request['operational_retry'] = dict(kind='ROOT_APPROVED_RESOURCE_COORDINATION_AFTER_PREALLOCATION_NO_GO',
        prior_request_sha256=OLD_SHA, prior_worker_result_sha256=NO_GO_SHA, prior_outer_sha256=OUTER_NO_GO_SHA,
        previous_elapsed_seconds=outer['elapsed_seconds'], previous_native_models=0, previous_optimizer_steps=0,
        previous_optimized_targets=0, same_authorization=True, same_native_run_id=True,
        unchanged_preallocation_floor_bytes=4*2**30, no_automatic_retry=True)
    for n in ('specification', 'evidence', 'selected_spec_sha256', 'authorization_file', 'authorization_sha256', 'allocation'):
        need(request[n] == previous[n], 'preserve all scientific identity, authority and allocation')
    need(time.perf_counter()-started < 25., 'finite metadata preparation')
    OUT.mkdir()
    publish(OUT/'before.json', dict(old_request_sha256=OLD_SHA, authorization_sha256=sha(auth),
        native_existed=False, request_existed=False, source_pins=request['source_pins']))
    publish(REQUEST, request)
    need(sha(auth) == previous['authorization_sha256'] and sha(OLD) == OLD_SHA and not native.exists(), 'authority/parent bytes unchanged, no native execution')
    publish(OUT/'result.json', dict(status='PREPARED_NEW_OPERATIONAL_REQUEST_ONLY_SAME_AUTH_NATIVE_RUN',
        request_sha256=sha(REQUEST), authorization_sha256=sha(auth), auth_written=False, models_executed=False,
        prior_NO_GO_preserved=True, elapsed_seconds=time.perf_counter()-started))


if __name__ == '__main__':
    main()
