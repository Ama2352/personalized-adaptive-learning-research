"""ROOT-only CPU09 mastery replay, owned177/worker173/whole180 monitor."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import threading
import time
import traceback

START, WALL = time.perf_counter(), time.time()
ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP / 'rq1_cpu09_mastery_native01_packet.json'
OUT = PREP / 'rq1-cpu09-mastery-native01-outer'
OWNED = PREP / 'rq1-cpu09-mastery-native01-owned'
INNER = PREP / 'rq1-cpu09-native-mastery-attempt01'


def need(value, message):
    if not value:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter() - START, time.time() - WALL)


def physical(path):
    path = path.absolute()
    need(path.is_relative_to(ROOT) and ROOT.resolve() == ROOT, 'workspace physical path')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'path alias')
    need(path.resolve() == path, 'resolved physical path')
    return path


def sha(path, cap=4 * 1024**2):
    path = physical(path)
    need(path.is_file() and path.stat().st_size <= cap, 'bounded regular input')
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while block := stream.read(65536):
            size += len(block)
            need(size <= cap, 'stream byte cap')
            digest.update(block)
    need(size == path.stat().st_size, 'stable bytes')
    return digest.hexdigest()


def read(path, cap=1024**2):
    need(physical(path).stat().st_size <= cap, 'JSON size cap')
    return json.loads(path.read_bytes())


def write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    need(len(raw) <= 4 * 1024**2, 'controller receipt cap')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


class FamilyMonitor:
    """Đo family thật, terminate đúng named Job của helper khi vi phạm."""

    def __init__(self, helper, limits, worker_sha):
        import psutil
        self.psutil, self.helper, self.limits, self.worker_sha = psutil, helper, limits, worker_sha
        self.parent = psutil.Process(os.getpid())
        self.stop_event = threading.Event()
        self.errors = []
        self.samples = self.child_samples = 0
        self.peak_family_rss = 0
        self.minimum_available = None
        self.terminated_owned_job = False
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def sample(self):
        family = [self.parent, *self.parent.children(recursive=True)]
        need(len(family) <= 17, 'bounded monitored family')
        observed = []
        total = 0
        for process in family:
            try:
                info = process.memory_info()
                value = max(int(info.rss), int(getattr(info, 'peak_wset', 0)))
                observed.append(dict(pid=process.pid, create_time=process.create_time(), rss=int(info.rss), peak=value))
                total += value
            except self.psutil.NoSuchProcess:
                need(process.pid != self.parent.pid, 'parent vanished')
        available = int(self.psutil.virtual_memory().available)
        self.samples += 1
        self.child_samples += int(any(p['pid'] != self.parent.pid for p in observed))
        self.peak_family_rss = max(self.peak_family_rss, total)
        self.minimum_available = available if self.minimum_available is None else min(self.minimum_available, available)
        need(self.samples <= 4000, 'monitor journal sample cap')
        record = dict(elapsed_seconds=elapsed(), family=observed, aggregate_peak_rss=total,
                      system_available_ram_bytes=available)
        self.journal.write(json.dumps(record, allow_nan=False) + '\n')
        self.journal.flush()
        need(self.journal.tell() <= 4 * 1024**2, 'monitor journal bytes')
        need(total <= self.limits['max_rss_bytes'], 'monitored family RSS/peak cap')
        need(available >= self.limits['min_available_ram_bytes'], 'original free RAM floor')

    def terminate_job(self):
        launch_path = OWNED / 'launch.json'
        deadline = min(time.perf_counter() + 1., START + 177.)
        launch = None
        while launch is None and time.perf_counter() < deadline:
            if launch_path.exists():
                try:
                    launch = read(launch_path, 32768)
                except json.JSONDecodeError:
                    pass
            if launch is None:
                time.sleep(.005)
        need(launch is not None, 'owned launch identity unavailable for monitor termination')
        worker = PREP / 'worker_rq1_cpu09_native_mastery01.py'
        need(launch['parent']['pid'] == os.getpid()
             and launch['worker_relative'] == worker.relative_to(ROOT).as_posix()
             and launch['worker_sha256'] == self.worker_sha
             and launch['job_name'] == 'KLTN_OWNED_' + launch['nonce'], 'monitor owned Job binding')
        api = self.helper.Kernel()
        handle = api.check(api.k.OpenJobObjectW(0x0004 | 0x0008, False, launch['job_name']))
        try:
            api.check(api.k.TerminateJobObject(handle, 1))
            self.terminated_owned_job = True
        finally:
            api.close(handle)

    def loop(self):
        try:
            with (OUT / 'memory.jsonl').open('x', encoding='utf-8') as self.journal:
                while not self.stop_event.is_set():
                    self.sample()
                    need(elapsed() < 180, 'whole monitor deadline')
                    self.stop_event.wait(.02)
                self.sample()
        except BaseException as error:
            self.errors.append(dict(type=type(error).__name__, message=str(error)))
            try:
                self.terminate_job()
            except BaseException as cleanup:
                self.errors.append(dict(type=type(cleanup).__name__, message='monitor Job termination: ' + str(cleanup)))

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=.5)
        need(not self.thread.is_alive(), 'monitor stopped')

    def result(self):
        return dict(samples=self.samples, child_family_samples=self.child_samples,
                    observed_family_peak_rss_bytes=self.peak_family_rss,
                    observed_minimum_available_ram_bytes=self.minimum_available,
                    errors=self.errors, monitor_stopped=not self.thread.is_alive(),
                    terminated_owned_job=self.terminated_owned_job,
                    scope='Observed parent+live descendants, sum lifetime peak where exposed; cooperative sampling')


def validate_pure(packet, external_sha):
    pure_path = ROOT / packet['pure']['result_path']
    need(sha(pure_path) == external_sha, 'external actual pure12 result SHA')
    pure = read(pure_path)
    expected_counts = dict(tests=12, failures=0, errors=0, skipped=0, unexpected_successes=0, expected_failures=0)
    need(pure['status'] == 'ACCEPTED_12_CPU09_MASTERY_PURE_METHODS' and pure['counts'] == expected_counts
         and pure['errors'] == [] and pure['source_sha256'] == packet['pure']['source_sha256']
         and pure['controller_sha256'] == packet['pure']['controller_sha256']
         and pure['packet_sha256'] == packet['pure']['packet_sha256'] and pure['elapsed_seconds'] < 30,
         'actual pure12 provenance/counts/time')
    child, owned = pure['worker_result'], pure['owned_receipt']
    need(child['status'] == 'ACCEPTED_MASTERY12_PENDING_OUTER' and child['calls'] == packet['pure']['calls']
         and len(child['subtests']) == 9 and all(row['error_type'] is None for row in child['subtests'])
         and child['source_after'] == packet['pure']['source_sha256'] and child['cached_file_opens'] == 0
         and child['methods_restored'] is True and child['monitor_stopped'] is True
         and child['errors'] == child['forbidden'] == child['heavy_modules'] == child['resource_errors'] == [],
         'pure bodies/metadata/data exclusion')
    need(owned['accepted'] is True and owned['cleanup_accepted'] is True and owned['returncode'] == 0
         and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True
         and owned['errors'] == [], 'actual pure owned Job0')
    need(not (pure_path.parent / 'postwrite-rejection.json').exists(), 'no late pure rejection')
    for name, pin in owned['output_sha256'].items():
        need(name in ('stdout.log', 'stderr.log')
             and sha(PREP / 'rq1-cpu09-mastery-pure01-owned' / name) == pin, 'actual pure streams')


def validate_outputs(contract, receipt):
    from datetime import datetime, timedelta, timezone
    from collections import Counter
    need({path.name for path in INNER.iterdir()} == set(contract['expected_files']), 'all exact7 terminal outputs')
    artifacts = {path.name: dict(sha256=sha(path, contract['limits']['max_output_file_bytes']), bytes=path.stat().st_size)
                 for path in INNER.iterdir()}
    need(sum(row['bytes'] for row in artifacts.values()) <= contract['limits']['max_total_output_bytes'], 'bounded directory')
    need(read(INNER / 'output-manifest.json')['outputs'] == {name: row for name, row in artifacts.items()
          if name != 'output-manifest.json'}, 'all output byteSHA/size')
    result = read(INNER / 'result.json', 2*1024**2)
    expected_sources = {name: row['sha256'] for name, row in {**contract['source_pins'], **contract['input_pins']}.items()}
    need(result['status'] == 'COMPLETE_MATCHED_CPU09_MASTERY_REPLAY_PENDING_OUTER'
         and result['source_before'] == result['source_after'] == expected_sources
         and result['native_started'] == result['native_returned'] == contract['native_call_caps']
         and result['direct_calls'] == contract['direct_call_counts']
         and (result['streams'], result['queried_concept_events'], result['groups'], result['repeated_group_row_uses'])
         == (120, 14400, 136, 43200) and result['profiler_restored'] is True and result['scope_denials'] == []
         and result['new_independent_seed_families'] == result['world_teacher_calls']
         == result['new_responses'] == result['neural_calls'] == 0 and result['fitted_model'] is False,
         'complete actual native/evaluator scope')
    for package in ('numpy', 'pandas'):
        path = physical(Path(result['package_origins'][package]))
        need(path.is_relative_to(ROOT / '.venv/Lib/site-packages' / package), 'actual package origin')
    metadata = result['native_metadata']
    need(metadata == read(INNER / 'native_metadata.json') and metadata['phase_closed'] is True
         and 0 <= metadata['helper_calls'] <= 3 and 0 <= metadata['local_gethostname_calls'] <= 3
         and metadata['outside_phase_popen_attempts'] == metadata['outside_phase_socket_attempts']
         == metadata['blocked_bootstrap_attempts'] == 0, 'real bounded closed metadata phase')
    reservation = read(INNER / 'reservation.json')
    need(reservation['status'] == 'RESERVED_BEFORE_ANY_ESTIMATOR' and reservation['source_before'] == expected_sources
         and reservation['truth_to_estimator'] is False
         and reservation['owner']['worker']['pid'] == receipt['actual_worker']['pid'], 'native owned reservation')
    grid = contract['grid']
    stream_keys = [(s, p, g, m) for s in grid['seeds'] for p in grid['profiles']
                   for g in (False, True) for m in (False, True)]
    expected_keys = [key + (step,) for key in stream_keys for step in range(120)]
    fields = {'seed', 'profile', 'graph_on', 'mechanism_on', 'step', 'concept', 'question', 'difficulty',
              'timestamp', 'source_clock_hours', 'prediction', 'theta_est', 'pi_task_stored', 'pi_time_stored',
              'pi_task_decayed', 'pi_time_decayed', 'native_M', 'theta_gate', 'stored_pi_gate',
              'source_true_theta_before', 'source_true_M'}
    rows = []
    with (INNER / 'native_query_readouts.jsonl').open('rb') as stream:
        for expected in expected_keys:
            raw = stream.readline(2049)
            need(raw.endswith(b'\n') and len(raw) <= 2048, 'complete bounded readout line')
            row = json.loads(raw)
            need(set(row) == fields and (row['seed'], row['profile'], row['graph_on'], row['mechanism_on'], row['step'])
                 == expected, 'complete ordered readout keys')
            step = row['step']
            # Dạng đóng đối chiếu độc lập với vòng lặp clock trong replay.
            offset = 6*(step+1) + 66*(step//28)
            expected_time = (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=offset)).isoformat()
            need(row['source_clock_hours'] == offset and row['timestamp'] == expected_time, 'source clock timestamp')
            need(all(type(row[name]) is bool for name in ('source_true_M', 'native_M', 'theta_gate', 'stored_pi_gate'))
                 and row['source_true_M'] == (row['source_true_theta_before'] >= 1250.)
                 and row['theta_gate'] == (row['theta_est'] >= 1250.)
                 and row['stored_pi_gate'] == (row['pi_task_stored'] <= .55)
                 and row['native_M'] == (row['theta_gate'] and row['stored_pi_gate']), 'literal truth/native gates')
            need(all(type(row[name]) is float and math.isfinite(row[name]) for name in
                 ('prediction', 'theta_est', 'pi_task_stored', 'pi_time_stored', 'pi_task_decayed', 'pi_time_decayed')),
                 'finite native float readouts')
            need(all(0 <= row[name] <= 1 for name in
                 ('prediction', 'pi_task_stored', 'pi_time_stored', 'pi_task_decayed', 'pi_time_decayed')),
                 'bounded probability/uncertainty')
            rows.append(row)
        need(stream.read(1) == b'', 'no trailing/subset readouts')
    parity = read(INNER / 'parity.json')
    before_truth = [{name: value for name, value in row.items() if name not in ('source_true_theta_before', 'source_true_M')}
                    for row in rows]
    parity_sha = hashlib.sha256(json.dumps(before_truth, ensure_ascii=False, sort_keys=True,
                                          separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    need(parity['status'] == 'ALL_STREAMS_EXACT_P_QUERY_SOURCE_CLOCK_PARITY_BEFORE_TRUTH'
         and parity['streams'] == 120 and parity['events'] == 14400 and parity['calls'] == contract['direct_call_counts']
         and parity['pretruth_readout_sha256'] == parity_sha, 'pretruth readout identity/full admission')
    expected_groups = {}
    count_names = ('rows', 'truth_mastered', 'native_M_true', 'theta_gate_true', 'stored_pi_gate_pass',
                   'theta_gate_true_pi_blocked', 'oracle_true_pi_blocked', 'M_TP', 'M_FP', 'M_FN', 'M_TN',
                   'theta_TP', 'theta_FP', 'theta_FN', 'theta_TN')
    for row in rows:
        memberships = (('world', row['seed'], row['profile'], row['graph_on'], row['mechanism_on']),
                       ('persona_arm', None, row['profile'], row['graph_on'], row['mechanism_on']),
                       ('arm', None, None, row['graph_on'], row['mechanism_on']))
        for key in memberships:
            count = expected_groups.setdefault(key, Counter({name: 0 for name in count_names}))
            count.update(rows=1, truth_mastered=int(row['source_true_M']), native_M_true=int(row['native_M']),
                theta_gate_true=int(row['theta_gate']), stored_pi_gate_pass=int(row['stored_pi_gate']),
                theta_gate_true_pi_blocked=int(row['theta_gate'] and not row['stored_pi_gate']),
                oracle_true_pi_blocked=int(row['source_true_M'] and row['theta_gate'] and not row['stored_pi_gate']))
            for label, predicted in (('M', row['native_M']), ('theta', row['theta_gate'])):
                cell = ('TP' if row['source_true_M'] else 'FP') if predicted else ('FN' if row['source_true_M'] else 'TN')
                count[label+'_'+cell] += 1
    groups = read(INNER / 'confusion.json')['groups']
    actual = {}
    for group in groups:
        key = tuple(group[name] for name in ('level', 'seed', 'profile', 'graph_on', 'mechanism_on'))
        need(key not in actual and set(group) == {'level', 'seed', 'profile', 'graph_on', 'mechanism_on', *count_names},
             'unique exact group schema')
        actual[key] = {name: group[name] for name in count_names}
    need(len(actual) == 136 and actual == expected_groups, 'all120/12/4 groups independent readout-count verification')
    return artifacts, dict(streams=120, queried_concept_events=14400, groups=136, parity_sha256=parity_sha,
                           complete_ordered_keys_verified=True, group_counts_independently_verified=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--controller-sha256', required=True)
    parser.add_argument('--pure-sha256', required=True)
    parser.add_argument('--approval-reference', required=True)
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT / '.venv' and Path.cwd().resolve() == ROOT, 'Root .venv fixed context')
    need(sha(Path(__file__)) == args.controller_sha256 and sha(PACKET) == args.packet_sha256, 'external reviewed outer/packet')
    packet = read(PACKET)
    worker = PREP / 'worker_rq1_cpu09_native_mastery01.py'
    contract_path = PREP / 'rq1_cpu09_native_mastery_contract01.json'
    need(sha(worker) == packet['worker_sha256'] and sha(contract_path) == packet['contract_sha256'], 'worker/contract')
    contract = read(contract_path)
    need(packet['limits'] == contract['limits'], 'same inner/outer finite allocation')
    validate_pure(packet, args.pure_sha256)
    need(not any(path.exists() for path in (OUT, OWNED, INNER)), 'all attempt namespaces exclusive/absent')
    expected = {**packet['source_pins'], **contract['input_pins']}
    before = {}
    for name, row in expected.items():
        need(sha(ROOT / name) == row['sha256'] and (ROOT / name).stat().st_size == row['bytes'], 'all source/input prehash')
        before[name] = row['sha256']
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    import windows_owned_worker as helper
    need(sha(Path(helper.__file__)) == packet['helper_sha256'], 'genuine owned helper')
    helper.entry()
    import psutil
    preflight = psutil.virtual_memory()
    root_info = psutil.Process(os.getpid()).memory_info()
    root_peak = max(root_info.rss, getattr(root_info, 'peak_wset', 0))
    need(preflight.available >= contract['limits']['min_available_ram_bytes']
         and root_peak <= contract['limits']['max_rss_bytes'], 'actual parent preallocation RAM')
    OUT.mkdir()
    write(OUT / 'before.json', dict(source_inputs_sha256=before, controller_sha256=args.controller_sha256,
          packet_sha256=args.packet_sha256, pure_sha256=args.pure_sha256, approval_reference=args.approval_reference))
    write(OUT / 'memory-preflight.json', dict(available_ram_bytes=preflight.available,
          parent_rss_bytes=root_info.rss, parent_peak_rss_bytes=root_peak))
    errors, receipt, artifacts, validation, after = [], None, {}, None, {}
    monitor = FamilyMonitor(helper, contract['limits'], packet['worker_sha256'])
    try:
        # Thread giữ journal riêng, cùng pattern monitor đã dùng ở response audit.
        monitor.thread.start()
        need(elapsed() < 5, 'setup before owned177 deadline reserve')
        receipt = helper.run_owned(worker, ['--source-sha256', packet['worker_sha256'],
            '--contract-sha256', packet['contract_sha256']], OWNED,
            expected_worker_sha256=packet['worker_sha256'], approval_reference=args.approval_reference,
            max_seconds=min(177., 180.-elapsed()-3.), cleanup_reserve_seconds=3, max_output_bytes=2*1024**2)
        write(OWNED / 'receipt.json', receipt)
        need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True and receipt['returncode'] == 0
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
             and receipt['errors'] == [], 'actual owned terminal/cleanup Job0')
        artifacts, validation = validate_outputs(contract, receipt)
        after = {name: sha(ROOT / name) for name in expected}
        need(after == before and sha(Path(__file__)) == args.controller_sha256 and sha(PACKET) == args.packet_sha256,
             'all actual inputs/source posthash')
        need(all(sha(OWNED / name) == pin for name, pin in receipt['output_sha256'].items()), 'original actual streams')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc(limit=6)))
    finally:
        try:
            monitor.stop()
        except BaseException as error:
            errors.append(dict(type=type(error).__name__, message=str(error)))
    resources = monitor.result()
    accepted = not errors and not resources['errors'] and resources['monitor_stopped'] and elapsed() < 180
    write(OUT / 'final.json', dict(status='ACCEPTED_CPU09_MATCHED_NATIVE_MASTERY_REPLAY' if accepted else 'REJECTED_KEEP_CPU09_MASTERY_REPLAY',
          errors=errors, elapsed_seconds=elapsed(), whole_cap_seconds=180, owned_receipt=receipt, resources=resources,
          artifacts=artifacts, validation=validation, source_inputs_before=before, source_inputs_after=after,
          packet_sha256=args.packet_sha256, controller_sha256=args.controller_sha256,
          oracle_access_scope='RAW_ORACLE_SCHEMA_NUMERIC_VALIDATION_PRE_PARITY; NO_ORACLE_TO_ESTIMATOR; CLASSIFICATION_ONLY_AFTER_ALL_PARITY',
          actual_pure_receipt_sha256=args.pure_sha256, automatic_retry=False))
    if elapsed() >= 180:
        write(OUT / 'postwrite-rejection.json', dict(elapsed_seconds=elapsed()))
        accepted = False
    print(json.dumps(dict(accepted=accepted, elapsed_seconds=elapsed(), final_sha256=sha(OUT / 'final.json'))))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()


