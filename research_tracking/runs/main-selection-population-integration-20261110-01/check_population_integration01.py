"""Kiểm helper canonical và quần thể selection thật, không mô hình hoặc lựa chọn."""
from pathlib import Path
from dataclasses import asdict
import csv
import hashlib
import io
import json
import os
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / 'main-selection-population-integration01'
START = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
OUT.mkdir(exist_ok=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard():
    assert time.perf_counter() - START < 18, 'Whole worker18s'


def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    assert len(raw) <= 2**20
    with (OUT / name).open('xb') as stream:
        stream.write(raw)


blocked = {'torch', 'numpy', 'pandas', 'scipy', 'sklearn', 'modal', 'boto3', 'pyBKT'}
denied = []


def audit(event, values):
    if (event == 'import' and str(values[0]).split('.')[0] in blocked
            or event == 'subprocess.Popen' or event.startswith('socket.')):
        denied.append(event)
        raise RuntimeError('Không model, scientific runtime, subprocess hoặc mạng')
    if event == 'open' and values and isinstance(values[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(values[0])).absolute().resolve()
        if any(path == ROOT / name or path.is_relative_to(ROOT / name)
               for name in ['dataset', 'artifacts/bkt_baseline', 'venv', '.wsl']):
            raise RuntimeError('Vùng bảo vệ không thuộc phép kiểm')
        mode = values[1] or ''
        flags = values[2] if type(values[2]) is int else 0
        if any(char in mode for char in 'wax+') or flags & (os.O_WRONLY | os.O_RDWR):
            assert path.is_relative_to(OUT), 'Chỉ ghi output riêng'


sys.addaudithook(audit)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing import research_admission as admission
from knowledge_tracing.research_population import PopulationLimits, prepare_selection_population
from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, read_public_research_corpus, PUBLIC_FILES
from knowledge_tracing.simulator_bridge import identity_hash
from knowledge_tracing.akt.authorization import gate2_build_hashes

source_before = gate2_build_hashes()
assert len(source_before) == 185
suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests/shared_kt'), pattern='test_research_population.py')
assert suite.countTestCases() == 6
tests = unittest.TextTestRunner(verbosity=2).run(suite)
assert tests.wasSuccessful() and not tests.skipped
inputs = {}
results = {}
for corpus_id, expected_learners, expected_targets, cap_events, cap_total in [
    ('grade10-development-lifecycle01-20261108', 6, 1260, 210, 12600),
    ('grade10-main-lifecycle-engineering10x84-20261109-01', 1, 84, 84, 840),
]:
    guard()
    directory = ROOT / 'artifacts/simulator/corpora' / corpus_id
    pins = {name: sha(directory / name) for name in (*PUBLIC_FILES, 'DONE.json')}
    inputs.update({(directory / name).relative_to(ROOT).as_posix(): digest for name, digest in pins.items()})
    corpus = read_public_research_corpus(corpus_id, expected_corpus_sha256=pins['corpus.json'],
        expected_done_sha256=pins['DONE.json'], limits=CorpusReadLimits(
            max_file_bytes=16 * 2**20, max_total_bytes=32 * 2**20, max_line_bytes=262144,
            max_learners_per_role=48, max_events_per_learner=cap_events,
            max_total_events=cap_total, max_wall_seconds=8.))
    role = corpus.role_data('selection')
    context = admission.MainSelectionContext('grade10_simulator', admission.PROTOCOL21, admission.RECIPE26,
        admission.ALLOCATION, identity_hash(corpus.bank.identity), pins['bank.json'], corpus.plan.identity,
        corpus.role_data('train').audit['audit']['shard_sha256'], role.audit['audit']['shard_sha256'])
    population = prepare_selection_population(role, context,
        expected_provenance_sha256=role.provenance.identity,
        expected_audit_receipt_sha256=role.audit['receipt_sha256'],
        limits=PopulationLimits(6, 1260, 210, 2**20, 3.))
    assert population.expectation.full_targets == expected_targets
    assert len(population.learner_target_counts) == expected_learners
    assert sum(population.class_counts) == expected_targets
    corpus.assert_integrity()
    assert {name: sha(directory / name) for name in pins} == pins
    results[corpus_id] = asdict(population)
    write(corpus_id + '.json', asdict(population))

# So độc lập với full84 target export của actual A0 đã nghiệm thu.
native = ROOT / 'experiments/akt/results/main-a0-graph29-continuous-engineering10x84-20261110-01'
claim_file = native / 'selected-claim.json'
target_file = native / 'selection/targets.csv'
claim = json.loads(claim_file.read_bytes())
assert sha(target_file) == claim['targets']['sha256']
inputs.update({file.relative_to(ROOT).as_posix(): sha(file) for file in [claim_file, target_file]})
rows = []
with target_file.open(encoding='utf-8', newline='') as stream:
    for row in csv.DictReader(stream):
        key = admission.ModelNeutralKey(row['learner_id'], row['item_id'], int(row['timestamp']),
            int(row['source_row']), int(row['global_rank']), row['history_hash_scheme'],
            row['history_sha256'], row['origin_role'])
        rows.append((key, int(row['correct'])))
rows.sort(key=lambda row: row[0])
assert len(rows) == 84
keys_hash = hashlib.sha256(b''.join(admission._canonical(key.values()) for key, _ in rows)).hexdigest()
labels_hash = hashlib.sha256(b''.join(admission._canonical((key.values(), label)) for key, label in rows)).hexdigest()
expectation = results['grade10-main-lifecycle-engineering10x84-20261109-01']['expectation']
assert keys_hash == expectation['full_keys_sha256'] and labels_hash == expectation['full_keys_labels_sha256']
guard()
assert gate2_build_hashes() == source_before and all(sha(ROOT / path) == digest for path, digest in inputs.items())
assert not blocked.intersection(sys.modules) and not denied
write('result.json', dict(status='ACCEPTED_CANONICAL_SELECTION_POPULATION_ONLY',
    actual_tests=6, failures=0, errors=0, skipped=0, source_before=source_before, source_after=source_before,
    inputs_sha256=inputs, populations=results, engineering_export_keys_labels_match=84,
    source_build_files=185, previous_gate183_requires_refresh=True, scientific_modules=[],
    actual_model_calls=0, actual_selection_performed=False, refit_authorized=False,
    elapsed_seconds=time.perf_counter() - START))
print('PASS six canonical tests, actualMain1260/sixlearners and engineering84/fullA0export hashes match; no model/selection.')
