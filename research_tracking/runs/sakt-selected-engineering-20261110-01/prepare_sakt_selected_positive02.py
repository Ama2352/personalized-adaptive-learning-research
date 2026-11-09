"""Dry metadata thật cho SAKT engineering8/1/1; không ghi quyền hoặc chạy NN."""
import time
PERF, WALL = time.perf_counter, time.time
START, START_WALL = PERF(), WALL()
import argparse
from dataclasses import asdict
import hashlib
from importlib.util import source_from_cache
import json
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP/'sakt_selected_positive02_packet.json'
OUT = PREP/'sakt-selected-positive-package02'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def elapsed():
    return max(PERF()-START, WALL()-START_WALL)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    need(len(raw) <= 2**20, 'bounded dry metadata')
    with (OUT/name).open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def main():
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate, safe
    owner = worker_gate()
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet-sha256', required=True)
    args = parser.parse_args()
    need(sha(safe(PACKET)) == args.packet_sha256, 'Root reviewed external packet SHA')
    packet = json.loads(PACKET.read_bytes()); pins = packet['source_pins']; inputs = packet['input_pins']
    runtime = packet['runtime_pins']
    need(not OUT.exists() and not (ROOT/packet['future_result']).exists()
         and not (ROOT/packet['future_authorization']).exists(), 'exclusive dry and future execution namespaces')
    OUT.mkdir()
    before = {n: sha(safe(ROOT/n)) for n in pins}
    inputs_before = {n: sha(safe(ROOT/n)) for n in inputs}
    runtime_before = {n: sha(Path(n)) for n in runtime}
    need(before == pins and inputs_before == inputs and runtime_before == runtime, 'actual frozen source/input/runtime bytes')
    need(Path(sys.prefix).resolve() == ROOT/'.venv' and sys.dont_write_bytecode, 'repository .venv source-only profile')
    timer = threading.Timer(max(.001, 50.-elapsed()), lambda: os._exit(124))
    timer.daemon = True; timer.start()
    sys.path[:0] = [str(ROOT), str(ROOT/'src')]
    import psutil
    process = psutil.Process()
    resources = dict(samples=0, peak_worker_rss_bytes=0, minimum_available_ram_bytes=None)
    blocked = {'torch','numpy','pandas','scipy','sklearn','modal','boto3'}
    denied = []; error = None; proposal = None
    allowed = {(ROOT/n).resolve() for n in (*pins, *inputs)}|{PACKET.resolve()}
    runtime_roots = (ROOT/'.venv', Path(sys.base_prefix).resolve())

    def check():
        need(elapsed() < 50., 'one cumulative metadata worker50s')
        sample = process.memory_info(); free = int(psutil.virtual_memory().available)
        resources['samples'] += 1
        resources['peak_worker_rss_bytes'] = max(resources['peak_worker_rss_bytes'], sample.rss, getattr(sample,'peak_wset',0))
        previous = resources['minimum_available_ram_bytes']
        resources['minimum_available_ram_bytes'] = free if previous is None else min(previous, free)
        need(resources['peak_worker_rss_bytes'] <= 256*2**20 and free >= 2**30, 'metadata worker RSS/free guard')

    def reject(kind, details):
        if len(denied) < 8:
            denied.append(dict(operation=kind, details=details))
        raise RuntimeError('dry metadata operation outside exact source/input/output scope')

    def audit(kind, values):
        if kind == 'import' and str(values[0]).split('.')[0] in blocked:
            reject(kind, str(values[0]))
        if kind == 'subprocess.Popen' or kind.startswith('socket.') or kind == 'os.system' or kind.startswith('os.spawn'):
            reject(kind, 'no processes/network/framework in dry builder')
        if kind == 'open' and values and not isinstance(values[0], int):
            name = os.fsdecode(values[0]); mode = values[1] or ''; flags = values[2] if type(values[2]) is int else 0
            path = Path(name).absolute().resolve()
            writing = any(c in mode for c in 'wax+') or bool(flags & (os.O_WRONLY|os.O_RDWR))
            if writing:
                if not path.is_relative_to(OUT): reject(kind, dict(path=str(path), mode=mode, flags=flags))
            else:
                # Existing standard import-cache mapping, never a project-root allowlist.
                source = None
                if path.suffix == '.pyc':
                    try: source = Path(source_from_cache(str(path))).resolve()
                    except ValueError: pass
                if path not in allowed and source not in allowed and not path.is_relative_to(OUT) and not any(path.is_relative_to(r) for r in runtime_roots):
                    reject(kind, dict(path=str(path), mode=mode, flags=flags))
        if kind in ('os.mkdir','os.remove','os.rmdir','os.rename'):
            paths = values[:2] if kind == 'os.rename' else values[:1]
            if not all(Path(v).absolute().resolve().is_relative_to(OUT) for v in paths): reject(kind, 'mutation outside own metadata directory')
        if kind in ('os.link','os.symlink'): reject(kind, 'links forbidden')
    sys.addaudithook(audit)
    try:
        check(); need(not blocked.intersection(sys.modules), 'cold metadata without scientific libraries')
        from knowledge_tracing.sakt import research_execution as execution
        from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, read_public_research_corpus
        from knowledge_tracing.research_admission import MainSelectionContext
        from knowledge_tracing.simulator_bridge import identity_hash
        metadata34 = json.loads((ROOT/packet['metadata34_file']).read_bytes())
        need(metadata34['status'] == 'ACCEPTED_34_SAKT_SELECTED_METADATA_NOT_NATIVE' and metadata34['errors'] == []
             and metadata34['child_result']['counts'] == dict(tests=34,failures=0,errors=0,skipped=0)
             and metadata34['owned_receipt']['accepted'] is True and metadata34['owned_receipt']['job_active_after_cleanup'] == 0,
             'actual accepted SAKT normal-entry metadata34 prerequisite')
        for name in ('src/knowledge_tracing/sakt/research_execution.py','src/knowledge_tracing/sakt/research_runner.py',
                     'tests/sakt/test_research_selected_runner.py'):
            need(metadata34['source_before'][name] == metadata34['source_after'][name] == pins[name], 'current own producer/test proof bytes')
        limits = CorpusReadLimits(**packet['read_limits'])
        corpus = read_public_research_corpus(packet['corpus_id'], expected_corpus_sha256=packet['corpus_sha256'],
            expected_done_sha256=packet['done_sha256'], limits=limits)
        counts = {}
        for role in ('train','selection','calibration'):
            data = corpus.role_data(role)
            counts[role] = dict(learners=len(data.trajectories), targets=data.audit['audit']['targets'])
        need(counts == dict(train=dict(learners=8,targets=672), selection=dict(learners=1,targets=84),
            calibration=dict(learners=1,targets=84)), 'same published engineering8/1/1 corpus')
        context = MainSelectionContext('grade10_simulator', packet['protocol21_sha256'], packet['recipe26_sha256'],
            packet['allocation_sha256'], identity_hash(corpus.bank.identity), packet['bank_sha256'], corpus.plan.identity,
            corpus.role_data('train').audit['audit']['shard_sha256'], corpus.role_data('selection').audit['audit']['shard_sha256'])
        source_names = set(execution.SOURCE_NAMES)
        source_names.update(n for n in pins if n.startswith('src/knowledge_tracing/sakt/') and n.endswith('.py'))
        expected_sources = tuple(sorted((n,pins[n]) for n in source_names))
        spec = execution.SAKTSelectedExecutionSpec(packet['run_id'], context, execution.SAKTSelectedRecipe(),
            packet['corpus_id'], packet['corpus_sha256'], packet['done_sha256'], json.dumps(asdict(limits),sort_keys=True),
            expected_sources, execution.SAKTSelectedBudget(**packet['selected_budget']))
        wire = packet['evidence']
        components = tuple(execution.SAKTComponentAcceptance(c['kind'], **{k:execution.FilePin(**c[k])
            for k in ('outer','child','owned')}) for c in wire['components'])
        evidence = execution.SAKTSelectedEvidence(**{k:execution.FilePin(**wire[k]) for k in ('runtime','gate_pointer','lock')},
            components=components, runtime_files=tuple(execution.FilePin(**pin) for pin in wire['runtime_files']))
        # The real factory is inspection only. It cannot issue an execution token.
        identity = execution.prepare_sakt_selected_identity(spec, evidence)
        # Public reader already performed its internal _Read.verify_after().
        corpus.assert_integrity(); check()
        need(not blocked.intersection(sys.modules), 'no lazy model import during genuine inspection')
        proposal = dict(status='GENUINE_SAKT_DRY_IDENTITY_NOT_EXECUTION_AUTHORITY', specification=asdict(spec),
            evidence=asdict(evidence), actual_identity=identity, actual_role_counts=counts,
            future_authorization_file=packet['future_authorization'], future_result=packet['future_result'],
            requested_phases=list(execution.PHASES), selected_spec_sha256=spec.identity,
            explicit_root_review_and_materialization_required=True, oracle_opened=False,
            actual_model_or_optimizer_constructed=False, source_dependent=True,
            metadata34_sha256=inputs[packet['metadata34_file']])
        write('proposal.json', proposal)
    except BaseException as caught:
        error = dict(type=type(caught).__name__, message=str(caught))
    finally:
        after = {n:sha(ROOT/n) for n in pins}; inputs_after = {n:sha(ROOT/n) for n in inputs}
        runtime_after = {n:sha(Path(n)) for n in runtime}
        cold = not blocked.intersection(sys.modules)
        accepted = error is None and not denied and before == after and inputs_before == inputs_after and runtime_before == runtime_after and cold and elapsed() < 50.
        write('result.json', dict(status='ACCEPTED_SAKT_GENUINE_DRY_PENDING_OUTER_NOT_NN' if accepted else 'REJECTED_SAKT_DRY_KEEP_ALL',
            accepted=accepted, error=error, denied=denied, source_before=before, source_after=after,
            input_before=inputs_before, input_after=inputs_after, runtime_before=runtime_before, runtime_after=runtime_after,
            scientific_modules_absent=cold, packet_sha256=args.packet_sha256, resources=resources,
            elapsed_seconds=elapsed(), model_calls=0, authorization_written=False, owner_gate=owner['status'],
            proposal_sha256=None if proposal is None else sha(OUT/'proposal.json')))
        if elapsed() >= 50.:
            write('postwrite_rejection.json',dict(reason='same metadata deadline after publication')); accepted=False
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
