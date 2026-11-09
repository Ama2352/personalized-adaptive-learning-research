"""Một US prospective, hai continuity branch cùng draws; ROOT duyệt trước chạy."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP/'paper1_seeded_domain01_allocation.json'
OUTPUT = ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01'
NAMES = {'reservation.json', 'domain.json', 'draw_manifest.json', 'oracle_initial_profile.json', 'B1_observable.jsonl',
         'B1_oracle.jsonl', 'GA_observable.jsonl', 'GA_oracle.jsonl', 'result.json', 'manifest.json'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def guard():
    need(elapsed() < 26, 'original worker26 deadline')


def sha(path):
    guard()
    need(path.is_file() and path.stat().st_size <= 2*1024**2, 'bounded regular pinned file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value, *, rows=False):
    guard()
    need(name in NAMES | {'failure.json'}, 'fixed output names')
    raw = b''.join((json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8') for row in value) if rows else (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
    need(len(raw) <= 256*1024, 'per-file output256KiB')
    with (OUTPUT/name).open('xb') as stream:
        need(stream.write(raw) == len(raw), 'complete output write')
        stream.flush()
        os.fsync(stream.fileno())
    need(sha(OUTPUT/name) == hashlib.sha256(raw).hexdigest(), 'durable output SHA')
    guard()


def main():
    sys.path.insert(0, str(ROOT/'scripts/research'))
    import windows_owned_worker as helper
    owner = helper.worker_gate()
    need(len(sys.argv) == 2 and sha(PACKET) == sys.argv[1], 'external reviewed allocation SHA')
    packet = json.loads(PACKET.read_bytes())
    need(sha(Path(__file__)) == packet['worker_sha256'] and packet['output_relative'] == OUTPUT.relative_to(ROOT).as_posix(),
         'exact reviewed worker/output')
    need(packet['draw_request'] == dict(persona='US', function_chapter='Hàm số bậc 2 và đồ thị',
        root_seed=42, replicate_id='paper1-rng-smoke01', horizon=500)
        and packet['call_caps'] == dict(controllers=2, worlds=2, select=1002, observe=1000,
            respond=1000, prepare=1, random_events=14028, episodes=2), 'exact one-profile/two-branch scope')
    before = {name: sha(Path(name) if Path(name).is_absolute() else ROOT/name) for name in packet['pins']}
    need(before == packet['pins'], 'all source/input/runtime pins before allocation')
    need(not OUTPUT.exists() and OUTPUT.parent.is_dir(), 'fresh scientific output, parent prepared by ROOT launcher')
    helper.safe(OUTPUT)
    OUTPUT.mkdir()
    errors, changed, compiled, counters = [], [], [], {}
    forbidden = []
    phase = 'source_loading'

    def audit(event, args):
        if event in ('subprocess.Popen', 'os.system', 'socket.__new__'):
            forbidden.append(event)
            raise PermissionError('no child/network/world outside declared operation')
        if event == 'import' and str(args[0]).split('.')[0] in ('torch', 'numpy', 'pandas'):
            forbidden.append(str(args[0]))
            raise ImportError('scientific framework outside stdlib simulator packet')
        if event == 'open':
            path, mode, flags = args
            if not isinstance(path, (str, bytes, os.PathLike)):
                return
            target = Path(os.fsdecode(path)).absolute()
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writing:
                need(target.parent == OUTPUT and target.name in NAMES | {'failure.json'}, 'exact owned output writes only')
            elif target.is_relative_to(ROOT) and not target.is_relative_to(ROOT/'.venv'):
                allowed = {str((Path(name) if Path(name).is_absolute() else ROOT/name).absolute()) for name in packet['pins']}
                need(str(target) in allowed or target == PACKET or target.parent == OUTPUT,
                     'exact project inputs only, no dataset/cache/PYC')

    sys.addaudithook(audit)
    try:
        import types
        from dataclasses import asdict
        for name, relative, package in packet['compiled_modules']:
            need(name not in sys.modules and sha(ROOT/relative) == packet['pins'][relative], 'fresh pinned real module')
            module = types.ModuleType(name)
            module.__file__ = str(ROOT/relative)
            module.__package__ = name if package else name.rpartition('.')[0]
            if package:
                module.__path__ = [str((ROOT/relative).parent)]
            sys.modules[name] = module
            parent, _, child = name.rpartition('.')
            if parent:
                setattr(sys.modules[parent], child, module)
            exec(compile((ROOT/relative).read_bytes(), str(ROOT/relative), 'exec'), module.__dict__)
            compiled.append(dict(module=name, source=relative, sha256=sha(ROOT/relative)))
        domain_module = sys.modules['knowledge_tracing.paper1_pdf.domain']
        seeded = sys.modules['knowledge_tracing.paper1_pdf.seeded_episode']
        primitive = sys.modules['knowledge_tracing.paper1_pdf.simulator']

        def observe(target, name, label):
            original = getattr(target, name)
            counters[label] = dict(started=0, returned=0)

            def wrapped(*args, **kwargs):
                guard()
                counters[label]['started'] += 1
                need(counters[label]['started'] <= packet['call_caps'][label], 'finite call allocation '+label)
                value = original(*args, **kwargs)
                counters[label]['returned'] += 1
                guard()
                return value

            setattr(target, name, wrapped)
            changed.append((target, name, original, wrapped))

        for cls, name, label in ((primitive.Paper1PdfController, '__init__', 'controllers'),
            (primitive.Paper1PdfLearner, '__init__', 'worlds'),
            (primitive.Paper1PdfController, 'predict_next', 'select'),
            (primitive.Paper1PdfController, 'observe', 'observe'),
            (primitive.Paper1PdfLearner, 'respond', 'respond'),
            (seeded, 'prepare_seeded_draws', 'prepare'), (seeded, '_random_for_event', 'random_events'),
            (seeded, 'run_continuity_episode_seeded', 'episodes')):
            observe(cls, name, label)
        write('reservation.json', dict(status='RESERVED_NOT_ACTUAL_COUNTS', call_caps=packet['call_caps'],
            output_relative=packet['output_relative'], allocation_sha256=sys.argv[1]))
        phase = 'domain'
        domain = domain_module.load_prospective_paper2_domain()
        need(len(domain.nodes) == 28 and len(domain.bank.items) == 84 and len(domain.baseline_edges) == 25
             and len(domain.advanced_edges) == 31 and domain.canonical_candidate_pins, 'actual prospective28/84/25/31')
        write('domain.json', dict(identity=domain.identity, metadata=domain.metadata()))
        phase = 'prepare_once'
        rng_before = seeded.random.getstate()
        draws = seeded.prepare_seeded_draws(domain.bank, chapters=dict(domain.chapters), **packet['draw_request'])
        draw_identity = draws.identity
        need(draws.logical_draw_counts == dict(initial_normal_events=28, response_uniform_events=14000), 'one complete tape')
        write('oracle_initial_profile.json', asdict(draws.profile))
        write('draw_manifest.json', dict(identity=draw_identity, recipe=draws.recipe, root_seed=draws.root_seed,
            replicate_id=draws.replicate_id, horizon=draws.horizon, profile_sha256=draws.profile.identity,
            logical_draw_counts=draws.logical_draw_counts, runtime=asdict(draws.runtime),
            unused_tape_exported=False, global_rng_before_sha256=hashlib.sha256(repr(rng_before).encode()).hexdigest()))
        branches = {}
        for label, edges, order in (('B1', domain.baseline_edges, domain.baseline_traversal_order),
                                    ('GA', domain.advanced_edges, domain.advanced_traversal_order)):
            phase = 'episode_'+label
            episode = seeded.run_continuity_episode_seeded(domain.bank, chapters=dict(domain.chapters),
                edges=edges, traversal_order=order, draws=draws)
            value = episode.result
            need(episode.draws_sha256 == draw_identity == draws.identity and 1 <= len(value.observable) <= 500
                 and len(value.oracle) == len(value.observable), 'same immutable draws, bounded complete traces')
            write(label+'_observable.jsonl', [asdict(row) for row in value.observable], rows=True)
            write(label+'_oracle.jsonl', [asdict(row) for row in value.oracle], rows=True)
            metadata = asdict(value)
            for key in ('observable', 'oracle', 'final_latent'):
                metadata.pop(key)
            branches[label] = dict(identity=episode.identity, core_identity=value.identity, metadata=metadata,
                final_latent_sha256=seeded.identity_hash(value.final_latent), rows=len(value.observable))
        need(seeded.random.getstate() == rng_before, 'global RNG unchanged')
        total = sum(row['rows'] for row in branches.values())
        need(counters['controllers'] == counters['worlds'] == counters['episodes'] == dict(started=2, returned=2)
             and counters['prepare'] == dict(started=1, returned=1)
             and counters['random_events'] == dict(started=14028, returned=14028)
             and counters['respond'] == counters['observe'] == dict(started=total, returned=total)
             and total <= 1000, 'exact two episodes, consumed feedback counters')
    except BaseException as error:
        errors.append(dict(phase=phase, type=type(error).__name__, message=str(error)))
    finally:
        for target, name, original, wrapped in reversed(changed):
            if getattr(target, name) is not wrapped:
                errors.append(dict(phase='restore', message='observer binding changed '+name))
            else:
                setattr(target, name, original)
    after = {name: sha(Path(name) if Path(name).is_absolute() else ROOT/name) for name in packet['pins']}
    if errors:
        write('failure.json', dict(status='REJECTED_KEEP_PARTIAL_NO_RETRY', errors=errors, counters=counters,
            source_before=before, source_after=after, elapsed_seconds=elapsed()))
    need(not errors and not forbidden and before == after and sha(PACKET) == sys.argv[1] and elapsed() < 26,
         'complete operation, restored methods and stable pins '+repr(errors))
    need(not any(name in sys.modules for name in ('torch', 'numpy', 'pandas')), 'no scientific frameworks')
    write('result.json', dict(status='COMPLETED_TWO_PROSPECTIVE_EPISODES_PENDING_OUTER', allocation_sha256=sys.argv[1],
        owner=owner, domain_identity=domain.identity, draw_identity=draw_identity, branches=branches,
        counters=counters, consumed_feedback=total, source_before=before, source_after=after,
        compiled_modules=compiled, forbidden=forbidden, methods_restored=True, global_rng_unchanged=True,
        scientific_modules_absent=True, elapsed_seconds=elapsed(), worker_cap_seconds=26,
        scope_vi='Một US42, hai continuity branches; engineering, chưa matrix hoặc historical reproduction.'))
    existing = {path.name: dict(sha256=sha(path), bytes=path.stat().st_size) for path in OUTPUT.iterdir()}
    need(set(existing) == NAMES-{'manifest.json'}, 'exact nine outputs before COMPLETE manifest')
    write('manifest.json', dict(status='COMPLETE_TWO_EPISODE_ENGINEERING', files=existing,
        allocation_sha256=sys.argv[1], source_after=after))
    guard()


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if OUTPUT.is_dir() and not (OUTPUT/'failure.json').exists():
            write('failure.json', dict(status='REJECTED_KEEP_PARTIAL_NO_RETRY', type=type(error).__name__,
                message=str(error), elapsed_seconds=elapsed()))
        raise
