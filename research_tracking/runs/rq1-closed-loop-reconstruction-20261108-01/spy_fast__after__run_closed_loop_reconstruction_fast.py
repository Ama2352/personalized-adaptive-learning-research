"""Current-source diagnostic reconstruction; model phase requires explicit parent dispatch."""
import argparse
import ast
from contextlib import nullcontext
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from closed_loop_observer import canonical, digest, exact, fingerprint
from closed_loop_observer_fast import ConstructorRegistry, ProfileObserver, make_profile_dispatch

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
HISTORICAL = ROOT / 'research_tracking/runs/cpu-closedloop-20261107-01'
ROLE = 'CURRENT_SOURCE_DIAGNOSTIC_RECONSTRUCTION_NOT_EXACT_HISTORICAL_SOURCE'
CAP = 300.0
OVERALL_CAP = 430.0
PRIOR_FAILED_SECONDS = 120.02970600000117
PRIOR_DIAGNOSTIC_SECONDS = 0.18320319999475032


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fresh_output(path):
    path = path.resolve()
    if path.parent != PREP or path == PREP or path.exists() or path.is_symlink():
        raise ValueError('exclusive direct prep child required')
    return path


def verify_inventory(path, expected_sha):
    if len(expected_sha) != 64 or any(c not in '0123456789abcdef' for c in expected_sha):
        raise ValueError('SHA256 format')
    if path.resolve().parent != PREP or path.is_symlink() or sha(path) != expected_sha:
        raise ValueError('frozen source inventory binding')
    inventory = json.loads(path.read_text(encoding='utf-8'))
    if (inventory.get('revision_cap_seconds') != CAP or inventory.get('overall_cap_seconds') != OVERALL_CAP
            or inventory.get('prior_failed_seconds') != PRIOR_FAILED_SECONDS
            or inventory.get('prior_diagnostic_seconds') != PRIOR_DIAGNOSTIC_SECONDS):
        raise ValueError('explicit revision/overall budget ledger mismatch')
    if inventory['role'] != ROLE:
        raise ValueError('wrong reconstruction identity')
    for rel, digest_value in inventory['files_sha256'].items():
        candidate = ROOT / rel
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(ROOT) or sha(candidate) != digest_value:
            raise ValueError('source/input drift: ' + rel)
    required = {str((PREP / name).relative_to(ROOT)).replace('\\', '/') for name in
                ('closed_loop_observer_fast.py', 'run_closed_loop_reconstruction_fast.py', 'test_closed_loop_observer_fast.py')}
    if not required <= inventory['files_sha256'].keys():
        raise ValueError('missing frozen implementation sources')
    return inventory


class TraceSink:
    def __init__(self, stream, expected, check):
        self.stream, self.expected, self.check = stream, expected, check
        self.observer, self.keys = None, set()

    def write(self, text):
        self.check()
        row = json.loads(text)
        key = (row['seed'], row['profile'], row['variant'], row['step'])
        if key in self.keys or key not in self.expected or not exact(row, self.expected[key]):
            raise ValueError('STORED_LEGACY_EXACT_PARITY_FAILED; no tolerance/drop/repair')
        if self.observer is not None:
            self.observer.legacy(row)
        self.stream.write(text)
        self.keys.add(key)


def write_phase_receipt(output, label, summary, elapsed, inventory_sha):
    if (label not in ('control', 'observed') or summary['pass'] != label
            or summary['legacy_rows'] != 3240 or summary['outcome_rows'] != 27
            or len(summary['native_state_fingerprints']) != 27
            or len(summary['uniform_fingerprints']) != 9
            or not math.isfinite(elapsed) or not 0 <= elapsed <= CAP):
        raise ValueError('incomplete or overbudget phase cannot be published')
    payload = {'kind': 'ENGINEERING_PHASE_PROGRESS_NOT_FINAL_PARITY',
               'status': 'COMPLETED_PHASE_EXACT_STORED_LEGACY_PROJECTION', 'phase': label,
               'role': ROLE, 'source_inventory_sha256': inventory_sha,
               'original_a585_whole_source_recovered': False, 'elapsed_seconds': elapsed,
               'summary': summary,
               'complete_gzip_sha256': {name: sha(output / name) for name in
                   (label + '_legacy.jsonl.gz', label + '_metadata.jsonl.gz')},
               'overall_control_observed_final_parity_accepted': False}
    with (output / (label + '_phase.json')).open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    return payload


def execute_worker(output, inventory_path, expected_sha, remaining):
    # This is deliberately unreachable from imports or spy tests.
    import numpy as np
    import pandas as pd
    from knowledge_tracing.paper2_reference import load_reference
    if Path(sys.prefix).resolve() != ROOT / '.venv':
        raise ValueError('project isolated venv required')
    start = time.perf_counter()
    deadline = start + remaining
    def check():
        if time.perf_counter() > deadline:
            raise TimeoutError('newrevision300s reconstruction deadline')
    inventory = verify_inventory(inventory_path, expected_sha)
    original_manifest = json.loads((HISTORICAL / 'manifest.json').read_text())
    for rel, value in original_manifest['outputs_sha256'].items():
        if sha(HISTORICAL / rel) != value:
            raise ValueError('historical artifact drift')
    provenance = json.loads((HISTORICAL / 'source_provenance.json').read_text())
    source = (ROOT / 'scripts/research/run_cpu_diagnostics.py').read_text(encoding='utf-8')
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'closed_loop_pilot')
    excerpt_sha = hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest()
    if excerpt_sha != inventory['candidate_function_excerpt_sha256']:
        raise ValueError('candidate function identity drift')
    scope = {'np': np, 'pd': pd, 'json': json}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'PINNED_CURRENT_SOURCE_CLOSED_LOOP', 'exec'), scope)
    function = scope['closed_loop_pilot']
    expected = {}
    with gzip.open(HISTORICAL / 'traces.jsonl.gz', 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            key = (row['seed'], row['profile'], row['variant'], row['step'])
            if key in expected:
                raise ValueError('duplicate historical key')
            expected[key] = row
    if len(expected) != 3240:
        raise ValueError('historical population mismatch')
    expected_outcomes = json.loads((HISTORICAL / 'closed_loop_outcomes.json').read_text())
    if len(expected_outcomes) != 27:
        raise ValueError('historical aggregate population mismatch')
    summaries = []
    for observed in (False, True):
        check()
        label = 'observed' if observed else 'control'
        phase_start = time.perf_counter()
        reference, empty = load_reference(), load_reference(estimator_edges=[])
        if not exact(reference['provenance'], provenance) or not exact(empty['provenance'], provenance):
            raise ValueError('native definitions/input provenance drift')
        if list(reference['environment']['PERSONAS']) != ['PG', 'PY', 'PYH']:
            raise ValueError('profile identity drift')
        registry = ConstructorRegistry()
        policy_classes = [reference['estimator']['GAMKTPolicy'], empty['estimator']['GAMKTPolicy']]
        env_class = reference['environment']['LatentStudentEnvironment']
        methods = {name: [getattr(cls, name) for cls in policy_classes] for name in
                   ('select', 'ready_set', 'is_mastered', 'mastery_score', 'predict', 'update')}
        methods['interact'] = [env_class.interact]
        ref = {**reference, 'environment': dict(reference['environment']), 'estimator': dict(reference['estimator'])}
        emp = {**empty, 'estimator': dict(empty['estimator'])}
        ref['environment']['LatentStudentEnvironment'] = registry.environment_factory(env_class)
        ref['estimator']['GAMKTPolicy'] = registry.policy_factory(policy_classes[0])
        emp['estimator']['GAMKTPolicy'] = registry.policy_factory(policy_classes[1], empty=True)
        outcomes, uniform_hashes = [], []
        with gzip.open(output / (label + '_legacy.jsonl.gz'), 'wt', encoding='utf-8') as stream, \
                gzip.open(output / (label + '_metadata.jsonl.gz'), 'wt', encoding='utf-8') as metadata:
            sink = TraceSink(stream, expected, check)
            observer = ProfileObserver(registry, methods, reference['estimator']['nodes'], metadata,
                                       deadline=deadline) if observed else None
            sink.observer = observer
            # Uniform bytes are recovered from the function's existing return frame only.
            # Control captures them with the SAME outer-function profile hook as observed;
            # the control hook never inspects or instruments native method frames.
            capture = make_profile_dispatch(function, uniform_hashes, observer)
            if sys.getprofile() is not None:
                raise RuntimeError('existing profiler; STOP')
            sys.setprofile(capture)
            try:
                for seed in (20000, 20001, 20002):
                    for profile in ('PG', 'PY', 'PYH'):
                        check()
                        registry.begin(seed, profile)
                        outcomes.extend(function(ref, emp, seed=seed, profile=profile, steps=120, stream=sink))
                        check()
            finally:
                sys.setprofile(None)
            if sink.keys != set(expected) or not exact(outcomes, expected_outcomes):
                raise ValueError('aggregate/coverage exact parity failed')
            if observer is not None:
                observer.finish(expected_rows=3240, expected_steps=120)
            state = registry.summaries()
            if len(state) != 27 or len(uniform_hashes) != 9:
                raise ValueError('native object/uniform coverage')
            if any(sum(s.attempts for s in obj.states.values()) != 120 for obj in registry.policies.values()):
                raise ValueError('native completed update counts')
            summaries.append({'pass': label, 'legacy_rows': len(sink.keys), 'outcome_rows': len(outcomes),
                              'native_state_fingerprints': state, 'uniform_fingerprints': uniform_hashes,
                              'observed_rows': len(observer.rows) if observer else 0,
                              'observed_native_call_ledger': dict(observer.calls) if observer else None})
        write_phase_receipt(output, label, summaries[-1], time.perf_counter() - phase_start, expected_sha)
        check()
    if not exact(summaries[0]['native_state_fingerprints'], summaries[1]['native_state_fingerprints']):
        raise ValueError('control/observed final state mismatch')
    if not exact(summaries[0]['uniform_fingerprints'], summaries[1]['uniform_fingerprints']):
        raise ValueError('control/observed uniforms mismatch')
    verify_inventory(inventory_path, expected_sha)
    for rel, value in original_manifest['outputs_sha256'].items():
        if sha(HISTORICAL / rel) != value:
            raise ValueError('historical post-run drift')
    check()
    result = {'status': 'PASS_CURRENT_SOURCE_RECONSTRUCTION_EXACT_STORED_LEGACY_PARITY',
              'role': ROLE, 'original_a585_whole_source_recovered': False,
              'source_inventory_sha256': expected_sha, 'passes': summaries,
              'native_predict_update_interact_calls_each_two_passes': 6480,
              'control_call_count_basis': 'frozen single-call loop plus exact legacy rows and native attempt counters',
              'observed_call_count_basis': 'native profile call ledger', 'optimizer_steps': 0,
              'new_independent_N': 0, 'historical_metadata_backfilled': False,
              'full_mastery_score_vector_available': False,
              'final_local_generator_state_available': False,
              'elapsed_seconds': time.perf_counter() - start}
    with (output / 'parity.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=ROLE)
    parser.add_argument('--execute-current-source-reconstruction', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-inventory', type=Path, required=True)
    parser.add_argument('--source-inventory-sha256', required=True)
    parser.add_argument('--spy-receipt', type=Path)
    parser.add_argument('--worker-remaining-seconds', type=float)
    args = parser.parse_args()
    if not args.execute_current_source_reconstruction:
        raise ValueError('model phase not authorized by mere import/source preparation')
    if args.worker_remaining_seconds is not None:
        remaining = args.worker_remaining_seconds
        if not math.isfinite(remaining) or not 0 < remaining <= CAP or not args.output.is_dir():
            raise ValueError('worker budget/output contract')
        execute_worker(args.output, args.source_inventory, args.source_inventory_sha256, remaining)
        return
    start = time.perf_counter()
    verify_inventory(args.source_inventory, args.source_inventory_sha256)
    if args.spy_receipt is None or args.spy_receipt.resolve().parent != PREP:
        raise ValueError('exact spy receipt required')
    spy = json.loads(args.spy_receipt.read_text(encoding='utf-8'))
    if (spy['status'] != 'PASS_FAST_SPY_BENCH_ONLY_NO_NATIVE_MODEL'
            or type(spy['controller_seconds']) not in (int, float)
            or not math.isfinite(spy['controller_seconds'])
            or not 0 <= spy['controller_seconds'] < CAP):
        raise ValueError('spy budget/status')
    for rel, value in spy['source_sha256'].items():
        if sha(ROOT / rel) != value:
            raise ValueError('spy source drift')
    remaining = min(CAP - spy['controller_seconds'], OVERALL_CAP - PRIOR_FAILED_SECONDS
                    - PRIOR_DIAGNOSTIC_SECONDS - spy['controller_seconds']) - (time.perf_counter() - start)
    output = fresh_output(args.output)
    output.mkdir(exist_ok=False)
    command = [sys.executable, '-B', str(Path(__file__).resolve()),
               '--execute-current-source-reconstruction', '--output', str(output),
               '--source-inventory', str(args.source_inventory.resolve()),
               '--source-inventory-sha256', args.source_inventory_sha256,
               '--worker-remaining-seconds', str(remaining)]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    env['PYTHONPATH'] = str(ROOT / 'src')
    receipt = {'role': ROLE, 'status': 'FAILED_RETAIN_NO_RETRY', 'command': command,
               'spy_controller_seconds': spy['controller_seconds'], 'cap_seconds': CAP,
               'prior_failed_seconds': PRIOR_FAILED_SECONDS, 'prior_diagnostic_seconds': PRIOR_DIAGNOSTIC_SECONDS,
               'overall_cap_seconds': OVERALL_CAP, 'revision': 'fast_dispatch_v2'}
    child = None
    try:
        with (output / 'stdout.log').open('xb') as stdout, (output / 'stderr.log').open('xb') as stderr:
            child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
            child.wait(timeout=max(0.001, remaining))
        elapsed = time.perf_counter() - start + spy['controller_seconds']
        if (child.returncode or not math.isfinite(elapsed) or elapsed > CAP
                or PRIOR_FAILED_SECONDS + PRIOR_DIAGNOSTIC_SECONDS + elapsed > OVERALL_CAP):
            raise RuntimeError('child failed or newrevision300s/overall430s exceeded')
        result = json.loads((output / 'parity.json').read_text())
        if result['status'] != 'PASS_CURRENT_SOURCE_RECONSTRUCTION_EXACT_STORED_LEGACY_PARITY':
            raise ValueError('missing exact parity')
        verify_inventory(args.source_inventory, args.source_inventory_sha256)
        receipt['status'] = result['status']
    except BaseException as exc:
        receipt['failure'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        receipt['controller_seconds_including_spy'] = time.perf_counter() - start + spy['controller_seconds']
        receipt['overall_seconds_including_prior_failure_and_diagnostic'] = (PRIOR_FAILED_SECONDS
            + PRIOR_DIAGNOSTIC_SECONDS + receipt['controller_seconds_including_spy'])
        if (not math.isfinite(receipt['controller_seconds_including_spy'])
                or receipt['controller_seconds_including_spy'] > CAP
                or receipt['overall_seconds_including_prior_failure_and_diagnostic'] > OVERALL_CAP):
            receipt['status'] = 'REJECTED_CUMULATIVE_RESOURCE_BOUND'
        receipt['native_model_descendants'] = 'no subprocess/native worker calls in pinned candidate function; one owned Python child'
        receipt['outputs_sha256'] = {p.name: sha(p) for p in output.iterdir() if p.is_file()}
        with (output / 'run.json').open('x', encoding='utf-8') as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
            stream.write('\n')


if __name__ == '__main__':
    main()
