"""ROOT-only hai episode domain28, whole35/owned30/cleanup3, không matrix."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import hashlib
import json
import math
import os
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'worker_paper1_seeded_domain01.py'
PACKET = PREP/'paper1_seeded_domain01_allocation.json'
OUT = PREP/'paper1-seeded-domain01-outer'
OWNED = PREP/'paper1-seeded-domain01-owned'
INNER = ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    need(elapsed() < 35 and path.stat().st_size <= 2*1024**2, 'whole35 bounded file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    need(path.stat().st_size <= 256*1024 and elapsed() < 35, 'bounded JSON metadata')
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class Monitor:
    def __init__(self, helper, psutil):
        self.helper, self.psutil = helper, psutil
        self.parent = psutil.Process(os.getpid())
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.errors, self.samples, self.child_samples, self.peak, self.minimum_free = [], 0, 0, 0, None

    def sample(self):
        rows = []
        for process in [self.parent, *self.parent.children(recursive=True)]:
            try:
                memory = process.memory_info()
                rows.append(dict(pid=process.pid, create_time=process.create_time(),
                    peak=max(memory.rss, getattr(memory, 'peak_wset', 0))))
            except self.psutil.NoSuchProcess:
                need(process.pid != self.parent.pid, 'parent remains alive')
        need(len(rows) <= 17, 'finite owned family')
        total = sum(row['peak'] for row in rows)
        free = int(self.psutil.virtual_memory().available)
        self.samples += 1
        self.child_samples += int(any(row['pid'] != self.parent.pid for row in rows))
        self.peak = max(self.peak, total)
        self.minimum_free = free if self.minimum_free is None else min(self.minimum_free, free)
        self.journal.write(json.dumps(dict(seconds=elapsed(), family=rows, family_peak_sum=total, free_bytes=free))+'\n')
        self.journal.flush()
        need(self.samples <= 800 and self.journal.tell() <= 512*1024, 'monitor sample/journal limits')
        need(total <= 256*1024**2 and free >= 512*1024**2 and elapsed() < 35, 'actual family256MiB/free512MiB/whole35')

    def loop(self):
        try:
            with (OUT/'memory.jsonl').open('x', encoding='utf-8') as self.journal:
                while not self.stop_event.wait(.05):
                    self.sample()
                self.sample()
        except BaseException as error:
            self.errors.append(dict(type=type(error).__name__, message=str(error)))
            try:
                launch = read(OWNED/'launch.json')
                need(launch['parent']['pid'] == os.getpid() and launch['worker_sha256'] == sha(WORKER)
                     and launch['worker_relative'] == WORKER.relative_to(ROOT).as_posix()
                     and launch['job_name'] == 'KLTN_OWNED_'+launch['nonce'], 'exact owned Job before termination')
                api = self.helper.Kernel()
                handle = api.check(api.k.OpenJobObjectW(0x0004 | 0x0008, False, launch['job_name']))
                try:
                    api.check(api.k.TerminateJobObject(handle, 1))
                finally:
                    api.close(handle)
            except BaseException as cleanup:
                self.errors.append(dict(type=type(cleanup).__name__, message=str(cleanup)))


def validate(packet, result):
    expected = {'reservation.json', 'domain.json', 'draw_manifest.json', 'oracle_initial_profile.json',
        'B1_observable.jsonl', 'B1_oracle.jsonl', 'GA_observable.jsonl', 'GA_oracle.jsonl', 'result.json', 'manifest.json'}
    need({p.name for p in INNER.iterdir()} == expected and all(p.is_file() and not p.is_symlink() for p in INNER.iterdir()),
         'exact ten terminal outputs, no failure or extra file')
    files = {p.name: dict(sha256=sha(p), bytes=p.stat().st_size) for p in INNER.iterdir()}
    need(sum(row['bytes'] for row in files.values()) <= 2*1024**2 and max(row['bytes'] for row in files.values()) <= 256*1024,
         'actual scientific output2MiB/perfile256KiB')
    manifest = read(INNER/'manifest.json')
    need(manifest['status'] == 'COMPLETE_TWO_EPISODE_ENGINEERING'
         and manifest['files'] == {name: row for name, row in files.items() if name != 'manifest.json'}
         and manifest['allocation_sha256'] == sys.argv[1], 'COMPLETE-last output identity')
    need(result['status'] == 'COMPLETED_TWO_PROSPECTIVE_EPISODES_PENDING_OUTER'
         and result['allocation_sha256'] == sys.argv[1]
         and result['source_before'] == result['source_after'] == manifest['source_after'] == packet['pins']
         and result['forbidden'] == [] and result['methods_restored'] is True
         and result['global_rng_unchanged'] is True and result['scientific_modules_absent'] is True
         and result['elapsed_seconds'] < result['worker_cap_seconds'] == 26, 'actual source/scope/worker verdict')
    domain = read(INNER/'domain.json')
    metadata = domain['metadata']
    need(domain['identity'] == result['domain_identity'] == identity(metadata)
         and len(metadata['nodes']) == 28 and len(metadata['baseline_edges']) == 25
         and len(metadata['advanced_edges']) == 31 and metadata['canonical_candidate_pins'] is True, 'actual domain identity')
    profile = read(INNER/'oracle_initial_profile.json')
    draws = read(INNER/'draw_manifest.json')
    need(draws['identity'] == result['draw_identity'] and draws['profile_sha256'] == identity(profile)
         and draws['recipe'] == 'paper1-pdf-keyed-private-random-v1'
         and draws['root_seed'] == 42 and draws['replicate_id'] == 'paper1-rng-smoke01'
         and draws['horizon'] == 500 and profile['persona'] == 'US'
         and profile['bank_sha256'] == identity(metadata['bank_identity'])
         and draws['logical_draw_counts'] == dict(initial_normal_events=28, response_uniform_events=14000)
         and packet['pins'][draws['runtime']['random_source_path']] == draws['runtime']['random_source_sha256'], 'one explicit draw profile/tape/runtime')
    rows_total = 0
    for label, graph, order in (('B1', metadata['baseline_edges'], metadata['baseline_traversal_order']),
                                ('GA', metadata['advanced_edges'], metadata['advanced_traversal_order'])):
        branch = result['branches'][label]
        observable = [json.loads(line) for line in (INNER/(label+'_observable.jsonl')).read_bytes().splitlines()]
        oracle = [json.loads(line) for line in (INNER/(label+'_oracle.jsonl')).read_bytes().splitlines()]
        need(len(observable) == len(oracle) == branch['rows'] and 1 <= branch['rows'] <= 500, 'two bounded complete traces')
        latent = dict(profile['initial_latent'])
        for step, (seen, truth) in enumerate(zip(observable, oracle, strict=True), 1):
            need(seen['step'] == truth['step'] == step and seen['item_id'] == truth['item_id']
                 and seen['concept_id'] == truth['concept_id'] and type(seen['correct']) is int and seen['correct'] in (0, 1),
                 'observable/oracle same event identity')
            need(all(type(value) in (int, float) and math.isfinite(value) for value in
                (seen['probability'], seen['estimated_before'], seen['estimated_after'], truth['probability_true'],
                 truth['latent_before'], truth['latent_after']))
                 and 0 <= seen['probability'] <= 1 and 0 <= truth['probability_true'] <= 1, 'finite probability/readout')
            need(truth['latent_before'] == latent[truth['concept_id']], 'oracle sequence starts from shared initial state')
            latent[truth['concept_id']] = truth['latent_after']
        final_latent = sorted(latent.items())
        core = dict(branch['metadata'], observable=observable, oracle=oracle, final_latent=final_latent)
        need(core['graph_sha256'] == identity(dict(bank=metadata['bank_identity'], chapters=metadata['chapters'],
             edges=graph, traversal_order=order)) and core['profile_sha256'] == draws['profile_sha256']
             and core['horizon'] == 500 and identity(core) == branch['core_identity']
             and identity(final_latent) == branch['final_latent_sha256']
             and branch['identity'] == identity(dict(draws_sha256=draws['identity'], result_sha256=branch['core_identity'])),
             'full lossless core/branch/graph/profile identities')
        need(dict(core['metrics'])['interactions'] == len(observable), 'reported consumed feedback agrees')
        rows_total += len(observable)
    need(set(result['branches']) == {'B1', 'GA'} and result['consumed_feedback'] == rows_total <= 1000, 'only two actual branches')
    calls = result['counters']
    for label, count in dict(controllers=2, worlds=2, episodes=2, prepare=1, random_events=14028,
                             respond=rows_total, observe=rows_total).items():
        need(calls[label] == dict(started=count, returned=count), 'exact actual call counts '+label)
    need(calls['select']['started'] == calls['select']['returned'] and rows_total <= calls['select']['returned'] <= rows_total+2,
         'optional terminal selection checks, no extra episodes')
    return dict(files=files, consumed_feedback=rows_total, branches={k: v['rows'] for k, v in result['branches'].items()},
        acceptance_uses_graph_ranking_or_zero_reentry=False)


def main():
    need(len(sys.argv) == 3 and sys.argv[2].strip(), 'external packet SHA and ROOT approval reference required')
    need(sha(PACKET) == sys.argv[1], 'reviewed packet bytes')
    packet = read(PACKET)
    need(sha(Path(__file__)) == packet['controller_sha256'] and sha(WORKER) == packet['worker_sha256'], 'reviewed entrypoints')
    need(packet['limits'] == dict(whole_seconds=35, owned_seconds=30, cleanup_seconds=3, worker_seconds=26,
         family_rss_bytes=268435456, min_available_ram_bytes=536870912), 'finite original allocation')
    before = {name: sha(Path(name) if Path(name).is_absolute() else ROOT/name) for name in packet['pins']}
    need(before == packet['pins'], 'all exact source/input/runtime pins')
    prerequisite = read(ROOT/packet['accepted_test_receipt'])
    need(prerequisite['status'] == 'ACCEPTED85_PAPER1_CASES_WITH13_SEEDED_CASES'
         and prerequisite['counts'] == dict(tests=85, failures=0, errors=0, skipped=0, scientific_modules_absent=True)
         and prerequisite['source_before'] == prerequisite['source_after']
         and all(packet['pins'][name] == pin for name, pin in prerequisite['source_after'].items()), 'genuine accepted85 prerequisite')
    sys.path.insert(0, str(ROOT/'scripts/research'))
    import windows_owned_worker as helper
    helper.entry()
    for path in (OUT, OWNED, INNER):
        helper.safe(path)
        need(not path.exists(), 'exclusive fresh operation')
    need(packet['output_relative'] == INNER.relative_to(ROOT).as_posix(), 'scientific output path')
    import psutil
    need(sha(Path(psutil.__file__)) == packet['pins'][str(Path(psutil.__file__).resolve())], 'actual pinned psutil origin')
    need(psutil.virtual_memory().available >= 512*1024**2 and elapsed() < 3, 'original freeRAM/prelaunch reserve')
    OUT.mkdir()
    # Chỉ tạo hai parent có vai trò simulator mới sau admission, không sửa run cũ.
    INNER.parent.mkdir(parents=True, exist_ok=True)
    monitor = Monitor(helper, psutil)
    errors, receipt, validation, result = [], None, None, None
    try:
        monitor.thread.start()
        need(not monitor.errors and elapsed() < 3, 'monitor and remaining whole35 reserve')
        receipt = helper.run_owned(WORKER, [sys.argv[1]], OWNED,
            expected_worker_sha256=packet['worker_sha256'], approval_reference=sys.argv[2],
            max_seconds=min(30., 35.-elapsed()-2.), cleanup_reserve_seconds=3, max_output_bytes=65536)
        write((OWNED if OWNED.is_dir() else OUT)/'receipt.json', receipt)
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
             and receipt['actual_worker_in_job_before_GO'] is True, 'genuine owned terminal/cleanup/Job0')
        result = read(INNER/'result.json')
        validation = validate(packet, result)
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error)))
    finally:
        if monitor.thread.ident is not None:
            monitor.stop_event.set()
            monitor.thread.join(timeout=.5)
        if monitor.thread.is_alive():
            errors.append(dict(type='Monitor', message='monitor not stopped'))
    after = {name: sha(Path(name) if Path(name).is_absolute() else ROOT/name) for name in packet['pins']}
    resources = dict(samples=monitor.samples, child_family_samples=monitor.child_samples,
        family_peak_rss_bytes=monitor.peak, minimum_available_ram_bytes=monitor.minimum_free,
        errors=monitor.errors, monitor_stopped=not monitor.thread.is_alive(), cadence_seconds=.05,
        scope='SAMPLED_PARENT_PLUS_LIVE_DESCENDANTS_NOT_HARD_OS_MEMORY_QUOTA')
    accepted = not errors and not monitor.errors and resources['monitor_stopped'] and monitor.child_samples > 0 and before == after and sha(PACKET) == sys.argv[1] and elapsed() < 35
    write(OUT/'final.json', dict(status='ACCEPTED_TWO_PROSPECTIVE_DOMAIN28_EPISODES' if accepted else 'REJECTED_KEEP_PARTIAL_NO_RETRY',
        errors=errors, receipt=receipt, validation=validation, resources=resources, source_before=before, source_after=after,
        allocation_sha256=sys.argv[1], approval_reference=sys.argv[2], elapsed_seconds=elapsed(), whole_cap_seconds=35,
        actual_domain_pilot=True, research_matrix=False, historical_reproduction_claimed=False, new_independent_N=0))
    if elapsed() >= 35:
        accepted = False
        write(OUT/'postwrite-rejection.json', dict(status='REJECTED_AFTER_FINALWRITE', elapsed_seconds=elapsed()))
    print(json.dumps(dict(accepted=accepted, elapsed_seconds=elapsed(), errors=errors)))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
