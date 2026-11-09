"""ROOT-only response reliability, reuse owned57/worker54/whole60 monitor."""

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
PACKET = PREP / 'rq1_response_reliability_native01_packet.json'
OUT = PREP / 'rq1-response-reliability-native01-outer'
OWNED = PREP / 'rq1-response-reliability-native01-owned'
INNER = PREP / 'rq1-response-reliability-attempt01'


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
        worker = PREP / 'check_rq1_response_reliability_native01.py'
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
    need(sha(pure_path) == packet['pure']['result_sha256'], 'actual pure7 receipt')
    pure = read(pure_path)
    need(pure['status'] == 'ACCEPTED_7_RESPONSE_RELIABILITY_PURE_METHODS' and pure['errors'] == []
         and pure['counts'] == dict(tests=7, failures=0, errors=0, skipped=0,
                                    unexpected_successes=0, expected_failures=0)
         and pure['source_sha256'] == packet['parser_test_contract_sha256']
         and pure['controller_sha256'] == packet['pure']['controller_sha256']
         and pure['packet_sha256'] == packet['pure']['packet_sha256']
         and 0 <= pure['elapsed_seconds'] < 30, 'actual7 sources/counts/time')
    child, owned = pure['worker_result'], pure['owned_receipt']
    need(child['status'] == 'ACCEPTED_RESPONSE7_PENDING_OUTER'
         and child['calls'] == dict(response_bins=75, grouped_reliability=2, main=0)
         and len(child['subtests']) == 31 and all(r['error_type'] is None for r in child['subtests'])
         and child['source_after'] == packet['parser_test_contract_sha256']
         and child['methods_restored'] is True and child['monitor_stopped'] is True
         and child['cached_file_opens'] == 0
         and child['errors'] == child['forbidden'] == child['heavy_modules'] == child['resource_errors'] == [],
         'actual pure bodies/subtests/scope')
    need(owned['accepted'] is True and owned['returncode'] == 0 and owned['cleanup_accepted'] is True
         and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True
         and owned['errors'] == [], 'pure owned acceptance')
    for name, value in owned['output_sha256'].items():
        need(name in ('stdout.log', 'stderr.log') and sha(PREP / 'rq1-response-reliability-pure01-owned' / name) == value,
             'original pure streams')
    need(not (pure_path.parent / 'postwrite-rejection.json').exists(), 'no pure late rejection')

def verify_stdlib(packet):
    expected_directory = Path(sys.base_prefix) / 'Lib'
    for name, value in packet['stdlib_preload_sources'].items():
        path = Path(value['path'])
        need(path == expected_directory / name and path.is_file() and not path.is_symlink()
             and path.stat().st_size == value['bytes'] and value['bytes'] <= 262144,
             'reviewed default formatter stdlib origin/size')
        need(hashlib.sha256(path.read_bytes()).hexdigest() == value['sha256'], 'reviewed stdlib source bytes')


def validate_outputs(packet, contract, base, receipt):
    names = {'reservation.json', 'reliability.json', 'result.json', 'output-manifest.json'}
    need({p.name for p in INNER.iterdir()} == names, 'exact complete4 outputs')
    artifacts = {n: dict(sha256=sha(INNER / n, 2*1024**2), bytes=(INNER / n).stat().st_size) for n in names}
    need(sum(v['bytes'] for v in artifacts.values()) <= 4*1024**2, 'output directory cap')
    manifest = read(INNER / 'output-manifest.json')
    need(set(manifest) == {'outputs'} and manifest['outputs'] == {n: v for n, v in artifacts.items()
          if n != 'output-manifest.json'}, 'all output hashes/sizes')
    result = read(INNER / 'result.json')
    expected_inputs = {n: v['sha256'] for n, v in base['inputs'].items()}
    need(result['status'] == 'COMPLETE_RESPONSE_RELIABILITY_PENDING_OUTER_ACCEPTANCE'
         and result['source_sha256'] == contract['analysis_source_sha256']
         and result['contract_sha256'] == packet['contract_sha256']
         and result['accepted_cache_receipt_sha256'] == packet['accepted_cache_receipt_sha256']
         and result['inputs_before'] == result['inputs_after'] == expected_inputs
         and result['source_before'] == result['source_after'] == packet['analysis_source_map']
         and type(result['elapsed_seconds']) in (int, float) and math.isfinite(result['elapsed_seconds'])
         and 0 <= result['elapsed_seconds'] <= 54 and result['scope'] == contract['scope'], 'actual completion/identity/time')
    for key, value in dict(worlds=120, trace_rows=14400, groups=136, bins=2040, repeated_group_row_uses=43200,
            seed_clusters_reused=10, new_independent_seed_families=0, actual_model_calls=0, new_world_transitions=0).items():
        need(type(result[key]) is int and result[key] == value, 'actual population:'+key)
    need(result['scalar_ece_additivity_claimed'] is False, 'absolute ECEs remain separate')
    reservation = read(INNER / 'reservation.json')
    need(reservation['inputs_before'] == expected_inputs and reservation['owner']['worker'] == receipt['actual_worker']
         and reservation['source_before'] == packet['analysis_source_map'], 'actual owned/source reservation')
    data = read(INNER / 'reliability.json', 2*1024**2)
    need(data['target'] == 'ACTUAL_ITEM_NEXT_RESPONSE_CORRECTNESS'
         and data['oracle_role'] == 'POSTHOC_EVALUATOR_ONLY' and data['native_mastery_truth_evaluated'] is False
         and data['response_temperature_fitted'] is False and data['bin_rule'] == contract['bin_rule'], 'response-only semantics')
    seeds, profiles = base['grid']['seeds'], base['grid']['profiles']
    expected = {('world',s,p,g,m) for s in seeds for p in profiles for g in (False,True) for m in (False,True)}
    expected |= {('persona_arm',None,p,g,m) for p in profiles for g in (False,True) for m in (False,True)}
    expected |= {('arm',None,None,g,m) for g in (False,True) for m in (False,True)}
    groups = data['groups']; need(type(groups) is list and len(groups)==136, 'all136 groups')
    table = {}
    fields = ('mean_prediction','mean_correct','mean_oracle_probability')
    gaps = ('empirical_signed_gap','oracle_signed_gap','realized_response_residual')
    for group in groups:
        key = tuple(group[n] for n in ('level','seed','profile','graph_on','mechanism_on'))
        need(key in expected and key not in table and type(group['graph_on']) is type(group['mechanism_on']) is bool,
             'unique full group identity')
        if group['level']=='world': need(type(group['seed']) is int, 'integer worldseed')
        n = {'world':120,'persona_arm':1200,'arm':3600}[group['level']]
        need(type(group['rows']) is int and group['rows']==n and len(group['bins'])==15
             and group['scalar_ece_decomposition_claimed'] is False, 'group coverage/semantics')
        for index, row in enumerate(group['bins']):
            need(set(row)=={'bin_index','left','right','right_inclusive','rows',*fields,*gaps}
                 and type(row['bin_index']) is int and row['bin_index']==index
                 and row['left']==index/15 and row['right']==(index+1)/15
                 and type(row['right_inclusive']) is bool and row['right_inclusive']==(index==14)
                 and type(row['rows']) is int and 0<=row['rows']<=n, 'exact15bin edges/counts')
            if row['rows']==0:
                need(all(row[f] is None for f in (*fields,*gaps)), 'empty-bin nulls')
            else:
                need(all(type(row[f]) in (int,float) and math.isfinite(row[f]) and 0<=row[f]<=1 for f in fields)
                     and all(type(row[f]) in (int,float) and math.isfinite(row[f]) and -1<=row[f]<=1 for f in gaps), 'finite nonempty means/gaps')
                p,y,o = (row[f] for f in fields)
                need(abs(row['empirical_signed_gap']-(p-y))<=1e-12
                     and abs(row['oracle_signed_gap']-(p-o))<=1e-12
                     and abs(row['realized_response_residual']-(o-y))<=1e-12
                     and abs(row['empirical_signed_gap']-row['oracle_signed_gap']-row['realized_response_residual'])<=1e-12,
                     'independent signed bin identity')
        need(sum(r['rows'] for r in group['bins'])==n,'all group rows assigned')
        for metric, gap in (('ordinary_ece15','empirical_signed_gap'),('oracle_response_ece15','oracle_signed_gap')):
            value = group[metric]
            independently = math.fsum(r['rows']/n*abs(r[gap]) for r in group['bins'] if r['rows'])
            need(type(value) in (int,float) and math.isfinite(value) and 0<=value<=1
                 and abs(value-independently)<=1e-12, 'independent '+metric)
        table[key] = group
    need(set(table)==expected, 'all120+12+4 identifiers')
    for key,parent in table.items():
        if key[0]=='world': continue
        selected = [v for k,v in table.items() if k[0]=='world' and k[3:]==key[3:]
                    and (key[0]=='arm' or k[2]==key[2])]
        need(len(selected)==(10 if key[0]=='persona_arm' else 30), 'hierarchical world membership')
        for index, row in enumerate(parent['bins']):
            children = [g['bins'][index] for g in selected]
            total = sum(c['rows'] for c in children)
            need(total==row['rows'], 'pooled per-bin count from worlds')
            if total:
                for field in fields:
                    independently = math.fsum(c['rows']*c[field] for c in children if c['rows'])/total
                    need(abs(row[field]-independently)<=1e-12,'pooled mean from world sums')
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
        contract = read(PREP / 'rq1_response_reliability_contract01.json')
        base = read(PREP / 'rq2_cache_mechanism_contract01.json')
        need(sha(PREP / 'rq1_response_reliability_contract01.json') == packet['contract_sha256'], 'frozen analysis contract')
        need(sha(PREP / 'rq2-cached-mechanism-native02-outer/final.json') == packet['accepted_cache_receipt_sha256'],
             'accepted original cache admission')
        for name, value in base['inputs'].items():
            need(sha(ROOT / name, value['bytes']) == value['sha256']
                 and (ROOT / name).stat().st_size == value['bytes'], 'cached input preflight')
            before[name] = value['sha256']
        sys.path.insert(0, str(ROOT / 'scripts/research'))
        import windows_owned_worker as helper
        helper.entry()
        need(not any(n in sys.modules for n in ('knowledge_tracing', 'numpy', 'pandas', 'torch')), 'stdlib/resource-only parent')
        worker = PREP / 'check_rq1_response_reliability_native01.py'
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
        need(scope['status'] == 'RESPONSE_RELIABILITY_MAIN_RETURNED' and scope['original_main_exit_code'] == 0
             and scope['parser_sha256'] == contract['analysis_source_sha256']
             and scope['contract_sha256'] == packet['contract_sha256']
             and scope['bootstrap_process_network_denials'] == []
             and scope['display_override'] == dict(COLUMNS='80', LINES='24')
             and scope['display_environment_restored'] is True
             and scope['error'] is None and scope['denied_events'] == [] and scope['unexpected_heavy_modules'] == [],
             'actual parser main read/import/network scope')
        artifacts = validate_outputs(packet, contract, base, receipt)
        after = {n: sha(ROOT / n, v['bytes']) for n, v in base['inputs'].items()}
        need(after == before and all(sha(ROOT / n) == h for n, h in packet['source_pins'].items())
             and sha(PACKET, 65536) == args.packet_sha256, 'all final input/source/packet bytes')
        verify_stdlib(packet)
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
    final = dict(status='ACCEPTED_CACHED_RQ1_RESPONSE_RELIABILITY' if not errors else 'REJECTED_RESPONSE_RELIABILITY_ATTEMPT',
                 errors=errors, elapsed_seconds=elapsed(), whole_cap_seconds=60,
                 packet_sha256=args.packet_sha256, source_before=packet['source_pins'],
                 source_after={n: sha(ROOT / n) for n in packet['source_pins']}, inputs_before=before,
                 inputs_after=after, resources=resources, owned_receipt=receipt, artifacts=artifacts,
                 accepted_base_cache_sha256=packet['accepted_cache_receipt_sha256'],
                 bootstrap_scope=scope, actual_model_calls=0, new_world_transitions=0,
                 new_independent_seed_families=0, automatic_retry=False)
    write(OUT / 'final.json', final)
    accepted = not errors and elapsed() < 60
    if elapsed() >= 60:
        write(OUT / 'postwrite-rejection.json', dict(status='REJECTED_POSTPUBLICATION_WHOLE60', elapsed_seconds=elapsed()))
        accepted = False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_RESPONSE_RELIABILITY_ATTEMPT',
                         elapsed_seconds=elapsed(), result_sha256=sha(OUT / 'final.json'))))
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
