"""Root-only owned 34case metadata allocation30s; chưa cấp quyền NN."""
import time
PERF, WALL = time.perf_counter, time.time
START, START_WALL = PERF(), WALL()
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'check_sakt_selected_metadata05.py'
PACKET = PREP/'sakt_selected_metadata05_packet.json'
OUT = PREP/'sakt-selected-metadata05-owned'
CHILD = PREP/'sakt-selected-metadata05'
TMP = ROOT/'artifacts/akt/local-tests/ssm05'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed():
    return max(PERF()-START, WALL()-START_WALL)


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    for name in ('packet-sha256','worker-sha256','controller-sha256','approval-reference'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import entry, safe, run_owned
    entry()
    need(sha(safe(PACKET)) == args.packet_sha256 and sha(safe(WORKER)) == args.worker_sha256
         and sha(Path(__file__)) == args.controller_sha256 and args.approval_reference.strip(), 'external reviewed source pins/reference')
    packet = json.loads(PACKET.read_bytes()); pins = packet['source_pins']; runtime = packet['runtime_pins']
    before = {n: sha(safe(ROOT/n)) for n in pins}; runtime_before = {n: sha(Path(n)) for n in runtime}
    need(before == pins and runtime_before == runtime, 'current source/runtime pins')
    need(not any(safe(path).exists() for path in (OUT, CHILD, TMP)), 'exclusive attempt only')
    import psutil
    available = int(psutil.virtual_memory().available)
    if available < 1280*2**20:
        OUT.mkdir()
        write(OUT/'final.json', dict(status='NO_GO_SAKT_METADATA_RAM', available_ram_bytes=available,
            prelaunch_floor_bytes=1280*2**20, owned_launch_started=False, automatic_retry=False))
        raise SystemExit(1)
    owned_seconds = min(27., 30.-elapsed()-3.)
    need(owned_seconds > 3., 'same outer deadline reserve before GO')
    receipt = run_owned(WORKER, ['--packet-sha256', args.packet_sha256], OUT,
        expected_worker_sha256=args.worker_sha256, approval_reference=args.approval_reference,
        max_seconds=owned_seconds, cleanup_reserve_seconds=3, max_output_bytes=65536)
    if not OUT.exists():
        OUT.mkdir()
    write(OUT/'receipt.json', receipt)
    errors = []; child = None
    try:
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup'] == 0
             and receipt['popen_handle_closed'] is True and receipt['errors'] == receipt['cleanup_errors'] == [], 'actual owned terminal/Job0')
        path = CHILD/'result.json'
        need(path.stat().st_size <= 2**20, 'bounded actual child receipt')
        child = json.loads(path.read_bytes())
        need(child['status'] == 'ACCEPTED_34_SAKT_METADATA_PENDING_OUTER' and child['accepted'] is True
             and child['counts'] == dict(tests=34, failures=0, errors=0, skipped=0) and child['pytest_exit_code'] == 0
             and child['error'] is child['junit_error'] is None and child['denied'] == [], 'actual34 cases noFES')
        need(child['nodeids'] == child['body_nodeids'] and len(set(child['nodeids'])) == 34, 'all collected bodies executed')
        optional = child['optional_pytest_symlink_blocks']
        need(type(optional['count']) is int and optional['count'] == len(optional['records']) <= 64
             and all(record['prevented_before_OS'] is True and record['operation'] == 'os.symlink'
                 and record['dir_fd'] == -1 and record['callsite']['pytest_function'] == '_force_symlink'
                 and record['callsite']['pytest_line'] == 219 for record in optional['records']), 'bounded optional Pytest link blocks retain full callsite proof')
        need(child['source_before'] == child['source_after'] == pins and child['runtime_before'] == child['runtime_after'] == runtime
             and child['environment_restored'] is child['actual_scientific_modules_absent'] is True
             and child['packet_sha256'] == args.packet_sha256 and child['elapsed_seconds'] < 20., 'source/runtime/environment/scope')
        memory = child['resources']
        need(memory['samples'] > 0 and memory['peak_worker_rss_bytes'] <= 128*2**20
             and memory['minimum_available_ram_bytes'] >= 2**30 and not (CHILD/'postwrite_rejection.json').exists(), 'observed cooperative worker resources/no late verdict')
    except BaseException as caught:
        errors.append(dict(type=type(caught).__name__, message=str(caught)))
    after = {n: sha(ROOT/n) for n in pins}; runtime_after = {n: sha(Path(n)) for n in runtime}
    outputs = {}
    if CHILD.is_dir():
        for path in CHILD.iterdir():
            if path.is_file():
                need(path.stat().st_size <= 2**20, 'bounded retained metadata evidence')
                outputs[path.name] = dict(bytes=path.stat().st_size, sha256=sha(path))
    accepted = not errors and before == after and runtime_before == runtime_after and sha(PACKET) == args.packet_sha256 and elapsed() < 30.
    final = dict(status='ACCEPTED_34_SAKT_SELECTED_METADATA_NOT_NATIVE' if accepted else 'REJECTED_SAKT_METADATA_KEEP_ALL',
        errors=errors, child_result=child, owned_receipt=receipt, source_before=before, source_after=after,
        runtime_before=runtime_before, runtime_after=runtime_after, outputs=outputs, packet_sha256=args.packet_sha256,
        worker_sha256=args.worker_sha256, controller_sha256=args.controller_sha256, prelaunch_available_ram_bytes=available,
        elapsed_seconds=elapsed(), whole_cap_seconds=30, worker_cap_seconds=20, owned_allocated_seconds=owned_seconds,
        cleanup_reserve_seconds=3, automatic_retry=False, typed_producer_native_validated=False)
    write(OUT/'final.json', final)
    if elapsed() >= 30.:
        write(OUT/'postwrite_rejection.json', dict(reason='same outer deadline after publication')); accepted = False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_SAKT_METADATA_KEEP_ALL', seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
