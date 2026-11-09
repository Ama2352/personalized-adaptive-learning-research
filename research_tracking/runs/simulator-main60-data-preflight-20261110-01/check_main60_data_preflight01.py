"""Kiểm hình học corpus60 đã có, không model hoặc fit."""
import time
START = time.perf_counter()
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import os
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / 'main60-data-preflight01'
CORPUS_ID = 'grade10-development-lifecycle01-20261108'
PUBLIC = ROOT / 'artifacts/simulator/corpora' / CORPUS_ID
FILES = ('corpus.json', 'DONE.json', 'bank.json', 'plan.json', 'train.jsonl',
    'train.manifest.json', 'selection.jsonl', 'selection.manifest.json',
    'calibration.jsonl', 'calibration.manifest.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    assert time.perf_counter() - START < 55, 'Whole55s before finalization'


def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    assert len(raw) < 1024**2
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
assert not OUT.exists()
OUT.mkdir()
before = {name: sha(PUBLIC / name) for name in FILES}
write('reservation.json', dict(public_inputs_sha256=before, whole_cap_seconds=60,
    worker_deadline_seconds=55, role_limits=dict(train=48, selection=6, calibration=6),
    max_events_per_learner=210, model_optimizer_world_calls_permitted=0))
timer = threading.Timer(max(.001, 59 - (time.perf_counter() - START)), lambda: os._exit(124))
timer.daemon = True
timer.start()
denied = []


def audit(event, args):
    if (event == 'import' and str(args[0]).split('.')[0] in ('torch', 'modal', 'boto3', 'pyBKT')) or event.startswith('socket.') or event == 'subprocess.Popen':
        denied.append(event)
        raise RuntimeError('Không model, network hoặc child trong data preflight')
    if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).absolute().resolve()
        if any(path == ROOT / n or path.is_relative_to(ROOT / n) for n in ('dataset', 'artifacts/bkt_baseline', 'venv', '.wsl')):
            denied.append(event)
            raise RuntimeError('Không đọc vùng bảo vệ')


sys.addaudithook(audit)
sys.path.insert(0, str(ROOT / 'src'))
error = None
summary = None
try:
    import psutil
    assert psutil.virtual_memory().available >= 1536 * 1024**2
    from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, read_public_research_corpus
    from knowledge_tracing.akt import research_simulator_data as data
    from knowledge_tracing.akt.research_runner import _phase
    corpus = read_public_research_corpus(CORPUS_ID, expected_corpus_sha256=before['corpus.json'],
        expected_done_sha256=before['DONE.json'], limits=CorpusReadLimits(
            max_file_bytes=2*1024**2, max_total_bytes=4*1024**2, max_line_bytes=256*1024,
            max_trajectories_per_role=48, max_events_per_learner=210,
            max_total_events=12600, max_wall_seconds=25.))
    check()
    roles = {}
    groups = {}
    for role in ('train', 'selection', 'calibration'):
        rows = corpus.role_data(role)
        groups[role] = {t.learner_id for t in rows.trajectories}
        roles[role] = dict(learners=len(rows.trajectories), targets=rows.audit['audit']['targets'],
            class_counts=rows.class_counts, two_class_support=rows.two_class_support,
            item_coverage=len({o.query.item_id for t in rows.trajectories for o in t.observations}))
    assert roles['train']['learners'] == 48 and roles['train']['targets'] == 10080
    assert roles['selection']['learners'] == roles['calibration']['learners'] == 6
    assert roles['selection']['targets'] == roles['calibration']['targets'] == 1260
    assert all(not groups[a] & groups[b] for a,b in [('train','selection'),('train','calibration'),('selection','calibration')])
    train = _phase(data, corpus, 'select_train80')
    selection = _phase(data, corpus, 'raw_selection10')
    encoding = data.fit_research_encoding(train)
    assert len(encoding.support) == 84
    geometry = {}
    for role, phase, training in [('train', train, True), ('selection', selection, False)]:
        counts = Counter()
        targets = set()
        for value in data.iter_research_windows(phase, encoding, context=100, target_block=100, training=training):
            check()
            assert not isinstance(value, data.ResearchUnseenTarget)
            window = value.window if training else value
            counts['windows'] += 1
            counts['input_slots'] += len(window.inputs.item_ids)
            counts['target_slots'] += int(window.target_mask.sum())
            counts['maximum_window_length'] = max(counts['maximum_window_length'], len(window.inputs.item_ids))
            for i in range(len(window.target_mask)):
                if window.target_mask[i]:
                    key = (window.inputs.user_ids[i], int(window.global_ranks[i]), int(window.inputs.source_rows[i]))
                    assert key not in targets, 'Không trùng scored target giữa windows'
                    targets.add(key)
        assert counts['target_slots'] == roles[role]['targets'] == len(targets)
        assert counts['maximum_window_length'] <= 200
        geometry[role] = dict(counts)
    train_concepts = []
    item_to_concept = {item.item_id: item.concept_id for item in corpus.bank.items}
    for trajectory in corpus.role_data('train').trajectories:
        train_concepts.append({item_to_concept[o.query.item_id] for o in trajectory.observations})
    concept_support = {concept: sum(concept in values for values in train_concepts) for concept in sorted(set(item_to_concept.values()))}
    corpus.assert_integrity()
    check()
    info = psutil.Process().memory_info()
    assert info.rss <= 512*1024**2
    summary = dict(status='PUBLIC_CORPUS_DATA_GEOMETRY_VERIFIED_NO_MODEL', corpus_id=CORPUS_ID,
        roles=roles, learner_disjoint=True, train_vocabulary_items=len(encoding.support),
        geometry=geometry, train_concept_learner_support=concept_support,
        planned_AKT_train_batches_per_epoch=math.ceil(geometry['train']['windows']/4),
        planned_AKT_max20_optimized_targets=20*roles['train']['targets'],
        planned_SAKT_terminal_batches_per_epoch=math.ceil(roles['train']['targets']/128),
        planned_SAKT_max50_optimized_targets=50*roles['train']['targets'],
        planned_GKT_whole_trajectory_batches_per_epoch=math.ceil(roles['train']['learners']/4),
        runtime_or_GPU_throughput_measured=False, current_worker_rss_bytes=info.rss,
        actual_public_reader_seconds=corpus.elapsed_seconds, actual_model_world_optimizer_calls=0,
        scope_vi='Kiểm dữ liệu corpus đã có, không cấp quyền main training/refit/calibration hoặc claim learning benefit.')
except BaseException as caught:
    error = dict(type=type(caught).__name__, message=str(caught))
finally:
    after = {name: sha(PUBLIC / name) for name in FILES}
    accepted = error is None and before == after and not denied and 'torch' not in sys.modules
    write('result.json', dict(accepted=accepted, error=error, denied=denied,
        input_before=before, input_after=after, summary=summary,
        elapsed_seconds=time.perf_counter()-START))
    check()
    timer.cancel()
print(json.dumps(dict(accepted=accepted, error=error)))
raise SystemExit(0 if accepted else 1)
