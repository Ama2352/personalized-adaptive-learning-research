"""ROOT-only full CPU09 mới, whole300 gồm cleanup và kiểm outputs streaming."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP / 'worker_rq1_cpu09_targeted_full02.py'
CONTRACT = PREP / 'rq1_cpu09_targeted_full_contract02.json'
START, WALL = time.perf_counter(), time.time()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter() - START, time.time() - WALL)


def sha(path, cap=4 * 1024**2):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical workspace path')
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        current /= part
        need(not current.is_symlink() and not getattr(current, 'is_junction', lambda: False)(), 'no aliases')
    need(path.is_file() and path.stat().st_size <= cap, 'bounded regular file')
    digest, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        while block := stream.read(65536):
            need(elapsed() < 300, 'same whole300 while hashing')
            size += len(block)
            need(size <= cap, 'stream SHA byte cap')
            digest.update(block)
    need(size == path.stat().st_size, 'stable SHA size')
    return digest.hexdigest()


def read(path):
    need(path.stat().st_size <= 1024**2, 'metadata JSON1MiB only')
    sha(path)
    return json.loads(path.read_bytes())


def write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    need(len(raw) <= 1024**2, 'controller metadata1MiB')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def validate_full_outputs(inner, contract, files):
    """Stream haiJSONL, giữ identity hash/count/zero-cells; không model import."""
    parity = read(inner / 'parity.json')
    genuine = parity['genuine_parity']
    columns = contract['readout_columns']
    need(len(columns) == len(set(columns)) == 19 and parity['readout_columns'] == columns,
         'exact unique lossless19columns')
    need(genuine['status'] == 'ALL_STREAMS_EXACT_P_QUERY_SOURCE_CLOCK_PARITY_BEFORE_TRUTH'
         and genuine['streams'] == 120 and genuine['events'] == 14400
         and genuine['calls'] == contract['direct_call_caps'] and parity['all_classes_restored'] is True
         and parity['source_checked_before_truth'] is True, 'genuine full pretruth parity')
    frozen = parity['pretruth_readouts']
    need(frozen == dict(path='pretruth_readouts.jsonl', rows=14400,
         bytes=files['pretruth_readouts.jsonl']['bytes'], sha256=files['pretruth_readouts.jsonl']['sha256']), 'frozen actual pretruth artifact')
    keys = [(seed, profile, g, m) for seed in contract['grid']['seeds'] for profile in contract['grid']['profiles']
            for g in (False, True) for m in (False, True)]
    offsets, clock = [], 0
    for step in range(120):
        clock += 72 if step > 0 and step % 28 == 0 else 6
        offsets.append(clock)
    need(genuine['clock_hours'] == offsets and genuine['clock_origin'] == 'SOURCE_DERIVED_NOT_A_LOGGED_TIMESTAMP_FIELD', 'literal source clock, not loggedtimestamp claim')
    bank = {}
    bank_path = ROOT / contract['question_bank_path']
    sha(bank_path)
    with bank_path.open(encoding='utf-8-sig', newline='') as stream:
        for item in csv.DictReader(stream):
            need(item['question_id'] not in bank, 'unique bank question')
            bank[item['question_id']] = (item['concept_id'], float(item['elo_difficulty']))
    need(len(bank) == 84, 'boundbank84')

    def decode(raw):
        def unique(items):
            value = {}
            for name, item in items:
                need(name not in value, 'duplicate JSON key')
                value[name] = item
            return value
        def invalid(value):
            raise ValueError('nonfinite JSON ' + value)
        return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)

    def rows(path, cap):
        count, size = 0, 0
        with path.open('rb') as stream:
            while True:
                need(elapsed() < 300, 'whole300 streaming validation')
                raw = stream.readline(8193)
                if not raw:
                    break
                count += 1
                size += len(raw)
                need(count <= 14400 and len(raw) <= 8192 and raw.endswith(b'\n') and size <= cap, 'complete bounded JSONL')
                yield decode(raw)
        need(count == 14400, 'exact14400records atEOF')

    count_names = ('rows', 'truth_mastered', 'native_M_true', 'theta_gate_true', 'stored_pi_gate_pass',
        'theta_gate_true_pi_blocked', 'oracle_true_pi_blocked', 'M_TP', 'M_FP', 'M_FN', 'M_TN',
        'theta_TP', 'theta_FP', 'theta_FN', 'theta_TN')
    counts, seen = {}, set()
    digest = hashlib.sha256(b'[')
    n = 0
    paired = zip(rows(inner / 'pretruth_readouts.jsonl', 8 * 1024**2),
                 rows(inner / 'truth_sidecar.jsonl', 4 * 1024**2), strict=True)
    for values, truth in paired:
        need(type(values) is list and len(values) == 19, 'lossless array row shape')
        row = dict(zip(columns, values, strict=True))
        need(type(row['seed']) is int and type(row['step']) is int and type(row['profile']) is str
             and type(row['graph_on']) is bool and type(row['mechanism_on']) is bool, 'exact identity types')
        key = row['seed'], row['profile'], row['graph_on'], row['mechanism_on'], row['step']
        need(key not in seen and key == (*keys[n // 120], n % 120), 'exact chronological fullgrid order/unique keys')
        seen.add(key)
        need(set(truth) == {'seed', 'profile', 'graph_on', 'mechanism_on', 'step', 'theta_before', 'sourceTrueM'}
             and all(type(truth[name]) is type(row[name]) and truth[name] == row[name]
                     for name in ('seed', 'profile', 'graph_on', 'mechanism_on', 'step')), 'strict sidecar5key join')
        need(type(row['question']) is str and row['question'] in bank
             and bank[row['question']] == (row['concept'], row['difficulty']), 'query/bank mapping')
        for name in ('difficulty', 'prediction', 'theta_est', 'pi_task_stored', 'pi_time_stored', 'pi_task_decayed', 'pi_time_decayed'):
            need(type(row[name]) is float and math.isfinite(row[name]), 'genuine binary64 readout types')
        need(0 <= row['prediction'] <= 1 and all(0 <= row[name] <= 1 for name in
             ('pi_task_stored', 'pi_time_stored', 'pi_task_decayed', 'pi_time_decayed')), 'probability/uncertainty range')
        need(all(type(row[name]) is bool for name in ('native_M', 'theta_gate', 'stored_pi_gate'))
             and row['theta_gate'] == (row['theta_est'] >= 1250.)
             and row['stored_pi_gate'] == (row['pi_task_stored'] <= .55)
             and row['native_M'] == (row['theta_gate'] and row['stored_pi_gate']), 'literal nativeM/gates')
        need(type(truth['theta_before']) in (int, float) and math.isfinite(truth['theta_before'])
             and type(truth['sourceTrueM']) is bool and truth['sourceTrueM'] == (truth['theta_before'] >= 1250.), 'source truth criterion')
        need(type(row['source_clock_hours']) is int and row['source_clock_hours'] == offsets[row['step']]
             and row['timestamp'] == (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=offsets[row['step']])).isoformat(),
             'source-derived timestamp, no time substitution')
        if n:
            digest.update(b',')
        digest.update(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
        actual, mastered, theta_gate, pi_gate = truth['sourceTrueM'], row['native_M'], row['theta_gate'], row['stored_pi_gate']
        memberships = (('world', *key[:4]), ('persona_arm', None, key[1], key[2], key[3]), ('arm', None, None, key[2], key[3]))
        for group in memberships:
            counter = counts.setdefault(group, Counter(dict.fromkeys(count_names, 0)))
            counter.update(rows=1, truth_mastered=int(actual), native_M_true=int(mastered), theta_gate_true=int(theta_gate),
                stored_pi_gate_pass=int(pi_gate), theta_gate_true_pi_blocked=int(theta_gate and not pi_gate),
                oracle_true_pi_blocked=int(actual and theta_gate and not pi_gate))
            for label, flag in (('M', mastered), ('theta', theta_gate)):
                cell = 'TP' if flag and actual else 'FP' if flag else 'FN' if actual else 'TN'
                counter[label + '_' + cell] += 1
        n += 1
    digest.update(b']')
    need(n == len(seen) == 14400 and digest.hexdigest() == genuine['pretruth_readout_sha256'], 'genuine canonical row-list identity reconstructed streaming')
    groups = read(inner / 'groups.json')
    need(groups['truth_sidecar'] == dict(path='truth_sidecar.jsonl', rows=14400,
         bytes=files['truth_sidecar.jsonl']['bytes'], sha256=files['truth_sidecar.jsonl']['sha256']), 'actual sidecar SHA/size')
    actual_groups = {}
    for row in groups['groups']:
        key = tuple(row[name] for name in ('level', 'seed', 'profile', 'graph_on', 'mechanism_on'))
        need(key not in actual_groups and set(row) == {'level', 'seed', 'profile', 'graph_on', 'mechanism_on', *count_names}, 'all unique group/count fields including zeroes')
        need(all(type(row[name]) is int and row[name] >= 0 for name in count_names), 'exact nonnegative integer counts, not bool')
        actual_groups[key] = {name: row[name] for name in count_names}
    need(len(actual_groups) == len(counts) == 136 and actual_groups == {k: dict(v) for k, v in counts.items()}, 'all136groups independently recounted')
    policies = read(inner / 'policy_observers.json')
    need(len(policies['policies']) == 120 and policies['method_started'] == policies['method_returned']
         == contract['native_method_total'], 'complete per-policy observation ledger')
    for key, row in zip(keys, policies['policies'], strict=True):
        receipt = row['observer']
        need(row['key'] == list(key) and row['completed_updates'] == 120
             and receipt['started'] == receipt['returned'] == contract['method_caps_per_policy']
             and receipt['raised'] == {} and receipt['cleanup_errors'] == [] and receipt['pending_attributes'] == []
             and receipt['class_attributes_restored'] is True and receipt['live'] is False
             and receipt['instance_attributes_added'] is False, 'all120 original methods restored and bodycaps exact')
    return dict(streamed_pretruth_rows=n, streamed_truth_rows=n, full_grid_unique_keys=True,
        exact_genuine_identity_sha256=digest.hexdigest(), complete_groups=136, complete_policy_observers=120,
        no_additional_model_calls=True, queried_concept_units_only=True)


class FamilyMonitor:
    """Monitor owned family, sample3300/journal2MiB, cùng whole300 clock."""
    def __init__(self, helper, owned, output, worker_sha):
        import psutil
        self.psutil, self.helper, self.owned, self.output = psutil, helper, owned, output
        self.worker_sha = worker_sha
        self.parent = psutil.Process(os.getpid())
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.errors = []
        self.samples = self.child_samples = self.peak = 0
        self.minimum_free = None
        self.terminated_job = False

    def sample(self):
        total, rows = 0, []
        family = [self.parent, *self.parent.children(recursive=True)]
        need(len(family) <= 17, 'bounded owned family')
        for process in family:
            try:
                memory = process.memory_info()
                peak = max(memory.rss, getattr(memory, 'peak_wset', 0))
                total += peak
                rows.append(dict(pid=process.pid, create_time=process.create_time(), rss=memory.rss, peak=peak))
            except self.psutil.NoSuchProcess:
                need(process.pid != self.parent.pid, 'parent vanished')
        free = int(self.psutil.virtual_memory().available)
        self.samples += 1
        self.child_samples += int(any(row['pid'] != self.parent.pid for row in rows))
        self.peak = max(self.peak, total)
        self.minimum_free = free if self.minimum_free is None else min(self.minimum_free, free)
        self.journal.write(json.dumps(dict(seconds=elapsed(), family=rows, family_peak_sum_bytes=total, free_bytes=free)) + '\n')
        self.journal.flush()
        need(self.samples <= 3300 and self.journal.tell() <= 2 * 1024**2, 'journal-only2MiB / sample3300')
        need(total <= 512 * 1024**2 and free >= 1536 * 1024**2, 'actual family RSS/freeRAM caps')
        need(elapsed() < 300, 'same whole300 deadline')

    def terminate_owned(self):
        path = self.owned / 'launch.json'
        until = min(time.perf_counter() + 1, START + 300)
        launch = None
        while launch is None and time.perf_counter() < until:
            if path.exists():
                try:
                    launch = read(path)
                except json.JSONDecodeError:
                    pass
            if launch is None:
                time.sleep(.005)
        need(launch is not None and launch['parent']['pid'] == os.getpid()
             and launch['worker_relative'] == WORKER.relative_to(ROOT).as_posix()
             and launch['worker_sha256'] == self.worker_sha
             and launch['job_name'] == 'KLTN_OWNED_' + launch['nonce'], 'exact current owned Job binding')
        api = self.helper.Kernel()
        handle = api.check(api.k.OpenJobObjectW(0x0004 | 0x0008, False, launch['job_name']))
        try:
            api.check(api.k.TerminateJobObject(handle, 1))
            self.terminated_job = True
        finally:
            api.close(handle)

    def loop(self):
        try:
            with (self.output / 'memory.jsonl').open('x', encoding='utf-8') as self.journal:
                while not self.stop_event.wait(.1):
                    self.sample()
                self.sample()
        except BaseException as error:
            self.errors.append(dict(type=type(error).__name__, message=str(error)))
            try:
                self.terminate_owned()
            except BaseException as cleanup:
                self.errors.append(dict(type=type(cleanup).__name__, message=str(cleanup)))

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=.5)
        need(not self.thread.is_alive(), 'monitor stopped')

    def result(self):
        return dict(samples=self.samples, child_family_samples=self.child_samples,
            observed_family_peak_rss_bytes=self.peak, observed_minimum_available_ram_bytes=self.minimum_free,
            monitor_stopped=not self.thread.is_alive(), terminated_owned_job=self.terminated_job, errors=self.errors,
            scope='SAMPLED_PARENT_AND_LIVE_DESCENDANTS_NOT_CONTINUOUS_HARD_RSS_PROOF')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--controller-sha256', required=True)
    parser.add_argument('--approval-reference', required=True)
    args = parser.parse_args()
    need(Path.cwd().resolve() == ROOT and Path(sys.prefix).resolve() == ROOT / '.venv', 'actual repository .venv')
    need(sha(WORKER) == args.source_sha256 and sha(CONTRACT) == args.contract_sha256
         and sha(Path(__file__).resolve()) == args.controller_sha256 and args.approval_reference.strip(), 'Root reviewed exact source pins')
    contract = read(CONTRACT)
    need(contract['worker_sha256'] == args.source_sha256
         and contract['controller_sha256'] == args.controller_sha256, 'contract source agreement')
    before = {}
    for name, row in contract['bindings'].items():
        need(sha(ROOT / name) == row['sha256'] and (ROOT / name).stat().st_size == row['bytes'], 'prebound source/input bytes')
        before[name] = row['sha256']
    output = PREP / contract['outer_name']
    owned = PREP / contract['owned_name']
    output_relative = 'experiments/gam_kt/results/rq1-cpu09-native-mastery-20261109-02'
    need(contract['output_relative'] == output_relative, 'fixed scientific output directory')
    inner = ROOT / output_relative
    need(output.parent == owned.parent == PREP and inner.parent.is_dir(), 'correct transient/scientific roles')
    for path in (output, owned, inner):
        need(path.is_relative_to(ROOT) and path.resolve() == path and not path.exists(), 'exclusive physical new namespaces')
        cursor = ROOT
        for part in path.relative_to(ROOT).parts:
            cursor /= part
            need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no output aliases')
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    import windows_owned_worker as helper
    need(sha(Path(helper.__file__)) == '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1', 'genuine unchanged owner helper')
    helper.entry()
    monitor = FamilyMonitor(helper, owned, output, args.source_sha256)
    import psutil
    need(psutil.virtual_memory().available >= 1536 * 1024**2, 'actual parent freeRAM before any worker')
    output.mkdir()
    write(output / 'admission.json', dict(source_input_before=before, approval_reference=args.approval_reference,
        phase='full_native', whole_seconds=300, owned_seconds=285, worker_seconds=270, cleanup_seconds=5,
        old_native05_lane_reopened=False, new_allocation=True))
    errors, receipt, files, after, validation = [], None, {}, {}, None
    original_environment = {name: os.environ.get(name) for name in ('CUDA_VISIBLE_DEVICES', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}
    try:
        os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        monitor.thread.start()
        need(elapsed() < 10, 'prelaunch work within whole300 reserve')
        receipt = helper.run_owned(WORKER, ['--source-sha256', args.source_sha256,
            '--contract-sha256', args.contract_sha256], owned,
            expected_worker_sha256=args.source_sha256, approval_reference=args.approval_reference,
            max_seconds=min(285., 300. - elapsed() - 10.), cleanup_reserve_seconds=5, max_output_bytes=65536)
        write((owned if owned.is_dir() else output) / 'receipt.json', receipt)
        need(receipt['accepted'] is True and receipt['returncode'] == receipt['worker_returncode_before_cleanup'] == 0
             and receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup'] == 0
             and receipt['popen_handle_closed'] is True and receipt['errors'] == receipt['cleanup_errors'] == [], 'actual clean owned terminal')
        expected = {'pure_checks.json', 'native_metadata.json', 'reservation.json', 'pretruth_readouts.jsonl',
                    'parity.json', 'policy_observers.json', 'truth_sidecar.jsonl', 'groups.json', 'result.json'}
        need({path.name for path in inner.iterdir()} == expected, 'all terminal output files, no failure/partial acceptance')
        caps = {'pretruth_readouts.jsonl': 8 * 1024**2, 'truth_sidecar.jsonl': 4 * 1024**2}
        files = {path.name: dict(sha256=sha(path, caps.get(path.name, 1024**2)), bytes=path.stat().st_size) for path in inner.iterdir()}
        need(sum(row['bytes'] for row in files.values()) <= 16 * 1024**2, 'bounded native artifacts')
        result = read(inner / 'result.json')
        need(read(inner / 'pure_checks.json')['manufactured_checks'] == 5, 'actual five manufactured checks')
        need(result['errors'] == result['restoration_errors'] == result['denied'] == []
             and result['output_relative'] == output_relative
             and result['deny_contexts'] == [] and result['audit_denial_count'] == 0
             and result['source_before'] == result['source_after'] == before
             and result['profiler_installed'] is False and result['old_five_attempt_lane_reopened'] is False,
             'all source/restoration/pilot scope checks')
        need(result['status'] == 'COMPLETE_ALL120_CPU09_NATIVE_MASTERY_PENDING_ROOT'
             and result['factory_attempted'] == result['factory_returned'] == result['policies_complete'] == 120
             and result['method_started'] == result['method_returned'] == contract['native_method_total']
             and result['pending_policy_observer'] is None and result['pretruth_frozen'] is True
             and result['truth_join_started'] is True and result['truth_join_completed'] is True, 'all full native calls / truth sequencing')
        metadata = read(inner / 'native_metadata.json')
        need(metadata['phase_closed'] is True and metadata['outside_phase_popen_attempts'] == metadata['outside_phase_socket_attempts']
             == metadata['blocked_bootstrap_attempts'] == 0, 'real metadata closed and no late attempts')
        validation = validate_full_outputs(inner, contract, files)
        after = {name: sha(ROOT / name) for name in before}
        need(after == before and sha(CONTRACT) == args.contract_sha256
             and sha(Path(__file__).resolve()) == args.controller_sha256, 'all source/input final hashes')
        need(all(sha(owned / name) == pin for name, pin in receipt['output_sha256'].items()), 'original stdout/stderr identity')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error)))
    finally:
        if monitor.thread.ident is not None:
            try:
                monitor.stop()
            except BaseException as error:
                errors.append(dict(type=type(error).__name__, message=str(error)))
        for name, value in original_environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    resources = monitor.result()
    restored = all(os.environ.get(name) == value for name, value in original_environment.items())
    total_existing = sum(path.stat().st_size for directory in (inner, owned, output) if directory.exists()
                         for path in directory.iterdir() if path.is_file())
    if total_existing > 15 * 1024**2:
        errors.append(dict(type='OutputBudget', message='global16MiB requires1MiB final metadata reserve'))
    accepted = not errors and not resources['errors'] and resources['monitor_stopped'] and restored and elapsed() < 300
    final = dict(status='ACCEPTED_FULL_CPU09_TARGETED_NATIVE_MASTERY_REPLAY' if accepted else 'REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY',
        phase='full_native', errors=errors, elapsed_before_receipt_seconds=elapsed(), whole_cap_seconds=300,
        receipt=receipt, source_input_before=before, source_input_after=after, outputs=files,
        worker_output_relative=output_relative,
        resources=resources, environment_restored=restored, validation=validation,
        old_five_attempt_lane_reopened=False, automatic_retry=False)
    write(output / 'final.json', final)
    if elapsed() >= 300:
        accepted = False
        write(output / 'postwrite-rejection.json', dict(status='REJECTED_AFTER_FINALWRITE', elapsed_seconds=elapsed()))
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY', errors=errors, elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
