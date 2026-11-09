"""ROOT-only controller cho cache CPU09, owned57/worker54/whole60."""

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
PACKET = PREP / 'rq2_cached_mechanism_native02_packet.json'
OUT = PREP / 'rq2-cached-mechanism-native02-outer'
OWNED = PREP / 'rq2-cached-mechanism-native02-owned'
INNER = PREP / 'rq2-cache-mechanism-attempt01'


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
        deadline = min(time.perf_counter() + 1., START + 57.)
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
        worker = PREP / 'check_rq2_cached_mechanism_native02.py'
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
                    need(elapsed() < 60, 'whole monitor deadline')
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


def validate_pure(packet):
    pure_path = ROOT / packet['pure']['result_path']
    need(sha(pure_path) == packet['pure']['result_sha256'], 'actual pure16 result SHA')
    pure = read(pure_path)
    need(pure['status'] == 'ACCEPTED_16_SYNTHETIC_RQ2_METHODS_ONLY' and pure['errors'] == []
         and pure['counts'] == dict(tests=16, failures=0, errors=0, skipped=0,
                                    unexpected_successes=0, expected_failures=0)
         and pure['controller_sha256'] == packet['pure']['controller_sha256']
         and pure['packet_sha256'] == packet['pure']['packet_sha256']
         and pure['source_sha256'] == packet['parser_test_contract_sha256']
         and type(pure['elapsed_seconds']) in (int, float) and 0 <= pure['elapsed_seconds'] < 60,
         'actual pure16 source/counts/clock')
    owned = pure['owned_receipt']
    need(owned['accepted'] is True and owned['returncode'] == 0 and owned['cleanup_accepted'] is True
         and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True
         and owned['actual_worker_in_job_before_GO'] is True and owned['errors'] == [], 'pure owned acceptance')
    for name, value in pure['outputs_before_result'].items():
        path = pure_path.parent / name
        need(sha(path) == value['sha256'] and path.stat().st_size == value['bytes'], 'pure emitted artifact')
    owned_dir = PREP / 'rq2-cached-mechanism-pure01-owned'
    for name, expected in owned['output_sha256'].items():
        need(name in ('stdout.log', 'stderr.log') and sha(owned_dir / name) == expected, 'pure original streams')
    need(not (pure_path.parent / 'postwrite-rejection.json').exists(), 'pure late rejection')


def verify_stdlib(packet):
    expected_directory = Path(sys.base_prefix) / 'Lib'
    for name, value in packet['stdlib_preload_sources'].items():
        path = Path(value['path'])
        need(path == expected_directory / name and path.is_file() and not path.is_symlink()
             and path.stat().st_size == value['bytes'] and value['bytes'] <= 262144,
             'reviewed default formatter stdlib origin/size')
        need(hashlib.sha256(path.read_bytes()).hexdigest() == value['sha256'], 'reviewed stdlib source bytes')


def validate_outputs(packet, contract, receipt):
    names = {'reservation.json', 'arm_exposures.json', 'paired_trajectories.json',
             'joined_contrasts.json', 'result.json', 'output-manifest.json'}
    need({p.name for p in INNER.iterdir()} == names, 'exact complete6 outputs; no failure marker')
    artifacts = {name: dict(sha256=sha(INNER / name, 1024**2), bytes=(INNER / name).stat().st_size) for name in names}
    need(sum(v['bytes'] for v in artifacts.values()) <= 16 * 1024**2, 'inner output directory cap')
    manifest = read(INNER / 'output-manifest.json')
    need(set(manifest) == {'outputs'} and manifest['outputs'] == {n: v for n, v in artifacts.items()
                                                               if n != 'output-manifest.json'}, 'all output SHA/size bindings')
    result = read(INNER / 'result.json')
    expected_inputs = {n: v['sha256'] for n, v in contract['inputs'].items()}
    need(result['status'] == 'COMPLETE_CACHED_SECONDARY_ANALYSIS_PENDING_OUTER_ACCEPTANCE'
         and result['source_sha256'] == contract['analysis_source_sha256']
         and result['contract_sha256'] == packet['contract_sha256']
         and result['inputs_before'] == result['inputs_after'] == expected_inputs
         and type(result['elapsed_seconds']) in (int, float) and math.isfinite(result['elapsed_seconds'])
         and 0 <= result['elapsed_seconds'] <= 54 and result['scope'] == contract['scope'], 'parser completion/identity/time')
    for key, value in dict(arms=120, pairs=120, contrasts=30, seed_clusters=10,
                           new_independent_seed_families=0, model_calls=0, world_transitions=0).items():
        need(type(result[key]) is int and result[key] == value, 'parser count: ' + key)
    reservation = read(INNER / 'reservation.json')
    need(reservation['input_hashes'] == expected_inputs and reservation['source_sha256'] == result['source_sha256']
         and reservation['contract_sha256'] == packet['contract_sha256']
         and reservation['owner']['worker'] == receipt['actual_worker'], 'actual parser owned identity')
    seeds, profiles = contract['grid']['seeds'], contract['grid']['profiles']
    arm_keys = {(s, p, g, m) for s in seeds for p in profiles for g in (False, True) for m in (False, True)}
    pair_keys = {(s, p, axis, flag) for s in seeds for p in profiles
                 for axis in ('mechanism', 'policy') for flag in (False, True)}
    arms, pairs, joined = (read(INNER / name) for name in
                          ('arm_exposures.json', 'paired_trajectories.json', 'joined_contrasts.json'))
    need(type(arms) is list and len(arms) == 120 and type(pairs) is list and len(pairs) == 120
         and type(joined) is list and len(joined) == 30, 'emitted row populations')
    arm_map, pair_map = {}, {}
    for row in arms:
        key = row['seed'], row['profile'], row['graph_on'], row['mechanism_on']
        need(type(row['seed']) is int and type(row['profile']) is str
             and type(row['graph_on']) is type(row['mechanism_on']) is bool
             and key in arm_keys and key not in arm_map, 'unique arm key')
        need(all(type(row[n]) is int for n in ('events', 'positive_true_deficit_events', 'root_events',
                                              'nonroot_events', 'served_concepts'))
             and row['events'] == 120 and row['root_events'] + row['nonroot_events'] == 120
             and 0 <= row['root_events'] <= 120 and 0 <= row['positive_true_deficit_events'] <= row['nonroot_events']
             and 1 <= row['served_concepts'] <= 28, 'all14400 event coverage')
        need(all(type(row[n]) in (int, float) and math.isfinite(row[n]) and 0 <= row[n] <= 1
                 for n in ('mean_true_deficit', 'max_true_deficit')), 'true deficit bounds')
        if row['profile'] == 'PG':
            need(row['positive_true_deficit_events'] == row['mean_true_deficit'] == row['max_true_deficit'] == 0,
                 'all PG true deficit negative')
        arm_map[key] = row
    for row in pairs:
        key = row['seed'], row['profile'], row['axis'], row['fixed_other_flag']
        need(type(row['seed']) is int and type(row['profile']) is str and type(row['fixed_other_flag']) is bool
             and key in pair_keys and key not in pair_map, 'unique paired trajectory')
        need(row['orientation'] == 'false_vs_true' and type(row['paired_steps']) is int
             and row['paired_steps'] == 120, 'pair direction/coverage')
        q, y = row['first_query_difference_step'], row['first_label_difference_step']
        need(all(v is None or (type(v) is int and 0 <= v < 120) for v in (q, y)), 'divergence index/null')
        need(all(type(row[n]) is int and 0 <= row[n] <= 120 for n in
                 ('common_query_prefix_steps', 'common_observable_prefix_steps', 'same_query_steps',
                  'different_query_steps', 'different_label_steps'))
             and row['same_query_steps'] + row['different_query_steps'] == 120
             and (row['different_query_steps'] == 0) == (q is None)
             and (row['different_label_steps'] == 0) == (y is None)
             and row['common_query_prefix_steps'] == (120 if q is None else q)
             and row['common_observable_prefix_steps'] == min((v for v in (q, y) if v is not None), default=120),
             'complete divergent/nondivergent pair fields')
        if row['profile'] == 'PG' and row['axis'] == 'mechanism':
            need(q is y is None, 'PG mechanism pair negative')
        pair_map[key] = row
    need(set(arm_map) == arm_keys and set(pair_map) == pair_keys
         and sum(r['events'] for r in arms) == 14400, 'all arms/pairs/events represented')
    source_endpoints = read(ROOT / contract['paths']['outcomes'])
    endpoint_map = {(r['seed'], r['profile'], r['graph_on'], r['prerequisite_mechanism_on']): r['outcome']
                    for r in source_endpoints}
    original_contrasts = {(r['seed'], r['profile']): r for r in read(ROOT / contract['paths']['contrasts'])}
    seen = set()
    for row in joined:
        key = row['seed'], row['profile']
        need(key in original_contrasts and key not in seen, 'all30 joined contrasts')
        seen.add(key)
        for field in ('graph_effect_mechanism_on', 'graph_effect_mechanism_off', 'interaction_contrast'):
            need(type(row[field]) in (int, float) and math.isfinite(row[field])
                 and abs(row[field] - original_contrasts[key][field]) <= 1e-12, 'preserved endpoint contrasts')
        expected_outcomes = [dict(graph_on=g, mechanism_on=m, outcome=endpoint_map[*key, g, m])
                             for g in (False, True) for m in (False, True)]
        need(row['outcomes'] == expected_outcomes
             and row['arm_exposures'] == [arm_map[*key, g, m] for g in (False, True) for m in (False, True)]
             and row['paired_trajectories'] == [pair_map[*key, axis, flag]
                  for axis in ('mechanism', 'policy') for flag in (False, True)], 'joined identities match emitted/source rows')
    return artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--approval-reference', required=True)
    args = parser.parse_args()
    need(sha(PACKET, 65536) == args.packet_sha256 and args.approval_reference.strip(), 'reviewed packet/dispatch reference')
    packet = read(PACKET)
    need(Path.cwd().resolve() == ROOT and Path(sys.prefix).resolve() == ROOT / '.venv', 'fixed repository venv')
    for path in (OUT, OWNED, INNER):
        need(not physical(path).exists(), 'one exclusive attempt; no retry')
    OUT.mkdir()
    errors, before, after, artifacts = [], {}, {}, {}
    receipt = monitor = scope = None
    try:
        for name, pin in packet['source_pins'].items():
            need(sha(ROOT / name) == pin, 'reviewed source bytes')
        validate_pure(packet)
        verify_stdlib(packet)
        for name, pin in packet['prior_attempt']['files_sha256'].items():
            need(sha(ROOT / name) == pin, 'historical01 evidence preserved')
        need(not INNER.exists(), 'frozen contract inner01 never materialized during rejected native01')
        contract = read(PREP / 'rq2_cache_mechanism_contract01.json')
        need(sha(PREP / 'rq2_cache_mechanism_contract01.json') == packet['contract_sha256'], 'frozen analysis contract')
        for name, value in contract['inputs'].items():
            need(sha(ROOT / name, value['bytes']) == value['sha256']
                 and (ROOT / name).stat().st_size == value['bytes'], 'cached input preflight')
            before[name] = value['sha256']
        sys.path.insert(0, str(ROOT / 'scripts/research'))
        import windows_owned_worker as helper
        helper.entry()
        need(not any(n in sys.modules for n in ('knowledge_tracing', 'numpy', 'pandas', 'torch')), 'stdlib/resource-only parent')
        worker = PREP / 'check_rq2_cached_mechanism_native02.py'
        worker_sha = packet['source_pins'][worker.relative_to(ROOT).as_posix()]
        monitor = FamilyMonitor(helper, contract['limits'], worker_sha)
        monitor.journal = (OUT / 'memory-preflight.jsonl').open('x', encoding='utf-8')
        try:
            monitor.sample()
        finally:
            monitor.journal.close()
        write(OUT / 'before.json', dict(packet_sha256=args.packet_sha256, approval_reference=args.approval_reference,
              sources=packet['source_pins'], inputs=before, pure_sha256=packet['pure']['result_sha256'],
              resource_limits=contract['limits']))
        allowance = min(57., 60. - elapsed() - 3.)
        need(math.isfinite(allowance) and allowance > 3, 'finite remaining owned budget')
        monitor.thread.start()
        receipt = helper.run_owned(worker, ['--source-sha256', contract['analysis_source_sha256'],
            '--contract-sha256', packet['contract_sha256'], '--output-name', INNER.name], OWNED,
            expected_worker_sha256=worker_sha, approval_reference=args.approval_reference,
            max_seconds=allowance, cleanup_reserve_seconds=3, max_output_bytes=32768)
        write(OWNED / 'receipt.json', receipt)
        need(receipt['accepted'] is True and receipt['returncode'] == 0
             and receipt['worker_returncode_before_cleanup'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['cleanup_errors'] == []
             and receipt['errors'] == [], 'original owned execution/Job0/cleanup')
        for name, pin in receipt['output_sha256'].items():
            need(name in ('stdout.log', 'stderr.log') and sha(OWNED / name, 32768) == pin, 'original native streams')
        scope = read(OWNED / 'scope.json')
        need(scope['status'] == 'FROZEN_PARSER_MAIN_RETURNED' and scope['original_main_exit_code'] == 0
             and scope['parser_sha256'] == contract['analysis_source_sha256']
             and scope['contract_sha256'] == packet['contract_sha256']
             and scope['bootstrap_process_network_denials'] == []
             and scope['display_override'] == dict(COLUMNS='80', LINES='24')
             and scope['display_environment_restored'] is True
             and scope['error'] is None and scope['denied_events'] == [] and scope['unexpected_heavy_modules'] == [],
             'actual parser main read/import/network scope')
        artifacts = validate_outputs(packet, contract, receipt)
        after = {n: sha(ROOT / n, v['bytes']) for n, v in contract['inputs'].items()}
        need(after == before and all(sha(ROOT / n) == h for n, h in packet['source_pins'].items())
             and sha(PACKET, 65536) == args.packet_sha256, 'all final input/source/packet bytes')
        verify_stdlib(packet)
        need(all(sha(ROOT / n) == h for n, h in packet['prior_attempt']['files_sha256'].items()),
             'historical01 postcheck')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()))
    finally:
        if monitor is not None and monitor.thread.ident is not None:
            try:
                monitor.stop()
            except BaseException as error:
                errors.append(dict(type=type(error).__name__, message=str(error)))
    resources = None if monitor is None else monitor.result()
    if (resources is None or resources['errors'] or not resources['monitor_stopped']
            or resources['child_family_samples'] == 0 or resources['observed_family_peak_rss_bytes'] > 1024**3
            or resources['observed_minimum_available_ram_bytes'] is None
            or resources['observed_minimum_available_ram_bytes'] < 2*1024**3):
        errors.append(dict(type='ResourceVerification', message='live family/original floor not accepted'))
    if not math.isfinite(elapsed()) or elapsed() >= 60:
        errors.append(dict(type='WholeTime', message='whole60 post-validation limit'))
    final = dict(status='ACCEPTED_CACHED_RQ2_SECONDARY_ANALYSIS' if not errors else 'REJECTED_KEEP_CACHED_RQ2_ATTEMPT',
                 errors=errors, elapsed_seconds=elapsed(), whole_cap_seconds=60,
                 packet_sha256=args.packet_sha256, source_before=packet['source_pins'],
                 source_after={n: sha(ROOT / n) for n in packet['source_pins']}, inputs_before=before,
                 inputs_after=after, resources=resources, owned_receipt=receipt, artifacts=artifacts,
                 historical_attempt01=packet['prior_attempt'],
                 namespace_note=packet['namespace_note'],
                 conservative_total_ceiling_seconds=packet['conservative_total_ceiling_seconds'],
                 bootstrap_scope=scope, actual_model_calls=0, new_world_transitions=0,
                 new_independent_seed_families=0, automatic_retry=False)
    write(OUT / 'final.json', final)
    accepted = not errors and elapsed() < 60
    if elapsed() >= 60:
        write(OUT / 'postwrite-rejection.json', dict(status='REJECTED_POSTPUBLICATION_WHOLE60', elapsed_seconds=elapsed()))
        accepted = False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_KEEP_CACHED_RQ2_ATTEMPT',
                         elapsed_seconds=elapsed(), result_sha256=sha(OUT / 'final.json'))))
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
