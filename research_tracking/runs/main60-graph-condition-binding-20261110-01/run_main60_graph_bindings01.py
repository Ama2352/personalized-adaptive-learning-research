"""Root-only kiểm sáu graph condition, whole60/owned57/worker50, không fit."""
import time
START, WALL = time.perf_counter(), time.time()
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'check_main60_graph_bindings01.py'
PACKET = PREP/'main60_graph_bindings01_packet.json'
OUT = PREP/'main60-graph-conditions01'
OWNED = PREP/'main60-graph-conditions01-owned'
TEMP = OWNED/'runtime-temp'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    need(elapsed() < 60. and path.stat().st_size <= 8*2**20, 'small pinned metadata/source only')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    for name in ('packet-sha256', 'worker-sha256', 'outer-sha256', 'approval-reference'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import entry, safe, run_owned
    entry()
    need(sha(safe(PACKET)) == args.packet_sha256 and sha(safe(WORKER)) == args.worker_sha256
         and sha(Path(__file__)) == args.outer_sha256 and args.approval_reference.strip(), 'external Root source/packet pins')
    packet = json.loads(PACKET.read_bytes())
    pins, inputs, runtime = (packet[n] for n in ('source_pins', 'input_pins', 'runtime_pins'))
    need(all(sha(safe(ROOT/n)) == h for n,h in {**pins, **inputs}.items())
         and all(sha(Path(n)) == h for n,h in runtime.items()), 'actual current source/input/runtime')
    need(not OUT.exists() and not OWNED.exists(), 'exclusive operation')
    import psutil
    available = int(psutil.virtual_memory().available)
    if available < 2*2**30:
        OWNED.mkdir(); write(OWNED/'final.json', dict(status='NO_GO_MAIN60_BINDING_RAM',
            owned_launch_requested=False, available_ram_bytes=available, required_available_ram_bytes=2*2**30, automatic_retry=False))
        raise SystemExit(1)
    environment = dict(os.environ); receipt = result = None; errors = []; outputs = {}
    try:
        os.environ.update(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void',
            OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', TEMP=str(TEMP), TMP=str(TEMP), TMPDIR=str(TEMP))
        remaining = min(57., 60.-elapsed()-3.)
        need(remaining > 3., 'whole deadline leaves cleanup/publication')
        receipt = run_owned(WORKER, ['--packet-sha256', args.packet_sha256], OWNED,
            expected_worker_sha256=args.worker_sha256, approval_reference=args.approval_reference,
            max_seconds=remaining, cleanup_reserve_seconds=3, max_output_bytes=65536)
        if OWNED.exists(): write(OWNED/'receipt.json', receipt)
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup'] == 0
             and receipt['popen_handle_closed'] is True and receipt['errors'] == receipt['cleanup_errors'] == [], 'owned terminal/cleanup')
        need((OUT/'result.json').stat().st_size <= 2**20, 'small result')
        result = json.loads((OUT/'result.json').read_bytes()); summary = result['summary']
        need(result['status'] == 'SIX_MAIN60_CONDITIONS_PENDING_OUTER' and result['error'] is None
             and result['denied'] == result['monitor_errors'] == [] and result['monitor_stopped'] is True
             and result['job_query_handle_closed'] is True and result['environment_and_sys_restored'] is True
             and result['scientific_modules_absent'] is True and result['elapsed_seconds'] < 50., 'data-only worker closure')
        need(result['source_before'] == result['source_after'] == pins and result['input_before'] == result['input_after'] == inputs
             and result['runtime_before'] == result['runtime_after'] == runtime and result['packet_sha256'] == args.packet_sha256, 'pre/post exact pins')
        resource = result['resources']
        need(resource['samples'] > 0 and resource['maximum_job_processes'] >= 1
             and resource['peak_worker_rss_bytes'] <= 512*2**20 and resource['peak_family_rss_bytes'] <= 512*2**20
             and resource['minimum_available_ram_bytes'] >= 1536*2**20
             and result['resource_scope'] == 'CURRENT_EXACT_OWNED_JOB_MEMBERS', 'sampled exact Job limits')
        need(set(summary['conditions']) == set(packet['expected_conditions']) and summary['loader_calls'] == 2
             and summary['new_surrogate_fits'] == summary['neural_model_calls'] == summary['optimizer_calls'] == summary['teacher_calls'] == 0
             and summary['wrong_corpus_rejected'] is True and summary['authority'] is False, 'exact six-condition non-fit scope')
        expected = {'result.json', 'expert-topology.json', 'windows-metadata.json', *(name+'.json' for name in packet['expected_conditions'])}
        need({f.name for f in OUT.iterdir()} == expected, 'exact nine small outputs/no late failures')
        total = 0
        for file in OUT.iterdir():
            need(not file.is_symlink() and not getattr(file,'is_junction',lambda:False)(), 'output alias')
            total += file.stat().st_size; need(total <= 2**20, 'aggregate small output1MiB')
            outputs[file.name] = dict(sha256=sha(file), bytes=file.stat().st_size)
        need(outputs['expert-topology.json']['sha256'] == summary['expert_topology_sha256'], 'shared expert topology bytes')
        need(all(outputs[n]['sha256'] == h for n,h in summary['output_sha256'].items()), 'six exact condition payloads')
        need(all(sha(safe(ROOT/n)) == h for n,h in {**pins, **inputs}.items())
             and all(sha(Path(n)) == h for n,h in runtime.items()), 'outer postcheck pins')
    except BaseException as caught:
        errors.append(dict(type=type(caught).__name__, message=str(caught)))
    finally:
        os.environ.clear(); os.environ.update(environment)
    if not OWNED.exists(): OWNED.mkdir()
    accepted = not errors and os.environ == environment and elapsed() < 60.
    final = dict(status='ACCEPTED_SIX_MAIN60_CONDITION_BINDINGS_NO_MODELS' if accepted else 'REJECTED_MAIN60_BINDINGS_KEEP_PARTIAL',
        errors=errors, owned_receipt=receipt, worker_result=result, output_sha256=outputs,
        packet_sha256=args.packet_sha256, elapsed_seconds=elapsed(), whole_cap_seconds=60,
        authority=False, neural_fit=False, solver_refit=False, automatic_retry=False)
    write(OWNED/'final.json', final)
    if elapsed() >= 60.:
        write(OWNED/'postwrite-rejection.json', dict(reason='same outer deadline')); accepted = False
    print(json.dumps(dict(status=final['status'], elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
